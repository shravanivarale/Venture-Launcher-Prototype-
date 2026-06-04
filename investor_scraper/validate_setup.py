"""
Validation script to verify system setup and dependencies.
Run: python validate_setup.py
"""

import sys
import os
from pathlib import Path


class ValidationChecker:
    """Validates system setup and environment."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.project_root = Path(__file__).parent

    def header(self, title: str):
        """Print section header."""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}\n")

    def check(self, name: str, condition: bool, error: str = ""):
        """Check a condition and report result."""
        if condition:
            print(f"✅ {name}")
            self.passed += 1
        else:
            print(f"❌ {name}")
            if error:
                print(f"   Error: {error}")
            self.failed += 1

    def warning(self, name: str, message: str):
        """Report a warning."""
        print(f"⚠️  {name}")
        print(f"   {message}")
        self.warnings += 1

    def run(self):
        """Run all validations."""
        print("\n" + "="*60)
        print("🚀 INVESTOR SCRAPER SETUP VALIDATION")
        print("="*60)

        # 1. Python environment
        self.header("Python Environment")
        self._check_python()

        # 2. Dependencies
        self.header("Dependencies")
        self._check_dependencies()

        # 3. Project structure
        self.header("Project Structure")
        self._check_structure()

        # 4. Imports
        self.header("Module Imports")
        self._check_imports()

        # 5. Configuration
        self.header("Configuration")
        self._check_config()

        # 6. Output directories
        self.header("Output Directories")
        self._check_directories()

        # Summary
        self._print_summary()

    def _check_python(self):
        """Check Python version and executability."""
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self.check(f"Python {version}", sys.version_info >= (3, 8), 
                   "Requires Python 3.8+")

        self.check("Virtual Environment Active",
                   hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))

    def _check_dependencies(self):
        """Check required packages."""
        required = {
            "requests": "HTTP requests",
            "bs4": "BeautifulSoup (HTML parsing)",
            "pydantic": "Data validation",
            "pandas": "Data processing",
            "openpyxl": "Excel export",
        }

        for package, description in required.items():
            try:
                __import__(package)
                self.check(f"{package}: {description}", True)
            except ImportError as e:
                self.check(f"{package}: {description}", False,
                          "Install with: pip install -r requirements.txt")

    def _check_structure(self):
        """Check project directory structure."""
        required_dirs = [
            "core",
            "scrapers",
            "pipeline",
            "utils",
            "output",
            "logs",
        ]

        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            self.check(f"Directory: {dir_name}/", dir_path.is_dir(),
                      f"Missing directory: {dir_path}")

        required_files = [
            "main.py",
            "config.py",
            "requirements.txt",
            "README.md",
            "core/engine.py",
            "core/schemas.py",
            "core/exceptions.py",
            "scrapers/base_scraper.py",
            "scrapers/angellist.py",
            "pipeline/cleaner.py",
            "pipeline/deduplicator.py",
            "pipeline/exporter.py",
            "utils/logger.py",
            "utils/validators.py",
        ]

        for file_name in required_files:
            file_path = self.project_root / file_name
            self.check(f"File: {file_name}", file_path.is_file(),
                      f"Missing file: {file_path}")

    def _check_imports(self):
        """Check that modules can be imported."""
        try:
            from config import SCRAPER_CONFIG, SECTOR_TAXONOMY
            self.check("config module", True)
        except ImportError as e:
            self.check("config module", False, str(e))

        try:
            from core.schemas import InvestorRecord
            self.check("core.schemas module", True)
        except ImportError as e:
            self.check("core.schemas module", False, str(e))

        try:
            from core.exceptions import InvestorScraperError
            self.check("core.exceptions module", True)
        except ImportError as e:
            self.check("core.exceptions module", False, str(e))

        try:
            from utils.logger import get_logger
            self.check("utils.logger module", True)
        except ImportError as e:
            self.check("utils.logger module", False, str(e))

        try:
            from utils.validators import Validators
            self.check("utils.validators module", True)
        except ImportError as e:
            self.check("utils.validators module", False, str(e))

        try:
            from scrapers.base_scraper import BaseScraper
            self.check("scrapers.base_scraper module", True)
        except ImportError as e:
            self.check("scrapers.base_scraper module", False, str(e))

    def _check_config(self):
        """Check configuration."""
        try:
            from config import SCRAPERS, SECTOR_TAXONOMY, SCRAPER_CONFIG

            self.check("SCRAPERS defined", len(SCRAPERS) >= 3,
                      f"Only {len(SCRAPERS)} scrapers defined, expected ≥3")

            self.check("SECTOR_TAXONOMY defined", len(SECTOR_TAXONOMY) >= 5,
                      f"Only {len(SECTOR_TAXONOMY)} sectors defined")

            self.check("SCRAPER_CONFIG defined", "timeout" in SCRAPER_CONFIG,
                      "SCRAPER_CONFIG missing required keys")

            for scraper_name in ["angellist", "crunchbase", "tracxn"]:
                self.check(f"  Scraper '{scraper_name}' configured",
                          scraper_name in SCRAPERS)

        except Exception as e:
            self.check("Configuration valid", False, str(e))

    def _check_directories(self):
        """Check and create output directories."""
        directories = [
            self.project_root / "output",
            self.project_root / "logs",
        ]

        for dir_path in directories:
            if not dir_path.exists():
                try:
                    dir_path.mkdir(exist_ok=True)
                    self.check(f"Created: {dir_path.name}/", True)
                except Exception as e:
                    self.check(f"Created: {dir_path.name}/", False, str(e))
            else:
                self.check(f"Exists: {dir_path.name}/", True)

            # Check write permissions
            try:
                test_file = dir_path / ".write_test"
                test_file.write_text("test")
                test_file.unlink()
                self.check(f"Write permission: {dir_path.name}/", True)
            except Exception as e:
                self.warning(f"Write permission: {dir_path.name}/",
                           "May have permission issues")

    def _print_summary(self):
        """Print validation summary."""
        print("\n" + "="*60)
        print("📊 VALIDATION SUMMARY")
        print("="*60)

        total = self.passed + self.failed
        print(f"\n✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"⚠️  Warnings: {self.warnings}")

        if self.failed == 0:
            print("\n" + "="*60)
            print("🎉 ALL CHECKS PASSED! System ready for use.")
            print("="*60)
            print("\nNext steps:")
            print("1. Run sample: python main.py --sample")
            print("2. Run full pipeline: python main.py")
            print("3. Check output: ls output/")
            print("4. Read docs: cat README.md")
            return 0
        else:
            print("\n" + "="*60)
            print("❌ SETUP INCOMPLETE. Please fix issues above.")
            print("="*60)
            print("\nCommon fixes:")
            print("1. Install dependencies: pip install -r requirements.txt")
            print("2. Create directories: mkdir output logs")
            print("3. Check Python version: python --version")
            return 1


def main():
    """Run validation."""
    checker = ValidationChecker()
    exit_code = checker.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
