"""Traffic data API endpoints."""

from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from core.database import get_db
from models.models import TrafficMetric, VehicleCount, CongestionLevel
from models.schemas import (
    TrafficMetricResponse,
    VehicleCountResponse,
    DashboardSummary
)

router = APIRouter()


@router.get("/metrics", response_model=List[TrafficMetricResponse])
async def get_traffic_metrics(
    intersection_id: int = None,
    lane_id: int = None,
    hours: int = Query(default=24, le=168),
    skip: int = 0,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db)
):
    """Get traffic metrics with optional filtering."""
    query = select(TrafficMetric)
    
    # Time filter
    since = datetime.utcnow() - timedelta(hours=hours)
    query = query.where(TrafficMetric.timestamp >= since)
    
    if intersection_id:
        query = query.where(TrafficMetric.intersection_id == intersection_id)
    if lane_id:
        query = query.where(TrafficMetric.lane_id == lane_id)
    
    query = query.order_by(TrafficMetric.timestamp.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/vehicle-counts", response_model=List[VehicleCountResponse])
async def get_vehicle_counts(
    camera_id: int = None,
    hours: int = Query(default=24, le=168),
    skip: int = 0,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db)
):
    """Get vehicle count records."""
    query = select(VehicleCount)
    
    since = datetime.utcnow() - timedelta(hours=hours)
    query = query.where(VehicleCount.timestamp >= since)
    
    if camera_id:
        query = query.where(VehicleCount.camera_id == camera_id)
    
    query = query.order_by(VehicleCount.timestamp.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/current")
async def get_current_traffic(
    intersection_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    """Get current traffic status across all or specific intersection."""
    # Get latest metrics for each intersection/lane combination
    subquery = (
        select(
            TrafficMetric.intersection_id,
            TrafficMetric.lane_id,
            func.max(TrafficMetric.timestamp).label("max_timestamp")
        )
        .group_by(TrafficMetric.intersection_id, TrafficMetric.lane_id)
        .subquery()
    )
    
    query = select(TrafficMetric).join(
        subquery,
        and_(
            TrafficMetric.intersection_id == subquery.c.intersection_id,
            TrafficMetric.lane_id == subquery.c.lane_id,
            TrafficMetric.timestamp == subquery.c.max_timestamp
        )
    )
    
    if intersection_id:
        query = query.where(TrafficMetric.intersection_id == intersection_id)
    
    result = await db.execute(query)
    metrics = result.scalars().all()
    
    # Aggregate data
    total_vehicles = sum(m.vehicle_count for m in metrics)
    avg_congestion = sum(
        {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(m.congestion_level.value, 1) 
        for m in metrics
    ) / max(len(metrics), 1)
    
    # Determine overall congestion level
    if avg_congestion <= 1.5:
        overall = CongestionLevel.LOW
    elif avg_congestion <= 2.5:
        overall = CongestionLevel.MEDIUM
    elif avg_congestion <= 3.5:
        overall = CongestionLevel.HIGH
    else:
        overall = CongestionLevel.CRITICAL
    
    return {
        "timestamp": datetime.utcnow(),
        "total_vehicles": total_vehicles,
        "overall_congestion": overall,
        "metrics_by_intersection": [
            {
                "intersection_id": m.intersection_id,
                "lane_id": m.lane_id,
                "direction": m.direction,
                "vehicle_count": m.vehicle_count,
                "congestion_level": m.congestion_level,
                "density": m.density
            }
            for m in metrics
        ]
    }


@router.get("/congestion-summary")
async def get_congestion_summary(
    hours: int = Query(default=1, le=24),
    db: AsyncSession = Depends(get_db)
):
    """Get congestion summary for the specified time period."""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Count metrics by congestion level
    query = (
        select(
            TrafficMetric.congestion_level,
            func.count(TrafficMetric.id).label("count")
        )
        .where(TrafficMetric.timestamp >= since)
        .group_by(TrafficMetric.congestion_level)
    )
    
    result = await db.execute(query)
    congestion_counts = {row.congestion_level.value: row.count for row in result}
    
    total = sum(congestion_counts.values())
    
    return {
        "period_hours": hours,
        "since": since,
        "total_measurements": total,
        "distribution": {
            level: {
                "count": congestion_counts.get(level, 0),
                "percentage": round(congestion_counts.get(level, 0) / max(total, 1) * 100, 2)
            }
            for level in ["low", "medium", "high", "critical"]
        }
    }


@router.get("/density-history")
async def get_density_history(
    intersection_id: int,
    hours: int = Query(default=24, le=168),
    interval_minutes: int = Query(default=15, ge=5, le=60),
    db: AsyncSession = Depends(get_db)
):
    """Get density history for an intersection with time intervals."""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Get all metrics for the period
    query = (
        select(TrafficMetric)
        .where(
            and_(
                TrafficMetric.intersection_id == intersection_id,
                TrafficMetric.timestamp >= since
            )
        )
        .order_by(TrafficMetric.timestamp)
    )
    
    result = await db.execute(query)
    metrics = result.scalars().all()
    
    # Group by time intervals
    intervals = {}
    for metric in metrics:
        # Round to nearest interval
        interval_start = metric.timestamp.replace(
            minute=(metric.timestamp.minute // interval_minutes) * interval_minutes,
            second=0,
            microsecond=0
        )
        key = interval_start.isoformat()
        
        if key not in intervals:
            intervals[key] = {"density_sum": 0, "count": 0, "vehicle_sum": 0}
        
        intervals[key]["density_sum"] += metric.density
        intervals[key]["count"] += 1
        intervals[key]["vehicle_sum"] += metric.vehicle_count
    
    # Calculate averages
    history = [
        {
            "timestamp": key,
            "avg_density": round(data["density_sum"] / data["count"], 2),
            "avg_vehicles": round(data["vehicle_sum"] / data["count"])
        }
        for key, data in sorted(intervals.items())
    ]
    
    return {
        "intersection_id": intersection_id,
        "period_hours": hours,
        "interval_minutes": interval_minutes,
        "data_points": len(history),
        "history": history
    }
