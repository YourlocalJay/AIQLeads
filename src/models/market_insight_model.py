from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from sqlalchemy.exc import SQLAlchemyError
from src.database import Base


class MarketInsight(Base):
    """
    Market Insight model for analytics and regional market data.
    Handles aggregated market statistics, trends, and geospatial analysis.
    """
    __tablename__ = 'market_insights'

    id = Column(Integer, primary_key=True)
    region_name = Column(String(100), nullable=False)
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)

    # Market Statistics
    median_price = Column(Float, nullable=False)
    avg_price = Column(Float, nullable=False)
    price_per_sqft = Column(Float, nullable=False)
    inventory_count = Column(Integer, nullable=False)
    avg_days_on_market = Column(Float, nullable=False)

    # Property Type Distribution
    property_type_distribution = Column(JSONB, nullable=False, default=dict)

    # Trend Data
    price_trends = Column(JSONB, nullable=False, default=dict)
    demand_metrics = Column(JSONB, nullable=False, default=dict)

    # Temporal Data
    analysis_period_start = Column(DateTime, nullable=False)
    analysis_period_end = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="market_insights")

    # Indexes
    __table_args__ = (
        Index('ix_market_insights_region', region_name),
        Index('ix_market_insights_created_at', created_at),
        Index('idx_market_insights_location', location, postgresql_using='gist'),
    )

    def update_price_trends(self, trends: dict) -> None:
        """Update price trend data with validated metrics."""
        required_keys = {'weekly', 'monthly', 'quarterly', 'yearly'}
        if not all(key in trends for key in required_keys):
            raise ValueError("Missing required trend periods")
        self.price_trends = trends
        self.updated_at = datetime.utcnow()

    def update_demand_metrics(self, metrics: dict) -> None:
        """Update demand metrics with validated indicators."""
        required_keys = {'views', 'inquiries', 'offers'}
        if not all(key in metrics for key in required_keys):
            raise ValueError("Missing required demand metrics")
        self.demand_metrics = metrics
        self.updated_at = datetime.utcnow()

    def get_nearby_insights(self, radius_miles: float = 5.0) -> Optional[List['MarketInsight']]:
        """Retrieve market insights within a specified radius."""
        from sqlalchemy import func
        meters_per_mile = 1609.34
        radius_meters = radius_miles * meters_per_mile
        try:
            return (
                MarketInsight.query
                .filter(
                    func.ST_DWithin(
                        MarketInsight.location,
                        self.location,
                        radius_meters
                    )
                )
                .filter(MarketInsight.id != self.id)
                .all()
            )
        except SQLAlchemyError as e:
            print(f"Database query failed: {e}")
            return None

    def calculate_market_velocity(self) -> float:
        """Calculate market velocity based on inventory and days on market."""
        if self.avg_days_on_market == 0:
            return 0.0
        return (self.inventory_count / self.avg_days_on_market) * 100

    def to_dict(self) -> dict:
        """Convert market insight to dictionary representation."""
        location_data = None
        if self.location:
            location_data = {
                'lat': float(self.location.latitude),
                'lng': float(self.location.longitude)
            }

        return {
            'id': self.id,
            'region_name': self.region_name,
            'location': location_data,
            'median_price': self.median_price,
            'avg_price': self.avg_price,
            'price_per_sqft': self.price_per_sqft,
            'inventory_count': self.inventory_count,
            'avg_days_on_market': self.avg_days_on_market,
            'property_type_distribution': self.property_type_distribution,
            'price_trends': self.price_trends,
            'demand_metrics': self.demand_metrics,
            'analysis_period_start': self.analysis_period_start.isoformat() if self.analysis_period_start else None,
            'analysis_period_end': self.analysis_period_end.isoformat() if self.analysis_period_end else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self) -> str:
        """String representation of the Market Insight model."""
        return f'<MarketInsight {self.region_name}>'
    def __repr__(self) -> str:
        """String representation of the MarketInsight model."""
        return f'<MarketInsight {self.analysis_type} {self.created_at}>'
