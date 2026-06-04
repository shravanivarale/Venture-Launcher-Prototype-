"""
LetsVenture scraper.
Extracts investor profiles from LetsVenture public pages.
"""

from typing import List
from bs4 import BeautifulSoup

from core.schemas import InvestorRecord
from scrapers.base_scraper import BaseScraper
from config import SCRAPERS
from utils.logger import get_logger
from utils.validators import Validators
from utils.linkedin_safe import LinkedInSafeExtractor


logger = get_logger(__name__)


class LetsVentureScraper(BaseScraper):
    """Scraper for LetsVenture investor data."""

    def __init__(self):
        config = SCRAPERS["letsventure"]
        super().__init__(
            name="letsventure",
            base_url=config["base_url"],
            timeout=config.get("timeout", 15),
        )
        self.linkedin_extractor = LinkedInSafeExtractor()

    def scrape(self) -> List[InvestorRecord]:
        """
        Scrape LetsVenture for Indian investors.
        LetsVenture is a crowdfunding platform focused on India.
        """
        records = []

        try:
            logger.info(f"🔍 {self.name}: Fetching investor data from public pages")

            # LetsVenture investor pages
            search_urls = [
                "https://www.letsventure.com/investors",
                "https://www.letsventure.com/explore/investors",
            ]

            for search_url in search_urls:
                try:
                    soup = self.fetch_url(search_url)
                    if not soup:
                        continue

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
        """Extract investor records from page."""
        records = []

        try:
            investor_cards = soup.find_all(
                class_=lambda x: x and ("investor" in x.lower() or "profile" in x.lower())
            )

            if not investor_cards:
                investor_cards = soup.find_all(
                    "div", class_=lambda x: x and "card" in x.lower()
                )

            for card in investor_cards[:12]:
                record = self._extract_investor_from_card(card)
                if record and record.is_valid():
                    records.append(record)

        except Exception as e:
            logger.warning(f"Error parsing LetsVenture page: {str(e)}")

        return records

    def _extract_investor_from_card(self, card: BeautifulSoup) -> InvestorRecord:
        """Extract investor record from card."""
        try:
            # Extract name
            name_elem = card.find(class_=lambda x: x and "name" in x.lower())
            if not name_elem:
                name_elem = card.find("h4") or card.find("h3")

            investor_name = self._extract_text(name_elem)

            if not Validators.is_valid_investor_name(investor_name):
                return None

            # Extract investor type
            type_elem = card.find(class_=lambda x: x and "type" in x.lower())
            investor_type = Validators.normalize_investor_type(
                self._extract_text(type_elem, "VC")
            )

            # Extract URL
            url_elem = card.find("a")
            website_url = self._extract_attr(url_elem, "href")
            if website_url and not website_url.startswith("http"):
                website_url = f"https://www.letsventure.com{website_url}"

            # Extract description
            desc_elem = card.find(
                class_=lambda x: x and ("description" in x or "bio" in x.lower())
            )
            description = self._extract_text(desc_elem, "")

            # Extract sectors
            sectors = Validators.normalize_sectors(
                self._extract_sectors_from_text(description)
            )

            # Try LinkedIn
            linkedin_url = self.linkedin_extractor.search_investor_with_fallback(
                investor_name
            )

            return InvestorRecord(
                investor_name=investor_name,
                investor_type=investor_type or "VC",
                website_url=website_url if Validators.is_valid_url(website_url) else None,
                investment_stage=None,
                sectors_of_interest=sectors,
                notable_portfolio_companies=[],
                linkedin_profile_url=linkedin_url,
                source="letsventure",
                data_quality_score=0.65,
            )

        except Exception as e:
            logger.debug(f"Error extracting LetsVenture investor: {str(e)}")
            return None

    def _extract_sectors_from_text(self, text: str) -> List[str]:
        """Extract sector keywords from description."""
        if not text:
            return []

        keywords = {
            "AI/ML": ["ai", "ml", "machine learning"],
            "SaaS": ["saas", "software"],
            "Fintech": ["fintech", "finance"],
            "Healthtech": ["health", "medical"],
            "Logistics": ["logistics", "supply chain"],
        }

        sectors = []
        for sector, words in keywords.items():
            for word in words:
                if word in text.lower():
                    sectors.append(sector)
                    break

        return sectors
