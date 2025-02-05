from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator, constr
from enum import Enum


class AnalysisType(str, Enum):
    """Valid types of market analysis."""

    TREND = "trend"
    PREDICTION = "prediction"
    GEOGRAPHIC = "geographic"
    DEMOGRAPHIC = "demographic"
    PRICE = "price"
    CUSTOM = "custom"


class LocationPoint(BaseModel):
    """Geographic location point."""

    longitude: float = Field(..., ge=-180, le=180)
    latitude: float = Field(..., ge=-90, le=90)


class MetricsBase(BaseModel):
    """Base model for market metrics."""

    price_range: List[float] = Field(..., min_items=2, max_items=2)
    property_type: str
    bedrooms: Optional[int] = Field(None, ge=0)
    bathrooms: Optional[int] = Field(None, ge=0)
    square_footage: Optional[float] = Field(None, gt=0)
    year_built: Optional[int] = Field(None, ge=1800, le=datetime.now().year)


class AnalysisParameters(BaseModel):
    """Parameters for market analysis."""

    radius_miles: float = Field(..., gt=0, le=100)
    min_confidence: float = Field(..., ge=0, le=1)
    include_pending: bool = Field(default=True)
    time_window_days: int = Field(..., ge=1, le=365)
    grouping: Optional[str] = None
    filters: Dict[str, Any] = Field(default_factory=dict)


class MarketInsightBase(BaseModel):
    """Base model for market insights."""

    location: LocationPoint
    date_range: List[datetime] = Field(..., min_items=2, max_items=2)
    metrics: MetricsBase
    analysis_type: AnalysisType
    parameters: AnalysisParameters
    tags: List[constr(min_length=1, max_length=50)] = Field(..., max_items=10)

    @validator("date_range")
    def validate_date_range(cls, v):
        """Validate date range order."""
        if v[0] >= v[1]:
            raise ValueError("End date must be after start date")
        if v[0] > datetime.now():
            raise ValueError("Start date cannot be in the future")
        return v


class MarketInsightCreate(MarketInsightBase):
    """Model for creating a new market insight."""

    pass


class MarketInsightUpdate(BaseModel):
    """Model for updating an existing market insight."""

    metrics: Optional[MetricsBase] = None
    parameters: Optional[AnalysisParameters] = None
    results: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    tags: Optional[List[constr(min_length=1, max_length=50)]] = Field(
        None, max_items=10
    )


class MarketInsightInDB(MarketInsightBase):
    """Model for market insight in database."""

    id: int
    user_id: int
    results: Dict[str, Any]
    confidence_score: float = Field(..., ge=0, le=1)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MarketInsightResponse(MarketInsightInDB):
    """Model for market insight API response."""

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class MarketInsightList(BaseModel):
    """Model for listing multiple market insights."""

    items: List[MarketInsightResponse]
    total: int
    page: int
    size: int
    pages: int


class MarketInsightStats(BaseModel):
    """Model for market insight statistics."""

    total_insights: int
    avg_confidence: float
    analysis_types: Dict[str, int]
    recent_tags: List[str]
    date_range: List[datetime]
