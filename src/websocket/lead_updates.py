from fastapi import WebSocket, WebSocketDisconnect, status
from typing import Dict, List, Optional
import json
import asyncio
import weakref
from datetime import datetime, timedelta
from pydantic import BaseModel, ValidationError
import logging
from collections import defaultdict
from app.services.security import validate_websocket_token  # Auth service
from app.services.metrics import ws_metrics  # Monitoring service
from app.services.ai_recommendations import (
    get_smart_lead_suggestions,
)  # AI-powered lead filtering

logger = logging.getLogger("websocket")


class SubscriptionFilter(BaseModel):
    lead_types: Optional[List[str]] = None
    min_score: Optional[float] = None
    regions: Optional[List[str]] = None
    max_price: Optional[float] = None
    min_update_frequency: int = 5  # Seconds between updates


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, weakref.WeakSet[WebSocket]] = defaultdict(
            weakref.WeakSet
        )
        self.subscriptions: Dict[WebSocket, SubscriptionFilter] = {}
        self.rate_limits: Dict[WebSocket, datetime] = {}
        self.HEARTBEAT_INTERVAL = 30
        self.HEARTBEAT_TIMEOUT = 45

    async def authenticate(self, websocket: WebSocket, token: str) -> str:
        """Authenticate connection and return client ID"""
        try:
            client_id = await validate_websocket_token(token)
            await websocket.send_json({"type": "auth_success", "client_id": client_id})
            return client_id
        except Exception as e:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(e))
            raise

    async def connect(self, websocket: WebSocket, client_id: str):
        """Register connection with default subscriptions"""
        await websocket.accept()
        self.active_connections[client_id].add(websocket)
        self.subscriptions[websocket] = SubscriptionFilter()
        ws_metrics.connection_opened(client_id)

    async def disconnect(self, websocket: WebSocket, client_id: str):
        """Cleanup connection resources"""
        self.active_connections[client_id].discard(websocket)
        if not self.active_connections[client_id]:
            del self.active_connections[client_id]
        self.subscriptions.pop(websocket, None)
        self.rate_limits.pop(websocket, None)
        ws_metrics.connection_closed(client_id)

    async def update_subscription(self, websocket: WebSocket, filters: dict):
        """Update client's subscription filters"""
        try:
            sub = SubscriptionFilter(**filters)
            self.subscriptions[websocket] = sub
            await websocket.send_json(
                {"type": "subscription_updated", "filters": sub.dict()}
            )
        except ValidationError as e:
            await self.send_error(websocket, "invalid_filter", str(e))

    async def enforce_rate_limit(self, websocket: WebSocket) -> bool:
        """Token bucket rate limiting implementation"""
        now = datetime.now()
        last_message = self.rate_limits.get(websocket, now - timedelta(seconds=10))

        if (now - last_message).total_seconds() < 0.5:  # 2 messages/sec
            await self.send_error(websocket, "rate_limit", "Message rate exceeded")
            return False

        self.rate_limits[websocket] = now
        return True

    async def broadcast_lead(self, lead: dict):
        """Distribute lead to subscribed clients with matching filters"""
        for websocket, subscription in self.subscriptions.items():
            if self._matches_filters(lead, subscription):
                try:
                    await websocket.send_json(lead)
                    ws_metrics.message_sent()
                except WebSocketDisconnect:
                    await self.handle_disconnect(websocket)

    def _matches_filters(self, lead: dict, subscription: SubscriptionFilter) -> bool:
        """Check if lead matches client's subscription filters"""
        return (
            (not subscription.lead_types or lead["type"] in subscription.lead_types)
            and (
                subscription.min_score is None
                or lead["score"] >= subscription.min_score
            )
            and (not subscription.regions or lead["region"] in subscription.regions)
            and (
                subscription.max_price is None
                or lead["price"] <= subscription.max_price
            )
        )

    async def handle_disconnect(self, websocket: WebSocket):
        """Cleanup disconnected websocket"""
        for client_id, connections in self.active_connections.items():
            if websocket in connections:
                await self.disconnect(websocket, client_id)
                break


async def handle_client_connection(websocket: WebSocket, client_id: str):
    """Main WebSocket connection handler with heartbeat & AI recommendations"""
    try:
        token = await websocket.receive_text()
        client_id = await manager.authenticate(websocket, token)

        await manager.connect(websocket, client_id)
        last_activity = datetime.now()

        heartbeat_task = asyncio.create_task(
            send_heartbeats(websocket, manager.HEARTBEAT_INTERVAL)
        )

        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(), timeout=manager.HEARTBEAT_TIMEOUT
                )
                last_activity = datetime.now()

                if not await manager.enforce_rate_limit(websocket):
                    continue

                message = json.loads(data)

                if message["type"] == "update_subscription":
                    await manager.update_subscription(websocket, message["filters"])

                elif message["type"] == "ping":
                    await websocket.send_json({"type": "pong"})

                elif message["type"] == "get_ai_recommendations":
                    ai_suggestions = await get_smart_lead_suggestions(client_id)
                    await websocket.send_json(
                        {"type": "recommendations", "data": ai_suggestions}
                    )

            except asyncio.TimeoutError:
                if (
                    datetime.now() - last_activity
                ).total_seconds() > manager.HEARTBEAT_TIMEOUT:
                    raise WebSocketDisconnect()

    finally:
        heartbeat_task.cancel()
        await manager.handle_disconnect(websocket)


async def send_heartbeats(websocket: WebSocket, interval: int):
    """Maintain connection with regular heartbeats"""
    while True:
        try:
            await asyncio.sleep(interval)
            await websocket.send_json(
                {"type": "heartbeat", "timestamp": datetime.utcnow().isoformat()}
            )
        except WebSocketDisconnect:
            break
