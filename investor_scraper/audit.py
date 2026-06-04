"""
Audit CLI - Verify and enrich existing investor data
Usage: python audit.py [--input file.csv] [--report] [--export]
"""

import sys
import argparse
from pathlib import Path
import csv

from core.schemas import InvestorRecord
from pipeline.auditor import InvestorAuditor, create_enriched_record
from pipeline.audit_report import (
    AuditReportGenerator,
    generate_verified_csv,
    generate_verified_markdown,
)
from config import OUTPUT_CONFIG
from utils.logger import get_logger


logger = get_logger(__name__)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Audit and enrich investor data for accuracy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python audit.py                              # Audit default CSV
  python audit.py --input custom.csv           # Audit specific file
  python audit.py --report                     # Generate detailed audit report
  python audit.py --export verified.csv        # Export verified data
  python audit.py --markdown                   # Export as markdown table
  python audit.py --all                        # Full audit + all outputs
        """,
    )

    parser.add_argument(
        "--input",
        type=str,
        default=str(OUTPUT_CONFIG["csv_file"]),
        help="Input CSV file to audit (default: output/investors.csv)",
    )

    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate detailed audit report (Markdown)",
    )

    parser.add_argument(
        "--export",
        type=str,
        default=None,
        help="Export verified data to CSV file",
    )

    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Export verified data as Markdown table",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Run full audit + generate all outputs",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose logging",
    )

    return parser.parse_args()


def load_csv(filepath: str) -> list:
    """Load investor records from CSV."""
    records = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    record = InvestorRecord(
                        investor_name=row.get("Investor Name", ""),
                        investor_type=row.get("Investor Type", "VC"),
                        website_url=row.get("Website URL"),
                        investment_stage=row.get("Investment Stage"),
                        sectors_of_interest=row.get("Sectors of Interest", "").split("; ") if row.get("Sectors of Interest") else [],
                        notable_portfolio_companies=row.get("Portfolio Companies", "").split("; ") if row.get("Portfolio Companies") else [],
                        linkedin_profile_url=row.get("LinkedIn Profile"),
                        source=row.get("Data Source", "unknown"),
                    )
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Error parsing row: {str(e)}")
                    continue

        logger.info(f"✅ Loaded {len(records)} records from {filepath}")
        return records

    except FileNotFoundError:
        logger.error(f"❌ File not found: {filepath}")
        return []
    except Exception as e:
        logger.error(f"❌ Error loading CSV: {str(e)}")
        return []


def main():
    """Main audit execution."""
    try:
        args = parse_arguments()

        logger.info("=" * 80)
        logger.info("🔍 INVESTOR DATA AUDIT ENGINE")
        logger.info("=" * 80)

        # Load data
        logger.info(f"\n📂 Loading: {args.input}")
        records = load_csv(args.input)

        if not records:
            logger.error("❌ No records to audit")
            return 1

        # Run audit
        logger.info(f"\n🔍 Auditing {len(records)} records...")
        auditor = InvestorAuditor()
        audit_summary = auditor.audit_batch(records)
        audit_results = audit_summary["results"]

        # Display summary
        logger.info("\n" + "=" * 80)
        logger.info("📊 AUDIT RESULTS")
        logger.info("=" * 80)
        logger.info(f"High Confidence (≥85%): {audit_summary['high_confidence']}/{len(records)}")
        logger.info(f"Needs Review: {audit_summary['needs_review']}/{len(records)}")

        # Generate report if requested
        if args.report or args.all:
            logger.info("\n📋 Generating audit report...")
            report_gen = AuditReportGenerator()
            markdown = report_gen.generate_markdown_report(audit_results)
            report_path = report_gen.save_report(markdown)
            logger.info(f"✅ Report: {report_path}")

        # Export verified CSV if requested
        export_file = args.export
        if export_file or args.all:
            if not export_file:
                export_file = str(OUTPUT_CONFIG["csv_file"].parent / "verified_investors.csv")

            logger.info(f"\n📊 Exporting verified data to {export_file}...")
            csv_content = generate_verified_csv(audit_results)

            with open(export_file, "w", encoding="utf-8") as f:
                f.write(csv_content)

            logger.info(f"✅ Exported: {export_file}")

        # Export markdown if requested
        if args.markdown or args.all:
            logger.info("\n📝 Generating markdown table...")
            markdown_table = generate_verified_markdown(audit_results)
            markdown_file = str(
                OUTPUT_CONFIG["csv_file"].parent / "verified_investors.md"
            )

            with open(markdown_file, "w", encoding="utf-8") as f:
                f.write(markdown_table)

            logger.info(f"✅ Markdown table: {markdown_file}")

        # Display sample of corrections
        corrections = [r for r in audit_results if r.corrected_name != r.original_name]
        if corrections:
            logger.info("\n" + "=" * 80)
            logger.info(f"🔄 REBRANDING CORRECTIONS ({len(corrections)})")
            logger.info("=" * 80)
            for result in corrections[:5]:  # Show first 5
                logger.info(f"{result.original_name} → {result.corrected_name}")

        logger.info("\n" + "=" * 80)
        logger.info("✅ AUDIT COMPLETE")
        logger.info("=" * 80)

        return 0

    except KeyboardInterrupt:
        logger.error("\n⚠️  Audit interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"\n❌ Audit failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
