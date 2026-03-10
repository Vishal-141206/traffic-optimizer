"""Video Feed API endpoints for uploading and processing traffic camera feeds."""

import os
import uuid
import asyncio
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.config import settings
from services.traffic_processor import TrafficProcessor
from api.websocket import broadcast_traffic_update

router = APIRouter()

# Storage for uploaded videos
UPLOAD_DIR = "./uploads/videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Active processing tasks
processing_tasks = {}


@router.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    camera_id: int = 1,
    intersection_id: int = 1,
    db: AsyncSession = Depends(get_db)
):
    """Upload a video file for processing."""
    # Validate file type
    allowed_types = ["video/mp4", "video/avi", "video/mpeg", "video/quicktime"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {allowed_types}"
        )
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "mp4"
    filename = f"{file_id}.{file_extension}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Start background processing
    background_tasks.add_task(
        process_video_background,
        file_id,
        filepath,
        camera_id,
        intersection_id
    )
    
    return {
        "status": "uploaded",
        "file_id": file_id,
        "filename": filename,
        "size_bytes": len(content),
        "processing": "started",
        "message": "Video uploaded and processing started. Check /video/status/{file_id} for progress."
    }


async def process_video_background(
    file_id: str,
    filepath: str,
    camera_id: int,
    intersection_id: int
):
    """Background task to process uploaded video."""
    processing_tasks[file_id] = {
        "status": "processing",
        "progress": 0,
        "started_at": datetime.utcnow(),
        "results": []
    }
    
    try:
        processor = TrafficProcessor()
        
        # Process video and get results
        async for result in processor.process_video_file(filepath, camera_id, intersection_id):
            processing_tasks[file_id]["progress"] = result.get("progress", 0)
            processing_tasks[file_id]["results"].append(result)
            
            # Broadcast real-time update
            await broadcast_traffic_update({
                "file_id": file_id,
                "camera_id": camera_id,
                "intersection_id": intersection_id,
                **result
            })
        
        processing_tasks[file_id]["status"] = "completed"
        processing_tasks[file_id]["completed_at"] = datetime.utcnow()
        
    except Exception as e:
        processing_tasks[file_id]["status"] = "error"
        processing_tasks[file_id]["error"] = str(e)


@router.get("/status/{file_id}")
async def get_processing_status(file_id: str):
    """Get the processing status of an uploaded video."""
    if file_id not in processing_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing task not found"
        )
    
    task = processing_tasks[file_id]
    return {
        "file_id": file_id,
        "status": task["status"],
        "progress": task["progress"],
        "started_at": task["started_at"].isoformat(),
        "completed_at": task.get("completed_at", None),
        "error": task.get("error", None),
        "results_count": len(task.get("results", []))
    }


@router.get("/results/{file_id}")
async def get_processing_results(
    file_id: str,
    skip: int = 0,
    limit: int = 100
):
    """Get the processing results for a video."""
    if file_id not in processing_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing task not found"
        )
    
    task = processing_tasks[file_id]
    results = task.get("results", [])
    
    return {
        "file_id": file_id,
        "total_results": len(results),
        "results": results[skip:skip + limit]
    }


@router.post("/simulate")
async def start_simulation(
    background_tasks: BackgroundTasks,
    intersection_id: int = 1,
    duration_seconds: int = 60
):
    """Start a simulated traffic feed for testing."""
    sim_id = str(uuid.uuid4())
    
    background_tasks.add_task(
        run_simulation,
        sim_id,
        intersection_id,
        duration_seconds
    )
    
    return {
        "simulation_id": sim_id,
        "intersection_id": intersection_id,
        "duration_seconds": duration_seconds,
        "status": "started"
    }


async def run_simulation(sim_id: str, intersection_id: int, duration: int):
    """Run traffic simulation."""
    import random
    
    processing_tasks[sim_id] = {
        "status": "simulating",
        "progress": 0,
        "started_at": datetime.utcnow(),
        "results": []
    }
    
    start_time = datetime.utcnow()
    frame_count = 0
    fps = 2  # Simulated frames per second
    
    while (datetime.utcnow() - start_time).seconds < duration:
        frame_count += 1
        
        # Generate simulated detection data
        vehicles = {
            "car": random.randint(0, 15),
            "bus": random.randint(0, 3),
            "truck": random.randint(0, 5),
            "motorcycle": random.randint(0, 8),
            "bicycle": random.randint(0, 4)
        }
        
        total = sum(vehicles.values())
        
        # Determine congestion level
        if total <= 10:
            congestion = "low"
            density = round(random.uniform(0.1, 0.3), 2)
        elif total <= 20:
            congestion = "medium"
            density = round(random.uniform(0.3, 0.6), 2)
        elif total <= 30:
            congestion = "high"
            density = round(random.uniform(0.6, 0.85), 2)
        else:
            congestion = "critical"
            density = round(random.uniform(0.85, 1.0), 2)
        
        # Random chance of emergency vehicle
        emergency_detected = random.random() < 0.02
        
        result = {
            "frame": frame_count,
            "timestamp": datetime.utcnow().isoformat(),
            "intersection_id": intersection_id,
            "vehicles": vehicles,
            "total_vehicles": total,
            "congestion_level": congestion,
            "density": density,
            "emergency_detected": emergency_detected,
            "emergency_type": "ambulance" if emergency_detected else None,
            "progress": min(100, int((datetime.utcnow() - start_time).seconds / duration * 100))
        }
        
        processing_tasks[sim_id]["results"].append(result)
        processing_tasks[sim_id]["progress"] = result["progress"]
        
        # Broadcast update
        await broadcast_traffic_update(result)
        
        await asyncio.sleep(1 / fps)
    
    processing_tasks[sim_id]["status"] = "completed"
    processing_tasks[sim_id]["completed_at"] = datetime.utcnow()


@router.delete("/upload/{file_id}")
async def delete_upload(file_id: str):
    """Delete an uploaded video and its processing data."""
    # Find and delete file
    for filename in os.listdir(UPLOAD_DIR):
        if filename.startswith(file_id):
            os.remove(os.path.join(UPLOAD_DIR, filename))
            break
    
    # Remove processing data
    if file_id in processing_tasks:
        del processing_tasks[file_id]
    
    return {"status": "deleted", "file_id": file_id}
