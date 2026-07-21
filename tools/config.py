"""
config.py — Configuration loader for water-puppetry-staging-design.

Merges KNOWLEDGE_CONFIG defaults with environment variables and CLI arguments
into a single typed configuration object.

Usage:
    from tools.config import load_config, AppConfig
    cfg = load_config(keywords=["custom kw"])
    print(cfg.domain)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ScoringWeights:
    recency: float = 0.4
    keyword_relevance: float = 0.4
    citation_count: float = 0.2


@dataclass
class AppConfig:
    domain: str = "Traditional Performing Arts Staging & Production Design"
    keywords: list[str] = field(default_factory=list)
    arxiv_categories: list[str] = field(default_factory=list)
    arxiv_base: str = "https://export.arxiv.org/api/query"
    semantic_scholar_base: str = "https://api.semanticscholar.org/graph/v1/paper/search"
    rss_feeds: list[str] = field(default_factory=list)
    authoritative_docs: list[str] = field(default_factory=list)
    scoring_weights: ScoringWeights = field(default_factory=ScoringWeights)
    max_results_per_source: int = 10
    max_new_entries_per_run: int = 20
    log_level: str = "INFO"
    log_file: str = ""
    dry_run: bool = False
    news_only: bool = False

    @property
    def brain_path(self) -> Path:
        return Path(__file__).parent.parent / "SECOND-KNOWLEDGE-BRAIN.md"

    @property
    def log_path(self) -> Path | None:
        if self.log_file:
            return Path(__file__).parent.parent / self.log_file
        return None


DEFAULT_CONFIG: dict[str, Any] = {
    "domain": "Traditional Performing Arts Staging & Production Design",
    "keywords": [
        "water puppetry stage design",
        "traditional puppet mechanism",
        "stage lighting design DMX",
        "water theatre engineering",
        "multimedia performance effects",
        "Vietnamese folk tale repertoire",
    ],
    "arxiv_categories": [],
    "arxiv_base": "https://export.arxiv.org/api/query",
    "semantic_scholar_base": "https://api.semanticscholar.org/graph/v1/paper/search",
    "rss_feeds": [],
    "authoritative_docs": [
        "Theatre Journal — Johns Hopkins UP",
        "Performance Research — Taylor & Francis",
        "Journal of Theatre and Performance Design — Taylor & Francis",
        "Lighting Research & Technology — SAGE",
        "Entertainment Computing — Elsevier",
        "Asian Theatre Journal — Project MUSE",
    ],
    "scoring_weights": {
        "recency": 0.4,
        "keyword_relevance": 0.4,
        "citation_count": 0.2,
    },
    "max_results_per_source": 10,
    "max_new_entries_per_run": 20,
}


def _env_bool(key: str, default: bool = False) -> bool:
    val = os.environ.get(key, "").lower()
    if val in ("1", "true", "yes", "on"):
        return True
    if val in ("0", "false", "no", "off"):
        return False
    return default


def _env_list(key: str, default: list[str] | None = None) -> list[str]:
    val = os.environ.get(key, "")
    if not val:
        return default or []
    try:
        parsed = json.loads(val)
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    return [v.strip() for v in val.split(",") if v.strip()]


def load_config(
    keywords: list[str] | None = None,
    dry_run: bool = False,
    news_only: bool = False,
    log_level: str = "",
    log_file: str = "",
) -> AppConfig:
    cfg = AppConfig(
        domain=DEFAULT_CONFIG["domain"],
        keywords=keywords or DEFAULT_CONFIG["keywords"],
        arxiv_categories=DEFAULT_CONFIG.get("arxiv_categories", []),
        arxiv_base=DEFAULT_CONFIG.get("arxiv_base", "https://export.arxiv.org/api/query"),
        semantic_scholar_base=DEFAULT_CONFIG.get(
            "semantic_scholar_base", "https://api.semanticscholar.org/graph/v1/paper/search"
        ),
        rss_feeds=_env_list("WPSD_RSS_FEEDS", DEFAULT_CONFIG.get("rss_feeds", [])),
        authoritative_docs=DEFAULT_CONFIG.get("authoritative_docs", []),
        scoring_weights=ScoringWeights(**DEFAULT_CONFIG.get("scoring_weights", {})),
        max_results_per_source=DEFAULT_CONFIG.get("max_results_per_source", 10),
        max_new_entries_per_run=DEFAULT_CONFIG.get("max_new_entries_per_run", 20),
        log_level=log_level or os.environ.get("WPSD_LOG_LEVEL", "INFO"),
        log_file=log_file or os.environ.get("WPSD_LOG_FILE", ""),
        dry_run=dry_run or _env_bool("WPSD_DRY_RUN"),
        news_only=news_only or _env_bool("WPSD_NEWS_ONLY"),
    )
    return cfg
