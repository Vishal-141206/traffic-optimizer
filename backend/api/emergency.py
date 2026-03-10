"""Emergency Events API endpoints."""

from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from core.database import get_db
from core.redis import get_redis, RedisManager
from models.models import EmergencyEvent, Intersection
from models.schemas import (
    EmergencyEventCreate,
    EmergencyEventUpdate,
    EmergencyEventResponse
)

router = APIRouter()


@router.get("/", response_model=List[EmergencyEventResponse])
async def get_emergency_events(
    intersection_id: int = None,
    active_only: bool = False,
    hours: int = Query(default=24, le=168),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get emergency events with optional filtering."""
    query = select(EmergencyEvent)
    
    since = datetime.utcnow() - timedelta(hours=hours)
    query = query.where(EmergencyEvent.detected_at >= since)
    
    if intersection_id:
        query = query.where(EmergencyEvent.intersection_id == intersection_id)
    
    if active_only:
        query = query.where(EmergencyEvent.resolved_at == None)
    
    query = query.order_by(EmergencyEvent.detected_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/active")
async def get_active_emergencies(
    db: AsyncSession = Depends(get_db)
):
    """Get all currently active (unresolved) emergency events."""
    query = select(EmergencyEvent).where(
        EmergencyEvent.resolved_at == None
    ).order_by(EmergencyEvent.detected_at.desc())
    
    result = await db.execute(query)
    events = result.scalars().all()
    
    return {
        "count": len(events),
        "events": [
            {
                "id": e.id,
                "intersection_id": e.intersection_id,
                "emergency_type": e.emergency_type,
                "approach_direction": e.approach_direction,
                "corridor_activated": e.corridor_activated,
                "corridor_route": e.corridor_route,
                "detected_at": e.detected_at,
                "duration_seconds": (datetime.utcnow() - e.detected_at).seconds
            }
            for e in events
        ]
    }


@router.get("/{event_id}", response_model=EmergencyEventResponse)
async def get_emergency_event(
    event_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific emergency event."""
    result = await db.execute(
        select(EmergencyEvent).where(EmergencyEvent.id == event_id)
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency event not found"
        )
    return event


@router.post("/", response_model=EmergencyEventResponse, status_code=status.HTTP_201_CREATED)
async def create_emergency_event(
    event_data: EmergencyEventCreate,
    db: AsyncSession = Depends(get_db),
    redis: RedisManager = Depends(get_redis)
):
    """Create a new emergency event (detected emergency vehicle)."""
    # Verify intersection exists
    result = await db.execute(
        select(Intersection).where(Intersection.id == event_data.intersection_id)
    )
    intersection = result.scalar_one_or_none()
    if not intersection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intersection not found"
        )
    
    # Create event
    event = EmergencyEvent(**event_data.model_dump())
    db.add(event)
    await db.commit()
    await db.refresh(event)
    
    # Publish to Redis for real-time notification
    await redis.publish("emergency_alerts", {
        "event_id": event.id,
        "intersection_id": event.intersection_id,
        "intersection_name": intersection.name,
        "emergency_type": event.emergency_type.value,
        "approach_direction": event.approach_direction,
        "detected_at": event.detected_at.isoformat(),
        "message": f"Emergency vehicle ({event.emergency_type.value}) detected approaching {intersection.name} from {event.approach_direction}"
    })
    
    return event


@router.put("/{event_id}", response_model=EmergencyEventResponse)
async def update_emergency_event(
    event_id: int,
    event_data: EmergencyEventUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an emergency event."""
    result = await db.execute(
        select(EmergencyEvent).where(EmergencyEvent.id == event_id)
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency event not found"
        )
    
    update_data = event_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)
    
    await db.commit()
    await db.refresh(event)
    return event


@router.post("/{event_id}/activate-corridor")
async def activate_green_corridor(
    event_id: int,
    corridor_route: List[int],
    db: AsyncSession = Depends(get_db),
    redis: RedisManager = Depends(get_redis)
):
    """Activate green corridor for an emergency event."""
    result = await db.execute(
        select(EmergencyEvent).where(EmergencyEvent.id == event_id)
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency event not found"
        )
    
    if event.resolved_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot activate corridor for resolved event"
        )
    
    event.corridor_activated = True
    event.corridor_route = corridor_route
    await db.commit()
    
    # Publish corridor activation
    await redis.publish("corridor_activated", {
        "event_id": event.id,
        "corridor_route": corridor_route,
        "emergency_type": event.emergency_type.value,
        "message": f"Green corridor activated for {event.emergency_type.value}"
    })
    
    return {
        "status": "corridor_activated",
        "event_id": event.id,
        "corridor_route": corridor_route,
        "intersections_affected": len(corridor_route)
    }


@router.post("/{event_id}/resolve")
async def resolve_emergency_event(
    event_id: int,
    notes: str = None,
    db: AsyncSession = Depends(get_db),
    redis: RedisManager = Depends(get_redis)
):
    """Mark an emergency event as resolved."""
    result = await db.execute(
        select(EmergencyEvent).where(EmergencyEvent.id == event_id)
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency event not found"
        )
    
    if event.resolved_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event already resolved"
        )
    
    event.resolved_at = datetime.utcnow()
    if notes:
        event.notes = notes
    
    await db.commit()
    
    # Publish resolution
    await redis.publish("emergency_resolved", {
        "event_id": event.id,
        "resolved_at": event.resolved_at.isoformat(),
        "duration_seconds": (event.resolved_at - event.detected_at).seconds
    })
    
    return {
        "status": "resolved",
        "event_id": event.id,
        "resolved_at": event.resolved_at,
        "duration_seconds": (event.resolved_at - event.detected_at).seconds
    }


@router.get("/stats/summary")
async def get_emergency_stats(
    hours: int = Query(default=168, le=720),
    db: AsyncSession = Depends(get_db)
):
    """Get emergency event statistics."""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    query = select(EmergencyEvent).where(
        EmergencyEvent.detected_at >= since
    )
    
    result = await db.execute(query)
    events = result.scalars().all()
    
    # Calculate statistics
    total = len(events)
    resolved = sum(1 for e in events if e.resolved_at)
    corridor_activated = sum(1 for e in events if e.corridor_activated)
    
    # Average response time (detection to resolution)
    resolved_events = [e for e in events if e.resolved_at]
    avg_response_time = None
    if resolved_events:
        total_response = sum(
            (e.resolved_at - e.detected_at).total_seconds() 
            for e in resolved_events
        )
        avg_response_time = total_response / len(resolved_events)
    
    # By type
    by_type = {}
    for e in events:
        t = e.emergency_type.value
        by_type[t] = by_type.get(t, 0) + 1
    
    return {
        "period_hours": hours,
        "total_events": total,
        "resolved": resolved,
        "active": total - resolved,
        "corridor_activations": corridor_activated,
        "average_response_time_seconds": avg_response_time,
        "by_type": by_type
    }
