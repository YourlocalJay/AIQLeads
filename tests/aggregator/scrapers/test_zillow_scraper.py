import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch
from aiohttp import ClientSession, ClientResponse
from src.aggregator.scrapers.zillow_scraper import ZillowScraper
from src.aggregator.exceptions import NetworkError, ParseError
from src.schemas.lead_schema import LeadCreate

@pytest.fixture
def mock_response():
    """Mock successful API response fixture."""
    return {
        'searchResults': {
            'listings': [{
                'id': '12345',
                'propertyType': 'SINGLE_FAMILY',
                'price': 500000,
                'daysOnZillow': 30,
                'isFSBO': False,
                'location': {
                    'latitude': 40.7128,
                    'longitude': -74.0060
                },
                'agent': {
                    'name': 'John Smith',
                    'brokerName': 'Best Realty',
                    'phoneNumber': '+1-234-567-8900',
                    'email': 'john@bestrealty.com'
                }
            }]
        }
    }

@pytest.fixture
def zillow_scraper():
    """Initialize scraper fixture."""
    return ZillowScraper(api_key='test_key')

@pytest.mark.asyncio
async def test_initialization(zillow_scraper):
    """Test scraper initialization."""
    assert zillow_scraper.api_key == 'test_key'
    assert zillow_scraper.rate_limiter is not None
    assert zillow_scraper._session is None
    
    await zillow_scraper.initialize()
    assert isinstance(zillow_scraper._session, ClientSession)
    assert 'Authorization' in zillow_scraper._session._default_headers

@pytest.mark.asyncio
async def test_successful_search(zillow_scraper, mock_response):
    """Test successful listing search."""
    async def mock_post(*args, **kwargs):
        response = Mock(spec=ClientResponse)
        response.status = 200
        response.json = Mock(return_value=mock_response)
        return response
    
    with patch.object(ClientSession, 'post', side_effect=mock_post):
        await zillow_scraper.initialize()
        leads = await zillow_scraper.search('New York, NY')
        
        assert len(leads) == 1
        assert isinstance(leads[0], LeadCreate)
        assert leads[0].company_name == 'Best Realty'
        assert leads[0].contact_name == 'John Smith'
        assert leads[0].email == 'john@bestrealty.com'

@pytest.mark.asyncio
async def test_network_error(zillow_scraper):
    """Test network error handling."""
    async def mock_error_post(*args, **kwargs):
        response = Mock(spec=ClientResponse)
        response.status = 403
        response.text = Mock(return_value='Access denied')
        return response
    
    with patch.object(ClientSession, 'post', side_effect=mock_error_post):
        await zillow_scraper.initialize()
        with pytest.raises(NetworkError) as exc_info:
            await zillow_scraper.search('Invalid Location')
        assert 'Zillow API returned 403' in str(exc_info.value)

@pytest.mark.asyncio
async def test_fsbo_listing(zillow_scraper):
    """Test FSBO listing parsing."""
    fsbo_response = {
        'searchResults': {
            'listings': [{
                'id': '67890',
                'propertyType': 'SINGLE_FAMILY',
                'price': 400000,
                'daysOnZillow': 15,
                'isFSBO': True,
                'location': {
                    'latitude': 40.7128,
                    'longitude': -74.0060
                },
                'owner': {
                    'name': 'Jane Doe',
                    'phoneNumber': '+1-234-567-8901',
                    'email': 'jane@email.com'
                }
            }]
        }
    }
    
    async def mock_post(*args, **kwargs):
        response = Mock(spec=ClientResponse)
        response.status = 200
        response.json = Mock(return_value=fsbo_response)
        return response
    
    with patch.object(ClientSession, 'post', side_effect=mock_post):
        await zillow_scraper.initialize()
        leads = await zillow_scraper.search('New York, NY', fsbo_only=True)
        
        assert len(leads) == 1
        assert leads[0].company_name == 'FSBO'
        assert leads[0].contact_name == 'Jane Doe'
        assert leads[0].metadata['is_fsbo'] is True

@pytest.mark.asyncio
async def test_filter_building(zillow_scraper):
    """Test search filter construction."""
    filters = zillow_scraper._build_filters(
        fsbo_only=True,
        price_min=300000,
        price_max=600000,
        days_on_zillow=30
    )
    
    assert filters['isForSaleByOwner'] is True
    assert filters['price']['min'] == 300000
    assert filters['price']['max'] == 600000
    assert filters['daysOnZillow'] == 30

@pytest.mark.asyncio
async def test_rate_limiting(zillow_scraper):
    """Test rate limit handling."""
    await zillow_scraper.initialize()
    
    # Exhaust rate limit
    zillow_scraper.rate_limiter.tokens = 0
    zillow_scraper.rate_limiter.next_reset = datetime.utcnow()
    
    assert await zillow_scraper.is_rate_limited() is True