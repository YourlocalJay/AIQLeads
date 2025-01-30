from typing import Dict, List, Optional
from dataclasses import dataclass
import numpy as np

@dataclass
class SignalWeights:
    intent: float = 0.35
    market: float = 0.25
    regional: float = 0.20
    trends: float = 0.20

class SignalProcessor:
    def __init__(self, weights: Optional[SignalWeights] = None):
        self.weights = weights or SignalWeights()

    def calculate_weighted_scores(
        self,
        property_data: Dict,
        intent_score: float,
        market_score: float,
        regional_score: float,
        trend_score: float
    ) -> Dict:
        """Calculate weighted scores for a property."""
        final_score = (
            intent_score * self.weights.intent +
            market_score * self.weights.market +
            regional_score * self.weights.regional +
            trend_score * self.weights.trends
        )

        return {
            'final_score': final_score,
            'component_scores': {
                'intent_score': intent_score,
                'market_score': market_score,
                'regional_score': regional_score,
                'trend_score': trend_score
            }
        }

    def generate_match_reasons(self, component_scores: Dict) -> List[str]:
        """Generate human-readable reasons for property match."""
        reasons = []
        thresholds = {
            'high': 0.8,
            'medium': 0.6
        }

        score_messages = {
            'intent_score': {
                'high': "Strongly matches your preferences",
                'medium': "Aligns with your preferences"
            },
            'market_score': {
                'high': "Excellent market potential",
                'medium': "Good market conditions"
            },
            'regional_score': {
                'high': "Prime location",
                'medium': "Desirable area"
            },
            'trend_score': {
                'high': "Strong current demand",
                'medium': "Growing interest"
            }
        }

        for score_type, score in component_scores.items():
            if score > thresholds['high']:
                reasons.append(score_messages[score_type]['high'])
            elif score > thresholds['medium']:
                reasons.append(score_messages[score_type]['medium'])

        return reasons

    def predict_property_trends(
        self,
        property_data: Dict,
        component_scores: Dict,
        market_data: Dict
    ) -> Dict:
        """Predict future trends for a property."""
        try:
            value_trend = (
                market_data.get('value_forecast', 1.0) *
                component_scores['market_score']
            )
            
            demand_trend = (
                market_data.get('demand_forecast', 1.0) *
                component_scores['trend_score']
            )

            return {
                'value_trend': value_trend,
                'demand_trend': demand_trend,
                'predicted_appreciation': value_trend * 0.1,
                'market_stability': self.calculate_market_stability(market_data),
                'competition_forecast': self.forecast_competition(property_data, market_data)
            }
        except Exception as e:
            print(f"Error predicting property trends: {str(e)}")
            return {}

    def calculate_market_stability(self, market_data: Dict) -> float:
        """Calculate market stability score."""
        try:
            # Key factors for stability
            price_volatility = market_data.get('price_volatility', 0.5)
            demand_consistency = market_data.get('demand_consistency', 0.5)
            inventory_turnover = market_data.get('inventory_turnover', 0.5)

            # Lower volatility is better for stability
            stability_score = (
                (1 - price_volatility) * 0.4 +
                demand_consistency * 0.3 +
                (1 - abs(0.5 - inventory_turnover)) * 0.3
            )

            return max(0.0, min(1.0, stability_score))
        except Exception as e:
            print(f"Error calculating market stability: {str(e)}")
            return 0.5

    def forecast_competition(self, property_data: Dict, market_data: Dict) -> Dict:
        """Forecast future competition levels."""
        try:
            # Current competition metrics
            current_inventory = market_data.get('current_inventory', 0)
            new_listings_rate = market_data.get('new_listings_rate', 0)
            market_absorption = market_data.get('absorption_rate', 0)

            # Calculate projected inventory
            projected_inventory = max(0, current_inventory + 
                (new_listings_rate - market_absorption))

            # Calculate competition intensity
            competition_intensity = min(1.0, projected_inventory / 
                market_data.get('optimal_inventory', current_inventory))

            return {
                'projected_inventory': projected_inventory,
                'competition_intensity': competition_intensity,
                'market_pressure': self.calculate_market_pressure(
                    competition_intensity,
                    market_data
                )
            }
        except Exception as e:
            print(f"Error forecasting competition: {str(e)}")
            return {}

    def calculate_market_pressure(
        self,
        competition_intensity: float,
        market_data: Dict
    ) -> str:
        """Calculate market pressure level."""
        try:
            demand_supply_ratio = market_data.get('demand_supply_ratio', 1.0)
            pressure_score = competition_intensity / demand_supply_ratio

            if pressure_score < 0.33:
                return "low"
            elif pressure_score < 0.66:
                return "moderate"
            else:
                return "high"
        except Exception as e:
            print(f"Error calculating market pressure: {str(e)}")
            return "moderate"