"""
Custom exceptions for investor scraper pipeline.
"""


class InvestorScraperError(Exception):
    """Base exception for all scraper errors."""

    pass


class ScraperConfigError(InvestorScraperError):
    """Configuration-related error."""

    pass


class ScraperExecutionError(InvestorScraperError):
    """Error during scraper execution."""

    pass


class DataExtractionError(InvestorScraperError):
    """Error extracting data from HTML/JSON."""

    pass


class DataValidationError(InvestorScraperError):
    """Data validation failure."""

    pass


class DataCleaningError(InvestorScraperError):
    """Error during data cleaning/normalization."""

    pass


class RateLimitError(InvestorScraperError):
    """Rate limiting triggered."""

    pass


class CircuitBreakerOpenError(InvestorScraperError):
    """Circuit breaker is open (service unavailable)."""

    pass


class DataDeduplicationError(InvestorScraperError):
    """Error during deduplication."""

    pass


class OutputGenerationError(InvestorScraperError):
    """Error generating output files."""

    pass
