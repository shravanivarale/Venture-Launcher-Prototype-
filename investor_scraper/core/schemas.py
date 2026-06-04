"""
Data schemas using Pydantic for type safety and validation.
"""

from typing import Optional, List, Set
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, validator


class InvestorRecord(BaseModel):
    """
    Schema for a single investor record.
    Represents normalized, cleaned investor data.
    """

    investor_name: str = Field(..., description="Name of the investor")
    investor_type: str = Field(..., description="VC / Angel / Seed Fund")
    website_url: Optional[str] = Field(None, description="Investor website URL")
    investment_stage: Optional[str] = Field(
        None, description="Pre-seed / Seed / Series A / Growth"
    )
    sectors_of_interest: List[str] = Field(default_factory=list, description="List of sectors")
    notable_portfolio_companies: List[str] = Field(
        default_factory=list, description="Known portfolio companies"
    )
    linkedin_profile_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    
    # Metadata
    source: str = Field(..., description="Source scraper")
    data_collected_at: datetime = Field(default_factory=datetime.utcnow)
    data_quality_score: float = Field(default=0.5, ge=0, le=1.0)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def is_valid(self) -> bool:
        """Check if record has minimum required fields."""
        return bool(
            self.investor_name
            and self.investor_type
            and len(self.investor_name.strip()) >= 3
        )

    def merge(self, other: "InvestorRecord") -> "InvestorRecord":
        """
        Intelligently merge two investor records.
        Keeps best non-null values, merges lists.
        """
        return InvestorRecord(
            investor_name=self.investor_name or other.investor_name,
            investor_type=self.investor_type or other.investor_type,
            website_url=self.website_url or other.website_url,
            investment_stage=self.investment_stage or other.investment_stage,
            sectors_of_interest=list(
                set(self.sectors_of_interest + other.sectors_of_interest)
            ),
            notable_portfolio_companies=list(
                set(self.notable_portfolio_companies + other.notable_portfolio_companies)
            ),
            linkedin_profile_url=self.linkedin_profile_url or other.linkedin_profile_url,
            source=f"{self.source},{other.source}",
            data_collected_at=max(self.data_collected_at, other.data_collected_at),
            data_quality_score=max(self.data_quality_score, other.data_quality_score),
        )


class ScraperResult(BaseModel):
    """Result from a single scraper execution."""

    scraper_name: str
    records: List[InvestorRecord] = Field(default_factory=list)
    success: bool
    error_message: Optional[str] = None
    records_count: int = 0
    duration_seconds: float = 0.0

    def __init__(self, **data):
        super().__init__(**data)
        self.records_count = len(self.records)


class PipelineConfig(BaseModel):
    """Configuration for a pipeline run."""

    scrapers_to_run: List[str]
    limit_per_scraper: Optional[int] = None
    enable_caching: bool = True
    enable_deduplication: bool = True
    output_format: str = "both"  # 'csv', 'excel', 'both'
    verbose: bool = False
