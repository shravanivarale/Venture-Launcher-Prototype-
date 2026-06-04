"""
Data cleaning and normalization pipeline.
Validates, cleans, and normalizes investor records.
"""

from typing import List, Optional
from core.schemas import InvestorRecord
from core.exceptions import DataCleaningError
from utils.validators import Validators
from utils.logger import get_logger


logger = get_logger(__name__)


class DataCleaner:
    """
    Clean and normalize investor records.
    Handles:
    - Validation
    - Type normalization
    - Stage normalization
    - Sector standardization
    - Duplicate removal
    """

    def clean(self, records: List[InvestorRecord]) -> List[InvestorRecord]:
        """
        Main cleaning pipeline.
        Returns cleaned and validated records.
        """
        logger.info(f"🧹 Cleaning {len(records)} records")

        cleaned = []

        for record in records:
            try:
                cleaned_record = self._clean_record(record)
                if cleaned_record and cleaned_record.is_valid():
                    cleaned.append(cleaned_record)
                else:
                    logger.debug(f"   Removed invalid record: {record.investor_name}")

            except Exception as e:
                logger.warning(f"   Error cleaning record: {str(e)}")
                continue

        logger.info(f"✅ Cleaned to {len(cleaned)} valid records")
        return cleaned

    def _clean_record(self, record: InvestorRecord) -> Optional[InvestorRecord]:
        """
        Clean a single record.
        Returns cleaned record or None if invalid.
        """
        try:
            # Clean name
            investor_name = self._clean_name(record.investor_name)
            if not investor_name:
                return None

            # Normalize investor type
            investor_type = Validators.normalize_investor_type(record.investor_type)
            if not investor_type:
                investor_type = "VC"  # Default

            # Validate and clean URL
            website_url = self._clean_url(record.website_url)

            # Normalize investment stage
            investment_stage = None
            if record.investment_stage:
                investment_stage = Validators.normalize_investment_stage(
                    record.investment_stage
                )

            # Normalize sectors
            sectors = Validators.normalize_sectors(record.sectors_of_interest)

            # Clean portfolio companies
            portfolio = self._clean_portfolio_companies(record.notable_portfolio_companies)

            # Validate LinkedIn URL
            linkedin_url = None
            if record.linkedin_profile_url:
                if Validators.is_valid_linkedin_url(record.linkedin_profile_url):
                    linkedin_url = record.linkedin_profile_url

            # Create cleaned record
            cleaned = InvestorRecord(
                investor_name=investor_name,
                investor_type=investor_type,
                website_url=website_url,
                investment_stage=investment_stage,
                sectors_of_interest=sectors,
                notable_portfolio_companies=portfolio,
                linkedin_profile_url=linkedin_url,
                source=record.source,
                data_collected_at=record.data_collected_at,
                data_quality_score=self._calculate_quality_score(record),
            )

            return cleaned

        except Exception as e:
            logger.debug(f"Error cleaning record: {str(e)}")
            return None

    def _clean_name(self, name: Optional[str]) -> Optional[str]:
        """
        Clean investor name.
        Removes extra spaces, standardizes case.
        """
        if not name:
            return None

        # Remove extra whitespace
        name = " ".join(name.split())

        # Remove HTML entities
        name = name.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")

        # Trim length
        name = name[: 200]

        # Validate
        if Validators.is_valid_investor_name(name):
            return name

        return None

    def _clean_url(self, url: Optional[str]) -> Optional[str]:
        """
        Clean and validate URL.
        """
        if not url:
            return None

        url = url.strip()

        # Remove trailing slashes
        url = url.rstrip("/")

        # Ensure http/https
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        # Validate
        if Validators.is_valid_url(url):
            return url

        return None

    def _clean_portfolio_companies(self, companies: List[str]) -> List[str]:
        """
        Clean portfolio company names.
        Removes invalid entries.
        """
        if not companies:
            return []

        cleaned = []

        for company in companies:
            if not company or not isinstance(company, str):
                continue

            company = company.strip()

            # Filter by length
            if 2 < len(company) < 200:
                cleaned.append(company)

        return cleaned[:20]  # Limit to 20

    def _calculate_quality_score(self, record: InvestorRecord) -> float:
        """
        Calculate data quality score (0.0 - 1.0).
        Based on completeness and source reliability.
        """
        score = 0.5  # Base score

        # Has website
        if record.website_url:
            score += 0.15

        # Has LinkedIn
        if record.linkedin_profile_url:
            score += 0.15

        # Has sectors
        if record.sectors_of_interest:
            score += 0.1

        # Has portfolio companies
        if record.notable_portfolio_companies:
            score += 0.1

        # Has investment stage
        if record.investment_stage:
            score += 0.05

        # Source reliability multiplier
        source_quality = {
            "crunchbase": 1.0,
            "angellist": 0.95,
            "tracxn": 0.90,
            "letsventure": 0.85,
            "google_fallback": 0.70,
        }

        multiplier = source_quality.get(record.source, 0.75)
        score *= multiplier

        return min(score, 1.0)  # Cap at 1.0
