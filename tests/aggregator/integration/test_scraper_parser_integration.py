import pytest
import asyncio
from typing import List
from unittest.mock import Mock, patch
from src.aggregator.scrapers import ZillowScraper, FacebookScraper
from src.aggregator.parsers import ZillowParser, FacebookParser
from src.models.lead import Lead
from src.config import settings

class TestScraperParserIntegration:
    @pytest.fixture
    async def zillow_integration(self):
        scraper = ZillowScraper(api_key=settings.ZILLOW_API_KEY, rate_limit=100)
        parser = ZillowParser()
        return scraper, parser

    @pytest.fixture
    async def facebook_integration(self):
        scraper = FacebookScraper(api_key=settings.FACEBOOK_API_KEY, rate_limit=100)
        parser = FacebookParser()
        return scraper, parser

    @pytest.mark.asyncio
    async def test_zillow_end_to_end(self, zillow_integration):
        """Test complete Zillow data pipeline from scraping to parsing"""
        scraper, parser = zillow_integration
        mock_listings = [
            {
                "zpid": "12345",
                "address": {
                    "streetAddress": "123 Main St",
                    "city": "San Francisco",
                    "state": "CA",
                    "zipcode": "94105"
                },
                "price": 1200000,
                "bedrooms": 3,
                "bathrooms": 2,
                "livingArea": 2000,
                "yearBuilt": 1985,
                "latitude": 37.7749,
                "longitude": -122.4194
            }
        ]

        with patch.object(scraper, 'fetch_listings') as mock_fetch:
            mock_fetch.return_value = mock_listings
            
            # Simulate scraping
            listings = await scraper.fetch_listings(
                location="San Francisco, CA",
                max_price=2000000
            )
            
            # Parse scraped data
            leads: List[Lead] = [parser.parse(listing) for listing in listings]
            
            assert len(leads) == 1
            lead = leads[0]
            assert isinstance(lead, Lead)
            assert lead.address == "123 Main St, San Francisco, CA 94105"
            assert lead.price == 1200000
            assert lead.source == "zillow"

    @pytest.mark.asyncio
    async def test_facebook_end_to_end(self, facebook_integration):
        """Test complete Facebook data pipeline from scraping to parsing"""
        scraper, parser = facebook_integration
        mock_listings = [
            {
                "listing": {
                    "id": "67890",
                    "location": {
                        "address": "456 Market St, San Francisco, CA 94105",
                        "coordinates": {
                            "latitude": 37.7749,
                            "longitude": -122.4194
                        }
                    },
                    "price": {
                        "amount": 750000,
                        "currency": "USD"
                    },
                    "propertyDetails": {
                        "bedrooms": 2,
                        "bathrooms": 1,
                        "squareFeet": 1200
                    }
                }
            }
        ]

        with patch.object(scraper, 'fetch_listings') as mock_fetch:
            mock_fetch.return_value = mock_listings
            
            # Simulate scraping
            listings = await scraper.fetch_listings(
                location="San Francisco, CA",
                max_price=1000000
            )
            
            # Parse scraped data
            leads: List[Lead] = [parser.parse(listing) for listing in listings]
            
            assert len(leads) == 1
            lead = leads[0]
            assert isinstance(lead, Lead)
            assert "456 Market St" in lead.address
            assert lead.price == 750000
            assert lead.source == "facebook"

    @pytest.mark.asyncio
    async def test_data_transformation_consistency(self, zillow_integration, facebook_integration):
        """Test data consistency across different sources"""
        zillow_scraper, zillow_parser = zillow_integration
        facebook_scraper, facebook_parser = facebook_integration

        # Common property details
        property_data = {
            "address": "789 Oak St, San Francisco, CA 94110",
            "price": 900000,
            "bedrooms": 3,
            "bathrooms": 2,
            "square_feet": 1800,
            "latitude": 37.7749,
            "longitude": -122.4194
        }

        # Create source-specific mock data
        zillow_mock = self._create_zillow_mock(property_data)
        facebook_mock = self._create_facebook_mock(property_data)

        with patch.object(zillow_scraper, 'fetch_listings') as zillow_mock_fetch, \
             patch.object(facebook_scraper, 'fetch_listings') as facebook_mock_fetch:
            
            zillow_mock_fetch.return_value = [zillow_mock]
            facebook_mock_fetch.return_value = [facebook_mock]

            # Process data from both sources
            zillow_listings = await zillow_scraper.fetch_listings(location="San Francisco")
            facebook_listings = await facebook_scraper.fetch_listings(location="San Francisco")

            zillow_lead = zillow_parser.parse(zillow_listings[0])
            facebook_lead = facebook_parser.parse(facebook_listings[0])

            # Verify data consistency
            assert zillow_lead.price == facebook_lead.price
            assert zillow_lead.bedrooms == facebook_lead.bedrooms
            assert zillow_lead.bathrooms == facebook_lead.bathrooms
            assert zillow_lead.square_feet == facebook_lead.square_feet
            assert zillow_lead.latitude == facebook_lead.latitude
            assert zillow_lead.longitude == facebook_lead.longitude

    def _create_zillow_mock(self, data):
        """Create Zillow-formatted mock data"""
        return {
            "zpid": "12345",
            "address": {
                "streetAddress": data["address"].split(",")[0],
                "city": "San Francisco",
                "state": "CA",
                "zipcode": "94110"
            },
            "price": data["price"],
            "bedrooms": data["bedrooms"],
            "bathrooms": data["bathrooms"],
            "livingArea": data["square_feet"],
            "latitude": data["latitude"],
            "longitude": data["longitude"]
        }

    def _create_facebook_mock(self, data):
        """Create Facebook-formatted mock data"""
        return {
            "listing": {
                "location": {
                    "address": data["address"],
                    "coordinates": {
                        "latitude": data["latitude"],
                        "longitude": data["longitude"]
                    }
                },
                "price": {
                    "amount": data["price"],
                    "currency": "USD"
                },
                "propertyDetails": {
                    "bedrooms": data["bedrooms"],
                    "bathrooms": data["bathrooms"],
                    "squareFeet": data["square_feet"]
                }
            }
        }