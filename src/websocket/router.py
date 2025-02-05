from fastapi import APIRouter, WebSocket, Depends, HTTPException, Query
from fastapi.security import APIKeyHeader
from typing import Optional, List
from datetime import datetime
import asyncio
from .lead_updates import handle_client_connection
from .event_processor import event_processor
from app.services.analytics import WebSocketAnalytics
from app.services.security import validate_api_key, get_client_permissions
from app.monitoring.metrics import ws_metrics

router = APIRouter(prefix="/ws", tags=["WebSocket"])
api_key_header = APIKeyHeader(name="X-API-Key")
analytics = WebSocketAnalytics()


@router.websocket("/leads/{client_id}")
async def leads_endpoint(
    websocket: WebSocket,
    client_id: str,
    regions: Optional[List[str]] = Query(None),
    min_score: Optional[float] = Query(None),
    api_key: Optional[str] = Depends(api_key_header),
):
    """
    Real-time lead updates with AI-driven insights and market analytics
    """
    try:
        permissions = await validate_api_key(api_key)
        await handle_client_connection(
            websocket, client_id, regions, min_score, permissions
        )
    except HTTPException as e:
        await websocket.close(code=4001, reason=str(e))
    except Exception as e:
        await websocket.close(code=4000, reason=str(e))


@router.websocket("/market-events/{client_id}")
async def market_events_endpoint(
    websocket: WebSocket,
    client_id: str,
    regions: Optional[List[str]] = Query(None),
    confidence_threshold: float = Query(0.7, ge=0, le=1),
    api_key: Optional[str] = Depends(api_key_header),
):
    """
    Real-time market events and competitor activity tracking
    """
    try:
        permissions = await validate_api_key(api_key)
        client_regions = await get_client_permissions(client_id, "regions")

        if regions:
            # Validate requested regions against permissions
            invalid_regions = set(regions) - set(client_regions)
            if invalid_regions:
                raise HTTPException(
                    status_code=403,
                    detail=f"No access to regions: {', '.join(invalid_regions)}",
                )

        await websocket.accept()

        # Start analytics tracking
        session_id = analytics.start_session(client_id, "market_events")

        try:
            while True:
                # Process market events
                market_events = await event_processor.process_market_event(
                    {
                        "regions": regions or client_regions,
                        "threshold": confidence_threshold,
                    }
                )

                if market_events:
                    await websocket.send_json(
                        {
                            "type": "market_events",
                            "events": [event.dict() for event in market_events],
                        }
                    )

                # Process competitor activities
                competitor_activities = await event_processor.track_competitor_activity(
                    {"regions": regions or client_regions}
                )

                if competitor_activities:
                    await websocket.send_json(
                        {
                            "type": "competitor_activity",
                            "activities": [
                                activity.dict() for activity in competitor_activities
                            ],
                        }
                    )

                # Update analytics
                analytics.record_events_sent(
                    session_id, len(market_events) + len(competitor_activities)
                )

                await asyncio.sleep(5)  # Adjust frequency as needed

        except Exception as e:
            logger.error(f"Error in market events stream: {str(e)}")
            raise

        finally:
            analytics.end_session(session_id)

    except HTTPException as e:
        await websocket.close(code=4001, reason=str(e))
    except Exception as e:
        await websocket.close(code=4000, reason=str(e))


@router.websocket("/analytics/{client_id}")
async def analytics_endpoint(
    websocket: WebSocket,
    client_id: str,
    api_key: Optional[str] = Depends(api_key_header),
):
    """
    WebSocket performance metrics and historical analysis
    """
    try:
        await validate_api_key(api_key)
        await websocket.accept()

        while True:
            # Gather performance metrics
            metrics = ws_metrics.get_current_metrics()

            # Get historical analysis
            historical_data = analytics.get_historical_analysis(client_id)

            # Combine and send analytics
            await websocket.send_json(
                {
                    "type": "analytics_update",
                    "timestamp": datetime.utcnow().isoformat(),
                    "metrics": {
                        "current": metrics,
                        "historical": historical_data,
                        "predictions": await analytics.generate_predictions(
                            historical_data
                        ),
                    },
                }
            )

            await asyncio.sleep(15)  # Update every 15 seconds

    except HTTPException as e:
        await websocket.close(code=4001, reason=str(e))
    except Exception as e:
        await websocket.close(code=4000, reason=str(e))
