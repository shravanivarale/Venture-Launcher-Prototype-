"""
Data extraction and transformation utilities.
"""

from typing import List, Optional
import re

from core.schemas import InvestorRecord
from utils.validators import Validators
from utils.logger import get_logger


logger = get_logger(__name__)


class Extractor:
    """
    Advanced extraction using multiple strategies:
    - HTML parsing
    - Regex fallback
    - Heuristic-based extraction
    """

    @staticmethod
    def extract_email(text: str) -> Optional[str]:
        """Extract email from text using regex."""
        if not text:
            return None

        pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        matches = re.findall(pattern, text)
        return matches[0] if matches else None

    @staticmethod
    def extract_phone(text: str) -> Optional[str]:
        """Extract phone number from text."""
        if not text:
            return None

        # Indian phone pattern
        pattern = r"(?:\+91|\+1)?[-.\s]?[6-9]\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}"
        matches = re.findall(pattern, text)
        return matches[0] if matches else None

    @staticmethod
    def extract_sectors_from_text(text: str) -> List[str]:
        """
        Extract sector keywords from text using pattern matching.
        Looks for sector-specific keywords.
        """
        if not text:
            return []

        from config import SECTOR_TAXONOMY

        sectors = []
        text_lower = text.lower()

        for sector, aliases in SECTOR_TAXONOMY.items():
            for alias in aliases:
                if alias in text_lower:
                    sectors.append(sector)
                    break

        return list(set(sectors))  # Remove duplicates

    @staticmethod
    def extract_investment_stages(text: str) -> List[str]:
        """Extract investment stages mentioned in text."""
        if not text:
            return []

        text_lower = text.lower()
        stages = []

        stage_keywords = {
            "Pre-seed": ["pre-seed", "preseed", "pre seed"],
            "Seed": ["seed stage", "seed", "series seed"],
            "Series A": ["series a", "series-a"],
            "Series B": ["series b", "series-b"],
            "Growth": ["growth stage", "growth", "scale"],
        }

        for stage, keywords in stage_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    stages.append(stage)
                    break

        return stages

    @staticmethod
    def extract_portfolio_companies(text: str) -> List[str]:
        """Extract portfolio company names from text."""
        if not text:
            return []

        # Look for patterns like "portfolio includes X, Y, Z"
        pattern = r"portfolio[^:]*:?\s*([^.]+)"
        matches = re.findall(pattern, text, re.IGNORECASE)

        companies = []
        for match in matches:
            # Split by comma and clean
            parts = match.split(",")
            for part in parts:
                company = part.strip()
                if company and len(company) < 100:
                    companies.append(company)

        return companies[:10]  # Limit to 10

    @staticmethod
    def merge_investor_records(
        records: List[InvestorRecord],
    ) -> List[InvestorRecord]:
        """
        Merge duplicate investor records intelligently.
        Keeps best non-null values.
        """
        if not records:
            return []

        # Group by investor name (normalized)
        groups = {}
        for record in records:
            key = record.investor_name.lower().strip()
            if key not in groups:
                groups[key] = []
            groups[key].append(record)

        # Merge each group
        merged = []
        for group in groups.values():
            if len(group) == 1:
                merged.append(group[0])
            else:
                # Merge multiple records
                primary = group[0]
                for secondary in group[1:]:
                    primary = primary.merge(secondary)
                merged.append(primary)

        return merged
