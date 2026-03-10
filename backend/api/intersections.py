"""Intersection API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from core.database import get_db
from models.models import Intersection
from models.schemas import (
    IntersectionCreate,
    IntersectionUpdate,
    IntersectionResponse
)

router = APIRouter()


@router.get("/", response_model=List[IntersectionResponse])
async def get_intersections(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Get all intersections with optional filtering."""
    query = select(Intersection)
    if active_only:
        query = query.where(Intersection.is_active == True)
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{intersection_id}", response_model=IntersectionResponse)
async def get_intersection(
    intersection_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific intersection by ID."""
    result = await db.execute(
        select(Intersection).where(Intersection.id == intersection_id)
    )
    intersection = result.scalar_one_or_none()
    
    if not intersection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intersection not found"
        )
    return intersection


@router.post("/", response_model=IntersectionResponse, status_code=status.HTTP_201_CREATED)
async def create_intersection(
    intersection_data: IntersectionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new intersection."""
    intersection = Intersection(**intersection_data.model_dump())
    db.add(intersection)
    await db.commit()
    await db.refresh(intersection)
    return intersection


@router.put("/{intersection_id}", response_model=IntersectionResponse)
async def update_intersection(
    intersection_id: int,
    intersection_data: IntersectionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing intersection."""
    result = await db.execute(
        select(Intersection).where(Intersection.id == intersection_id)
    )
    intersection = result.scalar_one_or_none()
    
    if not intersection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intersection not found"
        )
    
    update_data = intersection_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(intersection, key, value)
    
    await db.commit()
    await db.refresh(intersection)
    return intersection


@router.delete("/{intersection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_intersection(
    intersection_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an intersection (soft delete by deactivating)."""
    result = await db.execute(
        select(Intersection).where(Intersection.id == intersection_id)
    )
    intersection = result.scalar_one_or_none()
    
    if not intersection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intersection not found"
        )
    
    intersection.is_active = False
    await db.commit()
    return None


@router.get("/{intersection_id}/status")
async def get_intersection_status(
    intersection_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get current status of an intersection including traffic and signal info."""
    result = await db.execute(
        select(Intersection)
        .options(selectinload(Intersection.cameras))
        .where(Intersection.id == intersection_id)
    )
    intersection = result.scalar_one_or_none()
    
    if not intersection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intersection not found"
        )
    
    # Return comprehensive status
    return {
        "intersection_id": intersection.id,
        "name": intersection.name,
        "is_active": intersection.is_active,
        "num_cameras": len(intersection.cameras),
        "cameras": [
            {
                "id": c.id,
                "name": c.name,
                "direction": c.direction,
                "is_active": c.is_active
            }
            for c in intersection.cameras
        ]
    }
