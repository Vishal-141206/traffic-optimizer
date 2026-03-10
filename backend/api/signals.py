"""Traffic Signal API endpoints."""

from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from core.database import get_db
from models.models import SignalStateRecord, SignalState, Intersection
from models.schemas import (
    SignalStateCreate,
    SignalStateUpdate,
    SignalStateResponse
)

router = APIRouter()


@router.get("/", response_model=List[SignalStateResponse])
async def get_signal_states(
    intersection_id: int = None,
    current_only: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get signal states with optional filtering."""
    query = select(SignalStateRecord)
    
    if intersection_id:
        query = query.where(SignalStateRecord.intersection_id == intersection_id)
    
    if current_only:
        query = query.where(SignalStateRecord.ended_at == None)
    
    query = query.order_by(SignalStateRecord.started_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{intersection_id}/current")
async def get_current_signals(
    intersection_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get current signal states for an intersection."""
    # Verify intersection exists
    result = await db.execute(
        select(Intersection).where(Intersection.id == intersection_id)
    )
    intersection = result.scalar_one_or_none()
    if not intersection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intersection not found"
        )
    
    # Get current (non-ended) signal states
    query = select(SignalStateRecord).where(
        and_(
            SignalStateRecord.intersection_id == intersection_id,
            SignalStateRecord.ended_at == None
        )
    )
    
    result = await db.execute(query)
    signals = result.scalars().all()
    
    return {
        "intersection_id": intersection_id,
        "intersection_name": intersection.name,
        "timestamp": datetime.utcnow(),
        "signals": [
            {
                "lane_id": s.lane_id,
                "direction": s.direction,
                "state": s.state,
                "duration": s.duration,
                "started_at": s.started_at,
                "is_emergency_override": s.is_emergency_override,
                "time_remaining": max(0, s.duration - (datetime.utcnow() - s.started_at).seconds)
            }
            for s in signals
        ]
    }


@router.post("/", response_model=SignalStateResponse, status_code=status.HTTP_201_CREATED)
async def create_signal_state(
    signal_data: SignalStateCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new signal state (changes signal)."""
    # Verify intersection exists
    result = await db.execute(
        select(Intersection).where(Intersection.id == signal_data.intersection_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intersection not found"
        )
    
    # End any existing signal for this lane
    existing = await db.execute(
        select(SignalStateRecord).where(
            and_(
                SignalStateRecord.intersection_id == signal_data.intersection_id,
                SignalStateRecord.lane_id == signal_data.lane_id,
                SignalStateRecord.ended_at == None
            )
        )
    )
    existing_signal = existing.scalar_one_or_none()
    if existing_signal:
        existing_signal.ended_at = datetime.utcnow()
    
    # Create new signal state
    signal = SignalStateRecord(**signal_data.model_dump())
    db.add(signal)
    await db.commit()
    await db.refresh(signal)
    return signal


@router.put("/{signal_id}", response_model=SignalStateResponse)
async def update_signal_state(
    signal_id: int,
    signal_data: SignalStateUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing signal state."""
    result = await db.execute(
        select(SignalStateRecord).where(SignalStateRecord.id == signal_id)
    )
    signal = result.scalar_one_or_none()
    
    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signal state not found"
        )
    
    update_data = signal_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(signal, key, value)
    
    await db.commit()
    await db.refresh(signal)
    return signal


@router.post("/{intersection_id}/emergency-override")
async def trigger_emergency_override(
    intersection_id: int,
    direction: str,
    db: AsyncSession = Depends(get_db)
):
    """Trigger emergency override for an intersection."""
    # Verify intersection exists
    result = await db.execute(
        select(Intersection).where(Intersection.id == intersection_id)
    )
    intersection = result.scalar_one_or_none()
    if not intersection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intersection not found"
        )
    
    # End all current signals and set to red except emergency direction
    current_signals = await db.execute(
        select(SignalStateRecord).where(
            and_(
                SignalStateRecord.intersection_id == intersection_id,
                SignalStateRecord.ended_at == None
            )
        )
    )
    
    now = datetime.utcnow()
    for signal in current_signals.scalars():
        signal.ended_at = now
    
    # Create new signals - green for emergency direction, red for others
    directions = ["north", "south", "east", "west"]
    new_signals = []
    
    for i, d in enumerate(directions):
        is_emergency_direction = d == direction
        signal = SignalStateRecord(
            intersection_id=intersection_id,
            lane_id=i + 1,
            direction=d,
            state=SignalState.GREEN if is_emergency_direction else SignalState.RED,
            duration=60 if is_emergency_direction else 120,
            is_emergency_override=True,
            started_at=now
        )
        db.add(signal)
        new_signals.append({
            "direction": d,
            "state": "green" if is_emergency_direction else "red",
            "is_emergency": is_emergency_direction
        })
    
    await db.commit()
    
    return {
        "status": "emergency_override_activated",
        "intersection_id": intersection_id,
        "emergency_direction": direction,
        "signals": new_signals,
        "activated_at": now
    }


@router.post("/{intersection_id}/reset")
async def reset_signals(
    intersection_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Reset intersection signals to normal operation."""
    # End all emergency override signals
    current_signals = await db.execute(
        select(SignalStateRecord).where(
            and_(
                SignalStateRecord.intersection_id == intersection_id,
                SignalStateRecord.ended_at == None,
                SignalStateRecord.is_emergency_override == True
            )
        )
    )
    
    now = datetime.utcnow()
    count = 0
    for signal in current_signals.scalars():
        signal.ended_at = now
        count += 1
    
    await db.commit()
    
    return {
        "status": "signals_reset",
        "intersection_id": intersection_id,
        "signals_ended": count,
        "reset_at": now
    }


@router.get("/{intersection_id}/history")
async def get_signal_history(
    intersection_id: int,
    hours: int = Query(default=24, le=168),
    db: AsyncSession = Depends(get_db)
):
    """Get signal change history for an intersection."""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    query = select(SignalStateRecord).where(
        and_(
            SignalStateRecord.intersection_id == intersection_id,
            SignalStateRecord.started_at >= since
        )
    ).order_by(SignalStateRecord.started_at.desc())
    
    result = await db.execute(query)
    signals = result.scalars().all()
    
    return {
        "intersection_id": intersection_id,
        "period_hours": hours,
        "total_changes": len(signals),
        "history": [
            {
                "id": s.id,
                "lane_id": s.lane_id,
                "direction": s.direction,
                "state": s.state,
                "duration": s.duration,
                "is_emergency_override": s.is_emergency_override,
                "started_at": s.started_at,
                "ended_at": s.ended_at
            }
            for s in signals
        ]
    }
