"""
Rate limiting to respect domain bandwidth and avoid blocks.
"""

import time
from typing import Dict
from urllib.parse import urlparse
from config import SCRAPER_CONFIG
from utils.logger import get_logger


logger = get_logger(__name__)


class RateLimiter:
    """
    Per-domain rate limiter.
    Tracks last request time per domain and enforces delays.
    """

    def __init__(self, delay_seconds: float = SCRAPER_CONFIG["rate_limit_delay"]):
        self.delay_seconds = delay_seconds
        self.last_request_time: Dict[str, float] = {}

    def wait_if_needed(self, url: str):
        """
        Wait if necessary to respect rate limit for this domain.
        """
        domain = self._extract_domain(url)

        if domain in self.last_request_time:
            elapsed = time.time() - self.last_request_time[domain]
            if elapsed < self.delay_seconds:
                wait_time = self.delay_seconds - elapsed
                logger.debug(f"⏱️  Rate limit: waiting {wait_time:.2f}s for {domain}")
                time.sleep(wait_time)

        self.last_request_time[domain] = time.time()

    def reset_domain(self, url: str):
        """Reset rate limit counter for a domain."""
        domain = self._extract_domain(url)
        if domain in self.last_request_time:
            del self.last_request_time[domain]
            logger.debug(f"🔄 Rate limit reset for {domain}")

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc or parsed.path
        except Exception:
            return "unknown"
