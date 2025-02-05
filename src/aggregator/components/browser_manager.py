import random
from typing import Dict, Optional
from playwright.async_api import async_playwright, Browser, Page

from app.core.config import settings
from app.services.logging import logger
from .request_fingerprint import RequestFingerprinter
from ..exceptions import BrowserError


class PersistentBrowserManager:
    """
    Manages persistent browser sessions per domain
    """

    _instance = None
    _browser: Optional[Browser] = None
    _sessions: Dict[str, Page] = {}

    @classmethod
    async def get_instance(cls):
        """
        Get singleton instance

        Returns:
            PersistentBrowserManager: Singleton instance

        Raises:
            BrowserError: If browser initialization fails
        """
        if not cls._instance:
            cls._instance = PersistentBrowserManager()
            await cls._instance._initialize()
        return cls._instance

    async def _initialize(self):
        """
        Initialize browser instance

        Raises:
            BrowserError: If browser initialization fails
        """
        try:
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(
                headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
        except Exception as e:
            raise BrowserError(f"Failed to initialize browser: {e}")

    async def get_session(self, domain: str) -> Page:
        """
        Get or create browser session for domain

        Args:
            domain: Target domain

        Returns:
            Page: Browser page instance

        Raises:
            BrowserError: If session creation fails
        """
        try:
            if not self._browser:
                await self._initialize()

            # Clean up old sessions if limit reached
            if len(self._sessions) >= settings.MAX_BROWSER_SESSIONS:
                oldest_domain = next(iter(self._sessions))
                await self._sessions[oldest_domain].close()
                del self._sessions[oldest_domain]

            # Create new session if needed
            if domain not in self._sessions:
                self._sessions[domain] = await self._browser.new_page()
                await self._sessions[domain].set_extra_http_headers(
                    {"User-Agent": random.choice(RequestFingerprinter.USER_AGENTS)}
                )

            return self._sessions[domain]

        except Exception as e:
            raise BrowserError(f"Failed to get browser session for {domain}: {e}")

    async def close_sessions(self):
        """
        Close all browser sessions and cleanup
        """
        try:
            for session in self._sessions.values():
                await session.close()

            if self._browser:
                await self._browser.close()

            self._sessions.clear()
            self._browser = None

        except Exception as e:
            logger.error(f"Error closing browser sessions: {e}")

    def __del__(self):
        """Cleanup on deletion"""
        try:
            import asyncio

            asyncio.create_task(self.close_sessions())
        except Exception as e:
            logger.error(f"Error in browser manager cleanup: {e}")
