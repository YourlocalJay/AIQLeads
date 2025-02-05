from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional

from app.services.logging import logger
from ..exceptions import RateLimitExceeded


class RateLimiter:
    """
    Dynamic rate limiting with adaptive adjustment based on response patterns
    """

    def __init__(self, default_rate_limit: int = 10):
        """
        Initialize rate limiter

        Args:
            default_rate_limit: Default requests per minute limit
        """
        self._rate_limits: Dict[str, int] = defaultdict(lambda: default_rate_limit)
        self._request_timestamps: Dict[str, List[datetime]] = defaultdict(list)
        self._error_counters: Dict[str, int] = defaultdict(int)
        self._last_adjustment: Dict[str, datetime] = defaultdict(datetime.now)

    def can_make_request(self, domain: str) -> bool:
        """
        Check if a request can be made for a specific domain

        Args:
            domain: Target domain

        Returns:
            bool: Whether request is allowed

        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        current_time = datetime.now()
        rate_limit = self._rate_limits[domain]
        timestamps = self._request_timestamps[domain]

        # Remove timestamps older than one minute
        timestamps[:] = [
            ts for ts in timestamps if (current_time - ts).total_seconds() <= 60
        ]

        if len(timestamps) < rate_limit:
            timestamps.append(current_time)
            return True

        wait_time = 60 - (current_time - timestamps[0]).total_seconds()
        raise RateLimitExceeded(
            f"Rate limit exceeded for {domain}. Try again in {wait_time:.1f} seconds",
            domain=domain,
            rate_limit=rate_limit,
            wait_time=wait_time,
        )

    def record_error(self, domain: str, status_code: Optional[int] = None):
        """
        Adjust rate limit based on errors

        Args:
            domain: Target domain
            status_code: HTTP status code
        """
        current_time = datetime.now()
        self._error_counters[domain] += 1

        # Check if enough time has passed since last adjustment
        if (current_time - self._last_adjustment[domain]).total_seconds() < 60:
            return

        # Reduce rate limit on repeated errors or 429 status
        if status_code == 429 or self._error_counters[domain] > 5:
            current_limit = self._rate_limits[domain]
            new_limit = max(1, current_limit // 2)  # Reduce by 50%, minimum 1
            self._rate_limits[domain] = new_limit

            logger.warning(
                f"Rate limit reduced for {domain}: {current_limit} -> {new_limit}"
            )

            # Reset error counter and update adjustment time
            self._error_counters[domain] = 0
            self._last_adjustment[domain] = current_time

    def record_success(self, domain: str):
        """
        Gradually increase rate limit after successful requests

        Args:
            domain: Target domain
        """
        current_time = datetime.now()

        # Check if enough time has passed since last adjustment
        if (current_time - self._last_adjustment[domain]).total_seconds() < 300:
            return

        current_limit = self._rate_limits[domain]
        new_limit = min(30, int(current_limit * 1.2))  # 20% increase, max 30

        if new_limit > current_limit:
            self._rate_limits[domain] = new_limit
            self._error_counters[domain] = 0
            self._last_adjustment[domain] = current_time

            logger.info(
                f"Rate limit increased for {domain}: {current_limit} -> {new_limit}"
            )

    def get_rate_limit(self, domain: str) -> int:
        """
        Get current rate limit for domain

        Args:
            domain: Target domain

        Returns:
            int: Current rate limit
        """
        return self._rate_limits[domain]

    def reset(self, domain: str):
        """
        Reset rate limit state for domain

        Args:
            domain: Target domain
        """
        self._request_timestamps[domain].clear()
        self._error_counters[domain] = 0
        self._last_adjustment[domain] = datetime.now()
