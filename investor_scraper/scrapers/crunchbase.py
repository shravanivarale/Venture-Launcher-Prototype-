"""
Crunchbase scraper.
Extracts investor profiles from Crunchbase public pages.
"""

from typing import List
import re
from bs4 import BeautifulSoup

from core.schemas import InvestorRecord
from scrapers.base_scraper import BaseScraper
from config import SCRAPERS
from utils.logger import get_logger
from utils.validators import Validators
from utils.linkedin_safe import LinkedInSafeExtractor


logger = get_logger(__name__)


class CrunchbaseScraper(BaseScraper):
    """Scraper for Crunchbase investor data."""

    def __init__(self):
        config = SCRAPERS["crunchbase"]
        super().__init__(
            name="crunchbase",
            base_url=config["base_url"],
            timeout=config.get("timeout", 20),
        )
        self.linkedin_extractor = LinkedInSafeExtractor()

    def scrape(self) -> List[InvestorRecord]:
        """
        Scrape Crunchbase for Indian investors.
        Uses public investor profile pages and search.
        """
        records = []

        try:
            logger.info(f"🔍 {self.name}: Fetching investor data from public pages")

            # Crunchbase public investor search URLs
            search_urls = [
                "https://www.crunchbase.com/search/investors?query=India%20venture%20capital",
                "https://www.crunchbase.com/search/investors?query=India%20angel%20investor",
                "https://www.crunchbase.com/search/investors?query=Bangalore%20VC",
            ]

            for search_url in search_urls:
                try:
                    soup = self.fetch_url(search_url)
                    if not soup:
                        continue

                    # Extract investor profiles
                    page_records = self._extract_investors_from_page(soup)
                    records.extend(page_records)
                    logger.debug(
                        f"   Extracted {len(page_records)} records from page"
                    )

                except Exception as e:
                    logger.warning(f"❌ Error processing {search_url}: {str(e)}")
                    continue

            logger.info(f"✅ {self.name}: Extracted {len(records)} investor records")
            self.log_failed_urls()
            return records

        except Exception as e:
            logger.error(f"❌ {self.name} scraping failed: {str(e)}")
            self.log_failed_urls()
            return records

    def _extract_investors_from_page(self, soup: BeautifulSoup) -> List[InvestorRecord]:
        """Extract investor records from Crunchbase page."""
        records = []

        try:
            # Crunchbase uses component-based layout
            investor_cards = soup.find_all(
                class_=lambda x: x and ("investor-row" in x or "result-row" in x)
            )

            if not investor_cards:
                investor_cards = soup.find_all(
                    "div", class_=lambda x: x and "Card" in x
                )

            for card in investor_cards[:10]:
                record = self._extract_investor_from_card(card)
                if record and record.is_valid():
                    records.append(record)

        except Exception as e:
            logger.warning(f"Error parsing Crunchbase page: {str(e)}")

        return records

    def _extract_investor_from_card(self, card: BeautifulSoup) -> InvestorRecord:
        """Extract individual investor from card."""
        try:
            # Extract investor name
            name_elem = card.find("a", class_=lambda x: x and "name" in x.lower())
            if not name_elem:
                name_elem = card.find("h4") or card.find("h3")

            investor_name = self._extract_text(name_elem)

            if not Validators.is_valid_investor_name(investor_name):
                return None

            # Extract type/subtitle
            subtitle_elem = card.find(
                class_=lambda x: x and "subtitle" in x.lower()
            )
            investor_type = Validators.normalize_investor_type(
                self._extract_text(subtitle_elem, "VC")
            )

            # Extract profile URL
            url_elem = card.find("a")
            website_url = self._extract_attr(url_elem, "href")
            if website_url and not website_url.startswith("http"):
                website_url = f"https://www.crunchbase.com{website_url}"

            # Extract description/sectors
            desc_elem = card.find(
                class_=lambda x: x and ("description" in x or "text" in x)
            )
            description = self._extract_text(desc_elem, "")

            # Extract sectors from description
            sectors = Validators.normalize_sectors(
                self._extract_sectors_from_text(description)
            )

            # Extract portfolio companies if available
            portfolio_elems = card.find_all(
                class_=lambda x: x and "portfolio" in x.lower()
            )
            portfolio_companies = [
                self._extract_text(elem) for elem in portfolio_elems[:5]
            ]

            # Try to find LinkedIn profile
            linkedin_url = self.linkedin_extractor.search_investor_with_fallback(
                investor_name
            )

            return InvestorRecord(
                investor_name=investor_name,
                investor_type=investor_type or "VC",
                website_url=website_url if Validators.is_valid_url(website_url) else None,
                investment_stage=None,
                sectors_of_interest=sectors,
                notable_portfolio_companies=portfolio_companies,
                linkedin_profile_url=linkedin_url,
                source="crunchbase",
                data_quality_score=0.75,
            )

        except Exception as e:
            logger.debug(f"Error extracting Crunchbase investor: {str(e)}")
            return None

    def _extract_sectors_from_text(self, text: str) -> List[str]:
        """Extract sector keywords from description text."""
        if not text:
            return []

        # Keywords to look for
        sector_keywords = {
            "AI/ML": ["ai", "machine learning", "deep learning", "neural"],
            "SaaS": ["saas", "software", "cloud"],
            "Fintech": ["fintech", "payment", "banking", "finance"],
            "E-commerce": ["ecommerce", "marketplace", "retail"],
            "B2B": ["b2b", "enterprise"],
        }

        found_sectors = []
        text_lower = text.lower()

        for sector, keywords in sector_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_sectors.append(sector)
                    break

        return found_sectors
