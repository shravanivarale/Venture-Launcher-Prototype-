"""
Google Fallback scraper.
Uses Google Search to find investor information as last resort.
Respects robots.txt and user-agent policies.
"""

from typing import List
from urllib.parse import quote
from bs4 import BeautifulSoup
import requests

from core.schemas import InvestorRecord
from scrapers.base_scraper import BaseScraper
from config import SCRAPERS
from utils.logger import get_logger
from utils.validators import Validators
from utils.linkedin_safe import LinkedInSafeExtractor


logger = get_logger(__name__)


class GoogleFallbackScraper(BaseScraper):
    """
    Fallback scraper using Google Search.
    Finds investor information through search results when primary sources fail.
    """

    def __init__(self):
        config = SCRAPERS["google_fallback"]
        super().__init__(
            name="google_fallback",
            base_url=config["base_url"],
            timeout=config.get("timeout", 15),
        )
        self.linkedin_extractor = LinkedInSafeExtractor()

    def scrape(self) -> List[InvestorRecord]:
        """
        Use Google Search to discover investors.
        Searches for common investor keywords.
        """
        records = []

        try:
            logger.info(f"🔍 {self.name}: Searching for investors via Google")

            # Search queries targeting Indian investors
            search_queries = [
                "venture capital investors India",
                "angel investors Bangalore India",
                "early stage investors India",
                "seed stage investors India",
            ]

            for query in search_queries:
                try:
                    page_records = self._search_and_extract(query)
                    records.extend(page_records)
                    logger.debug(
                        f"   Found {len(page_records)} records for query: {query}"
                    )

                except Exception as e:
                    logger.warning(f"❌ Error searching for '{query}': {str(e)}")
                    continue

            logger.info(f"✅ {self.name}: Found {len(records)} investor records")
            self.log_failed_urls()
            return records

        except Exception as e:
            logger.error(f"❌ {self.name} scraping failed: {str(e)}")
            self.log_failed_urls()
            return records

    def _search_and_extract(self, query: str) -> List[InvestorRecord]:
        """Search Google and extract investor info from results."""
        records = []

        try:
            search_url = f"https://www.google.com/search?q={quote(query)}"
            soup = self.fetch_url(search_url)

            if not soup:
                return records

            # Extract information from search results
            records = self._extract_from_serp(soup, query)

        except Exception as e:
            logger.debug(f"Error in Google search: {str(e)}")

        return records

    def _extract_from_serp(self, soup: BeautifulSoup, query: str) -> List[InvestorRecord]:
        """
        Extract investor information from Google SERP.
        Looks for investor websites and LinkedIn profiles.
        """
        records = []

        try:
            # Find search result links
            results = soup.find_all("div", class_="g")

            for result in results[:5]:  # Limit to top 5 results
                try:
                    link_elem = result.find("a")
                    if not link_elem:
                        continue

                    url = link_elem.get("href", "")
                    title = link_elem.get_text()

                    if not url or "google.com" in url:
                        continue

                    # Check if it's a relevant investor link
                    if self._is_relevant_investor_link(url, title):
                        record = self._create_record_from_search_result(
                            title, url, query
                        )
                        if record:
                            records.append(record)

                except Exception as e:
                    logger.debug(f"Error processing search result: {str(e)}")
                    continue

        except Exception as e:
            logger.debug(f"Error extracting from SERP: {str(e)}")

        return records

    def _is_relevant_investor_link(self, url: str, title: str) -> bool:
        """Check if link is relevant to investor search."""
        investor_keywords = [
            "investor",
            "venture",
            "capital",
            "angel",
            "fund",
            "vc",
            "funding",
        ]

        combined = (url + " " + title).lower()
        return any(keyword in combined for keyword in investor_keywords)

    def _create_record_from_search_result(
        self, title: str, url: str, query: str
    ) -> InvestorRecord:
        """
        Create investor record from Google search result.
        This is a best-effort extraction with lower confidence.
        """
        try:
            # Extract name from title
            # Usually format is: "Name - Description | Company"
            name = title.split("|")[0].split("-")[0].strip()

            if not Validators.is_valid_investor_name(name):
                return None

            # Infer investor type from query and URL
            investor_type = "VC"
            if "angel" in query.lower():
                investor_type = "Angel"
            elif "seed" in query.lower():
                investor_type = "Seed Fund"

            # Try to find LinkedIn profile
            linkedin_url = self.linkedin_extractor.search_investor_with_fallback(name)

            return InvestorRecord(
                investor_name=name,
                investor_type=investor_type,
                website_url=url if Validators.is_valid_url(url) else None,
                investment_stage=None,
                sectors_of_interest=[],
                notable_portfolio_companies=[],
                linkedin_profile_url=linkedin_url,
                source="google_fallback",
                data_quality_score=0.45,  # Lower confidence for fallback source
            )

        except Exception as e:
            logger.debug(f"Error creating record from search result: {str(e)}")
            return None
