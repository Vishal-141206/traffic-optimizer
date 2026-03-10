"""
Vehicle Detection Module using YOLOv8

This module provides vehicle detection capabilities using the YOLOv8 model
for processing traffic camera frames.
"""

import os
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Warning: ultralytics not installed. Using mock detection.")


class VehicleClass(Enum):
    """Vehicle classification types."""
    CAR = "car"
    BUS = "bus"
    TRUCK = "truck"
    MOTORCYCLE = "motorcycle"
    BICYCLE = "bicycle"
    EMERGENCY = "emergency"


# COCO class IDs mapping to vehicle types
COCO_VEHICLE_CLASSES = {
    2: VehicleClass.CAR,      # car
    3: VehicleClass.MOTORCYCLE,  # motorcycle
    5: VehicleClass.BUS,      # bus
    7: VehicleClass.TRUCK,    # truck
    1: VehicleClass.BICYCLE,  # bicycle
}

# Emergency vehicle detection keywords (for model fine-tuning)
EMERGENCY_INDICATORS = ["ambulance", "fire_truck", "police", "emergency"]


@dataclass
class Detection:
    """Represents a single vehicle detection."""
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    class_id: int
    vehicle_type: VehicleClass
    confidence: float
    is_emergency: bool = False
    
    @property
    def center(self) -> Tuple[int, int]:
        """Get center point of bounding box."""
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)
    
    @property
    def area(self) -> int:
        """Get area of bounding box."""
        x1, y1, x2, y2 = self.bbox
        return (x2 - x1) * (y2 - y1)


class VehicleDetector:
    """YOLOv8-based vehicle detector."""
    
    def __init__(self, model_path: str = "yolov8n.pt", confidence_threshold: float = 0.5):
        """
        Initialize the vehicle detector.
        
        Args:
            model_path: Path to YOLOv8 model weights
            confidence_threshold: Minimum confidence for detections
        """
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.model_path = model_path
        
        if YOLO_AVAILABLE:
            self._load_model()
    
    def _load_model(self):
        """Load the YOLO model."""
        try:
            # Try to load from specified path first
            if os.path.exists(self.model_path):
                self.model = YOLO(self.model_path)
            else:
                # Download pre-trained model
                self.model = YOLO("yolov8n.pt")
            print(f"✅ YOLO model loaded successfully")
        except Exception as e:
            print(f"⚠️ Failed to load YOLO model: {e}")
            self.model = None
    
    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Detect vehicles in a frame.
        
        Args:
            frame: BGR image as numpy array
            
        Returns:
            List of Detection objects
        """
        if self.model is None:
            return self._mock_detect(frame)
        
        detections = []
        
        try:
            # Run inference
            results = self.model(frame, verbose=False)
            
            for result in results:
                boxes = result.boxes
                
                for box in boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    # Filter by confidence
                    if confidence < self.confidence_threshold:
                        continue
                    
                    # Check if it's a vehicle class
                    if class_id not in COCO_VEHICLE_CLASSES:
                        continue
                    
                    # Get bounding box
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    vehicle_type = COCO_VEHICLE_CLASSES[class_id]
                    
                    # Check for emergency vehicle indicators
                    is_emergency = self._check_emergency(frame[y1:y2, x1:x2])
                    if is_emergency:
                        vehicle_type = VehicleClass.EMERGENCY
                    
                    detection = Detection(
                        bbox=(x1, y1, x2, y2),
                        class_id=class_id,
                        vehicle_type=vehicle_type,
                        confidence=confidence,
                        is_emergency=is_emergency
                    )
                    detections.append(detection)
        
        except Exception as e:
            print(f"Detection error: {e}")
            return self._mock_detect(frame)
        
        return detections
    
    def _check_emergency(self, roi: np.ndarray) -> bool:
        """
        Check if a detected vehicle might be an emergency vehicle.
        Uses color analysis to detect red/blue lights or specific patterns.
        
        Args:
            roi: Region of interest (cropped vehicle image)
            
        Returns:
            True if emergency vehicle indicators detected
        """
        if roi.size == 0:
            return False
        
        try:
            # Convert to HSV for color analysis
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            
            # Define color ranges for emergency lights
            # Red (wraps around 0)
            lower_red1 = np.array([0, 100, 100])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([160, 100, 100])
            upper_red2 = np.array([180, 255, 255])
            
            # Blue
            lower_blue = np.array([100, 100, 100])
            upper_blue = np.array([130, 255, 255])
            
            # Create masks
            mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
            mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
            
            # Count pixels
            total_pixels = roi.shape[0] * roi.shape[1]
            red_pixels = cv2.countNonZero(mask_red1) + cv2.countNonZero(mask_red2)
            blue_pixels = cv2.countNonZero(mask_blue)
            
            # Check if significant amount of red/blue present
            emergency_ratio = (red_pixels + blue_pixels) / total_pixels
            
            # If more than 5% of vehicle shows emergency colors, flag it
            return emergency_ratio > 0.05
            
        except Exception:
            return False
    
    def _mock_detect(self, frame: np.ndarray) -> List[Detection]:
        """Generate mock detections for testing without YOLO."""
        import random
        
        detections = []
        h, w = frame.shape[:2]
        
        # Generate 0-10 random detections
        num_vehicles = random.randint(0, 10)
        
        for _ in range(num_vehicles):
            # Random vehicle type
            vehicle_type = random.choice(list(VehicleClass))
            if vehicle_type == VehicleClass.EMERGENCY:
                vehicle_type = VehicleClass.CAR
            
            # Random bounding box
            x1 = random.randint(0, w - 100)
            y1 = random.randint(0, h - 100)
            x2 = x1 + random.randint(50, 150)
            y2 = y1 + random.randint(50, 100)
            
            is_emergency = random.random() < 0.02  # 2% chance
            if is_emergency:
                vehicle_type = VehicleClass.EMERGENCY
            
            detection = Detection(
                bbox=(x1, y1, min(x2, w), min(y2, h)),
                class_id=2,
                vehicle_type=vehicle_type,
                confidence=random.uniform(0.6, 0.99),
                is_emergency=is_emergency
            )
            detections.append(detection)
        
        return detections
    
    def count_by_type(self, detections: List[Detection]) -> Dict[str, int]:
        """
        Count detections by vehicle type.
        
        Args:
            detections: List of Detection objects
            
        Returns:
            Dictionary mapping vehicle type to count
        """
        counts = {vt.value: 0 for vt in VehicleClass}
        
        for det in detections:
            counts[det.vehicle_type.value] += 1
        
        return counts
    
    def draw_detections(
        self, 
        frame: np.ndarray, 
        detections: List[Detection],
        draw_labels: bool = True
    ) -> np.ndarray:
        """
        Draw detection boxes on frame.
        
        Args:
            frame: Original frame
            detections: List of detections to draw
            draw_labels: Whether to draw class labels
            
        Returns:
            Frame with drawn detections
        """
        result = frame.copy()
        
        colors = {
            VehicleClass.CAR: (0, 255, 0),       # Green
            VehicleClass.BUS: (255, 165, 0),     # Orange
            VehicleClass.TRUCK: (0, 165, 255),   # Light orange
            VehicleClass.MOTORCYCLE: (255, 255, 0),  # Cyan
            VehicleClass.BICYCLE: (255, 0, 255),  # Magenta
            VehicleClass.EMERGENCY: (0, 0, 255),  # Red
        }
        
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            color = colors.get(det.vehicle_type, (255, 255, 255))
            
            # Draw box
            thickness = 3 if det.is_emergency else 2
            cv2.rectangle(result, (x1, y1), (x2, y2), color, thickness)
            
            if draw_labels:
                label = f"{det.vehicle_type.value}: {det.confidence:.2f}"
                
                # Draw label background
                (label_w, label_h), _ = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
                )
                cv2.rectangle(
                    result, 
                    (x1, y1 - label_h - 10), 
                    (x1 + label_w + 10, y1), 
                    color, 
                    -1
                )
                
                # Draw label text
                cv2.putText(
                    result, 
                    label, 
                    (x1 + 5, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, 
                    (255, 255, 255), 
                    1
                )
        
        return result
