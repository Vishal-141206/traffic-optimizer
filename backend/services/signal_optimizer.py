"""
Signal Optimization Engine

Adaptive traffic signal timing based on real-time traffic density
and emergency vehicle detection.
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from core.config import settings
from core.redis import redis_manager
from api.websocket import broadcast_signal_update, broadcast_emergency_alert


class SignalPhase(Enum):
    """Traffic signal phases."""
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"
    ALL_RED = "all_red"  # Safety phase between signal changes


@dataclass
class SignalTiming:
    """Signal timing configuration."""
    green_duration: int
    yellow_duration: int = 3
    all_red_duration: int = 2
    min_green: int = 10
    max_green: int = 60


@dataclass
class LaneSignal:
    """Current state of a lane's signal."""
    lane_id: int
    direction: str
    phase: SignalPhase
    duration: int
    started_at: datetime
    is_emergency_override: bool = False
    
    @property
    def time_remaining(self) -> int:
        """Calculate remaining time in current phase."""
        elapsed = (datetime.utcnow() - self.started_at).seconds
        return max(0, self.duration - elapsed)
    
    @property
    def is_expired(self) -> bool:
        """Check if current phase has expired."""
        return self.time_remaining <= 0


class SignalOptimizer:
    """
    Adaptive signal timing optimizer.
    
    Adjusts green light duration based on:
    - Traffic density
    - Vehicle queue length
    - Emergency vehicle presence
    - Time of day patterns
    """
    
    def __init__(self):
        """Initialize the signal optimizer."""
        # Default timing configuration
        self.default_timing = SignalTiming(
            green_duration=30,
            yellow_duration=settings.signal_yellow_duration,
            all_red_duration=settings.signal_all_red_duration,
            min_green=settings.signal_min_green,
            max_green=settings.signal_max_green
        )
        
        # Current signals by intersection
        self.intersection_signals: Dict[int, Dict[str, LaneSignal]] = {}
        
        # Traffic data cache
        self.traffic_cache: Dict[int, Dict] = {}
        
        # Emergency override state
        self.emergency_overrides: Dict[int, dict] = {}
        
        # Optimization params
        self.optimization_interval = settings.signal_optimization_interval
        self.running = False
    
    def calculate_green_duration(
        self,
        vehicle_count: int,
        congestion_level: str,
        queue_length: int = 0
    ) -> int:
        """
        Calculate optimal green light duration based on traffic conditions.
        
        Algorithm:
        - Base duration from congestion level
        - Adjust by queue length
        - Clamp to min/max bounds
        """
        # Base duration by congestion level
        base_durations = {
            "low": 10,
            "medium": 20,
            "high": 35,
            "critical": 45
        }
        
        base = base_durations.get(congestion_level, 20)
        
        # Adjust for vehicle count
        # Add 1 second per 2 vehicles above 5
        vehicle_adjustment = max(0, (vehicle_count - 5) // 2)
        
        # Adjust for queue length
        queue_adjustment = min(10, queue_length // 3)
        
        # Calculate final duration
        duration = base + vehicle_adjustment + queue_adjustment
        
        # Clamp to bounds
        return max(
            self.default_timing.min_green,
            min(self.default_timing.max_green, duration)
        )
    
    def optimize_intersection(
        self,
        intersection_id: int,
        traffic_data: Dict[str, Dict]
    ) -> Dict[str, SignalTiming]:
        """
        Optimize signal timing for an intersection.
        
        Args:
            intersection_id: Intersection identifier
            traffic_data: Dictionary mapping direction to traffic metrics
                         e.g., {"north": {"vehicles": 10, "congestion": "medium"}, ...}
        
        Returns:
            Dictionary mapping direction to optimized SignalTiming
        """
        # Store in cache
        self.traffic_cache[intersection_id] = traffic_data
        
        optimized = {}
        
        for direction, data in traffic_data.items():
            vehicle_count = data.get("vehicles", 0)
            congestion = data.get("congestion", "low")
            queue_length = data.get("queue_length", 0)
            
            green_duration = self.calculate_green_duration(
                vehicle_count,
                congestion,
                queue_length
            )
            
            optimized[direction] = SignalTiming(
                green_duration=green_duration,
                yellow_duration=self.default_timing.yellow_duration,
                all_red_duration=self.default_timing.all_red_duration,
                min_green=self.default_timing.min_green,
                max_green=self.default_timing.max_green
            )
        
        return optimized
    
    async def trigger_emergency_override(
        self,
        intersection_id: int,
        emergency_direction: str,
        emergency_type: str = "unknown"
    ):
        """
        Trigger emergency green corridor.
        
        Immediately switches the emergency approach direction to green
        and all other directions to red.
        """
        now = datetime.utcnow()
        
        # Store override state
        self.emergency_overrides[intersection_id] = {
            "direction": emergency_direction,
            "type": emergency_type,
            "started_at": now,
            "active": True
        }
        
        # Update all signals for this intersection
        directions = ["north", "south", "east", "west"]
        
        if intersection_id not in self.intersection_signals:
            self.intersection_signals[intersection_id] = {}
        
        for i, direction in enumerate(directions):
            is_emergency_direction = direction == emergency_direction
            
            self.intersection_signals[intersection_id][direction] = LaneSignal(
                lane_id=i + 1,
                direction=direction,
                phase=SignalPhase.GREEN if is_emergency_direction else SignalPhase.RED,
                duration=60 if is_emergency_direction else 120,
                started_at=now,
                is_emergency_override=True
            )
        
        # Broadcast update
        await broadcast_emergency_alert({
            "intersection_id": intersection_id,
            "emergency_type": emergency_type,
            "emergency_direction": emergency_direction,
            "signals": {
                d: "green" if d == emergency_direction else "red"
                for d in directions
            },
            "message": f"Emergency corridor activated: {emergency_type} approaching from {emergency_direction}"
        })
        
        await broadcast_signal_update({
            "intersection_id": intersection_id,
            "signals": {
                d: {
                    "phase": "green" if d == emergency_direction else "red",
                    "is_emergency": True
                }
                for d in directions
            }
        })
    
    async def clear_emergency_override(self, intersection_id: int):
        """Clear emergency override and resume normal operation."""
        if intersection_id in self.emergency_overrides:
            self.emergency_overrides[intersection_id]["active"] = False
            del self.emergency_overrides[intersection_id]
        
        # Reset to normal cycle
        await self._reset_to_normal_cycle(intersection_id)
    
    async def _reset_to_normal_cycle(self, intersection_id: int):
        """Reset intersection to normal signal cycle."""
        now = datetime.utcnow()
        directions = ["north", "south", "east", "west"]
        
        if intersection_id not in self.intersection_signals:
            self.intersection_signals[intersection_id] = {}
        
        # Start with north-south green, east-west red
        for i, direction in enumerate(directions):
            is_green = direction in ["north", "south"]
            
            self.intersection_signals[intersection_id][direction] = LaneSignal(
                lane_id=i + 1,
                direction=direction,
                phase=SignalPhase.GREEN if is_green else SignalPhase.RED,
                duration=30 if is_green else 35,
                started_at=now,
                is_emergency_override=False
            )
        
        await broadcast_signal_update({
            "intersection_id": intersection_id,
            "signals": {
                d: {
                    "phase": "green" if d in ["north", "south"] else "red",
                    "is_emergency": False
                }
                for d in directions
            }
        })
    
    async def run_optimization_loop(self):
        """
        Main optimization loop.
        
        Continuously monitors traffic and adjusts signal timing.
        """
        self.running = True
        
        while self.running:
            try:
                # Check each intersection
                for intersection_id, signals in self.intersection_signals.items():
                    # Skip if in emergency override
                    if intersection_id in self.emergency_overrides:
                        override = self.emergency_overrides[intersection_id]
                        if override.get("active"):
                            # Check if emergency is cleared (timeout after 2 minutes)
                            if (datetime.utcnow() - override["started_at"]).seconds > 120:
                                await self.clear_emergency_override(intersection_id)
                            continue
                    
                    # Check for expired signals and cycle
                    await self._cycle_signals(intersection_id)
                
                await asyncio.sleep(self.optimization_interval)
                
            except Exception as e:
                print(f"Optimization loop error: {e}")
                await asyncio.sleep(1)
    
    async def _cycle_signals(self, intersection_id: int):
        """Handle signal cycling for an intersection."""
        signals = self.intersection_signals.get(intersection_id, {})
        
        if not signals:
            return
        
        now = datetime.utcnow()
        
        # Find expired green signals
        for direction, signal in signals.items():
            if signal.phase == SignalPhase.GREEN and signal.is_expired:
                # Transition to yellow
                signals[direction] = LaneSignal(
                    lane_id=signal.lane_id,
                    direction=direction,
                    phase=SignalPhase.YELLOW,
                    duration=self.default_timing.yellow_duration,
                    started_at=now
                )
                
            elif signal.phase == SignalPhase.YELLOW and signal.is_expired:
                # Transition to red
                signals[direction] = LaneSignal(
                    lane_id=signal.lane_id,
                    direction=direction,
                    phase=SignalPhase.RED,
                    duration=60,  # Will be updated when it becomes green
                    started_at=now
                )
                
                # Activate perpendicular direction
                await self._activate_next_direction(intersection_id, direction)
        
        # Broadcast signal updates
        await broadcast_signal_update({
            "intersection_id": intersection_id,
            "signals": {
                d: {
                    "phase": s.phase.value,
                    "time_remaining": s.time_remaining,
                    "is_emergency": s.is_emergency_override
                }
                for d, s in signals.items()
            }
        })
    
    async def _activate_next_direction(self, intersection_id: int, completed_direction: str):
        """Activate the next direction in the cycle."""
        # Simple 2-phase cycle: north-south vs east-west
        signals = self.intersection_signals.get(intersection_id, {})
        now = datetime.utcnow()
        
        # Determine which phase to activate
        if completed_direction in ["north", "south"]:
            # Activate east-west
            for direction in ["east", "west"]:
                if direction in signals:
                    # Get optimized timing if available
                    traffic = self.traffic_cache.get(intersection_id, {})
                    dir_traffic = traffic.get(direction, {})
                    
                    duration = self.calculate_green_duration(
                        dir_traffic.get("vehicles", 5),
                        dir_traffic.get("congestion", "low")
                    )
                    
                    signals[direction] = LaneSignal(
                        lane_id=signals[direction].lane_id,
                        direction=direction,
                        phase=SignalPhase.GREEN,
                        duration=duration,
                        started_at=now
                    )
        else:
            # Activate north-south
            for direction in ["north", "south"]:
                if direction in signals:
                    traffic = self.traffic_cache.get(intersection_id, {})
                    dir_traffic = traffic.get(direction, {})
                    
                    duration = self.calculate_green_duration(
                        dir_traffic.get("vehicles", 5),
                        dir_traffic.get("congestion", "low")
                    )
                    
                    signals[direction] = LaneSignal(
                        lane_id=signals[direction].lane_id,
                        direction=direction,
                        phase=SignalPhase.GREEN,
                        duration=duration,
                        started_at=now
                    )
    
    def get_intersection_state(self, intersection_id: int) -> Dict:
        """Get current state of an intersection's signals."""
        signals = self.intersection_signals.get(intersection_id, {})
        override = self.emergency_overrides.get(intersection_id)
        
        return {
            "intersection_id": intersection_id,
            "signals": {
                d: {
                    "lane_id": s.lane_id,
                    "phase": s.phase.value,
                    "duration": s.duration,
                    "time_remaining": s.time_remaining,
                    "is_emergency_override": s.is_emergency_override
                }
                for d, s in signals.items()
            },
            "emergency_override": override,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def stop(self):
        """Stop the optimization loop."""
        self.running = False
