import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from geoalchemy2.elements import WKTElement
from src.models.market_insight_model import MarketInsight

class TestMarketInsightModel:
    @pytest.fixture
    def sample_insight(self):
        return MarketInsight(
            analysis_type="trend",
            region_name="Las Vegas Downtown",
            location=WKTElement('POINT(-115.1398 36.1699)', srid=4326),
            confidence_score=0.85,
            median_price=350000,
            avg_price=375000,
            price_per_sqft=250,
            inventory_count=100,
            avg_days_on_market=45,
            analysis_period_start=datetime.utcnow(),
            analysis_period_end=datetime.utcnow() + timedelta(days=30),
            user_id=1
        )

    def test_market_velocity_calculation(self, sample_insight):
        velocity = sample_insight.calculate_market_velocity()
        assert isinstance(velocity, float)
        assert velocity > 0

    def test_price_trends_validation(self, sample_insight):
        valid_trends = {
            'weekly': [100, 110, 120],
            'monthly': [95, 100, 105],
            'quarterly': [90, 95, 100],
            'yearly': [85, 90, 95]
        }
        sample_insight.update_price_trends(valid_trends)
        assert sample_insight.price_trends == valid_trends

    def test_demand_metrics_validation(self, sample_insight):
        valid_metrics = {
            'views': 100,
            'inquiries': 50,
            'offers': 10
        }
        sample_insight.update_demand_metrics(valid_metrics)
        assert sample_insight.demand_metrics == valid_metrics

    def test_to_dict_serialization(self, sample_insight):
        insight_dict = sample_insight.to_dict()
        assert isinstance(insight_dict, dict)
        assert 'market_velocity' in insight_dict
        assert 'location' in insight_dict
        assert isinstance(insight_dict['created_at'], str)