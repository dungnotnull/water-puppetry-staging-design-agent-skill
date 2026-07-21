"""
exceptions.py — Domain-specific exception hierarchy for water-puppetry-staging-design.

All tool modules should raise and catch exceptions from this module
for consistent error handling across the pipeline.

Usage:
    from tools.exceptions import CrawlError, BrainNotFoundError
    raise CrawlError("ArXiv API returned 429", source="arxiv", retryable=True)
"""


class WPSDError(Exception):
    """Base exception for water-puppetry-staging-design."""


class CrawlError(WPSDError):
    """Raised when a crawl source fails (timeout, HTTP error, parse failure)."""

    def __init__(self, message: str, source: str = "", retryable: bool = False) -> None:
        self.source = source
        self.retryable = retryable
        super().__init__(message)


class BrainNotFoundError(WPSDError):
    """Raised when SECOND-KNOWLEDGE-BRAIN.md does not exist at expected path."""

    def __init__(self, path: str) -> None:
        self.path = path
        super().__init__(f"Knowledge brain not found: {path}")


class AppendError(WPSDError):
    """Raised when appending entries to the knowledge base fails."""

    def __init__(self, message: str, count_attempted: int = 0) -> None:
        self.count_attempted = count_attempted
        super().__init__(message)


class ConfigError(WPSDError):
    """Raised when configuration is invalid or missing required keys."""

    def __init__(self, message: str, key: str = "") -> None:
        self.key = key
        super().__init__(message)


class ValidationError(WPSDError):
    """Raised when a quality gate or structural check fails."""

    def __init__(self, message: str, gate: str = "") -> None:
        self.gate = gate
        super().__init__(message)


class DataUnavailableError(WPSDError):
    """Raised when required data is completely unavailable (degradation Level 4)."""

    def __init__(self, message: str, missing_sources: list[str] | None = None) -> None:
        self.missing_sources = missing_sources or []
        super().__init__(message)
