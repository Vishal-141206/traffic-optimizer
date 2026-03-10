"""Database models for the Traffic Flow Optimizer system."""

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, 
    ForeignKey, Enum, JSON, Text
)
from sqlalchemy.orm import relationship
from core.database import Base


class CongestionLevel(str, PyEnum):
    """Traffic congestion level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SignalState(str, PyEnum):
    """Traffic signal state enumeration."""
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"
    FLASHING = "flashing"


class VehicleType(str, PyEnum):
    """Vehicle type enumeration."""
    CAR = "car"
    BUS = "bus"
    TRUCK = "truck"
    MOTORCYCLE = "motorcycle"
    BICYCLE = "bicycle"
    EMERGENCY = "emergency"


class EmergencyType(str, PyEnum):
    """Emergency vehicle type enumeration."""
    AMBULANCE = "ambulance"
    FIRE_TRUCK = "fire_truck"
    POLICE = "police"
    OTHER = "other"


class Intersection(Base):
    """Intersection model representing a traffic junction."""
    __tablename__ = "intersections"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    location_lat = Column(Float, nullable=False)
    location_lng = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    num_lanes = Column(Integer, default=4)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cameras = relationship("TrafficCamera", back_populates="intersection")
    signals = relationship("SignalStateRecord", back_populates="intersection")
    metrics = relationship("TrafficMetric", back_populates="intersection")
    emergency_events = relationship("EmergencyEvent", back_populates="intersection")


class TrafficCamera(Base):
    """Traffic camera model for video feeds."""
    __tablename__ = "traffic_cameras"
    
    id = Column(Integer, primary_key=True, index=True)
    intersection_id = Column(Integer, ForeignKey("intersections.id"), nullable=False)
    name = Column(String(255), nullable=False)
    stream_url = Column(String(500), nullable=True)
    lane_id = Column(Integer, nullable=False)  # Which lane this camera monitors
    direction = Column(String(50), nullable=False)  # north, south, east, west
    is_active = Column(Boolean, default=True)
    last_frame_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    intersection = relationship("Intersection", back_populates="cameras")
    vehicle_counts = relationship("VehicleCount", back_populates="camera")


class VehicleCount(Base):
    """Vehicle count records from camera detection."""
    __tablename__ = "vehicle_counts"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("traffic_cameras.id"), nullable=False)
    vehicle_type = Column(Enum(VehicleType), nullable=False)
    count = Column(Integer, default=0)
    confidence = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    camera = relationship("TrafficCamera", back_populates="vehicle_counts")


class SignalStateRecord(Base):
    """Traffic signal state records."""
    __tablename__ = "signal_states"
    
    id = Column(Integer, primary_key=True, index=True)
    intersection_id = Column(Integer, ForeignKey("intersections.id"), nullable=False)
    lane_id = Column(Integer, nullable=False)
    direction = Column(String(50), nullable=False)
    state = Column(Enum(SignalState), default=SignalState.RED)
    duration = Column(Integer, nullable=False)  # Duration in seconds
    is_emergency_override = Column(Boolean, default=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    # Relationships
    intersection = relationship("Intersection", back_populates="signals")


class TrafficMetric(Base):
    """Traffic metrics for analytics."""
    __tablename__ = "traffic_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    intersection_id = Column(Integer, ForeignKey("intersections.id"), nullable=False)
    lane_id = Column(Integer, nullable=False)
    direction = Column(String(50), nullable=False)
    vehicle_count = Column(Integer, default=0)
    congestion_level = Column(Enum(CongestionLevel), default=CongestionLevel.LOW)
    density = Column(Float, default=0.0)  # vehicles per unit area
    average_speed = Column(Float, nullable=True)
    wait_time = Column(Float, nullable=True)  # Average wait time in seconds
    throughput = Column(Integer, default=0)  # Vehicles passed per cycle
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    intersection = relationship("Intersection", back_populates="metrics")


class EmergencyEvent(Base):
    """Emergency vehicle detection events."""
    __tablename__ = "emergency_events"
    
    id = Column(Integer, primary_key=True, index=True)
    intersection_id = Column(Integer, ForeignKey("intersections.id"), nullable=False)
    emergency_type = Column(Enum(EmergencyType), nullable=False)
    vehicle_plate = Column(String(50), nullable=True)
    approach_direction = Column(String(50), nullable=False)
    corridor_activated = Column(Boolean, default=False)
    corridor_route = Column(JSON, nullable=True)  # List of intersection IDs
    confidence = Column(Float, default=0.0)
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    intersection = relationship("Intersection", back_populates="emergency_events")
