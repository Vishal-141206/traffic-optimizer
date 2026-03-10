"""Traffic Camera API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from core.database import get_db
from models.models import TrafficCamera, Intersection
from models.schemas import (
    CameraCreate,
    CameraUpdate,
    CameraResponse
)

router = APIRouter()


@router.get("/", response_model=List[CameraResponse])
async def get_cameras(
    intersection_id: int = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all cameras with optional filtering by intersection."""
    query = select(TrafficCamera)
    
    if intersection_id:
        query = query.where(TrafficCamera.intersection_id == intersection_id)
    if active_only:
        query = query.where(TrafficCamera.is_active == True)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific camera by ID."""
    result = await db.execute(
        select(TrafficCamera).where(TrafficCamera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    return camera


@router.post("/", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(
    camera_data: CameraCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new traffic camera."""
    # Verify intersection exists
    result = await db.execute(
        select(Intersection).where(Intersection.id == camera_data.intersection_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intersection not found"
        )
    
    camera = TrafficCamera(**camera_data.model_dump())
    db.add(camera)
    await db.commit()
    await db.refresh(camera)
    return camera


@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: int,
    camera_data: CameraUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing camera."""
    result = await db.execute(
        select(TrafficCamera).where(TrafficCamera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    update_data = camera_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(camera, key, value)
    
    await db.commit()
    await db.refresh(camera)
    return camera


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a camera (soft delete by deactivating)."""
    result = await db.execute(
        select(TrafficCamera).where(TrafficCamera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    camera.is_active = False
    await db.commit()
    return None


@router.post("/{camera_id}/heartbeat")
async def camera_heartbeat(
    camera_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Update camera's last frame timestamp (heartbeat)."""
    result = await db.execute(
        select(TrafficCamera).where(TrafficCamera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    camera.last_frame_at = datetime.utcnow()
    await db.commit()
    
    return {"status": "ok", "timestamp": camera.last_frame_at}
