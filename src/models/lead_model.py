from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Index, Enum, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geography
from geoalchemy2.functions import ST_Distance, ST_AsText
import enum

from src.database import Base


class LeadStatus(enum.Enum):
    """Enumeration for lead status tracking"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class Lead(Base):
    """Lead model with geospatial capabilities and relationship management"""
    __tablename__ = 'leads'

    # Primary and Foreign Keys
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Contact Information
    company_name = Column(String(200), nullable=False)
    contact_name = Column(String(100))
    contact_title = Column(String(100))
    email = Column(String(255))
    phone = Column(String(20))
    website = Column(String(255))

    # Address Components
    street_address = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100))

    # Geospatial Data
    location = Column(Geography(geometry_type='POINT', srid=4326))
    location_accuracy = Column(Float)
    
    # Business Information
    industry = Column(String(100))
    employee_count = Column(Integer)
    annual_revenue = Column(Float)
    
    # Status and Tracking
    status = Column(Enum(LeadStatus), default=LeadStatus.NEW, nullable=False)
    score = Column(Float)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Extended Attributes
    metadata = Column(JSONB)
    notes = Column(String(1000))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_contact = Column(DateTime)

    # Relationships
    owner = relationship("User", back_populates="leads")

    # Indexes for Optimization
    __table_args__ = (
        Index('ix_leads_status', status),
        Index('ix_leads_owner_id', owner_id),
        Index('ix_leads_company_name', company_name),
        Index('ix_leads_created_at', created_at),
        Index('ix_leads_location', location, postgresql_using='gist'),
    )

    def calculate_distance(self, other_location) -> Optional[float]:
        """Calculate the distance to another location in meters (WGS 84)"""
        if not self.location or not other_location:
            return None
        
        # Use PostGIS ST_Distance to calculate spherical distance
        from sqlalchemy import select
        from sqlalchemy.sql import text
        
        distance = select([func.ST_Distance(
            self.location, 
            other_location,
            use_spheroid=True
        )]).scalar()
        
        return float(distance)

    def to_dict(self) -> dict:
        """Convert lead object to dictionary representation"""
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'company_name': self.company_name,
            'contact_name': self.contact_name,
            'contact_title': self.contact_title,
            'email': self.email,
            'phone': self.phone,
            'website': self.website,
            'street_address': self.street_address,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'country': self.country,
            'location': str(self.location) if self.location else None,
            'location_accuracy': self.location_accuracy,
            'industry': self.industry,
            'employee_count': self.employee_count,
            'annual_revenue': self.annual_revenue,
            'status': self.status.value if self.status else None,
            'score': self.score,
            'is_active': self.is_active,
            'metadata': self.metadata,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_contact': self.last_contact.isoformat() if self.last_contact else None
        }

    def __repr__(self) -> str:
        """String representation of the Lead model"""
        return f'<Lead {self.company_name}>'