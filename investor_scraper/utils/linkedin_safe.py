"""
LinkedIn-safe extraction strategy.
Uses Google SERP queries instead of direct LinkedIn scraping.
Respects LinkedIn ToS by not using login automation or JavaScript rendering.
"""

import re
from typing import Optional, List, Dict
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup

from config import LINKEDIN_CONFIG, SCRAPER_CONFIG
from utils.logger import get_logger
from utils.retry import retry_with_backoff
from utils.rate_limiter import RateLimiter


logger = get_logger(__name__)


class LinkedInSafeExtractor:
    """
    Extract LinkedIn profile URLs and info using Google SERP queries.
    This approach:
    - Does NOT login to LinkedIn
    - Does NOT use JavaScript automation on LinkedIn
    - Does NOT scrape private profile data
    - Uses publicly available Google search results
    - Respects LinkedIn ToS
    """

    def __init__(self):
        self.rate_limiter = RateLimiter(delay_seconds=3)
        self.user_agent = SCRAPER_CONFIG["user_agents"][0]

    @retry_with_backoff(max_retries=2, exceptions=(requests.RequestException,))
    def search_linkedin_profile(self, investor_name: str) -> Optional[Dict]:
        """
        Search for LinkedIn profile using Google SERP.
        Returns profile URL and headline if found.
        """
        try:
            # Construct Google search query
            query = f'site:linkedin.com/in "{investor_name}"'
            search_url = f"https://www.google.com/search?q={quote(query)}"

            self.rate_limiter.wait_if_needed(search_url)

            # Fetch Google search results
            headers = {"User-Agent": self.user_agent}
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse results
            soup = BeautifulSoup(response.content, "html.parser")
            results = self._parse_google_results(soup)

            if results:
                logger.debug(
                    f"✅ Found LinkedIn profile for {investor_name}: "
                    f"{results.get('profile_url')}"
                )
                return results

            logger.debug(f"❌ No LinkedIn profile found for {investor_name}")
            return None

        except Exception as e:
            logger.warning(
                f"⚠️  LinkedIn search failed for {investor_name}: {str(e)}"
            )
            return None

    def _parse_google_results(self, soup: BeautifulSoup) -> Optional[Dict]:
        """
        Parse Google SERP results to extract LinkedIn profile URL.
        Only extracts publicly available information.
        """
        try:
            # Find search result links
            for result in soup.find_all("a"):
                href = result.get("href", "")

                # Check if it's a LinkedIn profile link
                if "linkedin.com/in/" in href and "/url?q=" in href:
                    # Extract actual URL from Google redirect
                    actual_url = href.split("/url?q=")[1].split("&")[0]

                    if "linkedin.com/in/" in actual_url:
                        # Extract headline if available
                        parent = result.find_parent("div")
                        snippet = parent.get_text() if parent else ""

                        return {
                            "profile_url": actual_url,
                            "headline": snippet[:100] if snippet else None,
                        }

            return None

        except Exception as e:
            logger.debug(f"Error parsing Google results: {str(e)}")
            return None

    @retry_with_backoff(max_retries=2, exceptions=(requests.RequestException,))
    def search_investor_with_fallback(
        self, investor_name: str, company_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Use multiple search strategies to find LinkedIn profile.
        Falls back to company + investor name if direct search fails.
        """
        # Try direct search first
        result = self.search_linkedin_profile(investor_name)
        if result:
            return result.get("profile_url")

        # Try with company name if available
        if company_name:
            combined_query = f"{company_name} {investor_name}"
            result = self.search_linkedin_profile(combined_query)
            if result:
                return result.get("profile_url")

        return None

    @staticmethod
    def extract_name_from_url(linkedin_url: str) -> Optional[str]:
        """
        Extract person name from LinkedIn URL.
        Example: https://linkedin.com/in/john-doe-123 -> john-doe
        """
        try:
            # Extract the ID part
            match = re.search(r"linkedin\.com/in/([^/?]+)", linkedin_url)
            if match:
                name_part = match.group(1)
                # Remove trailing numbers and hyphens
                name_part = re.sub(r"-\d+$", "", name_part)
                return name_part.replace("-", " ").title()
            return None
        except Exception:
            return None

    @staticmethod
    def is_linkedin_url(url: Optional[str]) -> bool:
        """Check if URL is a LinkedIn profile or company page."""
        if not url:
            return False
        return "linkedin.com" in url.lower()


# Convenience function
def extract_linkedin_safe(investor_name: str) -> Optional[str]:
    """
    Public API to safely extract LinkedIn profile URL.
    Returns profile URL or None.
    """
    if not LINKEDIN_CONFIG["use_google_serp"]:
        logger.debug("LinkedIn extraction disabled in config")
        return None

    extractor = LinkedInSafeExtractor()
    return extractor.search_investor_with_fallback(investor_name)
