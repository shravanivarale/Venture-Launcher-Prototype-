"""
Main entry point for investor scraping pipeline.
Orchestrates entire data collection, processing, and export workflow.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

from core.engine import ScrapeEngine
from core.schemas import PipelineConfig
from pipeline.cleaner import DataCleaner
from utils.logger import get_logger


logger = get_logger(__name__)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Production-grade investor data scraping pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Run full pipeline with all scrapers
  python main.py --limit 50                # Limit to 50 records per scraper
  python main.py --output csv              # Export only to CSV
  python main.py --output excel            # Export only to Excel
  python main.py --scrapers angellist crunchbase  # Run specific scrapers
  python main.py --no-deduplicate          # Skip deduplication
  python main.py --sample                  # Generate sample output only
        """,
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum records per scraper (default: no limit)",
    )

    parser.add_argument(
        "--output",
        choices=["csv", "excel", "both"],
        default="both",
        help="Output format(s) (default: both)",
    )

    parser.add_argument(
        "--scrapers",
        nargs="+",
        choices=["angellist", "crunchbase", "tracxn", "letsventure", "google_fallback"],
        help="Specific scrapers to run (default: all)",
    )

    parser.add_argument(
        "--no-deduplicate",
        action="store_true",
        help="Skip deduplication step",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose logging output",
    )

    parser.add_argument(
        "--sample",
        action="store_true",
        help="Generate sample output only (no actual scraping)",
    )

    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching (force fresh scrape)",
    )

    return parser.parse_args()


def main():
    """Main execution function."""
    try:
        # Parse arguments
        args = parse_arguments()

        # Build pipeline config
        scrapers = args.scrapers or [
            "angellist",
            "crunchbase",
            "tracxn",
            "letsventure",
            "google_fallback",
        ]

        config = PipelineConfig(
            scrapers_to_run=scrapers,
            limit_per_scraper=args.limit,
            enable_caching=not args.no_cache,
            enable_deduplication=not args.no_deduplicate,
            output_format=args.output,
            verbose=args.verbose,
        )

        # Handle sample mode
        if args.sample:
            logger.info("Generating verified investor dataset...")
            from pipeline.exporter import DataExporter

            exporter = DataExporter()
            verified_records = exporter.export_sample_data()

            logger.info(f"Generated {len(verified_records)} verified investors")
            
            # Save to verified_investors.csv by default for sample mode
            verified_csv_path = exporter.output_dir / "verified_investors.csv"
            exporter.to_csv(verified_records, filename=str(verified_csv_path))

            if args.output in ["excel", "both"]:
                verified_excel_path = exporter.output_dir / "verified_investors.xlsx"
                exporter.to_excel(verified_records)

            logger.info("Sample output generated successfully!")
            return 0

        # Run main pipeline
        logger.info("🚀 Starting Investor Scraper Pipeline")
        logger.info(f"Configuration:")
        logger.info(f"  Scrapers: {', '.join(scrapers)}")
        logger.info(f"  Limit: {args.limit or 'None'}")
        logger.info(f"  Output: {args.output}")
        logger.info(f"  Deduplicate: {not args.no_deduplicate}")

        # Create and run engine
        engine = ScrapeEngine(config)
        summary = engine.run()

        # Additional cleaning pass
        logger.info("\n🧹 Running additional data cleaning...")
        cleaner = DataCleaner()
        engine.all_records = cleaner.clean(engine.all_records)

        # Re-export with cleaned data
        if engine.config.enable_deduplication:
            logger.info("🔄 Final deduplication pass...")
            from pipeline.deduplicator import Deduplicator

            dedup = Deduplicator()
            engine.all_records = dedup.deduplicate(engine.all_records)

        logger.info(f"📊 Final record count: {len(engine.all_records)}")

        # Export final data
        engine._export_data()

        logger.info("\n" + "=" * 80)
        logger.info("✅ PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info(f"Total investors extracted: {len(engine.all_records)}")
        logger.info(f"Output files:")
        if args.output in ["csv", "both"]:
            logger.info(f"  - CSV: {engine.config.output_format}/investors.csv")
        if args.output in ["excel", "both"]:
            logger.info(f"  - Excel: {engine.config.output_format}/investors.xlsx")

        return 0

    except KeyboardInterrupt:
        logger.error("\n⚠️  Pipeline interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"\n❌ Pipeline failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
