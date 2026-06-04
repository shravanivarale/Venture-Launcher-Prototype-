"""
Data validation utilities for URLs, emails, and investor data.
"""

import re
from typing import Optional, List
from urllib.parse import urlparse
from utils.logger import get_logger


logger = get_logger(__name__)


class Validators:
    """Collection of validation utilities."""

    @staticmethod
    def is_valid_url(url: Optional[str]) -> bool:
        """Validate URL format."""
        if not url or not isinstance(url, str):
            return False

        url = url.strip()
        try:
            result = urlparse(url)
            return all([result.scheme in ["http", "https"], result.netloc])
        except Exception:
            return False

    @staticmethod
    def is_valid_linkedin_url(url: Optional[str]) -> bool:
        """Check if URL is a LinkedIn profile."""
        if not url:
            return False
        return "linkedin.com" in url.lower()

    @staticmethod
    def is_valid_email(email: Optional[str]) -> bool:
        """Validate email format."""
        if not email:
            return False

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    @staticmethod
    def is_valid_investor_name(name: Optional[str]) -> bool:
        """Validate investor name."""
        if not name or not isinstance(name, str):
            return False

        name = name.strip()
        # Minimum 3 characters, maximum 200
        if len(name) < 3 or len(name) > 200:
            return False

        # Should not be all numbers or all special characters
        if not re.search(r"[a-zA-Z]", name):
            return False

        return True

    @staticmethod
    def is_valid_investor_type(investor_type: Optional[str]) -> bool:
        """Validate investor type."""
        valid_types = ["VC", "Angel", "Seed Fund", "Corporate", "Individual"]
        return investor_type in valid_types if investor_type else False

    @staticmethod
    def normalize_investor_type(investor_type: Optional[str]) -> Optional[str]:
        """
        Normalize investor type to standard format.
        Handles variations like "venture capital", "angel investor", etc.
        """
        if not investor_type:
            return None

        investor_type = investor_type.strip().lower()

        # Map variations to standard types
        type_mappings = {
            "venture": "VC",
            "venture capital": "VC",
            "vc": "VC",
            "venture capitalist": "VC",
            "angel": "Angel",
            "angel investor": "Angel",
            "seed": "Seed Fund",
            "seed fund": "Seed Fund",
            "corporate": "Corporate",
            "cv": "VC",
            "individual": "Individual",
        }

        for key, standard_type in type_mappings.items():
            if key in investor_type:
                return standard_type

        # Default to VC if unclear
        return "VC"

    @staticmethod
    def is_valid_investment_stage(stage: Optional[str]) -> bool:
        """Validate investment stage."""
        valid_stages = ["Pre-seed", "Seed", "Series A", "Series B", "Series C+", "Growth", "Late Stage"]
        return stage in valid_stages if stage else False

    @staticmethod
    def normalize_investment_stage(stage: Optional[str]) -> Optional[str]:
        """
        Normalize investment stage to standard format.
        """
        if not stage:
            return None

        stage = stage.strip().lower()

        stage_mappings = {
            "pre-seed": "Pre-seed",
            "preseed": "Pre-seed",
            "seed": "Seed",
            "series a": "Series A",
            "series-a": "Series A",
            "seriesA": "Series A",
            "series b": "Series B",
            "series-b": "Series B",
            "seriesB": "Series B",
            "series c": "Series C+",
            "series-c": "Series C+",
            "seriesC": "Series C+",
            "series c+": "Series C+",
            "growth": "Growth",
            "late stage": "Late Stage",
            "late-stage": "Late Stage",
        }

        return stage_mappings.get(stage)

    @staticmethod
    def is_valid_sector(sector: Optional[str]) -> bool:
        """Check if sector is in standard taxonomy."""
        from config import SECTOR_TAXONOMY

        if not sector:
            return False

        # Check exact match or partial match
        for standard_sector in SECTOR_TAXONOMY.keys():
            if sector.lower() == standard_sector.lower():
                return True

        return False

    @staticmethod
    def normalize_sectors(sectors: Optional[List[str]]) -> List[str]:
        """
        Normalize sector names to standard taxonomy.
        Handles variations and multiple aliases.
        """
        from config import SECTOR_TAXONOMY

        if not sectors:
            return []

        normalized = []

        for sector in sectors:
            if not sector:
                continue

            sector_lower = sector.lower().strip()

            # Try exact match first
            for standard_sector, aliases in SECTOR_TAXONOMY.items():
                if sector_lower == standard_sector.lower():
                    normalized.append(standard_sector)
                    break
                # Try matching aliases
                for alias in aliases:
                    if alias in sector_lower:
                        normalized.append(standard_sector)
                        break

        return list(set(normalized))  # Remove duplicates
