    def _calculate_metric_stability(self, metrics: MarketMetrics) -> float:
        """Calculate stability of market metrics."""
        try:
            # Check for extreme values
            extremes = sum(
                1 for value in metrics.__dict__.values()
                if value < 0.1 or value > 0.9
            )
            
            # Penalize for extreme values
            stability = 1.0 - (extremes * 0.1)
            
            return max(0.0, stability)
        except Exception as e:
            print(f"Error calculating metric stability: {str(e)}")
            return 0.5

    def _calculate_indicator_consistency(self, indicators: Dict[str, float]) -> float:
        """Calculate consistency of economic indicators."""
        try:
            if not indicators:
                return 0.5

            # Calculate standard deviation of indicators
            values = list(indicators.values())
            std_dev = np.std(values)
            
            # Higher consistency with lower standard deviation
            consistency = 1.0 - min(1.0, std_dev)
            
            return consistency
        except Exception as e:
            print(f"Error calculating indicator consistency: {str(e)}")
            return 0.5

    def _analyze_property_trend(self, performance_data: Dict) -> PropertyTrend:
        """Analyze trend for a specific property type."""
        try:
            # Extract key metrics
            recent_growth = performance_data.get('recent_growth', 0.0)
            historical_growth = performance_data.get('historical_growth', 0.0)
            volume_change = performance_data.get('volume_change', 0.0)
            
            # Calculate trend direction (-1 to 1)
            trend_direction = np.tanh(recent_growth)  # Normalize to -1 to 1
            
            # Calculate momentum (0 to 1)
            momentum = abs(recent_growth - historical_growth)
            momentum = min(1.0, momentum)
            
            # Calculate confidence (0 to 1)
            confidence = min(1.0, abs(volume_change))
            
            return PropertyTrend(
                property_type=performance_data.get('type', 'unknown'),
                trend_direction=trend_direction,
                momentum=momentum,
                confidence=confidence
            )
        except Exception as e:
            print(f"Error analyzing property trend: {str(e)}")
            return PropertyTrend('unknown', 0.0, 0.0, 0.0)

    def _generate_trend_recommendations(
        self,
        property_trends: Dict[str, PropertyTrend]
    ) -> List[Dict]:
        """Generate recommendations based on property trends."""
        try:
            recommendations = []
            
            for prop_type, trend in property_trends.items():
                if trend.confidence < 0.3:
                    continue  # Skip low confidence trends
                    
                if trend.trend_direction > 0.3 and trend.momentum > 0.5:
                    recommendations.append({
                        'type': 'opportunity',
                        'property_type': prop_type,
                        'confidence': trend.confidence,
                        'action': 'Increase portfolio allocation',
                        'rationale': f"Strong positive trend with high momentum"
                    })
                elif trend.trend_direction < -0.3 and trend.momentum > 0.5:
                    recommendations.append({
                        'type': 'warning',
                        'property_type': prop_type,
                        'confidence': trend.confidence,
                        'action': 'Reduce exposure',
                        'rationale': f"Strong negative trend with high momentum"
                    })
                elif abs(trend.trend_direction) < 0.2:
                    recommendations.append({
                        'type': 'neutral',
                        'property_type': prop_type,
                        'confidence': trend.confidence,
                        'action': 'Maintain current allocation',
                        'rationale': f"Stable market conditions"
                    })
            
            return sorted(
                recommendations,
                key=lambda x: (x['confidence'], abs(trend.trend_direction)),
                reverse=True
            )
        except Exception as e:
            print(f"Error generating trend recommendations: {str(e)}")
            return []

    async def _get_economic_indicators(self, region_id: str) -> Dict[str, float]:
        """Get economic indicators for a region."""
        try:
            # Implementation would fetch real economic data
            return {
                'interest_rate': 0.05,
                'employment_rate': 0.95,
                'income_growth': 0.03,
                'market_confidence': 0.7
            }
        except Exception as e:
            print(f"Error getting economic indicators: {str(e)}")
            return {}

    async def _get_property_performance(self, region_id: str) -> Dict:
        """Get performance data for different property types."""
        try:
            # Implementation would fetch real performance data
            return {
                'residential': {
                    'type': 'residential',
                    'recent_growth': 0.08,
                    'historical_growth': 0.05,
                    'volume_change': 0.15
                },
                'commercial': {
                    'type': 'commercial',
                    'recent_growth': 0.03,
                    'historical_growth': 0.04,
                    'volume_change': -0.10
                }
            }
        except Exception as e:
            print(f"Error getting property performance: {str(e)}")
            return {}