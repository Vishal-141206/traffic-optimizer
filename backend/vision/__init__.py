"""Vision module exports."""

from vision.vehicle_detection import (
    VehicleDetector,
    Detection,
    VehicleClass
)

from vision.traffic_density import (
    TrafficDensityCalculator,
    LaneBasedDensityCalculator,
    DensityMetrics,
    CongestionLevel
)

from vision.emergency_detection import (
    EmergencyVehicleDetector,
    EmergencyDetection,
    EmergencyVehicleType
)

__all__ = [
    "VehicleDetector",
    "Detection",
    "VehicleClass",
    "TrafficDensityCalculator",
    "LaneBasedDensityCalculator",
    "DensityMetrics",
    "CongestionLevel",
    "EmergencyVehicleDetector",
    "EmergencyDetection",
    "EmergencyVehicleType"
]
