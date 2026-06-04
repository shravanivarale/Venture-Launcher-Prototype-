"""
Data export to CSV and Excel formats.
"""

from typing import List
import csv
from datetime import datetime
import pandas as pd

from core.schemas import InvestorRecord
from core.exceptions import OutputGenerationError
from config import OUTPUT_CONFIG
from utils.logger import get_logger


logger = get_logger(__name__)


class DataExporter:
    """Export investor data to CSV and Excel formats."""

    def __init__(self):
        self.output_dir = OUTPUT_CONFIG["csv_file"].parent
        self.encoding = OUTPUT_CONFIG["encoding"]

    def to_csv(self, records: List[InvestorRecord], filename: str = None) -> str:
        """
        Export records to CSV file.
        Returns path to created file.
        """
        try:
            csv_path = filename or OUTPUT_CONFIG["csv_file"]

            logger.info(f"Exporting to CSV: {csv_path}")

            # Create DataFrame
            data = self._prepare_data(records)
            df = pd.DataFrame(data)

            # Write to CSV
            df.to_csv(csv_path, index=False, encoding=self.encoding, quoting=csv.QUOTE_ALL)

            logger.info(f"CSV exported successfully ({len(records)} records)")
            logger.info(f"   Path: {csv_path}")

            return str(csv_path)

        except Exception as e:
            logger.error(f"Failed to export CSV: {str(e)}")
            raise OutputGenerationError(f"CSV export failed: {str(e)}")

    def to_excel(self, records: List[InvestorRecord]) -> str:
        """
        Export records to Excel file with formatting.
        Returns path to created file.
        """
        try:
            excel_path = OUTPUT_CONFIG["excel_file"]

            logger.info(f"📊 Exporting to Excel: {excel_path}")

            # Create DataFrame
            data = self._prepare_data(records)
            df = pd.DataFrame(data)

            # Write to Excel with formatting
            with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Investors", index=False)

                # Get the worksheet
                worksheet = writer.sheets["Investors"]

                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter

                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except Exception:
                            pass

                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

                # Freeze header row
                worksheet.freeze_panes = "A2"

            logger.info(f"✅ Excel exported successfully ({len(records)} records)")
            logger.info(f"   Path: {excel_path}")

            return str(excel_path)

        except Exception as e:
            logger.error(f"❌ Failed to export Excel: {str(e)}")
            raise OutputGenerationError(f"Excel export failed: {str(e)}")

    def _prepare_data(self, records: List[InvestorRecord]) -> List[dict]:
        """
        Prepare data for export.
        Converts records to dictionaries with proper formatting.
        """
        data = []

        for record in records:
            entry = {
                "Investor Name": record.investor_name,
                "Investor Type": record.investor_type,
                "Website URL": record.website_url or "",
                "Investment Stage": record.investment_stage or "",
                "Sectors of Interest": "; ".join(record.sectors_of_interest) or "",
                "Portfolio Companies": "; ".join(record.notable_portfolio_companies) or "",
                "LinkedIn Profile": record.linkedin_profile_url or "",
                "Data Source": record.source,
                "Data Quality Score": f"{record.data_quality_score:.0%}",
                "Data Collected": record.data_collected_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            data.append(entry)

        return data

    @staticmethod
    def export_sample_data() -> List[InvestorRecord]:
        """
        Create verified investor records from the audit database.
        Returns 30+ high-confidence verified investors.
        """
        from pipeline.auditor import VERIFIED_VCS
        from datetime import datetime
        
        verified_records = []
        
        # Generate records from verified database (all of them)
        for vc_name, vc_data in VERIFIED_VCS.items():
            record = InvestorRecord(
                investor_name=vc_data.get("official_name", vc_name),
                investor_type=vc_data.get("investor_type", "VC"),
                website_url=f"https://{vc_data.get('official_domain', 'unknown.com')}",
                investment_stage=", ".join(vc_data.get("investment_stages", ["Seed", "Series A"])[:2]),
                sectors_of_interest=vc_data.get("sectors", ["SaaS", "B2B"]),
                notable_portfolio_companies=vc_data.get("verified_portfolio", [])[:5],
                linkedin_profile_url=vc_data.get("linkedin", ""),
                source="verified_database",
                data_quality_score=0.95,  # All from verified database have high confidence
            )
            verified_records.append(record)
        
        return verified_records
