"""
Emergency Vehicle Detection Module

Enhanced detection for emergency vehicles (ambulances, fire trucks, police)
using color analysis, pattern recognition, and optional audio analysis.
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from vision.vehicle_detection import Detection, VehicleClass


class EmergencyVehicleType(Enum):
    """Types of emergency vehicles."""
    AMBULANCE = "ambulance"
    FIRE_TRUCK = "fire_truck"
    POLICE = "police"
    UNKNOWN = "unknown"


@dataclass
class EmergencyDetection:
    """Emergency vehicle detection result."""
    vehicle_type: EmergencyVehicleType
    bbox: Tuple[int, int, int, int]
    confidence: float
    approach_direction: str  # north, south, east, west
    estimated_distance: str  # near, medium, far
    light_pattern_detected: bool
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "vehicle_type": self.vehicle_type.value,
            "bbox": self.bbox,
            "confidence": self.confidence,
            "approach_direction": self.approach_direction,
            "estimated_distance": self.estimated_distance,
            "light_pattern_detected": self.light_pattern_detected,
            "timestamp": self.timestamp.isoformat()
        }


class EmergencyVehicleDetector:
    """
    Specialized detector for emergency vehicles.
    
    Uses multiple detection methods:
    1. Color analysis (red/blue lights)
    2. Size and shape analysis
    3. Movement pattern analysis (if tracking enabled)
    """
    
    def __init__(
        self,
        red_threshold: float = 0.05,
        blue_threshold: float = 0.05,
        min_confidence: float = 0.6
    ):
        """
        Initialize emergency detector.
        
        Args:
            red_threshold: Minimum ratio of red pixels to flag
            blue_threshold: Minimum ratio of blue pixels to flag
            min_confidence: Minimum confidence to report detection
        """
        self.red_threshold = red_threshold
        self.blue_threshold = blue_threshold
        self.min_confidence = min_confidence
        
        # Color ranges in HSV
        self.color_ranges = {
            "red_low": (np.array([0, 100, 100]), np.array([10, 255, 255])),
            "red_high": (np.array([160, 100, 100]), np.array([180, 255, 255])),
            "blue": (np.array([100, 100, 100]), np.array([130, 255, 255])),
            "white": (np.array([0, 0, 200]), np.array([180, 30, 255])),
        }
        
        # Historical detections for tracking
        self.detection_history: List[EmergencyDetection] = []
        self.max_history = 50
    
    def detect(
        self,
        frame: np.ndarray,
        vehicle_detections: List[Detection],
        frame_regions: Optional[Dict[str, Tuple[int, int, int, int]]] = None
    ) -> List[EmergencyDetection]:
        """
        Detect emergency vehicles in frame.
        
        Args:
            frame: BGR image
            vehicle_detections: Existing vehicle detections
            frame_regions: Optional regions defining directions
            
        Returns:
            List of EmergencyDetection objects
        """
        emergency_detections = []
        
        # Check each vehicle detection for emergency indicators
        for det in vehicle_detections:
            if det.is_emergency or det.vehicle_type == VehicleClass.EMERGENCY:
                # Already flagged as emergency
                emergency_det = self._analyze_emergency_vehicle(frame, det, frame_regions)
                if emergency_det and emergency_det.confidence >= self.min_confidence:
                    emergency_detections.append(emergency_det)
                continue
            
            # Check if this detection might be an emergency vehicle
            x1, y1, x2, y2 = det.bbox
            roi = frame[y1:y2, x1:x2]
            
            if roi.size == 0:
                continue
            
            is_emergency, confidence, vehicle_type = self._analyze_roi(roi)
            
            if is_emergency:
                direction = self._determine_direction(det.center, frame.shape[:2], frame_regions)
                distance = self._estimate_distance(det.bbox, frame.shape[:2])
                
                emergency_det = EmergencyDetection(
                    vehicle_type=vehicle_type,
                    bbox=det.bbox,
                    confidence=confidence,
                    approach_direction=direction,
                    estimated_distance=distance,
                    light_pattern_detected=True,
                    timestamp=datetime.utcnow()
                )
                
                if confidence >= self.min_confidence:
                    emergency_detections.append(emergency_det)
                    self._add_to_history(emergency_det)
        
        return emergency_detections
    
    def _analyze_emergency_vehicle(
        self,
        frame: np.ndarray,
        detection: Detection,
        frame_regions: Optional[Dict] = None
    ) -> Optional[EmergencyDetection]:
        """Analyze a known emergency vehicle detection."""
        x1, y1, x2, y2 = detection.bbox
        roi = frame[y1:y2, x1:x2]
        
        if roi.size == 0:
            return None
        
        # Determine vehicle type based on color and size
        vehicle_type = self._classify_emergency_type(roi, detection.bbox)
        
        direction = self._determine_direction(detection.center, frame.shape[:2], frame_regions)
        distance = self._estimate_distance(detection.bbox, frame.shape[:2])
        
        # Check for flashing lights
        light_detected = self._detect_flashing_lights(roi)
        
        return EmergencyDetection(
            vehicle_type=vehicle_type,
            bbox=detection.bbox,
            confidence=detection.confidence,
            approach_direction=direction,
            estimated_distance=distance,
            light_pattern_detected=light_detected,
            timestamp=datetime.utcnow()
        )
    
    def _analyze_roi(self, roi: np.ndarray) -> Tuple[bool, float, EmergencyVehicleType]:
        """
        Analyze region of interest for emergency indicators.
        
        Returns:
            (is_emergency, confidence, vehicle_type)
        """
        try:
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        except cv2.error:
            return False, 0.0, EmergencyVehicleType.UNKNOWN
        
        h, w = roi.shape[:2]
        total_pixels = h * w
        
        if total_pixels == 0:
            return False, 0.0, EmergencyVehicleType.UNKNOWN
        
        # Analyze red pixels
        mask_red1 = cv2.inRange(hsv, *self.color_ranges["red_low"])
        mask_red2 = cv2.inRange(hsv, *self.color_ranges["red_high"])
        red_pixels = cv2.countNonZero(mask_red1) + cv2.countNonZero(mask_red2)
        red_ratio = red_pixels / total_pixels
        
        # Analyze blue pixels
        mask_blue = cv2.inRange(hsv, *self.color_ranges["blue"])
        blue_pixels = cv2.countNonZero(mask_blue)
        blue_ratio = blue_pixels / total_pixels
        
        # Analyze white pixels (ambulance markings)
        mask_white = cv2.inRange(hsv, *self.color_ranges["white"])
        white_pixels = cv2.countNonZero(mask_white)
        white_ratio = white_pixels / total_pixels
        
        # Determine if emergency vehicle
        is_emergency = False
        confidence = 0.0
        vehicle_type = EmergencyVehicleType.UNKNOWN
        
        # Fire truck: primarily red
        if red_ratio > self.red_threshold * 2 and red_ratio > blue_ratio:
            is_emergency = True
            confidence = min(0.95, 0.5 + red_ratio * 2)
            vehicle_type = EmergencyVehicleType.FIRE_TRUCK
        
        # Police: primarily blue
        elif blue_ratio > self.blue_threshold * 2 and blue_ratio > red_ratio:
            is_emergency = True
            confidence = min(0.95, 0.5 + blue_ratio * 2)
            vehicle_type = EmergencyVehicleType.POLICE
        
        # Ambulance: mix of red, blue, and white
        elif (red_ratio > self.red_threshold and 
              (blue_ratio > self.blue_threshold or white_ratio > 0.1)):
            is_emergency = True
            confidence = min(0.95, 0.5 + (red_ratio + blue_ratio + white_ratio) * 1.5)
            vehicle_type = EmergencyVehicleType.AMBULANCE
        
        # Any significant red+blue combination
        elif (red_ratio + blue_ratio) > (self.red_threshold + self.blue_threshold):
            is_emergency = True
            confidence = min(0.85, 0.4 + (red_ratio + blue_ratio) * 2)
        
        return is_emergency, confidence, vehicle_type
    
    def _classify_emergency_type(
        self,
        roi: np.ndarray,
        bbox: Tuple[int, int, int, int]
    ) -> EmergencyVehicleType:
        """Classify the type of emergency vehicle."""
        _, _, vehicle_type = self._analyze_roi(roi)
        
        # Use size hints
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        aspect_ratio = width / max(height, 1)
        
        # Fire trucks are typically longer
        if aspect_ratio > 2.5 and vehicle_type == EmergencyVehicleType.UNKNOWN:
            vehicle_type = EmergencyVehicleType.FIRE_TRUCK
        
        return vehicle_type
    
    def _determine_direction(
        self,
        center: Tuple[int, int],
        frame_shape: Tuple[int, int],
        regions: Optional[Dict] = None
    ) -> str:
        """Determine approach direction based on position."""
        h, w = frame_shape
        cx, cy = center
        
        # Simple quadrant-based direction
        if cy < h / 2:
            if cx < w / 2:
                return "north"
            else:
                return "east"
        else:
            if cx < w / 2:
                return "west"
            else:
                return "south"
    
    def _estimate_distance(
        self,
        bbox: Tuple[int, int, int, int],
        frame_shape: Tuple[int, int]
    ) -> str:
        """Estimate distance based on detection size."""
        x1, y1, x2, y2 = bbox
        area = (x2 - x1) * (y2 - y1)
        frame_area = frame_shape[0] * frame_shape[1]
        
        ratio = area / frame_area
        
        if ratio > 0.1:
            return "near"
        elif ratio > 0.03:
            return "medium"
        else:
            return "far"
    
    def _detect_flashing_lights(self, roi: np.ndarray) -> bool:
        """
        Detect if there are bright spots that could be flashing lights.
        
        Note: For actual flashing detection, multiple frames would be needed.
        This is a simplified single-frame detection.
        """
        try:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # Find bright spots
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            bright_pixels = cv2.countNonZero(thresh)
            
            # Check if there are concentrated bright areas (lights)
            return bright_pixels > (roi.shape[0] * roi.shape[1] * 0.01)
        except cv2.error:
            return False
    
    def _add_to_history(self, detection: EmergencyDetection):
        """Add detection to history."""
        self.detection_history.append(detection)
        if len(self.detection_history) > self.max_history:
            self.detection_history.pop(0)
    
    def get_recent_detections(self, seconds: int = 60) -> List[EmergencyDetection]:
        """Get detections from the last N seconds."""
        cutoff = datetime.utcnow().timestamp() - seconds
        return [
            d for d in self.detection_history
            if d.timestamp.timestamp() > cutoff
        ]
    
    def is_emergency_active(self, seconds: int = 10) -> bool:
        """Check if there's been a recent emergency detection."""
        return len(self.get_recent_detections(seconds)) > 0
