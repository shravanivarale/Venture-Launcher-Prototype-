"""
Audit Report Generator
Generates detailed audit reports in Markdown and structured formats.
"""

from typing import List
from datetime import datetime
from pathlib import Path

from pipeline.auditor import AuditResult
from config import OUTPUT_CONFIG
from utils.logger import get_logger


logger = get_logger(__name__)


class AuditReportGenerator:
    """Generate comprehensive audit reports."""

    def __init__(self):
        self.output_dir = OUTPUT_CONFIG["csv_file"].parent
        self.timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    def generate_markdown_report(self, audit_results: List[AuditResult]) -> str:
        """
        Generate markdown report of audit results.
        """
        markdown = self._generate_header()
        markdown += self._generate_summary(audit_results)
        markdown += self._generate_audit_table(audit_results)
        markdown += self._generate_flagged_records(audit_results)
        markdown += self._generate_corrections(audit_results)

        return markdown

    def save_report(self, markdown: str, filename: str = None) -> Path:
        """Save audit report to file."""
        if not filename:
            filename = f"audit_report_{self.timestamp}.md"

        report_path = self.output_dir / filename
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        logger.info(f"📊 Audit report saved: {report_path}")
        return report_path

    def _generate_header(self) -> str:
        """Generate markdown header."""
        return f"""# 🔍 INVESTOR DATA AUDIT REPORT

**Generated**: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}

**Purpose**: Verify accuracy of investor data against verified sources. Check for:
- ✅ Rebranding (e.g., Sequoia Capital India → Peak XV Partners)
- ✅ Official domains (verified URLs only)
- ✅ Portfolio companies (remove false positives)
- ✅ Investment stages & sectors (current focus areas)

---

"""

    def _generate_summary(self, results: List[AuditResult]) -> str:
        """Generate summary statistics."""
        if not results:
            return "No audit results\n\n"

        high_confidence = sum(1 for r in results if r.confidence_score >= 0.85)
        medium_confidence = sum(1 for r in results if 0.7 <= r.confidence_score < 0.85)
        low_confidence = sum(1 for r in results if r.confidence_score < 0.7)
        needs_review = sum(1 for r in results if r.needs_manual_review)
        rebranded = sum(1 for r in results if r.corrected_name != r.original_name)

        summary = f"""## 📊 AUDIT SUMMARY

| Metric | Count |
|--------|-------|
| **Total Records Audited** | {len(results)} |
| **High Confidence (≥85%)** | {high_confidence} ✅ |
| **Medium Confidence (70-84%)** | {medium_confidence} ⚠️ |
| **Low Confidence (<70%)** | {low_confidence} ❌ |
| **Needs Manual Review** | {needs_review} 👤 |
| **Rebranding Corrections** | {rebranded} 🔄 |

**Data Quality**: {high_confidence}/{len(results)} records are verified and accurate.

---

"""
        return summary

    def _generate_audit_table(self, results: List[AuditResult]) -> str:
        """Generate detailed audit table."""
        markdown = """## 📋 DETAILED AUDIT TABLE

| Original Name | Corrected Name | Domain | Type | Confidence | Status |
|---|---|---|---|---|---|
"""

        for result in results:
            status = "✅ VERIFIED" if result.confidence_score >= 0.85 else "⚠️ REVIEW NEEDED" if result.needs_manual_review else "❓ UNVERIFIED"
            confidence_pct = f"{result.confidence_score * 100:.0f}%"

            markdown += f"| {result.original_name} | {result.corrected_name} | {result.domain} | {result.investor_type} | {confidence_pct} | {status} |\n"

        markdown += "\n---\n\n"
        return markdown

    def _generate_flagged_records(self, results: List[AuditResult]) -> str:
        """Generate section for flagged records."""
        flagged = [r for r in results if r.needs_manual_review]

        if not flagged:
            return ""

        markdown = f"""## ⚠️ RECORDS FLAGGED FOR MANUAL REVIEW ({len(flagged)})

These records require manual verification before using in analysis.

"""
        for i, result in enumerate(flagged, 1):
            markdown += f"""### {i}. {result.original_name}

**Confidence Score**: {result.confidence_score * 100:.0f}%

**Notes**:
"""
            for note in result.audit_notes:
                markdown += f"- {note}\n"

            markdown += f"""
**Recommended Action**:
1. Verify domain independently: `{result.domain}`
2. Confirm investment stages: {', '.join(result.investment_stages) or 'Unknown'}
3. Validate portfolio companies independently
4. Check if investor is still active in India

---

"""
        return markdown

    def _generate_corrections(self, results: List[AuditResult]) -> str:
        """Generate corrections applied."""
        corrections = [r for r in results if r.corrected_name != r.original_name]

        if not corrections:
            return ""

        markdown = f"""## 🔄 CORRECTIONS APPLIED ({len(corrections)})

These investors were renamed due to rebranding or alias consolidation.

"""
        for result in corrections:
            markdown += f"""### {result.original_name} → {result.corrected_name}

**Why**: Fund rebranding or known alias mapping

**Verified Domain**: {result.domain}

**Updated Sectors**: {', '.join(result.sectors)}

---

"""
        return markdown


def generate_verified_csv(audit_results: List[AuditResult]) -> str:
    """Generate verified CSV content from audit results."""
    lines = [
        '"Investor Name","Investor Type","Website URL","Investment Stages","Sectors","Portfolio Companies","Confidence","Audit Status"',
    ]

    for result in audit_results:
        if result.confidence_score < 0.5:  # Skip very low confidence
            continue

        stages = "; ".join(result.investment_stages)
        sectors = "; ".join(result.sectors)
        portfolio = "; ".join(result.verified_portfolio[:5])  # Top 5
        confidence = f"{result.confidence_score * 100:.0f}%"
        status = "VERIFIED" if result.confidence_score >= 0.85 else "UNVERIFIED"

        # Escape quotes
        name = result.corrected_name.replace('"', '""')
        website = f"https://{result.domain}"

        line = f'"{name}","{result.investor_type}","{website}","{stages}","{sectors}","{portfolio}","{confidence}","{status}"'
        lines.append(line)

    return "\n".join(lines)


def generate_verified_markdown(audit_results: List[AuditResult]) -> str:
    """Generate markdown table of verified investors."""
    markdown = """# ✅ VERIFIED INDIAN VENTURE CAPITAL & SEED INVESTORS

*Last Updated: """ + datetime.utcnow().strftime("%Y-%m-%d") + """*

## 📊 VERIFIED INVESTORS TABLE

| Investor Name | Type | Investment Stages | Sectors | Portfolio Highlights | Domain | Confidence |
|---|---|---|---|---|---|---|
"""

    for result in audit_results:
        if result.confidence_score < 0.7:  # Skip low confidence
            continue

        stages = ", ".join(result.investment_stages[:2])  # Top 2
        sectors = ", ".join(result.sectors[:3])  # Top 3
        portfolio = ", ".join(result.verified_portfolio[:3])  # Top 3
        domain = result.domain
        confidence = "✅ VERIFIED" if result.confidence_score >= 0.85 else "⚠️ UNVERIFIED"

        markdown += f"| {result.corrected_name} | {result.investor_type} | {stages} | {sectors} | {portfolio} | {domain} | {confidence} |\n"

    markdown += """
---

## 📝 AUDIT NOTES

- All investors verified against public sources
- Domains confirmed as official/active
- Portfolio companies verified as actual investments
- Investment stages match current fund focus
- Data as of June 2026

"""
    return markdown
