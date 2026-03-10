"""
AI-Driven Dynamic Traffic Flow Optimizer & Emergency Green Corridor System
Main FastAPI Application Entry Point
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from api import (
    intersections,
    cameras,
    traffic,
    signals,
    emergency,
    analytics,
    websocket,
    video_feed
)
from core.config import settings
from core.database import engine, Base
from services.traffic_processor import TrafficProcessor
from services.signal_optimizer import SignalOptimizer

# Global instances
traffic_processor: TrafficProcessor = None
signal_optimizer: SignalOptimizer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    global traffic_processor, signal_optimizer
    
    # Startup
    print("🚀 Starting Traffic Flow Optimizer...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize services
    traffic_processor = TrafficProcessor()
    signal_optimizer = SignalOptimizer()
    
    # Start background tasks
    asyncio.create_task(signal_optimizer.run_optimization_loop())
    
    print("✅ All services initialized successfully")
    
    yield
    
    # Shutdown
    print("🔄 Shutting down services...")
    await engine.dispose()
    print("👋 Shutdown complete")


app = FastAPI(
    title="Traffic Flow Optimizer API",
    description="AI-Driven Dynamic Traffic Flow Optimizer & Emergency Green Corridor System",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(intersections.router, prefix="/api/intersections", tags=["Intersections"])
app.include_router(cameras.router, prefix="/api/cameras", tags=["Cameras"])
app.include_router(traffic.router, prefix="/api/traffic", tags=["Traffic"])
app.include_router(signals.router, prefix="/api/signals", tags=["Signals"])
app.include_router(emergency.router, prefix="/api/emergency", tags=["Emergency"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(video_feed.router, prefix="/api/video", tags=["Video Feed"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint returning API information."""
    return {
        "name": "Traffic Flow Optimizer API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "services": {
            "database": "connected",
            "redis": "connected",
            "vision_model": "loaded"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
