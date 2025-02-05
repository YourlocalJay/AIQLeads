import random

class ProxyManager:
    """Handles rotating proxies dynamically."""

    def __init__(self, proxies: Optional[List[str]] = None):
        self.proxies = proxies or []

    def get_best_proxy(self, domain: str) -> Optional[str]:
        """Returns the best-performing proxy for a given domain."""
        return random.choice(self.proxies) if self.proxies else None
