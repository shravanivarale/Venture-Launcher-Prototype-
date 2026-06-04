"""
Deduplication engine using fuzzy matching and intelligent merging.
"""

from typing import List, Tuple
from difflib import SequenceMatcher
from config import CLEANING_CONFIG
from core.schemas import InvestorRecord
from utils.logger import get_logger


logger = get_logger(__name__)


class Deduplicator:
    """
    Remove duplicate investors using:
    - Exact matching (case-insensitive)
    - Fuzzy matching (Levenshtein distance)
    - Intelligent merging of partial records
    """

    def __init__(self, threshold: int = CLEANING_CONFIG["fuzzy_match_threshold"]):
        self.threshold = threshold

    def deduplicate(self, records: List[InvestorRecord]) -> List[InvestorRecord]:
        """
        Main deduplication logic.
        Returns list of unique records with merged data.
        """
        if not records:
            return []

        logger.info(f"🔄 Deduplicating {len(records)} records")

        # First pass: exact match + lowercase
        records = self._remove_exact_duplicates(records)
        logger.debug(f"   After exact match: {len(records)} records")

        # Second pass: fuzzy match
        records = self._remove_fuzzy_duplicates(records)
        logger.debug(f"   After fuzzy match: {len(records)} records")

        return records

    def _remove_exact_duplicates(self, records: List[InvestorRecord]) -> List[InvestorRecord]:
        """Remove exact duplicates using normalized name."""
        seen = {}
        unique = []

        for record in records:
            key = record.investor_name.lower().strip()

            if key not in seen:
                seen[key] = record
                unique.append(record)
            else:
                # Merge with existing record
                existing = seen[key]
                merged = existing.merge(record)
                # Replace in list
                idx = unique.index(existing)
                unique[idx] = merged
                seen[key] = merged

        return unique

    def _remove_fuzzy_duplicates(self, records: List[InvestorRecord]) -> List[InvestorRecord]:
        """
        Remove fuzzy duplicates using string similarity.
        Uses Jaro-Winkler-like similarity matching.
        """
        unique = []
        duplicates_found = []

        for i, record in enumerate(records):
            # Check if already marked as duplicate
            if any(i in dup_pair for dup_pair in duplicates_found):
                continue

            unique.append(record)

            # Compare with remaining records
            for j in range(i + 1, len(records)):
                if any(j in dup_pair for dup_pair in duplicates_found):
                    continue

                other_record = records[j]
                similarity = self._calculate_similarity(
                    record.investor_name,
                    other_record.investor_name,
                )

                if similarity >= self.threshold:
                    # Mark as duplicate and merge
                    duplicates_found.append((i, j))
                    logger.debug(
                        f"   Fuzzy match: '{record.investor_name}' "
                        f"~= '{other_record.investor_name}' ({similarity}%)"
                    )

                    # Merge record
                    merged = record.merge(other_record)
                    idx = unique.index(record)
                    unique[idx] = merged

        return unique

    def _calculate_similarity(self, name1: str, name2: str) -> int:
        """
        Calculate similarity between two names.
        Returns percentage (0-100).
        """
        s1 = name1.lower().strip()
        s2 = name2.lower().strip()

        if s1 == s2:
            return 100

        # Remove common words
        s1 = self._normalize_for_comparison(s1)
        s2 = self._normalize_for_comparison(s2)

        # Use SequenceMatcher for Jaro-like comparison
        matcher = SequenceMatcher(None, s1, s2)
        ratio = matcher.ratio() * 100

        return int(ratio)

    @staticmethod
    def _normalize_for_comparison(name: str) -> str:
        """Normalize name for comparison."""
        # Remove common suffixes
        suffixes = [" ventures", " capital", " fund", " inc", " ltd", " llc", " pvt"]
        name_lower = name.lower()

        for suffix in suffixes:
            if name_lower.endswith(suffix):
                name = name[: -len(suffix)]

        # Keep only alphanumeric and spaces
        name = "".join(c if c.isalnum() or c.isspace() else "" for c in name)
        return " ".join(name.split())
