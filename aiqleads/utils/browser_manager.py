from playwright.async_api import async_playwright, Page
from app.core.config import settings

class PersistentBrowserManager:
    """Handles persistent browser sessions per domain with LRU eviction."""

    _instance = None
    _browser = None
    _sessions = {}

    @classmethod
    async def get_instance(cls):
        if not cls._instance:
            cls._instance = PersistentBrowserManager()
            await cls._instance._initialize()
        return cls._instance

    async def _initialize(self):
        playwright = await async_playwright().start()
        self._browser = await playwright.chromium.launch(headless=True)

    async def get_session(self, domain: str) -> Page:
        """Creates or retrieves a browser session for a given domain."""
        if domain not in self._sessions:
            page = await self._browser.new_page()
            self._sessions[domain] = page
        return self._sessions[domain]

    async def close_sessions(self):
        """Closes all browser sessions."""
        await asyncio.gather(*[session.close() for session in self._sessions.values()])
        await self._browser.close()
