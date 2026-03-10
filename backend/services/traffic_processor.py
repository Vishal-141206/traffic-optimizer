"""
Traffic Processor Service

Coordinates video processing, vehicle detection, density calculation,
and database storage.
"""

import os
import asyncio
import cv2
from typing import AsyncGenerator, Optional, Dict, List
from datetime import datetime
import uuid

from core.config import settings
from vision.vehicle_detection import VehicleDetector, Detection
from vision.traffic_density import TrafficDensityCalculator, CongestionLevel
from vision.emergency_detection import EmergencyVehicleDetector


class TrafficProcessor:
    """
    Main traffic processing service.
    
    Processes video frames, detects vehicles, calculates density,
    and generates metrics for the dashboard.
    """
    
    def __init__(self):
        """Initialize the traffic processor."""
        # Initialize detection components
        self.vehicle_detector = VehicleDetector(
            model_path=settings.yolo_model_path,
            confidence_threshold=0.5
        )
        self.density_calculator = TrafficDensityCalculator(
            low_threshold=settings.low_density_threshold,
            medium_threshold=settings.medium_density_threshold,
            high_threshold=settings.high_density_threshold
        )
        self.emergency_detector = EmergencyVehicleDetector()
        
        # Processing state
        self.is_processing = False
        self.current_frame_id = 0
    
    async def process_frame(
        self,
        frame,
        camera_id: int = 1,
        intersection_id: int = 1
    ) -> Dict:
        """
        Process a single frame.
        
        Args:
            frame: BGR image as numpy array
            camera_id: Camera identifier
            intersection_id: Intersection identifier
            
        Returns:
            Dictionary with detection results and metrics
        """
        frame_id = str(uuid.uuid4())[:8]
        timestamp = datetime.utcnow()
        
        # Detect vehicles
        detections = self.vehicle_detector.detect(frame)
        
        # Calculate density
        density_metrics = self.density_calculator.calculate(
            detections,
            frame_dimensions=(frame.shape[1], frame.shape[0])
        )
        
        # Check for emergency vehicles
        emergency_detections = self.emergency_detector.detect(frame, detections)
        
        # Count vehicles by type
        vehicle_counts = self.vehicle_detector.count_by_type(detections)
        
        # Build result
        result = {
            "frame_id": frame_id,
            "camera_id": camera_id,
            "intersection_id": intersection_id,
            "timestamp": timestamp.isoformat(),
            
            # Detection counts
            "total_vehicles": len(detections),
            "vehicle_counts": vehicle_counts,
            
            # Density metrics
            "density": density_metrics.density,
            "congestion_level": density_metrics.congestion_level.value,
            "area_coverage": density_metrics.area_coverage,
            "estimated_wait_time": density_metrics.estimated_wait_time,
            "throughput_rate": density_metrics.throughput_rate,
            
            # Emergency
            "emergency_detected": len(emergency_detections) > 0,
            "emergency_vehicles": [e.to_dict() for e in emergency_detections],
            
            # Raw detection data
            "detections": [
                {
                    "bbox": d.bbox,
                    "type": d.vehicle_type.value,
                    "confidence": d.confidence
                }
                for d in detections
            ]
        }
        
        return result
    
    async def process_video_file(
        self,
        video_path: str,
        camera_id: int = 1,
        intersection_id: int = 1,
        sample_rate: int = 2  # Process every Nth frame
    ) -> AsyncGenerator[Dict, None]:
        """
        Process a video file frame by frame.
        
        Args:
            video_path: Path to video file
            camera_id: Camera identifier
            intersection_id: Intersection identifier
            sample_rate: Process every Nth frame (default: every 2nd)
            
        Yields:
            Detection results for each processed frame
        """
        if not os.path.exists(video_path):
            yield {
                "error": "Video file not found",
                "path": video_path
            }
            return
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            yield {
                "error": "Failed to open video file",
                "path": video_path
            }
            return
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        
        self.is_processing = True
        frame_count = 0
        processed_count = 0
        
        try:
            while cap.isOpened() and self.is_processing:
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                frame_count += 1
                
                # Skip frames based on sample rate
                if frame_count % sample_rate != 0:
                    continue
                
                processed_count += 1
                
                # Process frame
                result = await self.process_frame(frame, camera_id, intersection_id)
                
                # Add progress info
                result["frame_number"] = frame_count
                result["total_frames"] = total_frames
                result["progress"] = int((frame_count / total_frames) * 100)
                result["processed_count"] = processed_count
                
                yield result
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.01)
        
        finally:
            cap.release()
            self.is_processing = False
    
    async def process_stream(
        self,
        stream_url: str,
        camera_id: int = 1,
        intersection_id: int = 1,
        duration_seconds: Optional[int] = None
    ) -> AsyncGenerator[Dict, None]:
        """
        Process a video stream (RTSP, HTTP, etc.).
        
        Args:
            stream_url: URL of the video stream
            camera_id: Camera identifier
            intersection_id: Intersection identifier
            duration_seconds: Optional duration limit
            
        Yields:
            Detection results for each processed frame
        """
        cap = cv2.VideoCapture(stream_url)
        
        if not cap.isOpened():
            yield {
                "error": "Failed to connect to stream",
                "url": stream_url
            }
            return
        
        self.is_processing = True
        frame_count = 0
        start_time = datetime.utcnow()
        
        try:
            while cap.isOpened() and self.is_processing:
                ret, frame = cap.read()
                
                if not ret:
                    # Try to reconnect
                    await asyncio.sleep(1)
                    cap = cv2.VideoCapture(stream_url)
                    continue
                
                frame_count += 1
                
                # Check duration limit
                if duration_seconds:
                    elapsed = (datetime.utcnow() - start_time).seconds
                    if elapsed >= duration_seconds:
                        break
                
                # Process frame
                result = await self.process_frame(frame, camera_id, intersection_id)
                result["frame_number"] = frame_count
                result["stream_url"] = stream_url
                
                yield result
                
                # Control frame rate
                await asyncio.sleep(settings.frame_processing_interval)
        
        finally:
            cap.release()
            self.is_processing = False
    
    def stop_processing(self):
        """Stop current processing."""
        self.is_processing = False
    
    def get_annotated_frame(self, frame, detections: List[Detection]) -> bytes:
        """
        Get frame with detection annotations as JPEG bytes.
        
        Args:
            frame: Original frame
            detections: List of detections to draw
            
        Returns:
            JPEG encoded frame bytes
        """
        annotated = self.vehicle_detector.draw_detections(frame, detections)
        _, buffer = cv2.imencode('.jpg', annotated)
        return buffer.tobytes()
