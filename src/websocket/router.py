from fastapi import APIRouter, WebSocket, Depends, HTTPException, WebSocketDisconnect
from fastapi.security import APIKeyHeader
from typing import Optional, Dict, Set
import asyncio
import logging

from .lead_updates import handle_client_connection
from ..auth.dependencies import validate_api_key
from ..monitoring.system_status import get_system_metrics  # Hypothetical system monitoring module

router = APIRouter(prefix="/ws", tags=["WebSocket"])
api_key_header = APIKeyHeader(name="X-API-Key")

logger = logging.getLogger("websocket")

# Store active WebSocket connections
active_connections: Dict[str, Set[WebSocket]] = {}

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
        await websocket.accept()

        if client_id not in active_connections:
            active_connections[client_id] = set()
        active_connections[client_id].add(websocket)

        logger.info(f"Client {client_id} connected to lead updates.")

        # Handle client connection
        await handle_client_connection(websocket, client_id)

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected from lead updates.")
        active_connections[client_id].remove(websocket)
        if not active_connections[client_id]:
            del active_connections[client_id]

    except HTTPException:
        await websocket.close(code=4001, reason="Invalid API key")
    except Exception as e:
        logger.error(f"Error in WebSocket connection for {client_id}: {str(e)}", exc_info=True)
        await websocket.close(code=4000, reason=str(e))

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
        await websocket.accept()

        logger.info(f"Client {client_id} connected to system status updates.")

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
        await websocket.accept()

        logger.info(f"Client {client_id} subscribed to AI event updates.")

        while True:
            # Hypothetical AI event detection function
            ai_event_data = await detect_ai_events()
            await websocket.send_json(ai_event_data)

            await asyncio.sleep(10)  # Adjust event detection polling rate

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected from AI event updates.")

    except Exception as e:
        logger.error(f"Error in AI events WebSocket for {client_id}: {str(e)}", exc_info=True)
        await websocket.close(code=4000, reason=str(e))

async def detect_ai_events():
    """
    Simulated AI event detection function.
    """
    return {
        "event_type": "high_priority_lead",
        "details": {
            "lead_id": "12345",
            "score": 0.95,
            "market_trend": "expanding"
        }
    }
