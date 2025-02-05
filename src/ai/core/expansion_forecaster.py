from typing import List, Dict, NamedTuple
import numpy as np
from dataclasses import dataclass


@dataclass
class ExpansionScore:
    region_id: str
    potential_score: float
    market_gap: float
    competition_risk: float
    growth_trajectory: float


class MarketMetrics(NamedTuple):
    lead_density: float
    engagement_rate: float
    conversion_rate: float
    market_size: float
    competition_density: float


class CompetitorActivity(NamedTuple):
    active_listings: int
    market_share: float
    growth_rate: float
    expansion_velocity: float


class ExpansionForecaster:
    def __init__(self):
        self.market_cache: Dict[str, MarketMetrics] = {}
        self.competitor_cache: Dict[str, Dict[str, CompetitorActivity]] = {}
        self.historical_data: Dict[str, List[MarketMetrics]] = {}

    async def _analyze_competitor_presence(self, region_id: str) -> Dict:
        """Analyze competitor presence and activity in region."""
        try:
            if region_id not in self.competitor_cache:
                # Fetch and analyze competitor data
                competitor_data = await self._fetch_competitor_data(region_id)
                self.competitor_cache[region_id] = competitor_data

            competitor_activities = self.competitor_cache[region_id]

            # Calculate aggregate metrics
            total_market_share = sum(
                c.market_share for c in competitor_activities.values()
            )
            avg_growth_rate = np.mean(
                [c.growth_rate for c in competitor_activities.values()]
            )
            expansion_threat = self._calculate_expansion_threat(competitor_activities)

            return {
                "total_competitors": len(competitor_activities),
                "market_concentration": total_market_share,
                "avg_growth_rate": avg_growth_rate,
                "expansion_threat": expansion_threat,
                "competitor_details": {
                    comp_id: {
                        "market_share": activity.market_share,
                        "growth_rate": activity.growth_rate,
                        "expansion_velocity": activity.expansion_velocity,
                    }
                    for comp_id, activity in competitor_activities.items()
                },
            }
        except Exception as e:
            print(f"Error analyzing competitor presence: {str(e)}")
            return {}

    async def _identify_opportunities(
        self, expansion_score: ExpansionScore, competitor_risks: Dict
    ) -> List[Dict]:
        """Identify specific market opportunities."""
        try:
            opportunities = []

            # Market gap opportunities
            if expansion_score.market_gap > 0.3:  # Significant market gap
                opportunities.append(
                    {
                        "type": "market_gap",
                        "score": expansion_score.market_gap,
                        "description": "Significant untapped market potential",
                    }
                )

            # Growth opportunities
            if expansion_score.growth_trajectory > 0.6:  # High growth
                opportunities.append(
                    {
                        "type": "growth",
                        "score": expansion_score.growth_trajectory,
                        "description": "Strong market growth trajectory",
                    }
                )

            # Competitive advantage opportunities
            if expansion_score.competition_risk < 0.4:  # Low competition
                opportunities.append(
                    {
                        "type": "competitive_advantage",
                        "score": 1 - expansion_score.competition_risk,
                        "description": "Favorable competitive landscape",
                    }
                )

            return sorted(opportunities, key=lambda x: x["score"], reverse=True)
        except Exception as e:
            print(f"Error identifying opportunities: {str(e)}")
            return []

    async def _generate_recommendations(
        self, expansion_score: ExpansionScore, opportunities: List[Dict]
    ) -> List[Dict]:
        """Generate strategic recommendations based on opportunities."""
        try:
            recommendations = []

            for opportunity in opportunities:
                if opportunity["type"] == "market_gap":
                    recommendations.append(
                        {
                            "type": "expansion",
                            "priority": (
                                "high" if opportunity["score"] > 0.7 else "medium"
                            ),
                            "action": "Increase market presence",
                            "details": {
                                "target_market_share": min(0.3, opportunity["score"]),
                                "timeframe": (
                                    "3 months"
                                    if opportunity["score"] > 0.7
                                    else "6 months"
                                ),
                                "resource_allocation": self._calculate_resource_allocation(
                                    opportunity["score"]
                                ),
                            },
                        }
                    )
                elif opportunity["type"] == "growth":
                    recommendations.append(
                        {
                            "type": "growth_capture",
                            "priority": "high",
                            "action": "Scale operations",
                            "details": {
                                "growth_target": f"{int(opportunity['score'] * 100)}%",
                                "focus_areas": self._identify_growth_areas(
                                    expansion_score
                                ),
                            },
                        }
                    )

            return recommendations
        except Exception as e:
            print(f"Error generating recommendations: {str(e)}")
            return []

    async def _calculate_growth_trajectory(self, region_id: str) -> float:
        """Calculate growth trajectory based on historical data."""
        try:
            if region_id not in self.historical_data:
                return 0.0

            history = self.historical_data[region_id]
            if len(history) < 2:
                return 0.0

            # Calculate growth rates for key metrics
            growth_rates = []
            for i in range(1, len(history)):
                growth_rate = (
                    (history[i].lead_density - history[i - 1].lead_density)
                    / history[i - 1].lead_density
                    + (history[i].engagement_rate - history[i - 1].engagement_rate)
                    / history[i - 1].engagement_rate
                    + (history[i].conversion_rate - history[i - 1].conversion_rate)
                    / history[i - 1].conversion_rate
                ) / 3.0
                growth_rates.append(growth_rate)

            # Weight recent growth more heavily
            weights = np.exp(np.linspace(-1, 0, len(growth_rates)))
            weighted_growth = np.average(growth_rates, weights=weights)

            return max(0.0, min(1.0, (weighted_growth + 1) / 2))
        except Exception as e:
            print(f"Error calculating growth trajectory: {str(e)}")
            return 0.0

    def _calculate_expansion_threat(
        self, competitor_activities: Dict[str, CompetitorActivity]
    ) -> float:
        """Calculate overall expansion threat from competitors."""
        try:
            threats = []
            for activity in competitor_activities.values():
                threat = (
                    activity.market_share * 0.4
                    + activity.growth_rate * 0.3
                    + activity.expansion_velocity * 0.3
                )
                threats.append(threat)

            return max(threats) if threats else 0.0
        except Exception as e:
            print(f"Error calculating expansion threat: {str(e)}")
            return 0.0

    def _calculate_resource_allocation(self, opportunity_score: float) -> Dict:
        """Calculate recommended resource allocation."""
        base_allocation = opportunity_score * 100
        return {
            "marketing_budget": f"${int(base_allocation * 5000)}",
            "sales_team": max(1, int(base_allocation * 0.1)),
            "support_staff": max(1, int(base_allocation * 0.05)),
        }

    def _identify_growth_areas(self, expansion_score: ExpansionScore) -> List[str]:
        """Identify specific areas for growth focus."""
        growth_areas = []

        if expansion_score.market_gap > 0.4:
            growth_areas.append("market_penetration")
        if expansion_score.potential_score > 0.6:
            growth_areas.append("lead_generation")
        if expansion_score.growth_trajectory > 0.5:
            growth_areas.append("team_expansion")

        return growth_areas
