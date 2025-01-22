from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from geoalchemy2 import Geography
from src.database import Base

class MarketInsight(Base):
    """Market Insight model for analytics and trend analysis.
    
    Handles:
    - Market trend analysis
    - Price predictions
    - Geographical insights
    - Historical data analysis
    - Custom analytics reports
    """
    __tablename__ = 'market_insights'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    location = Column(Geography('POINT'), nullable=False)
    date_range = Column(ARRAY(DateTime), nullable=False)
    metrics = Column(JSONB, nullable=False)
    analysis_type = Column(String(50), nullable=False)
    parameters = Column(JSONB, nullable=False)
    results = Column(JSONB, nullable=False)
    confidence_score = Column(Float, nullable=False)
    tags = Column(ARRAY(String), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship('User', back_populates='market_insights')

    # Indexes for query optimization
    __table_args__ = (
        Index('ix_market_insights_user_id', user_id),
        Index('ix_market_insights_location', location, postgresql_using='gist'),
        Index('ix_market_insights_date_range', date_range, postgresql_using='gin'),
        Index('ix_market_insights_analysis_type', analysis_type),
        Index('ix_market_insights_tags', tags, postgresql_using='gin'),
    )

    def __init__(
        self,
        user_id: int,
        location: tuple,
        date_range: List[datetime],
        metrics: dict,
        analysis_type: str,
        parameters: dict,
        results: dict,
        confidence_score: float,
        tags: List[str]
    ):
        """Initialize a market insight.

        Args:
            user_id: ID of the user creating the insight
            location: Tuple of (longitude, latitude)
            date_range: List of start and end dates for the analysis
            metrics: Dictionary of metrics to analyze
            analysis_type: Type of analysis (trend, prediction, etc.)
            parameters: Analysis parameters and configurations
            results: Analysis results and insights
            confidence_score: Confidence level of the analysis (0-1)
            tags: List of tags for categorization
        """
        self.user_id = user_id
        self.location = f'POINT({location[0]} {location[1]})'
        self.date_range = date_range
        self.metrics = metrics
        self.analysis_type = analysis_type
        self.parameters = parameters
        self.results = results
        self.confidence_score = confidence_score
        self.tags = tags

    def update_analysis(
        self,
        metrics: Optional[dict] = None,
        parameters: Optional[dict] = None,
        results: Optional[dict] = None,
        confidence_score: Optional[float] = None
    ) -> None:
        """Update analysis results and parameters.

        Args:
            metrics: New metrics to analyze
            parameters: New analysis parameters
            results: New analysis results
            confidence_score: New confidence score
        """
        if metrics is not None:
            self.metrics = metrics
        if parameters is not None:
            self.parameters = parameters
        if results is not None:
            self.results = results
        if confidence_score is not None:
            self.confidence_score = confidence_score
        self.updated_at = datetime.utcnow()

    def add_tags(self, new_tags: List[str]) -> None:
        """Add new tags to the insight.

        Args:
            new_tags: List of tags to add
        """
        self.tags = list(set(self.tags + new_tags))
        self.updated_at = datetime.utcnow()

    def remove_tags(self, tags_to_remove: List[str]) -> None:
        """Remove tags from the insight.

        Args:
            tags_to_remove: List of tags to remove
        """
        self.tags = [tag for tag in self.tags if tag not in tags_to_remove]
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert insight to dictionary representation.

        Returns:
            Dictionary containing insight data
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'location': self.location,
            'date_range': [date.isoformat() for date in self.date_range],
            'metrics': self.metrics,
            'analysis_type': self.analysis_type,
            'parameters': self.parameters,
            'results': self.results,
            'confidence_score': self.confidence_score,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self) -> str:
        """String representation of the MarketInsight model."""
        return f'<MarketInsight {self.analysis_type} {self.created_at}>'