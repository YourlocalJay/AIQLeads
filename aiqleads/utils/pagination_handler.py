from typing import Any, Dict, Optional, AsyncGenerator
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from app.services.logging import logger

class PaginationHandler:
    """Handles paginated data extraction in AIQLeads scrapers."""

    @staticmethod
    async def handle_pagination(
        scraper,
        base_url: str,
        max_pages: int = 10,
        pagination_selector: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Yields data for each paginated page up to max_pages."""
        current_url = base_url
        current_page = 1

        while current_page <= max_pages:
            try:
                page_data = await scraper._safe_fetch(current_url)
                if not page_data:
                    break

                yield page_data

                next_url = await PaginationHandler._find_next_page_url(
                    current_url, page_data, pagination_selector
                )
                if not next_url:
                    break

                current_url = next_url
                current_page += 1
            except Exception as e:
                logger.error(f"Pagination error: {e}")
                break

    @staticmethod
    async def _find_next_page_url(
        current_url: str,
        page_data: Dict[str, Any],
        pagination_selector: Optional[str] = None,
    ) -> Optional[str]:
        """Extracts the next page URL from scraped HTML content."""
        try:
            soup = BeautifulSoup(page_data.get("html_content", ""), "html.parser")
            if pagination_selector:
                next_link = soup.select_one(pagination_selector)
                if next_link and "href" in next_link.attrs:
                    return urljoin(current_url, next_link["href"])
            return None
        except Exception as e:
            logger.error(f"Pagination parsing failed: {e}")
            return None
