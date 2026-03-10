"""WebSocket API for real-time updates."""

import asyncio
import json
from typing import Dict, Set
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.redis import get_redis, RedisManager

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        # Store connections by channel
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "traffic": set(),
            "signals": set(),
            "emergency": set(),
            "all": set()
        }
    
    async def connect(self, websocket: WebSocket, channel: str = "all"):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)
        self.active_connections["all"].add(websocket)
    
    def disconnect(self, websocket: WebSocket, channel: str = "all"):
        """Remove a WebSocket connection."""
        for ch in self.active_connections:
            self.active_connections[ch].discard(websocket)
    
    async def broadcast(self, message: dict, channel: str = "all"):
        """Broadcast a message to all connections in a channel."""
        if channel in self.active_connections:
            disconnected = []
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            
            # Cleanup disconnected
            for conn in disconnected:
                self.disconnect(conn)
    
    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send a message to a specific connection."""
        await websocket.send_json(message)


manager = ConnectionManager()


@router.websocket("/traffic")
async def websocket_traffic(websocket: WebSocket):
    """WebSocket endpoint for traffic updates."""
    await manager.connect(websocket, "traffic")
    try:
        while True:
            # Keep connection alive and receive any client messages
            data = await websocket.receive_text()
            
            # Handle subscription requests
            try:
                message = json.loads(data)
                if message.get("type") == "subscribe":
                    intersection_id = message.get("intersection_id")
                    await manager.send_personal(websocket, {
                        "type": "subscribed",
                        "intersection_id": intersection_id,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, "traffic")


@router.websocket("/signals")
async def websocket_signals(websocket: WebSocket):
    """WebSocket endpoint for signal state updates."""
    await manager.connect(websocket, "signals")
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await manager.send_personal(websocket, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, "signals")


@router.websocket("/emergency")
async def websocket_emergency(websocket: WebSocket):
    """WebSocket endpoint for emergency alerts."""
    await manager.connect(websocket, "emergency")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "emergency")


@router.websocket("/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket endpoint for dashboard updates (all channels)."""
    await manager.connect(websocket, "all")
    
    # Send welcome message
    await manager.send_personal(websocket, {
        "type": "connected",
        "message": "Connected to traffic dashboard",
        "timestamp": datetime.utcnow().isoformat()
    })
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                msg_type = message.get("type")
                
                if msg_type == "ping":
                    await manager.send_personal(websocket, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                elif msg_type == "request_update":
                    # Client requesting immediate update
                    await manager.send_personal(websocket, {
                        "type": "update_pending",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, "all")


# Background task to broadcast traffic updates
async def broadcast_traffic_update(update_data: dict):
    """Broadcast traffic update to all connected clients."""
    await manager.broadcast({
        "type": "traffic_update",
        "data": update_data,
        "timestamp": datetime.utcnow().isoformat()
    }, "traffic")
    
    await manager.broadcast({
        "type": "traffic_update",
        "data": update_data,
        "timestamp": datetime.utcnow().isoformat()
    }, "all")


async def broadcast_signal_update(signal_data: dict):
    """Broadcast signal state update."""
    await manager.broadcast({
        "type": "signal_update",
        "data": signal_data,
        "timestamp": datetime.utcnow().isoformat()
    }, "signals")
    
    await manager.broadcast({
        "type": "signal_update",
        "data": signal_data,
        "timestamp": datetime.utcnow().isoformat()
    }, "all")


async def broadcast_emergency_alert(alert_data: dict):
    """Broadcast emergency alert."""
    await manager.broadcast({
        "type": "emergency_alert",
        "data": alert_data,
        "timestamp": datetime.utcnow().isoformat()
    }, "emergency")
    
    await manager.broadcast({
        "type": "emergency_alert",
        "data": alert_data,
        "timestamp": datetime.utcnow().isoformat()
    }, "all")


# Export manager and broadcast functions
__all__ = [
    "manager",
    "broadcast_traffic_update",
    "broadcast_signal_update",
    "broadcast_emergency_alert"
]
