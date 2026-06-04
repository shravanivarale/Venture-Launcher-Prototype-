"""
Configuration for investor scraping pipeline.
All environment-specific settings centralized here.
"""

import os
from pathlib import Path

# ============== Paths ==============
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# ============== Scraping Settings ==============
SCRAPER_CONFIG = {
    "timeout": 15,  # seconds per request
    "max_retries": 3,
    "backoff_factor": 1.5,
    "rate_limit_delay": 2,  # seconds between requests per domain
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15",
    ],
}

# ============== Circuit Breaker Settings ==============
CIRCUIT_BREAKER_CONFIG = {
    "failure_threshold": 5,  # consecutive failures to trip circuit
    "recovery_timeout": 300,  # seconds (5 min) before retry
    "half_open_attempts": 2,
}

# ============== Data Processing ==============
CLEANING_CONFIG = {
    "min_name_length": 3,
    "max_name_length": 200,
    "fuzzy_match_threshold": 85,  # 0-100 similarity score
}

# ============== Output Settings ==============
OUTPUT_CONFIG = {
    "csv_file": OUTPUT_DIR / "investors.csv",
    "excel_file": OUTPUT_DIR / "investors.xlsx",
    "failed_urls_log": LOGS_DIR / "failed_urls.log",
    "encoding": "utf-8",
}

# ============== Logging Settings ==============
LOGGING_CONFIG = {
    "log_file": LOGS_DIR / "investor_scraper.log",
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}

# ============== Scraper Priority & Endpoints ==============
SCRAPERS = {
    "angellist": {
        "enabled": True,
        "priority": 1,
        "base_url": "https://www.angel.co",
        "timeout": 20,
    },
    "crunchbase": {
        "enabled": True,
        "priority": 2,
        "base_url": "https://www.crunchbase.com",
        "timeout": 20,
    },
    "tracxn": {
        "enabled": True,
        "priority": 3,
        "base_url": "https://tracxn.com",
        "timeout": 20,
    },
    "letsventure": {
        "enabled": True,
        "priority": 4,
        "base_url": "https://www.letsventure.com",
        "timeout": 15,
    },
    "google_fallback": {
        "enabled": True,
        "priority": 5,
        "base_url": "https://www.google.com",
        "timeout": 15,
    },
}

# ============== Sector Taxonomy ==============
SECTOR_TAXONOMY = {
    "AI/ML": ["artificial intelligence", "machine learning", "ai", "ml", "deep learning"],
    "SaaS": ["saas", "software as a service", "enterprise software"],
    "Fintech": ["fintech", "finance", "payment", "banking", "cryptocurrency", "web3"],
    "Healthtech": ["health", "medical", "healthcare", "biotech", "wellness"],
    "Edtech": ["education", "learning", "edtech", "training", "skill"],
    "E-commerce": ["ecommerce", "marketplace", "retail", "commerce"],
    "Logistics": ["logistics", "supply chain", "shipping", "delivery"],
    "Sustainability": ["green", "sustainability", "climate", "renewable"],
    "B2B": ["b2b", "enterprise", "business"],
}

# ============== LinkedIn Safe Search ==============
LINKEDIN_CONFIG = {
    "use_google_serp": True,
    "search_queries": [
        "site:linkedin.com/in venture capital india",
        "site:linkedin.com/in investor india bangalore",
        "site:linkedin.com/in startup founder investor",
    ],
    "extract_profile_url": True,
}

# ============== CLI Defaults ==============
CLI_DEFAULTS = {
    "limit": None,  # None = no limit
    "output": "both",  # 'csv', 'excel', 'both'
    "verbose": False,
    "cache": True,
}
