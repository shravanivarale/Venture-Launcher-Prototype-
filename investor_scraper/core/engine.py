"""
Main orchestration engine for the investor scraping pipeline.
Coordinates all scrapers, data processing, and output.
"""

import asyncio
import time
from typing import List, Dict, Optional
from datetime import datetime
import json

from core.schemas import InvestorRecord, ScraperResult, PipelineConfig
from core.exceptions import InvestorScraperError
from utils.logger import get_logger, Logger
from utils.rate_limiter import RateLimiter


logger = get_logger(__name__)


class ScrapeEngine:
    """
    Main engine that orchestrates the scraping and processing pipeline.
    Handles multi-source aggregation, deduplication, and output.
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig(scrapers_to_run=["angellist", "crunchbase"])
        self.rate_limiter = RateLimiter()
        self.all_records: List[InvestorRecord] = []
        self.scraper_results: Dict[str, ScraperResult] = {}
        self.failed_urls: List[Dict] = []
        self.pipeline_start_time = None

    def run(self) -> Dict:
        """
        Execute the full pipeline: scrape → extract → clean → deduplicate → output.
        Returns summary of pipeline execution.
        """
        self.pipeline_start_time = time.time()
        logger.info("=" * 80)
        logger.info("🚀 Starting Investor Scraper Pipeline")
        logger.info(f"Config: {self.config}")
        logger.info("=" * 80)

        try:
            # Phase 1: Run scrapers
            logger.info("\n📍 PHASE 1: Running Scrapers")
            self._run_all_scrapers()

            # Phase 2: Aggregate results
            logger.info("\n📍 PHASE 2: Aggregating Results")
            self._aggregate_results()

            # Phase 3: Deduplicate
            if self.config.enable_deduplication:
                logger.info("\n📍 PHASE 3: Deduplicating Records")
                self._deduplicate_records()

            # Phase 4: Export
            logger.info("\n📍 PHASE 4: Exporting Data")
            self._export_data()

            # Summary
            duration = time.time() - self.pipeline_start_time
            summary = self._generate_summary(duration)
            logger.info("\n" + "=" * 80)
            logger.info("✅ Pipeline Completed Successfully")
            logger.info(f"Total Records: {len(self.all_records)}")
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info("=" * 80)

            return summary

        except Exception as e:
            logger.error(f"❌ Pipeline failed: {str(e)}", exc_info=True)
            raise

    def _run_all_scrapers(self):
        """Run all enabled scrapers sequentially with error isolation."""
        scrapers = self._get_scrapers()

        for scraper_name, scraper_instance in scrapers.items():
            if scraper_name not in self.config.scrapers_to_run:
                logger.info(f"⏭️  Skipping {scraper_name} (not in config)")
                continue

            logger.info(f"\n▶️  Running scraper: {scraper_name}")
            try:
                start_time = time.time()
                records = scraper_instance.scrape()
                duration = time.time() - start_time

                # Apply limit if specified
                if self.config.limit_per_scraper:
                    records = records[: self.config.limit_per_scraper]

                result = ScraperResult(
                    scraper_name=scraper_name,
                    records=records,
                    success=True,
                    records_count=len(records),
                    duration_seconds=duration,
                )

                self.scraper_results[scraper_name] = result
                logger.info(
                    f"   ✅ {scraper_name}: {len(records)} records in {duration:.2f}s"
                )

            except CircuitBreakerOpenError:
                logger.warning(
                    f"   ⚠️  {scraper_name}: Circuit breaker is open (service recovering)"
                )
                self.scraper_results[scraper_name] = ScraperResult(
                    scraper_name=scraper_name,
                    success=False,
                    error_message="Circuit breaker open",
                )

            except Exception as e:
                logger.error(f"   ❌ {scraper_name} failed: {str(e)}")
                self.scraper_results[scraper_name] = ScraperResult(
                    scraper_name=scraper_name,
                    success=False,
                    error_message=str(e),
                )

    def _aggregate_results(self):
        """Combine all scraper results into a single list."""
        for result in self.scraper_results.values():
            if result.success:
                self.all_records.extend(result.records)

        logger.info(f"Aggregated {len(self.all_records)} total records from all scrapers")

    def _deduplicate_records(self):
        """Remove duplicate investors using name matching."""
        from pipeline.deduplicator import Deduplicator

        deduplicator = Deduplicator()
        self.all_records = deduplicator.deduplicate(self.all_records)
        logger.info(f"After deduplication: {len(self.all_records)} unique records")

    def _export_data(self):
        """Export data to CSV and Excel."""
        from pipeline.exporter import DataExporter

        exporter = DataExporter()

        if self.config.output_format in ["csv", "both"]:
            exporter.to_csv(self.all_records)
            logger.info("✅ Exported CSV")

        if self.config.output_format in ["excel", "both"]:
            exporter.to_excel(self.all_records)
            logger.info("✅ Exported Excel")

    def _generate_summary(self, duration: float) -> Dict:
        """Generate execution summary."""
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": duration,
            "total_records": len(self.all_records),
            "scrapers_run": self.config.scrapers_to_run,
            "scraper_results": {
                name: {
                    "success": result.success,
                    "records": result.records_count,
                    "duration": result.duration_seconds,
                    "error": result.error_message,
                }
                for name, result in self.scraper_results.items()
            },
        }

        # Save summary to logs
        summary_file = Logger.LOG_FILE.parent / "pipeline_summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        return summary

    def _get_scrapers(self) -> Dict:
        """Import and instantiate all scrapers dynamically."""
        from scrapers.angellist import AngelListScraper
        from scrapers.crunchbase import CrunchbaseScraper
        from scrapers.tracxn import TracxnScraper
        from scrapers.letsventure import LetsVentureScraper
        from scrapers.google_fallback import GoogleFallbackScraper

        return {
            "angellist": AngelListScraper(),
            "crunchbase": CrunchbaseScraper(),
            "tracxn": TracxnScraper(),
            "letsventure": LetsVentureScraper(),
            "google_fallback": GoogleFallbackScraper(),
        }


# Import at end to avoid circular imports
from core.exceptions import CircuitBreakerOpenError
