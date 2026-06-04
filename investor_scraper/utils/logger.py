"""
Centralized logging configuration and utilities.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import re
from config import LOGGING_CONFIG


class EncodingSafeFormatter(logging.Formatter):
    """Formatter that removes emoji for terminal compatibility."""
    
    def format(self, record):
        # Simple emoji removal: strip common emoji ranges
        msg = str(record.msg)
        # Remove emojis by replacing non-ASCII chars with spaces
        msg = ''.join(c if ord(c) < 128 else ' ' for c in msg)
        record.msg = msg.strip()
        return super().format(record)


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""

    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[41m",   # Red background
    }
    RESET = "\033[0m"

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


class Logger:
    """Centralized logger instance."""

    _instance = None
    LOG_FILE = Path(LOGGING_CONFIG["log_file"])

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize logger with file and console handlers."""
        self.logger = logging.getLogger("InvestorScraper")
        self.logger.setLevel(getattr(logging, LOGGING_CONFIG["level"]))

        # Ensure log directory exists
        self.LOG_FILE.parent.mkdir(exist_ok=True)

        # File handler (detailed) - UTF-8 for file
        file_handler = RotatingFileHandler(
            self.LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8',
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(LOGGING_CONFIG["format"])
        file_handler.setFormatter(file_formatter)

        # Console handler (colored) - use safe formatter to handle encoding
        import sys
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        # Use safe formatter that strips emoji for terminal compatibility
        console_formatter = EncodingSafeFormatter(LOGGING_CONFIG["format"])
        console_handler.setFormatter(console_formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        """Return the configured logger instance."""
        return self.logger


# Global logger instance
_logger_instance = Logger().get_logger()


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance with optional child name."""
    if name:
        return _logger_instance.getChild(name)
    return _logger_instance
