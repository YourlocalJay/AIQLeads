from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
from collections import defaultdict
import logging
from app.services.ai_recommendations import get_smart_lead_suggestions
from app.services.market_analytics import analyze_market_trends, detect_market_shifts
from app.services.competitor_analysis import track_competitor_movements

logger = logging.getLogger("websocket.events")


class MarketEvent(BaseModel):
    event_type: str
    timestamp: datetime
    region: str
    confidence: float
    details: Dict[str, Any]
    predicted_impact: float


class CompetitorActivity(BaseModel):
    competitor_id: str
    activity_type: str
    region: str
    timestamp: datetime
    details: Dict[str, Any]
    threat_level: float


class EventProcessor:
    def __init__(self):
        self.market_events: List[MarketEvent] = []
        self.competitor_activities: Dict[str, List[CompetitorActivity]] = defaultdict(
            list
        )
        self.region_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.alert_thresholds = {
            "market_shift": 0.7,
            "competitor_threat": 0.8,
            "lead_opportunity": 0.75,
        }

    async def process_market_event(self, event_data: dict) -> Optional[MarketEvent]:
        """Process and analyze market events with AI classification"""
        try:
            # Analyze market trends and detect shifts
            market_trends = await analyze_market_trends(event_data["region"])
            shift_detection = await detect_market_shifts(
                region=event_data["region"],
                historical_data=self.market_events[-50:] if self.market_events else [],
            )

            # Calculate event significance and impact
            event = MarketEvent(
                event_type=event_data["type"],
                timestamp=datetime.utcnow(),
                region=event_data["region"],
                confidence=shift_detection["confidence"],
                details={
                    "trend_direction": market_trends["direction"],
                    "velocity": market_trends["velocity"],
                    "key_factors": market_trends["factors"],
                    "historical_correlation": shift_detection["correlation"],
                },
                predicted_impact=shift_detection["predicted_impact"],
            )

            self.market_events.append(event)
            self._update_region_stats(event)

            return (
                event
                if event.confidence >= self.alert_thresholds["market_shift"]
                else None
            )

        except Exception as e:
            logger.error(f"Error processing market event: {str(e)}")
            return None

    async def track_competitor_activity(
        self, activity_data: dict
    ) -> Optional[CompetitorActivity]:
        """Monitor and analyze competitor activities"""
        try:
            competitor_movements = await track_competitor_movements(
                competitor_id=activity_data["competitor_id"],
                region=activity_data["region"],
            )

            activity = CompetitorActivity(
                competitor_id=activity_data["competitor_id"],
                activity_type=activity_data["type"],
                region=activity_data["region"],
                timestamp=datetime.utcnow(),
                details={
                    "movement_pattern": competitor_movements["pattern"],
                    "market_impact": competitor_movements["impact"],
                    "strategy_indicators": competitor_movements["indicators"],
                },
                threat_level=competitor_movements["threat_level"],
            )

            self.competitor_activities[activity.competitor_id].append(activity)
            return (
                activity
                if activity.threat_level >= self.alert_thresholds["competitor_threat"]
                else None
            )

        except Exception as e:
            logger.error(f"Error tracking competitor activity: {str(e)}")
            return None

    async def generate_lead_insights(
        self, region: str, lead_data: dict
    ) -> Dict[str, Any]:
        """Generate AI-driven insights for lead prioritization"""
        try:
            # Get market context and competitor landscape
            market_context = self._get_recent_market_events(region)
            competitor_context = self._get_competitor_activities(region)

            # Generate smart lead suggestions with context
            lead_insights = await get_smart_lead_suggestions(
                lead_data=lead_data,
                market_context=market_context,
                competitor_context=competitor_context,
            )

            return {
                "priority_score": lead_insights["priority_score"],
                "opportunity_level": lead_insights["opportunity_level"],
                "market_timing": lead_insights["timing_analysis"],
                "competitive_advantage": lead_insights["competitive_position"],
                "recommended_actions": lead_insights["recommendations"],
            }

        except Exception as e:
            logger.error(f"Error generating lead insights: {str(e)}")
            return {}

    def _get_recent_market_events(
        self, region: str, hours: int = 24
    ) -> List[MarketEvent]:
        """Get recent market events for a region"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [
            event
            for event in self.market_events
            if event.region == region and event.timestamp >= cutoff
        ]

    def _get_competitor_activities(
        self, region: str, hours: int = 24
    ) -> List[CompetitorActivity]:
        """Get recent competitor activities in a region"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        activities = []
        for competitor_activities in self.competitor_activities.values():
            activities.extend(
                [
                    activity
                    for activity in competitor_activities
                    if activity.region == region and activity.timestamp >= cutoff
                ]
            )
        return activities

    def _update_region_stats(self, event: MarketEvent):
        """Update regional statistics with new event data"""
        region = event.region
        stats = self.region_stats[region]

        # Update event counts
        stats["event_count"] = stats.get("event_count", 0) + 1
        stats["last_update"] = event.timestamp

        # Update moving averages
        stats["avg_confidence"] = (
            stats.get("avg_confidence", event.confidence) * 0.9 + event.confidence * 0.1
        )
        stats["avg_impact"] = (
            stats.get("avg_impact", event.predicted_impact) * 0.9
            + event.predicted_impact * 0.1
        )


event_processor = EventProcessor()
