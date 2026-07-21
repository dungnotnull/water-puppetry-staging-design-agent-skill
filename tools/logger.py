"""
logger.py — Centralized structured logging for water-puppetry-staging-design.

Provides a consistent logging setup used by all tool modules.
Outputs to stdout (colored) and optionally to a rotating file log.

Usage:
    from tools.logger import setup_logger
    logger = setup_logger(__name__)
    logger.info("Starting crawl for %s", domain)
"""

import logging
import sys
from pathlib import Path
from typing import Optional


_LOG_FORMAT = "%(asctime)s [%(levelname)-5s] %(name)s: %(message)s"
_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_DEFAULT_LEVEL = logging.INFO


class _ColoredFormatter(logging.Formatter):
    """Minimal ANSI color formatter for stdout visibility."""

    COLORS = {
        logging.DEBUG: "\033[36m",
        logging.INFO: "\033[32m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[1;31m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, "")
        formatted = super().format(record)
        if color and sys.stdout.isatty():
            return f"{color}{formatted}{self.RESET}"
        return formatted


def setup_logger(
    name: str,
    level: int = _DEFAULT_LEVEL,
    log_file: Optional[Path] = None,
) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(_ColoredFormatter(_LOG_FORMAT, _LOG_DATE_FORMAT))
    logger.addHandler(console_handler)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, _LOG_DATE_FORMAT))
        logger.addHandler(file_handler)

    return logger


def configure_root_logger(level: int = _DEFAULT_LEVEL, log_file: Optional[Path] = None) -> None:
    root = logging.getLogger()
    root.setLevel(level)
    if root.handlers:
        root.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(_ColoredFormatter(_LOG_FORMAT, _LOG_DATE_FORMAT))
    root.addHandler(console_handler)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, _LOG_DATE_FORMAT))
        root.addHandler(file_handler)
