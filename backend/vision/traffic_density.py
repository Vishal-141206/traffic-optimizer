"""
Traffic Density Calculator

This module calculates traffic density metrics from vehicle detections
and determines congestion levels.
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np

from vision.vehicle_detection import Detection, VehicleClass


class CongestionLevel(Enum):
    """Traffic congestion levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DensityMetrics:
    """Container for density calculation results."""
    vehicle_count: int
    density: float  # 0.0 to 1.0
    congestion_level: CongestionLevel
    vehicles_by_type: Dict[str, int]
    area_coverage: float
    estimated_wait_time: float  # seconds
    throughput_rate: float  # vehicles per minute
    emergency_present: bool


class TrafficDensityCalculator:
    """Calculates traffic density and congestion metrics."""
    
    def __init__(
        self,
        low_threshold: int = 5,
        medium_threshold: int = 15,
        high_threshold: int = 30,
        lane_capacity: int = 50
    ):
        """
        Initialize the density calculator.
        
        Args:
            low_threshold: Vehicle count below this is LOW congestion
            medium_threshold: Vehicle count below this is MEDIUM congestion
            high_threshold: Vehicle count below this is HIGH congestion
            lane_capacity: Maximum vehicles the lane can handle
        """
        self.low_threshold = low_threshold
        self.medium_threshold = medium_threshold
        self.high_threshold = high_threshold
        self.lane_capacity = lane_capacity
        
        # Historical data for trend analysis
        self.history: List[DensityMetrics] = []
        self.max_history = 100
    
    def calculate(
        self, 
        detections: List[Detection],
        frame_dimensions: Tuple[int, int] = (1920, 1080),
        lane_id: int = 1
    ) -> DensityMetrics:
        """
        Calculate traffic density metrics from detections.
        
        Args:
            detections: List of vehicle detections
            frame_dimensions: (width, height) of the frame
            lane_id: Optional lane identifier
            
        Returns:
            DensityMetrics with calculated values
        """
        vehicle_count = len(detections)
        frame_area = frame_dimensions[0] * frame_dimensions[1]
        
        # Count by vehicle type
        vehicles_by_type = self._count_by_type(detections)
        
        # Calculate area coverage (sum of detection areas / frame area)
        total_detection_area = sum(det.area for det in detections)
        area_coverage = min(1.0, total_detection_area / frame_area)
        
        # Calculate density (normalized 0-1)
        density = min(1.0, vehicle_count / self.lane_capacity)
        
        # Determine congestion level
        congestion_level = self._determine_congestion(vehicle_count, density)
        
        # Estimate wait time based on congestion
        estimated_wait_time = self._estimate_wait_time(congestion_level, vehicle_count)
        
        # Estimate throughput rate
        throughput_rate = self._estimate_throughput(congestion_level)
        
        # Check for emergency vehicles
        emergency_present = any(det.is_emergency for det in detections)
        
        metrics = DensityMetrics(
            vehicle_count=vehicle_count,
            density=round(density, 3),
            congestion_level=congestion_level,
            vehicles_by_type=vehicles_by_type,
            area_coverage=round(area_coverage, 3),
            estimated_wait_time=estimated_wait_time,
            throughput_rate=throughput_rate,
            emergency_present=emergency_present
        )
        
        # Store in history
        self._add_to_history(metrics)
        
        return metrics
    
    def _count_by_type(self, detections: List[Detection]) -> Dict[str, int]:
        """Count vehicles by type."""
        counts = {vt.value: 0 for vt in VehicleClass}
        for det in detections:
            counts[det.vehicle_type.value] += 1
        return counts
    
    def _determine_congestion(self, vehicle_count: int, density: float) -> CongestionLevel:
        """
        Determine congestion level based on vehicle count and density.
        
        Uses both absolute count and density ratio for more accurate assessment.
        """
        # Weight: 60% count-based, 40% density-based
        count_score = (
            1 if vehicle_count <= self.low_threshold else
            2 if vehicle_count <= self.medium_threshold else
            3 if vehicle_count <= self.high_threshold else 4
        )
        
        density_score = (
            1 if density <= 0.2 else
            2 if density <= 0.5 else
            3 if density <= 0.8 else 4
        )
        
        combined_score = count_score * 0.6 + density_score * 0.4
        
        if combined_score <= 1.5:
            return CongestionLevel.LOW
        elif combined_score <= 2.5:
            return CongestionLevel.MEDIUM
        elif combined_score <= 3.5:
            return CongestionLevel.HIGH
        else:
            return CongestionLevel.CRITICAL
    
    def _estimate_wait_time(self, congestion: CongestionLevel, vehicle_count: int) -> float:
        """Estimate wait time in seconds based on congestion."""
        base_times = {
            CongestionLevel.LOW: 10,
            CongestionLevel.MEDIUM: 30,
            CongestionLevel.HIGH: 60,
            CongestionLevel.CRITICAL: 120
        }
        
        base = base_times[congestion]
        # Add extra time based on vehicle count
        extra = vehicle_count * 2
        
        return min(300, base + extra)  # Cap at 5 minutes
    
    def _estimate_throughput(self, congestion: CongestionLevel) -> float:
        """Estimate vehicles passing through per minute."""
        throughput_rates = {
            CongestionLevel.LOW: 30,
            CongestionLevel.MEDIUM: 20,
            CongestionLevel.HIGH: 10,
            CongestionLevel.CRITICAL: 5
        }
        return throughput_rates[congestion]
    
    def _add_to_history(self, metrics: DensityMetrics):
        """Add metrics to history, maintaining max size."""
        self.history.append(metrics)
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def get_trend(self, window: int = 10) -> str:
        """
        Analyze recent trend in density.
        
        Returns:
            "increasing", "decreasing", or "stable"
        """
        if len(self.history) < window:
            return "stable"
        
        recent = self.history[-window:]
        densities = [m.density for m in recent]
        
        # Calculate slope
        x = np.arange(len(densities))
        slope = np.polyfit(x, densities, 1)[0]
        
        if slope > 0.01:
            return "increasing"
        elif slope < -0.01:
            return "decreasing"
        else:
            return "stable"
    
    def get_average_metrics(self, window: int = 10) -> Optional[Dict]:
        """Get average metrics over recent history."""
        if len(self.history) < 1:
            return None
        
        recent = self.history[-window:]
        
        return {
            "avg_vehicle_count": np.mean([m.vehicle_count for m in recent]),
            "avg_density": np.mean([m.density for m in recent]),
            "avg_wait_time": np.mean([m.estimated_wait_time for m in recent]),
            "samples": len(recent)
        }


class LaneBasedDensityCalculator:
    """Calculate density for multiple lanes."""
    
    def __init__(self, num_lanes: int = 4):
        """
        Initialize lane-based calculator.
        
        Args:
            num_lanes: Number of lanes to track
        """
        self.num_lanes = num_lanes
        self.lane_calculators = {
            i: TrafficDensityCalculator() for i in range(1, num_lanes + 1)
        }
    
    def calculate_by_lane(
        self,
        detections: List[Detection],
        lane_assignments: Dict[int, int],  # detection_index -> lane_id
        frame_dimensions: Tuple[int, int] = (1920, 1080)
    ) -> Dict[int, DensityMetrics]:
        """
        Calculate density for each lane.
        
        Args:
            detections: All detections in frame
            lane_assignments: Mapping of detection index to lane ID
            frame_dimensions: Frame size
            
        Returns:
            Dictionary mapping lane_id to DensityMetrics
        """
        # Group detections by lane
        lane_detections = {i: [] for i in range(1, self.num_lanes + 1)}
        
        for idx, det in enumerate(detections):
            lane_id = lane_assignments.get(idx, 1)
            if lane_id in lane_detections:
                lane_detections[lane_id].append(det)
        
        # Calculate metrics for each lane
        results = {}
        for lane_id, lane_dets in lane_detections.items():
            results[lane_id] = self.lane_calculators[lane_id].calculate(
                lane_dets,
                frame_dimensions,
                lane_id
            )
        
        return results
    
    def assign_lanes_by_position(
        self,
        detections: List[Detection],
        frame_width: int
    ) -> Dict[int, int]:
        """
        Automatically assign detections to lanes based on horizontal position.
        
        Simple approach: divide frame into equal vertical strips.
        """
        lane_width = frame_width // self.num_lanes
        assignments = {}
        
        for idx, det in enumerate(detections):
            center_x = det.center[0]
            lane_id = min(self.num_lanes, (center_x // lane_width) + 1)
            assignments[idx] = lane_id
        
        return assignments
