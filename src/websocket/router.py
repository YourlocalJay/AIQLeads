from fastapi import APIRouter, WebSocket, Depends, HTTPException
from fastapi.security import APIKeyHeader
from typing import Optional
from .lead_updates import handle_client_connection
from ..auth.dependencies import validate_api_key

router = APIRouter(prefix="/ws", tags=["WebSocket"])
api_key_header = APIKeyHeader(name="X-API-Key")

@router.websocket("/leads/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    api_key: Optional[str] = Depends(api_key_header)
):
    """
    WebSocket endpoint for real-time lead updates.
    Requires API key authentication.
    """
    try:
        # Validate API key before accepting connection
        await validate_api_key(api_key)
        await handle_client_connection(websocket, client_id)
    except HTTPException:
        await websocket.close(code=4001, reason="Invalid API key")
    except Exception as e:
        await websocket.close(code=4000, reason=str(e))

@router.websocket("/system-status/{client_id}")
async def system_status_endpoint(
    websocket: WebSocket,
    client_id: str,
    api_key: Optional[str] = Depends(api_key_header)
):
    """
    WebSocket endpoint for system status updates.
    Includes performance metrics and system health information.
    """
    # TODO: Implement system status updates
    pass