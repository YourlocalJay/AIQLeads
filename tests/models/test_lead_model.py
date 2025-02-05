import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from geoalchemy2.elements import WKTElement

from src.models.lead_model import Lead, LeadStatus
from src.database import Base


@pytest.fixture
def engine():
    """Create test database engine"""
    return create_engine("postgresql://localhost/test_db")


@pytest.fixture
def session(engine):
    """Create test database session"""
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_new_lead():
    """Test creating a new lead with basic attributes"""
    lead = Lead(
        owner_id=1,
        company_name="Test Company",
        contact_name="John Doe",
        email="contact@testcompany.com",
        status=LeadStatus.NEW,
    )

    assert lead.company_name == "Test Company"
    assert lead.contact_name == "John Doe"
    assert lead.email == "contact@testcompany.com"
    assert lead.status == LeadStatus.NEW
    assert lead.is_active is True
    assert lead.created_at is not None
    assert lead.updated_at is not None


def test_lead_with_location():
    """Test lead creation with geospatial data"""
    point = WKTElement("POINT(-73.935242 40.730610)", srid=4326)

    lead = Lead(
        owner_id=1, company_name="Test Company", location=point, location_accuracy=0.95
    )

    assert lead.location is not None
    assert lead.location_accuracy == 0.95
    assert "POINT" in str(lead.location)


def test_calculate_distance(session):
    """Test distance calculation between two leads"""
    # New York City coordinates
    nyc_point = WKTElement("POINT(-73.935242 40.730610)", srid=4326)
    nyc_lead = Lead(owner_id=1, company_name="NYC Company", location=nyc_point)

    # Los Angeles coordinates
    la_point = WKTElement("POINT(-118.243683 34.052235)", srid=4326)
    la_lead = Lead(owner_id=1, company_name="LA Company", location=la_point)

    session.add(nyc_lead)
    session.add(la_lead)
    session.commit()

    # Calculate distance
    distance = nyc_lead.calculate_distance(la_lead.location)

    # Distance should be approximately 3936 km
    assert distance is not None
    assert 3900000 < distance < 4000000  # Check distance in meters with tolerance


def test_distance_with_null_location():
    """Test distance calculation with null location"""
    lead = Lead(owner_id=1, company_name="Test Company")

    # Distance to null location should return None
    assert lead.calculate_distance(None) is None

    # Distance from lead without location to valid point should return None
    point = WKTElement("POINT(-73.935242 40.730610)", srid=4326)
    assert lead.calculate_distance(point) is None


def test_lead_status_transitions():
    """Test lead status changes"""
    lead = Lead(owner_id=1, company_name="Test Company", status=LeadStatus.NEW)

    assert lead.status == LeadStatus.NEW

    lead.status = LeadStatus.CONTACTED
    assert lead.status == LeadStatus.CONTACTED

    lead.status = LeadStatus.QUALIFIED
    assert lead.status == LeadStatus.QUALIFIED


def test_lead_metadata():
    """Test storing additional metadata"""
    metadata = {
        "source": "LinkedIn",
        "campaign_id": "12345",
        "tags": ["tech", "startup"],
    }

    lead = Lead(owner_id=1, company_name="Test Company", metadata=metadata)

    assert lead.metadata["source"] == "LinkedIn"
    assert "tech" in lead.metadata["tags"]
    assert lead.metadata["campaign_id"] == "12345"


def test_lead_to_dict():
    """Test converting lead object to dictionary"""
    now = datetime.utcnow()
    point = WKTElement("POINT(-73.935242 40.730610)", srid=4326)

    lead = Lead(
        owner_id=1,
        company_name="Test Company",
        contact_name="John Doe",
        location=point,
        status=LeadStatus.NEW,
        created_at=now,
        updated_at=now,
    )

    lead_dict = lead.to_dict()
    assert lead_dict["company_name"] == "Test Company"
    assert lead_dict["contact_name"] == "John Doe"
    assert lead_dict["status"] == "new"
    assert lead_dict["location"] is not None
    assert isinstance(lead_dict["created_at"], str)
    assert isinstance(lead_dict["updated_at"], str)
