from collections import defaultdict
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from app.services.logging import logger
from ..exceptions import ProxyError


class ProxyManager:
    """
    Advanced proxy management with performance tracking and rotation
    """

    def __init__(self, proxies: Optional[List[str]] = None):
        """
        Initialize proxy manager

        Args:
            proxies: List of proxy URLs
        """
        self._proxies = proxies or []
        self._proxy_performance: Dict[str, Dict[str, float]] = defaultdict(
            lambda: defaultdict(float)
        )
        self._last_used_time: Dict[str, Dict[str, datetime]] = defaultdict(
            lambda: defaultdict(datetime.now)
        )
        self._failure_counts: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self._banned_until: Dict[str, Dict[str, datetime]] = defaultdict(
            lambda: defaultdict(datetime.now)
        )
        self._usage_counts: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

    def get_best_proxy(self, domain: str) -> Optional[str]:
        """
        Select best performing proxy for a domain

        Args:
            domain: Target domain

        Returns:
            Optional[str]: Best proxy URL or None

        Raises:
            ProxyError: If no suitable proxies are available
        """
        if not self._proxies:
            return None

        current_time = datetime.now()
        available_proxies = []

        for proxy in self._proxies:
            # Skip banned proxies
            if current_time < self._banned_until[domain][proxy]:
                continue

            # Skip recently used proxies (within 5 seconds)
            if (current_time - self._last_used_time[domain][proxy]).total_seconds() < 5:
                continue

            # Calculate proxy score
            performance_score = self._proxy_performance[domain][proxy]
            usage_penalty = self._usage_counts[domain][proxy] * 0.1
            failure_penalty = self._failure_counts[domain][proxy] * 0.2
            total_score = max(0.1, performance_score - usage_penalty - failure_penalty)

            available_proxies.append((proxy, total_score))

        if not available_proxies:
            all_banned = all(
                current_time < self._banned_until[domain][p] for p in self._proxies
            )
            if all_banned:
                raise ProxyError("All proxies are temporarily banned", domain=domain)
            return None

        # Select proxy with highest score
        best_proxy = max(available_proxies, key=lambda x: x[1])[0]
        self._last_used_time[domain][best_proxy] = current_time
        self._usage_counts[domain][best_proxy] += 1

        return best_proxy

    def report_proxy_success(self, domain: str, proxy: str):
        """
        Record successful proxy usage

        Args:
            domain: Target domain
            proxy: Proxy URL
        """
        if proxy not in self._proxies:
            return

        current_score = self._proxy_performance[domain][proxy]
        self._proxy_performance[domain][proxy] = min(1.0, current_score + 0.1)
        self._failure_counts[domain][proxy] = max(
            0, self._failure_counts[domain][proxy] - 1
        )

    def report_proxy_failure(
        self, domain: str, proxy: str, status_code: Optional[int] = None
    ):
        """
        Record proxy failure and update ban status

        Args:
            domain: Target domain
            proxy: Proxy URL
            status_code: HTTP status code if available
        """
        if proxy not in self._proxies:
            return

        self._failure_counts[domain][proxy] += 1
        current_score = self._proxy_performance[domain][proxy]
        self._proxy_performance[domain][proxy] = max(0.0, current_score * 0.8)

        # Ban proxy temporarily based on failure count
        failures = self._failure_counts[domain][proxy]
        if failures >= 3:
            ban_duration = min(
                30 * (2 ** (failures - 3)), 3600
            )  # Exponential backoff, max 1 hour
            self._banned_until[domain][proxy] = datetime.now() + timedelta(
                seconds=ban_duration
            )

            logger.warning(
                f"Proxy {proxy} banned for {ban_duration}s due to {failures} failures on {domain}"
            )

    def add_proxy(self, proxy: str):
        """
        Add new proxy to pool

        Args:
            proxy: Proxy URL to add
        """
        if proxy not in self._proxies:
            self._proxies.append(proxy)

    def remove_proxy(self, proxy: str):
        """
        Remove proxy from pool

        Args:
            proxy: Proxy URL to remove
        """
        if proxy in self._proxies:
            self._proxies.remove(proxy)

    def reset_proxy(self, domain: str, proxy: str):
        """
        Reset all stats for a proxy on a domain

        Args:
            domain: Target domain
            proxy: Proxy URL
        """
        self._proxy_performance[domain][proxy] = 0.5  # Neutral score
        self._failure_counts[domain][proxy] = 0
        self._usage_counts[domain][proxy] = 0
        self._banned_until[domain][proxy] = datetime.now()
        self._last_used_time[domain][proxy] = datetime.now()

    def get_proxy_stats(self, domain: str, proxy: str) -> Dict[str, float]:
        """
        Get current stats for a proxy

        Args:
            domain: Target domain
            proxy: Proxy URL

        Returns:
            Dict[str, float]: Proxy statistics
        """
        current_time = datetime.now()
        return {
            "performance_score": self._proxy_performance[domain][proxy],
            "failure_count": self._failure_counts[domain][proxy],
            "usage_count": self._usage_counts[domain][proxy],
            "banned_remaining": max(
                0, (self._banned_until[domain][proxy] - current_time).total_seconds()
            ),
        }
