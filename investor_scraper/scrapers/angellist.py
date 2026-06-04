"""
AngelList/Wellfound scraper.
Extracts investor profiles from AngelList public pages.
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


class AngelListScraper(BaseScraper):
    """Scraper for AngelList/Wellfound investor data."""

    def __init__(self):
        config = SCRAPERS["angellist"]
        super().__init__(
            name="angellist",
            base_url=config["base_url"],
            timeout=config.get("timeout", 20),
        )
        self.linkedin_extractor = LinkedInSafeExtractor()

    def scrape(self) -> List[InvestorRecord]:
        """
        Scrape AngelList for Indian investors.
        Note: AngelList has deprecated their public API, so we use public pages.
        """
        records = []

        try:
            logger.info(f"🔍 {self.name}: Fetching investor data from public pages")

            # AngelList public investor listing URLs
            search_urls = [
                "https://www.angel.co/filter?filters%5Bbase%5D%5B%5D=India&sort=-founded",
                "https://www.angel.co/filter?filters%5Binvestor_type%5D%5B%5D=Venture%20Capital&filters%5Bbase%5D%5B%5D=India",
                "https://www.angel.co/filter?filters%5Binvestor_type%5D%5B%5D=Angel&filters%5Bbase%5D%5B%5D=India",
            ]

            for search_url in search_urls:
                try:
                    soup = self.fetch_url(search_url)
                    if not soup:
                        continue

                    # Extract investor profiles from page
                    page_records = self._extract_investors_from_page(soup)
                    records.extend(page_records)
                    logger.debug(
                        f"   Extracted {len(page_records)} records from {search_url}"
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
        """Extract investor records from AngelList page."""
        records = []

        try:
            # AngelList uses various selectors for investor cards
            investor_cards = soup.find_all(
                class_=lambda x: x and "investor-card" in x.lower()
            ) or soup.find_all(class_=lambda x: x and "profile-card" in x.lower())

            if not investor_cards:
                # Try alternative selectors
                investor_cards = soup.find_all("div", class_=lambda x: x and "Card" in x)

            for card in investor_cards[:10]:  # Limit to avoid rate limiting
                record = self._extract_investor_from_card(card)
                if record and record.is_valid():
                    records.append(record)

        except Exception as e:
            logger.warning(f"Error parsing AngelList page: {str(e)}")

        return records

    def _extract_investor_from_card(self, card: BeautifulSoup) -> InvestorRecord:
        """Extract individual investor record from card."""
        try:
            # Extract name
            name_elem = card.find(class_=lambda x: x and "name" in x.lower())
            investor_name = self._extract_text(name_elem)

            if not Validators.is_valid_investor_name(investor_name):
                return None

            # Extract type
            type_elem = card.find(class_=lambda x: x and "type" in x.lower())
            investor_type = Validators.normalize_investor_type(
                self._extract_text(type_elem, "VC")
            )

            # Extract URL
            url_elem = card.find("a")
            website_url = self._extract_attr(url_elem, "href")
            if website_url and not website_url.startswith("http"):
                website_url = f"https://www.angel.co{website_url}"

            # Extract stage
            stage_elem = card.find(class_=lambda x: x and "stage" in x.lower())
            investment_stage = Validators.normalize_investment_stage(
                self._extract_text(stage_elem)
            )

            # Extract sectors
            sectors = []
            sector_elems = card.find_all(class_=lambda x: x and "tag" in x.lower())
            if sector_elems:
                sectors = Validators.normalize_sectors(
                    [self._extract_text(elem) for elem in sector_elems[:5]]
                )

            # Try to find LinkedIn profile
            linkedin_url = self.linkedin_extractor.search_investor_with_fallback(
                investor_name
            )

            return InvestorRecord(
                investor_name=investor_name,
                investor_type=investor_type or "VC",
                website_url=website_url if Validators.is_valid_url(website_url) else None,
                investment_stage=investment_stage,
                sectors_of_interest=sectors,
                notable_portfolio_companies=[],
                linkedin_profile_url=linkedin_url,
                source="angellist",
                data_quality_score=0.7,
            )

        except Exception as e:
            logger.debug(f"Error extracting investor card: {str(e)}")
            return None
