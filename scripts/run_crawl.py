"""
scripts/run_crawl.py - Thin wrapper around the knowledge crawl pipeline.

Forwards CLI args to tools.knowledge_updater with sensible defaults, so ops
scripts and cron can call one entrypoint. Supports --dry-run, --news-only,
--keywords, --log-level, --log-file.

Usage:
    python -m scripts.run_crawl --dry-run
    python -m scripts.run_crawl --keywords "water puppetry" "DMX lighting"
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.config import load_config
from tools.knowledge_updater import run_pipeline
from tools.logger import configure_root_logger


def main() -> int:
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    news_only = "--news-only" in args
    log_level = "INFO"
    log_file = ""
    keywords: list[str] | None = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--log-level" and i + 1 < len(args):
            log_level = args[i + 1]
            i += 2
        elif a == "--log-file" and i + 1 < len(args):
            log_file = args[i + 1]
            i += 2
        elif a == "--keywords":
            keywords = []
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                keywords.append(args[i])
                i += 1
        else:
            i += 1

    configure_root_logger(
        level=getattr(logging, log_level.upper(), logging.INFO), log_file=Path(log_file) if log_file else None
    )
    cfg = load_config(keywords=keywords, dry_run=dry_run, news_only=news_only, log_level=log_level, log_file=log_file)
    result = run_pipeline(cfg)
    print(
        f"candidates={result['candidates']} appended={result['appended']} "
        f"errors={len(result['errors'])} dry_run={result['dry_run']}"
    )
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
