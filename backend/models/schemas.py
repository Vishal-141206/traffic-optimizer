"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from models.models import CongestionLevel, SignalState, VehicleType, EmergencyType


# ==================== Intersection Schemas ====================

class IntersectionBase(BaseModel):
    """Base schema for intersection."""
    name: str = Field(..., min_length=1, max_length=255)
    location_lat: float = Field(..., ge=-90, le=90)
    location_lng: float = Field(..., ge=-180, le=180)
    description: Optional[str] = None
    num_lanes: int = Field(default=4, ge=2, le=12)


class IntersectionCreate(IntersectionBase):
    """Schema for creating an intersection."""
    pass


class IntersectionUpdate(BaseModel):
    """Schema for updating an intersection."""
    name: Optional[str] = None
    description: Optional[str] = None
    num_lanes: Optional[int] = None
    is_active: Optional[bool] = None


class IntersectionResponse(IntersectionBase):
    """Schema for intersection response."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Camera Schemas ====================

class CameraBase(BaseModel):
    """Base schema for traffic camera."""
    name: str = Field(..., min_length=1, max_length=255)
    stream_url: Optional[str] = None
    lane_id: int = Field(..., ge=1)
    direction: str = Field(..., pattern="^(north|south|east|west)$")


class CameraCreate(CameraBase):
    """Schema for creating a camera."""
    intersection_id: int


class CameraUpdate(BaseModel):
    """Schema for updating a camera."""
    name: Optional[str] = None
    stream_url: Optional[str] = None
    is_active: Optional[bool] = None


class CameraResponse(CameraBase):
    """Schema for camera response."""
    id: int
    intersection_id: int
    is_active: bool
    last_frame_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Vehicle Count Schemas ====================

class VehicleCountBase(BaseModel):
    """Base schema for vehicle count."""
    vehicle_type: VehicleType
    count: int = Field(..., ge=0)
    confidence: float = Field(..., ge=0, le=1)


class VehicleCountCreate(VehicleCountBase):
    """Schema for creating vehicle count."""
    camera_id: int


class VehicleCountResponse(VehicleCountBase):
    """Schema for vehicle count response."""
    id: int
    camera_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


# ==================== Signal State Schemas ====================

class SignalStateBase(BaseModel):
    """Base schema for signal state."""
    lane_id: int
    direction: str
    state: SignalState
    duration: int = Field(..., ge=1)


class SignalStateCreate(SignalStateBase):
    """Schema for creating signal state."""
    intersection_id: int


class SignalStateUpdate(BaseModel):
    """Schema for updating signal state."""
    state: Optional[SignalState] = None
    duration: Optional[int] = None
    is_emergency_override: Optional[bool] = None


class SignalStateResponse(SignalStateBase):
    """Schema for signal state response."""
    id: int
    intersection_id: int
    is_emergency_override: bool
    started_at: datetime
    ended_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ==================== Traffic Metric Schemas ====================

class TrafficMetricBase(BaseModel):
    """Base schema for traffic metric."""
    lane_id: int
    direction: str
    vehicle_count: int = Field(..., ge=0)
    congestion_level: CongestionLevel
    density: float = Field(..., ge=0)
    average_speed: Optional[float] = None
    wait_time: Optional[float] = None
    throughput: int = Field(default=0, ge=0)


class TrafficMetricCreate(TrafficMetricBase):
    """Schema for creating traffic metric."""
    intersection_id: int


class TrafficMetricResponse(TrafficMetricBase):
    """Schema for traffic metric response."""
    id: int
    intersection_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


# ==================== Emergency Event Schemas ====================

class EmergencyEventBase(BaseModel):
    """Base schema for emergency event."""
    emergency_type: EmergencyType
    approach_direction: str
    vehicle_plate: Optional[str] = None
    confidence: float = Field(..., ge=0, le=1)


class EmergencyEventCreate(EmergencyEventBase):
    """Schema for creating emergency event."""
    intersection_id: int


class EmergencyEventUpdate(BaseModel):
    """Schema for updating emergency event."""
    corridor_activated: Optional[bool] = None
    corridor_route: Optional[List[int]] = None
    resolved_at: Optional[datetime] = None
    notes: Optional[str] = None


class EmergencyEventResponse(EmergencyEventBase):
    """Schema for emergency event response."""
    id: int
    intersection_id: int
    corridor_activated: bool
    corridor_route: Optional[List[int]]
    detected_at: datetime
    resolved_at: Optional[datetime]
    notes: Optional[str]
    
    class Config:
        from_attributes = True


# ==================== Real-time Update Schemas ====================

class RealtimeTrafficUpdate(BaseModel):
    """Schema for real-time traffic updates via WebSocket."""
    intersection_id: int
    lane_updates: List[dict]
    signal_states: List[dict]
    congestion_level: CongestionLevel
    vehicle_counts: dict
    timestamp: datetime


class RealtimeEmergencyAlert(BaseModel):
    """Schema for real-time emergency alerts."""
    event_id: int
    intersection_id: int
    emergency_type: EmergencyType
    approach_direction: str
    corridor_route: Optional[List[int]]
    message: str
    timestamp: datetime


# ==================== Analytics Schemas ====================

class TrafficAnalytics(BaseModel):
    """Schema for traffic analytics response."""
    period_start: datetime
    period_end: datetime
    total_vehicles: int
    average_congestion: float
    peak_hours: List[int]
    congestion_by_hour: dict
    vehicle_type_distribution: dict


class IntersectionAnalytics(BaseModel):
    """Schema for intersection-specific analytics."""
    intersection_id: int
    intersection_name: str
    total_vehicles: int
    average_wait_time: float
    congestion_distribution: dict
    emergency_events_count: int
    efficiency_score: float


# ==================== Dashboard Schemas ====================

class DashboardSummary(BaseModel):
    """Schema for dashboard summary."""
    active_intersections: int
    total_cameras: int
    current_vehicles: int
    active_emergencies: int
    overall_congestion: CongestionLevel
    alerts: List[dict]


class DetectionResult(BaseModel):
    """Schema for vehicle detection result."""
    camera_id: int
    frame_id: str
    detections: List[dict]
    vehicle_counts: dict
    density: float
    congestion_level: CongestionLevel
    emergency_detected: bool
    timestamp: datetime
