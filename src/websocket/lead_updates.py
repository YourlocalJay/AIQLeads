from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set, List, Any
import json
import asyncio
from datetime import datetime
from pydantic import BaseModel

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        async with self._lock:
            if client_id not in self.active_connections:
                self.active_connections[client_id] = set()
            self.active_connections[client_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, client_id: str):
        async with self._lock:
            if client_id in self.active_connections:
                self.active_connections[client_id].remove(websocket)
                if not self.active_connections[client_id]:
                    del self.active_connections[client_id]

    async def broadcast_to_client(self, client_id: str, message: dict):
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

class LeadUpdate(BaseModel):
    lead_id: int
    status: str
    update_type: str
    timestamp: datetime
    details: Dict[str, Any]

manager = ConnectionManager()

async def broadcast_lead_updates(leads: List[Any]):
    """
    Broadcast lead updates to connected clients.
    This function is called from the lead management controller.
    """
    for lead in leads:
        update = LeadUpdate(
            lead_id=lead.id,
            status="new",
            update_type="creation",
            timestamp=datetime.utcnow(),
            details={
                "score": lead.score,
                "source": lead.lead_source,
                "priority": lead.score * (1 if not hasattr(lead, 'conversion_probability') 
                                       else lead.conversion_probability)
            }
        )
        
        # Broadcast to all clients that should receive this lead update
        # TODO: Implement proper client filtering based on permissions/subscriptions
        for client_id in manager.active_connections.keys():
            await manager.broadcast_to_client(client_id, update.dict())

async def handle_client_connection(websocket: WebSocket, client_id: str):
    """
    Handle individual client WebSocket connections.
    """
    try:
        await manager.connect(websocket, client_id)
        
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Listen for client messages
        while True:
            try:
                data = await websocket.receive_text()
                # Handle client messages (e.g., subscription updates)
                message = json.loads(data)
                # TODO: Implement message handling logic
                
            except WebSocketDisconnect:
                break
                
    finally:
        await manager.disconnect(websocket, client_id)