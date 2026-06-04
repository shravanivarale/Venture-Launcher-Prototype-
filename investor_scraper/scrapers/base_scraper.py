"""
Base scraper class with common functionality.
All specific scrapers inherit from this.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import random
import requests
from bs4 import BeautifulSoup

from core.schemas import InvestorRecord
from core.exceptions import ScraperExecutionError
from config import SCRAPER_CONFIG
from utils.logger import get_logger
from utils.retry import retry_with_backoff, with_circuit_breaker
from utils.rate_limiter import RateLimiter


logger = get_logger(__name__)


class BaseScraper(ABC):
    """
    Base class for all scrapers.
    Provides common HTTP, parsing, and error handling utilities.
    """

    def __init__(self, name: str, base_url: str, timeout: int = SCRAPER_CONFIG["timeout"]):
        self.name = name
        self.base_url = base_url
        self.timeout = timeout
        self.rate_limiter = RateLimiter()
        self.failed_urls = []

    @abstractmethod
    def scrape(self) -> List[InvestorRecord]:
        """
        Main scraping method. Must be implemented by subclasses.
        Returns list of investor records.
        """
        pass

    @with_circuit_breaker("base_scraper")
    @retry_with_backoff(max_retries=SCRAPER_CONFIG["max_retries"])
    def fetch_url(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch URL with retry logic, rate limiting, and error handling.
        Returns BeautifulSoup object or None on failure.
        """
        try:
            self.rate_limiter.wait_if_needed(url)

            headers = {
                "User-Agent": self._get_random_user_agent(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": self.base_url,
            }

            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            return BeautifulSoup(response.content, "html.parser")

        except requests.RequestException as e:
            logger.warning(f"❌ Failed to fetch {url}: {str(e)}")
            self.failed_urls.append({"url": url, "error": str(e)})
            raise

    def _get_random_user_agent(self) -> str:
        """Get random user agent to avoid detection."""
        return random.choice(SCRAPER_CONFIG["user_agents"])

    def _extract_text(self, element, default: str = "") -> str:
        """Safely extract text from element."""
        try:
            return element.get_text(strip=True) if element else default
        except Exception:
            return default

    def _extract_attr(self, element, attr: str, default: str = "") -> str:
        """Safely extract attribute from element."""
        try:
            return element.get(attr, default) if element else default
        except Exception:
            return default

    def log_failed_urls(self):
        """Log all failed URLs during scraping."""
        if self.failed_urls:
            logger.warning(
                f"⚠️  {self.name} had {len(self.failed_urls)} failed URLs"
            )
            for entry in self.failed_urls:
                logger.debug(f"   Failed: {entry['url']} - {entry['error']}")
