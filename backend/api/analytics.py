"""Analytics API endpoints."""

from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract

from core.database import get_db
from models.models import (
    TrafficMetric, VehicleCount, EmergencyEvent, 
    Intersection, SignalStateRecord, CongestionLevel
)

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_data(
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive dashboard data."""
    now = datetime.utcnow()
    last_hour = now - timedelta(hours=1)
    last_day = now - timedelta(days=1)
    
    # Active intersections
    intersections = await db.execute(
        select(func.count(Intersection.id)).where(Intersection.is_active == True)
    )
    active_intersections = intersections.scalar()
    
    # Current vehicle count (from recent metrics)
    vehicles = await db.execute(
        select(func.sum(TrafficMetric.vehicle_count))
        .where(TrafficMetric.timestamp >= last_hour)
    )
    current_vehicles = vehicles.scalar() or 0
    
    # Active emergencies
    emergencies = await db.execute(
        select(func.count(EmergencyEvent.id))
        .where(EmergencyEvent.resolved_at == None)
    )
    active_emergencies = emergencies.scalar()
    
    # Recent congestion distribution
    congestion = await db.execute(
        select(
            TrafficMetric.congestion_level,
            func.count(TrafficMetric.id).label("count")
        )
        .where(TrafficMetric.timestamp >= last_hour)
        .group_by(TrafficMetric.congestion_level)
    )
    congestion_dist = {row.congestion_level.value: row.count for row in congestion}
    
    # Determine overall congestion
    total = sum(congestion_dist.values())
    if total > 0:
        weighted = (
            congestion_dist.get("low", 0) * 1 +
            congestion_dist.get("medium", 0) * 2 +
            congestion_dist.get("high", 0) * 3 +
            congestion_dist.get("critical", 0) * 4
        ) / total
        
        if weighted <= 1.5:
            overall = "low"
        elif weighted <= 2.5:
            overall = "medium"
        elif weighted <= 3.5:
            overall = "high"
        else:
            overall = "critical"
    else:
        overall = "low"
    
    # Recent alerts (last hour emergencies + high congestion)
    recent_emergencies = await db.execute(
        select(EmergencyEvent)
        .where(EmergencyEvent.detected_at >= last_hour)
        .order_by(EmergencyEvent.detected_at.desc())
        .limit(5)
    )
    
    alerts = [
        {
            "type": "emergency",
            "message": f"Emergency vehicle ({e.emergency_type.value}) detected",
            "intersection_id": e.intersection_id,
            "timestamp": e.detected_at.isoformat(),
            "severity": "high"
        }
        for e in recent_emergencies.scalars()
    ]
    
    return {
        "active_intersections": active_intersections,
        "current_vehicles": current_vehicles,
        "active_emergencies": active_emergencies,
        "overall_congestion": overall,
        "congestion_distribution": congestion_dist,
        "recent_alerts": alerts,
        "timestamp": now
    }


@router.get("/traffic-trends")
async def get_traffic_trends(
    hours: int = Query(default=24, le=168),
    interval_minutes: int = Query(default=30, ge=15, le=60),
    db: AsyncSession = Depends(get_db)
):
    """Get traffic trends over time."""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Get all metrics
    result = await db.execute(
        select(TrafficMetric)
        .where(TrafficMetric.timestamp >= since)
        .order_by(TrafficMetric.timestamp)
    )
    metrics = result.scalars().all()
    
    # Group by time intervals
    intervals = {}
    for m in metrics:
        interval_start = m.timestamp.replace(
            minute=(m.timestamp.minute // interval_minutes) * interval_minutes,
            second=0, microsecond=0
        )
        key = interval_start.isoformat()
        
        if key not in intervals:
            intervals[key] = {
                "vehicles": 0,
                "density_sum": 0,
                "count": 0,
                "congestion_scores": []
            }
        
        intervals[key]["vehicles"] += m.vehicle_count
        intervals[key]["density_sum"] += m.density
        intervals[key]["count"] += 1
        intervals[key]["congestion_scores"].append(
            {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(m.congestion_level.value, 1)
        )
    
    trends = []
    for timestamp, data in sorted(intervals.items()):
        avg_congestion = sum(data["congestion_scores"]) / len(data["congestion_scores"])
        trends.append({
            "timestamp": timestamp,
            "total_vehicles": data["vehicles"],
            "avg_density": round(data["density_sum"] / data["count"], 2),
            "avg_congestion_score": round(avg_congestion, 2)
        })
    
    return {
        "period_hours": hours,
        "interval_minutes": interval_minutes,
        "data_points": len(trends),
        "trends": trends
    }


@router.get("/peak-hours")
async def get_peak_hours(
    days: int = Query(default=7, le=30),
    db: AsyncSession = Depends(get_db)
):
    """Analyze peak traffic hours."""
    since = datetime.utcnow() - timedelta(days=days)
    
    # Get metrics grouped by hour
    result = await db.execute(
        select(
            extract('hour', TrafficMetric.timestamp).label('hour'),
            func.avg(TrafficMetric.vehicle_count).label('avg_vehicles'),
            func.avg(TrafficMetric.density).label('avg_density')
        )
        .where(TrafficMetric.timestamp >= since)
        .group_by(extract('hour', TrafficMetric.timestamp))
    )
    
    hourly_data = [
        {
            "hour": int(row.hour),
            "avg_vehicles": round(row.avg_vehicles, 1),
            "avg_density": round(row.avg_density, 2)
        }
        for row in result
    ]
    
    # Sort by vehicles to find peaks
    sorted_hours = sorted(hourly_data, key=lambda x: x["avg_vehicles"], reverse=True)
    peak_hours = [h["hour"] for h in sorted_hours[:3]]
    low_hours = [h["hour"] for h in sorted_hours[-3:]]
    
    return {
        "analysis_days": days,
        "peak_hours": peak_hours,
        "low_traffic_hours": low_hours,
        "hourly_breakdown": sorted(hourly_data, key=lambda x: x["hour"])
    }


@router.get("/intersection/{intersection_id}")
async def get_intersection_analytics(
    intersection_id: int,
    days: int = Query(default=7, le=30),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed analytics for a specific intersection."""
    since = datetime.utcnow() - timedelta(days=days)
    
    # Get intersection info
    intersection = await db.execute(
        select(Intersection).where(Intersection.id == intersection_id)
    )
    intersection = intersection.scalar_one_or_none()
    if not intersection:
        return {"error": "Intersection not found"}
    
    # Traffic metrics
    metrics = await db.execute(
        select(TrafficMetric)
        .where(and_(
            TrafficMetric.intersection_id == intersection_id,
            TrafficMetric.timestamp >= since
        ))
    )
    metrics = metrics.scalars().all()
    
    total_vehicles = sum(m.vehicle_count for m in metrics)
    avg_wait_time = sum(m.wait_time or 0 for m in metrics) / max(len(metrics), 1)
    avg_density = sum(m.density for m in metrics) / max(len(metrics), 1)
    
    # Congestion distribution
    congestion_dist = {}
    for m in metrics:
        level = m.congestion_level.value
        congestion_dist[level] = congestion_dist.get(level, 0) + 1
    
    # Emergency events
    emergencies = await db.execute(
        select(func.count(EmergencyEvent.id))
        .where(and_(
            EmergencyEvent.intersection_id == intersection_id,
            EmergencyEvent.detected_at >= since
        ))
    )
    emergency_count = emergencies.scalar()
    
    # Signal changes
    signals = await db.execute(
        select(func.count(SignalStateRecord.id))
        .where(and_(
            SignalStateRecord.intersection_id == intersection_id,
            SignalStateRecord.started_at >= since
        ))
    )
    signal_changes = signals.scalar()
    
    # Calculate efficiency score (0-100)
    # Based on wait time, congestion, and throughput
    congestion_score = (
        congestion_dist.get("low", 0) * 100 +
        congestion_dist.get("medium", 0) * 70 +
        congestion_dist.get("high", 0) * 40 +
        congestion_dist.get("critical", 0) * 10
    ) / max(sum(congestion_dist.values()), 1)
    
    efficiency_score = min(100, max(0, congestion_score))
    
    return {
        "intersection_id": intersection_id,
        "intersection_name": intersection.name,
        "analysis_period_days": days,
        "total_vehicles_detected": total_vehicles,
        "average_wait_time_seconds": round(avg_wait_time, 1),
        "average_density": round(avg_density, 2),
        "congestion_distribution": congestion_dist,
        "emergency_events": emergency_count,
        "signal_changes": signal_changes,
        "efficiency_score": round(efficiency_score, 1)
    }


@router.get("/vehicle-distribution")
async def get_vehicle_distribution(
    hours: int = Query(default=24, le=168),
    db: AsyncSession = Depends(get_db)
):
    """Get vehicle type distribution."""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    result = await db.execute(
        select(
            VehicleCount.vehicle_type,
            func.sum(VehicleCount.count).label("total")
        )
        .where(VehicleCount.timestamp >= since)
        .group_by(VehicleCount.vehicle_type)
    )
    
    distribution = {row.vehicle_type.value: row.total for row in result}
    total = sum(distribution.values())
    
    percentages = {
        k: round(v / max(total, 1) * 100, 1)
        for k, v in distribution.items()
    }
    
    return {
        "period_hours": hours,
        "total_vehicles": total,
        "distribution": distribution,
        "percentages": percentages
    }


@router.get("/congestion-heatmap")
async def get_congestion_heatmap(
    hours: int = Query(default=24, le=168),
    db: AsyncSession = Depends(get_db)
):
    """Get congestion data for heatmap visualization."""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Get latest congestion for each intersection
    result = await db.execute(
        select(
            Intersection.id,
            Intersection.name,
            Intersection.location_lat,
            Intersection.location_lng,
            TrafficMetric.congestion_level,
            TrafficMetric.density,
            TrafficMetric.vehicle_count
        )
        .join(TrafficMetric, TrafficMetric.intersection_id == Intersection.id)
        .where(TrafficMetric.timestamp >= since)
        .order_by(TrafficMetric.timestamp.desc())
    )
    
    # Deduplicate to get latest per intersection
    seen = set()
    heatmap_data = []
    for row in result:
        if row.id not in seen:
            seen.add(row.id)
            heatmap_data.append({
                "intersection_id": row.id,
                "name": row.name,
                "lat": row.location_lat,
                "lng": row.location_lng,
                "congestion_level": row.congestion_level.value,
                "density": row.density,
                "vehicle_count": row.vehicle_count,
                "intensity": {"low": 0.2, "medium": 0.5, "high": 0.8, "critical": 1.0}.get(
                    row.congestion_level.value, 0.2
                )
            })
    
    return {
        "period_hours": hours,
        "points": len(heatmap_data),
        "data": heatmap_data
    }
