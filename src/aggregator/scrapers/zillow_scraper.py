import aiohttp
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup

from src.aggregator.base_scraper import BaseScraper
from src.schemas.lead_schema import LeadCreate, CoordinatePoint
from src.aggregator.exceptions import NetworkError, ParseError, LocationError
import logging

logger = logging.getLogger(__name__)

class ZillowScraper(BaseScraper):
    """Scraper implementation for Zillow real estate listings."""
    
    BASE_URL = "https://www.zillow.com/graphql"
    SEARCH_OPERATION = "FullRenderQuery"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Zillow scraper with optional API credentials."""
        super().__init__(rate_limit=100, time_window=60)
        self.api_key = api_key
        self._session = None
    
    async def initialize(self) -> None:
        """Set up HTTP session with required headers."""
        if self._session is None:
            self._session = aiohttp.ClientSession(headers={
                'User-Agent': 'AIQLeads/1.0',
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.api_key}' if self.api_key else ''
            })
    
    async def search(self, location: str, radius_km: float = 50.0, **kwargs) -> List[LeadCreate]:
        """Search for FSBO and agent listings in the specified location."""
        try:
            logger.info(f"Starting Zillow search for location: {location}, radius: {radius_km} km")
            await self.rate_limiter.acquire()
            
            variables = {
                'location': location,
                'radius': radius_km,
                'filters': self._build_filters(**kwargs)
            }
            
            query = self._get_search_query()
            async with self._session.post(
                self.BASE_URL,
                json={
                    'operationName': self.SEARCH_OPERATION,
                    'query': query,
                    'variables': variables
                }
            ) as response:
                if response.status != 200:
                    raise NetworkError(
                        f"Zillow API returned {response.status}",
                        response=await response.text()
                    )
                
                data = await response.json()
                return await self._parse_listings(data)
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error during Zillow scraping: {e}")
            raise NetworkError(f"Failed to connect to Zillow: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing Zillow response: {e}")
            raise ParseError(f"Failed to process Zillow response: {str(e)}")
    
    async def extract_contact_info(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract contact information from listing data."""
        try:
            contact_info = {
                'email': None,
                'phone': None,
                'company_name': None,
                'contact_name': None
            }
            
            # Extract contact details from listing
            if 'listing' in listing_data:
                agent_data = listing_data['listing'].get('agent', {})
                contact_info.update({
                    'contact_name': agent_data.get('name'),
                    'company_name': agent_data.get('brokerName'),
                    'phone': agent_data.get('phoneNumber'),
                    'email': agent_data.get('email')
                })
            
            # For FSBO listings
            if listing_data.get('isFSBO'):
                owner_data = listing_data.get('owner', {})
                contact_info.update({
                    'contact_name': owner_data.get('name'),
                    'phone': owner_data.get('phoneNumber'),
                    'email': owner_data.get('email')
                })
            
            if not contact_info['phone'] and not contact_info['email']:
                raise ParseError("Contact information is incomplete.")
            
            return contact_info
            
        except Exception as e:
            logger.error(f"Failed to extract contact info: {e}")
            raise ParseError(f"Failed to extract contact info: {str(e)}")
    
    def _build_filters(self, **kwargs) -> Dict[str, Any]:
        """Build search filters from kwargs."""
        filters = {
            'isForSaleByOwner': kwargs.get('fsbo_only', False),
            'isNewConstruction': kwargs.get('new_construction', False),
            'daysOnZillow': kwargs.get('days_on_zillow'),
            'price': {
                'min': kwargs.get('price_min'),
                'max': kwargs.get('price_max')
            }
        }
        # Remove None values
        return {k: v for k, v in filters.items() if v is not None}
    
    async def _parse_listings(self, data: Dict[str, Any]) -> List[LeadCreate]:
        """Parse raw listing data into LeadCreate objects."""
        leads = []
        listings = data.get('searchResults', {}).get('listings', [])
        
        for listing in listings:
            try:
                contact_info = await self.extract_contact_info(listing)
                location = listing.get('location', {})
                
                lead = LeadCreate(
                    company_name=contact_info['company_name'] or 'FSBO',
                    contact_name=contact_info['contact_name'],
                    email=contact_info['email'],
                    phone=contact_info['phone'],
                    location=CoordinatePoint(
                        latitude=location.get('latitude'),
                        longitude=location.get('longitude')
                    ) if location else None,
                    metadata={
                        'property_type': listing.get('propertyType'),
                        'price': listing.get('price'),
                        'zillow_id': listing.get('id'),
                        'days_on_market': listing.get('daysOnZillow'),
                        'is_fsbo': listing.get('isFSBO', False)
                    }
                )
                leads.append(lead)
                
            except Exception as e:
                self.add_error('parse_error', f"Failed to parse listing: {str(e)}", 
                             {'listing_id': listing.get('id')})
                continue
        
        return leads
    
    def _get_search_query(self) -> str:
        """Get GraphQL query for property search."""
        return """
        query FullRenderQuery($location: String!, $filters: SearchFilters, $radius: Float) {
            searchResults(location: $location, filters: $filters, radius: $radius) {
                listings {
                    id
                    propertyType
                    price
                    daysOnZillow
                    isFSBO
                    location {
                        latitude
                        longitude
                    }
                    agent {
                        name
                        brokerName
                        phoneNumber
                        email
                    }
                    owner @include(if: $filters.isForSaleByOwner) {
                        name
                        phoneNumber
                        email
                    }
                }
            }
        }
        """
