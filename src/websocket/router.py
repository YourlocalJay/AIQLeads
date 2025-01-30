from fastapi import APIRouter, WebSocket, Depends, HTTPException, WebSocketDisconnect
from fastapi.security import APIKeyHeader
from typing import Optional, Dict, Set, List
import asyncio
import logging
from datetime import datetime
import json
from collections import defaultdict
from functools import lru_cache

from .lead_updates import handle_client_connection
from ..auth.dependencies import validate_api_key
from ..monitoring.system_status import get_system_metrics
from ..services.cache import redis_client  # Redis for connection state
from ..services.metrics import ws_metrics  # Monitoring service

router = APIRouter(prefix="/ws", tags=["WebSocket"])
api_key_header = APIKeyHeader(name="X-API-Key")

logger = logging.getLogger("websocket")

# Connection manager for WebSocket state
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str):
        """Register a new WebSocket connection"""
        async with self._lock:
            await websocket.accept()
            self.active_connections[client_id].add(websocket)
            ws_metrics.connection_opened(client_id)

    async def disconnect(self, websocket: WebSocket, client_id: str):
        """Clean up disconnected WebSocket"""
        async with self._lock:
            self.active_connections[client_id].discard(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
            ws_metrics.connection_closed(client_id)

    async def broadcast(self, client_id: str, message: dict):
        """Send message to all connections for a client"""
        if client_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[client_id]:
                try:
                    await connection.send_json(message)
                except WebSocketDisconnect:
                    disconnected.add(connection)
            
            # Clean up disconnected clients
            if disconnected:
                async with self._lock:
                    self.active_connections[client_id] = \
                        self.active_connections[client_id] - disconnected

manager = ConnectionManager()

@router.websocket("/leads/{client_id}")
async def websocket_leads_endpoint(
    websocket: WebSocket,
    client_id: str,
    api_key: Optional[str] = Depends(api_key_header)
):
    """
    WebSocket endpoint for real-time lead updates.
    Requires API key authentication.
    """
    try:
        # Validate API key
        await validate_api_key(api_key)
        await manager.connect(websocket, client_id)

        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Handle client connection
        await handle_client_connection(websocket, client_id)

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected from lead updates.")
    except HTTPException as e:
        await websocket.close(code=4001, reason=str(e.detail))
    except Exception as e:
        logger.error(f"Error in WebSocket connection for {client_id}: {str(e)}", exc_info=True)
        await websocket.close(code=4000, reason=str(e))
    finally:
        await manager.disconnect(websocket, client_id)

@router.websocket("/system-status/{client_id}")
async def websocket_system_status_endpoint(
    websocket: WebSocket,
    client_id: str,
    api_key: Optional[str] = Depends(api_key_header)
):
    """
    WebSocket endpoint for system status updates.
    Includes performance metrics and system health information.
    """
    try:
        await validate_api_key(api_key)
        await manager.connect(websocket, client_id)

        # Heartbeat task
        heartbeat_task = asyncio.create_task(send_heartbeats(websocket))

        while True:
            # Get system metrics
            system_metrics = await get_system_metrics()

            # Send system status updates to the client
            await websocket.send_json(system_metrics)
            await asyncio.sleep(5)  # Adjust polling interval as needed

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected from system status updates.")
    except Exception as e:
        logger.error(f"Error in system status WebSocket for {client_id}: {str(e)}", exc_info=True)
        await websocket.close(code=4000, reason=str(e))
    finally:
        heartbeat_task.cancel()
        await manager.disconnect(websocket, client_id)

@router.websocket("/events/{client_id}")
async def websocket_events_endpoint(
    websocket: WebSocket,
    client_id: str,
    api_key: Optional[str] = Depends(api_key_header)
):
    """
    WebSocket endpoint for AI-powered event tracking.
    Sends real-time notifications on high-value leads and market changes.
    """
    try:
        await validate_api_key(api_key)
        await manager.connect(websocket, client_id)

        # Heartbeat task
        heartbeat_task = asyncio.create_task(send_heartbeats(websocket))

        while True:
            # Get AI event data
            ai_event_data = await detect_ai_events()
            await websocket.send_json(ai_event_data)

            await asyncio.sleep(10)  # Adjust event detection polling rate

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected from AI event updates.")
    except Exception as e:
        logger.error(f"Error in AI events WebSocket for {client_id}: {str(e)}", exc_info=True)
        await websocket.close(code=4000, reason=str(e))
    finally:
        heartbeat_task.cancel()
        await manager.disconnect(websocket, client_id)

async def send_heartbeats(websocket: WebSocket, interval: int = 30):
    """Maintain connection with regular heartbeats"""
    while True:
        try:
            await asyncio.sleep(interval)
            await websocket.send_json({
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat()
            })
        except WebSocketDisconnect:
            break
        except Exception as e:
            logger.warning(f"Heartbeat failed: {str(e)}")
            break

@lru_cache(maxsize=1000)
async def detect_ai_events():
    """
    Simulated AI event detection function with caching.
    """
    return {
        "event_type": "high_priority_lead",
        "details": {
            "lead_id": "12345",
            "score": 0.95,
            "market_trend": "expanding"
        }
    }
