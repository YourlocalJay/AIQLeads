"""
MVP Data Collection using BrightData
"""

from typing import List, Dict, Any
import asyncio
import aiohttp
from ..core.config import (
    BRIGHTDATA_USERNAME,
    BRIGHTDATA_PASSWORD,
    BRIGHTDATA_ZONE,
    SCRAPING_BATCH_SIZE,
    SCRAPING_DELAY,
)


class DataCollector:
    def __init__(self):
        self.auth = aiohttp.BasicAuth(BRIGHTDATA_USERNAME, BRIGHTDATA_PASSWORD)
        self.base_url = f"https://{BRIGHTDATA_ZONE}.brightdata.com"
        self.session = None
        self.batch_size = SCRAPING_BATCH_SIZE
        self.delay = SCRAPING_DELAY

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(auth=self.auth)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def collect_leads(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collect leads based on search criteria"""
        leads = []
        try:
            raw_data = await self._fetch_listings(criteria)
            leads = self._process_listings(raw_data)
        except Exception as e:
            print(f"Error collecting leads: {str(e)}")
        return leads

    async def _fetch_listings(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch real estate listings from source"""
        listings = []
        page = 1

        while len(listings) < self.batch_size:
            try:
                params = self._build_params(criteria, page)
                async with self.session.get(
                    f"{self.base_url}/search", params=params
                ) as response:
                    if response.status != 200:
                        break

                    data = await response.json()
                    if not data.get("listings"):
                        break

                    listings.extend(data["listings"])
                    page += 1
                    await asyncio.sleep(self.delay)

            except Exception as e:
                print(f"Error on page {page}: {str(e)}")
                break

        return listings[: self.batch_size]

    def _build_params(self, criteria: Dict[str, Any], page: int) -> Dict[str, Any]:
        """Build search parameters"""
        return {
            "location": criteria.get("location", ""),
            "price_min": criteria.get("price_min", 0),
            "price_max": criteria.get("price_max", 9999999),
            "property_type": criteria.get("property_type", "any"),
            "page": page,
            "limit": min(50, self.batch_size),
        }

    def _process_listings(self, listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process raw listings into leads"""
        leads = []
        for listing in listings:
            try:
                lead = {
                    "id": listing.get("id"),
                    "location": listing.get("location", {}).get("address"),
                    "price": listing.get("price", 0),
                    "type": listing.get("propertyType"),
                    "features": listing.get("features", []),
                    "listing_age": listing.get("daysOnMarket", 0),
                    "property_value": listing.get("estimatedValue", 0),
                    "location_score": self._calculate_location_score(listing),
                    "market_trend": self._get_market_trend(listing),
                }
                leads.append(lead)
            except Exception as e:
                print(f"Error processing listing: {str(e)}")
                continue
        return leads

    def _calculate_location_score(self, listing: Dict[str, Any]) -> float:
        """Calculate basic location score"""
        score = 70.0  # Base score

        # Basic scoring for MVP
        if listing.get("location", {}).get("schools", []):
            score += 10
        if listing.get("location", {}).get("shopping", []):
            score += 5
        if listing.get("location", {}).get("transit", []):
            score += 5

        return min(max(score, 0), 100)

    def _get_market_trend(self, listing: Dict[str, Any]) -> float:
        """Get simple market trend score"""
        # Basic trend for MVP
        market_data = listing.get("marketData", {})
        trend = market_data.get("priceChange", 0)
        return min(max(50 + trend, 0), 100)
