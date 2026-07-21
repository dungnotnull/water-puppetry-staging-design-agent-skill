"""
knowledge_updater.py — Skill 167: water-puppetry-staging-design
Crawl pipeline: fetches latest papers + news -> scores -> appends to
SECOND-KNOWLEDGE-BRAIN.md.

Dependencies: pip install requests feedparser python-dateutil
Usage:
    python tools/knowledge_updater.py [--dry-run] [--news-only] [--keywords ...] [--log-level INFO]
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import math
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]
try:
    import feedparser
except ImportError:
    feedparser = None  # type: ignore[assignment]

from tools.config import AppConfig, load_config
from tools.exceptions import AppendError, BrainNotFoundError, CrawlError
from tools.logger import configure_root_logger, setup_logger

logger = setup_logger("knowledge_updater")

BRAIN_PATH = Path(__file__).parent.parent / "SECOND-KNOWLEDGE-BRAIN.md"


def build_identifier(title: str, doi_url: str) -> str:
    """Build a normalized identifier for dedup purposes."""
    return f"{title.strip().lower()}::{doi_url.strip().lower()}"


def compute_hash(identifier: str) -> str:
    """Compute SHA256 hash for dedup (case/whitespace-insensitive)."""
    return hashlib.sha256(identifier.strip().lower().encode()).hexdigest()


def load_existing_hashes(brain_path: Path) -> set[str]:
    """Extract all existing entry hashes from the knowledge brain."""
    if not brain_path.exists():
        return set()
    hashes: set[str] = set()
    text = brain_path.read_text(encoding="utf-8")
    for m in re.finditer(r"\*\*DOI/URL:\*\*\s*(\S+)", text):
        hashes.add(compute_hash(m.group(1)))
    return hashes


def score_entry(entry: dict[str, Any], keywords: list[str], now: datetime) -> float:
    """Compute composite relevance score (0–10) for an entry."""
    pub = entry.get("published_date")
    recency = 0.0
    if pub is not None:
        try:
            recency = max(0.0, 1.0 - (now - pub).days / 730.0)
        except Exception:
            recency = 0.0

    text = ((entry.get("title") or "") + " " + (entry.get("abstract") or "")).lower()
    hits = sum(1 for kw in keywords if kw.lower() in text)
    relevance = min(hits / max(len(keywords), 1), 1.0)

    cit = entry.get("citation_count") or 0
    cit = max(0, int(cit))
    cit_score = min(math.log1p(cit) / math.log1p(1000), 1.0)

    w = entry.get("_scoring_weights", {"recency": 0.4, "keyword_relevance": 0.4, "citation_count": 0.2})
    return round(
        (recency * w["recency"] + relevance * w["keyword_relevance"] + cit_score * w["citation_count"]) * 10.0, 2
    )


def fetch_with_retry(
    url: str,
    params: dict[str, Any] | None = None,
    max_retries: int = 3,
    base_delay: float = 2.0,
    source: str = "unknown",
) -> requests.Response | None:
    """HTTP GET with exponential backoff and rate-limit awareness."""
    if requests is None:
        logger.warning("requests library not installed; cannot fetch %s", source)
        return None

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                delay = base_delay * (2 ** (attempt - 1))
                logger.debug("Retry %d/%d for %s after %.1fs", attempt + 1, max_retries, source, delay)
                time.sleep(delay)

            resp = requests.get(url, params=params or {}, timeout=30)

            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After", "")
                wait = float(retry_after) if retry_after.isdigit() else base_delay * (2**attempt)
                logger.warning(
                    "Rate limited by %s (429), attempt %d/%d, waiting %.1fs", source, attempt + 1, max_retries, wait
                )
                if attempt < max_retries - 1:
                    time.sleep(wait)
                    continue
                raise CrawlError(f"Rate limited by {source}", source=source, retryable=True)

            if resp.status_code >= 500:
                logger.warning(
                    "Server error %d from %s, attempt %d/%d", resp.status_code, source, attempt + 1, max_retries
                )
                if attempt < max_retries - 1:
                    time.sleep(base_delay)
                    continue
                raise CrawlError(f"Server error {resp.status_code} from {source}", source=source, retryable=True)

            resp.raise_for_status()
            return resp

        except CrawlError:
            raise
        except requests.RequestException as ex:
            logger.warning("Request failed for %s (attempt %d/%d): %s", source, attempt + 1, max_retries, ex)
            if attempt < max_retries - 1:
                time.sleep(base_delay)
            else:
                raise CrawlError(f"Failed to fetch {source}: {ex}", source=source, retryable=True)

    return None


def fetch_arxiv(cfg: AppConfig) -> list[dict[str, Any]]:
    """Fetch papers from ArXiv based on configured keywords."""
    if requests is None:
        logger.info("requests not installed, skipping ArXiv fetch")
        return []
    if not cfg.arxiv_categories:
        logger.info("No ArXiv categories configured, skipping")
        return []

    cats = cfg.arxiv_categories
    kw_clause = " OR ".join(f'"{k}"' for k in cfg.keywords[:5])
    cat_clause = " OR ".join(f"cat:{c}" for c in cats)
    query = f"({cat_clause}) AND ({kw_clause})"

    try:
        resp = fetch_with_retry(
            cfg.arxiv_base,
            {
                "search_query": query,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
                "max_results": cfg.max_results_per_source,
            },
            source="arxiv",
        )
    except CrawlError as e:
        logger.error("ArXiv crawl failed: %s", e)
        return []

    if resp is None:
        return []

    import xml.etree.ElementTree as ET

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        logger.error("ArXiv response parse error: %s", e)
        return []

    out: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", ns):
        t = entry.find("atom:title", ns)
        s = entry.find("atom:summary", ns)
        i = entry.find("atom:id", ns)
        p = entry.find("atom:published", ns)

        title = (t.text or "").strip().replace("\n", " ") if t is not None else ""
        url = (i.text or "").strip() if i is not None else ""
        if not title or not url:
            continue

        pub: datetime | None = None
        if p is not None and p.text:
            try:
                from dateutil import parser as dateparser

                pub = dateparser.parse(p.text).replace(tzinfo=None)
            except (ValueError, OverflowError, TypeError) as parse_err:
                logger.debug("ArXiv date parse failed for '%s': %s", title[:60], parse_err)

        authors_elements = entry.findall("atom:author", ns)
        authors = []
        for a in authors_elements:
            name_el = a.find("atom:name", ns)
            if name_el is not None and name_el.text:
                authors.append(name_el.text)
        authors = authors[:3]

        abstract_text = (s.text or "")[:300] if s is not None else ""

        out.append(
            {
                "title": title,
                "authors": authors,
                "year": pub.year if pub else datetime.now().year,
                "venue": "ArXiv",
                "doi_or_url": url,
                "abstract": abstract_text,
                "published_date": pub,
                "citation_count": 0,
                "source": "arxiv",
            }
        )

    logger.info("ArXiv fetch complete: %d results", len(out))
    return out


def fetch_semantic_scholar(cfg: AppConfig) -> list[dict[str, Any]]:
    """Fetch papers from Semantic Scholar API."""
    if requests is None:
        logger.info("requests not installed, skipping Semantic Scholar fetch")
        return []

    try:
        resp = fetch_with_retry(
            cfg.semantic_scholar_base,
            {
                "query": " ".join(cfg.keywords[:4]),
                "fields": "title,authors,year,venue,externalIds,abstract,citationCount",
                "limit": cfg.max_results_per_source,
            },
            source="semantic_scholar",
        )
    except CrawlError as e:
        logger.error("Semantic Scholar crawl failed: %s", e)
        return []

    if resp is None:
        return []

    try:
        data = resp.json()
    except ValueError as e:
        logger.error("Semantic Scholar response parse error: %s", e)
        return []

    out: list[dict[str, Any]] = []
    for p in data.get("data", []):
        title = p.get("title", "")
        if not title:
            continue
        year = p.get("year") or datetime.now().year
        ext = p.get("externalIds", {})
        doi = ext.get("DOI") or ""
        if not doi and ext.get("ArXiv"):
            doi = f"https://arxiv.org/abs/{ext['ArXiv']}"
        if not doi:
            doi = f"https://www.semanticscholar.org/paper/{p.get('paperId', '')}"

        out.append(
            {
                "title": title,
                "authors": [a.get("name", "") for a in p.get("authors", [])[:3]],
                "year": year,
                "venue": p.get("venue") or "Unknown",
                "doi_or_url": doi,
                "abstract": (p.get("abstract") or "")[:300],
                "published_date": datetime(year, 1, 1),
                "citation_count": p.get("citationCount", 0),
                "source": "semantic_scholar",
            }
        )

    logger.info("Semantic Scholar fetch complete: %d results", len(out))
    return out


def fetch_rss(cfg: AppConfig) -> list[dict[str, Any]]:
    """Fetch entries from configured RSS feeds."""
    if feedparser is None:
        logger.info("feedparser not installed, skipping RSS fetch")
        return []
    if not cfg.rss_feeds:
        logger.info("No RSS feeds configured, skipping")
        return []

    out: list[dict[str, Any]] = []
    for url in cfg.rss_feeds:
        try:
            feed = feedparser.parse(url)
        except Exception as ex:
            logger.warning("RSS feed parse failed for %s: %s", url, ex)
            continue

        for item in feed.entries[:10]:
            title = item.get("title", "")
            link = item.get("link", "")
            if not title or not link:
                continue

            pp = item.get("published_parsed")
            pub = datetime(*pp[:6]) if pp else datetime.now()

            out.append(
                {
                    "title": title,
                    "authors": ["Editorial"],
                    "year": pub.year,
                    "venue": "RSS",
                    "doi_or_url": link,
                    "abstract": str(item.get("summary", ""))[:200],
                    "published_date": pub,
                    "citation_count": 0,
                    "source": "rss",
                }
            )

    logger.info("RSS fetch complete: %d results across %d feeds", len(out), len(cfg.rss_feeds))
    return out


def format_entry(entry: dict[str, Any], score: float) -> str:
    """Format a single knowledge entry as markdown for the brain."""
    d = datetime.now().strftime("%Y-%m-%d")
    authors = ", ".join(entry.get("authors", [])) or "Unknown"
    source_tag = entry.get("source", "crawl")

    lines = [
        f"\n### {d} [{source_tag}] {entry.get('title', 'Untitled')}",
        f"- **Authors:** {authors}",
        f"- **Year:** {entry.get('year', '')}",
        f"- **Venue:** {entry.get('venue', 'Unknown')}",
        f"- **DOI/URL:** {entry.get('doi_or_url', '')}",
        f"- **Relevance Score:** {score}/10",
        f"- **Key Finding:** {entry.get('abstract', 'No abstract available.')}",
    ]
    return "\n".join(lines) + "\n"


def append_to_brain(
    entries: list[dict[str, Any]],
    cfg: AppConfig,
    brain_path: Path | None = None,
) -> int:
    """Append new entries to SECOND-KNOWLEDGE-BRAIN.md if not already present."""
    bp = brain_path or cfg.brain_path

    if not bp.exists():
        raise BrainNotFoundError(str(bp))

    existing = load_existing_hashes(bp)
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    new_entries: list[dict[str, Any]] = []
    for e in entries:
        doi = e.get("doi_or_url", "")
        if not doi:
            continue
        h = compute_hash(doi)
        if h in existing:
            continue
        existing.add(h)
        new_entries.append(e)

    if not new_entries:
        logger.info("No new entries to append (all %d candidates already present)", len(entries))
        return 0

    for e in new_entries:
        e["_score"] = score_entry(e, cfg.keywords, now)
        w = cfg.scoring_weights
        e["_scoring_weights"] = {
            "recency": w.recency,
            "keyword_relevance": w.keyword_relevance,
            "citation_count": w.citation_count,
        }

    new_entries.sort(key=lambda x: float(x.get("_score", 0)), reverse=True)
    new_entries = new_entries[: cfg.max_new_entries_per_run]

    md_text = "".join(format_entry(e, float(e.get("_score", 0))) for e in new_entries)

    if cfg.dry_run:
        logger.info("DRY RUN: would append %d entries to knowledge brain", len(new_entries))
        for e in new_entries:
            logger.info("  [DRY] %s (score %.1f)", e.get("title", "")[:80], e.get("_score", 0))
        return len(new_entries)

    try:
        content = bp.read_text(encoding="utf-8")
    except OSError as e:
        raise AppendError(f"Cannot read brain file: {e}", count_attempted=len(new_entries))

    if "## 7. Knowledge Update Log" in content:
        content += md_text
    else:
        content += "\n## 7. Knowledge Update Log\n" + md_text

    try:
        bp.write_text(content, encoding="utf-8")
    except OSError as e:
        raise AppendError(f"Cannot write brain file: {e}", count_attempted=len(new_entries))

    logger.info("Appended %d new entries to knowledge brain", len(new_entries))
    return len(new_entries)


def run_pipeline(cfg: AppConfig) -> dict[str, Any]:
    """Run the full crawl-then-append pipeline. Returns summary dict."""
    all_entries: list[dict[str, Any]] = []
    errors: list[str] = []

    if not cfg.news_only:
        try:
            all_entries += fetch_arxiv(cfg)
            time.sleep(1)
        except Exception as e:
            errors.append(f"arxiv: {e}")

        try:
            all_entries += fetch_semantic_scholar(cfg)
            time.sleep(1)
        except Exception as e:
            errors.append(f"semantic_scholar: {e}")

    try:
        all_entries += fetch_rss(cfg)
    except Exception as e:
        errors.append(f"rss: {e}")

    logger.info("Total candidates before dedup: %d", len(all_entries))

    n_appended = 0
    try:
        n_appended = append_to_brain(all_entries, cfg)
    except (AppendError, BrainNotFoundError) as e:
        logger.error("Append failed: %s", e)
        errors.append(f"append: {e}")

    return {
        "candidates": len(all_entries),
        "appended": n_appended,
        "errors": errors,
        "dry_run": cfg.dry_run,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Knowledge updater crawl pipeline for water-puppetry-staging-design",
    )
    parser.add_argument("--dry-run", action="store_true", help="Fetch but do not write to knowledge base")
    parser.add_argument("--news-only", action="store_true", help="Only fetch RSS feeds (skip academic sources)")
    parser.add_argument("--keywords", nargs="+", help="Override keyword list for this run")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    parser.add_argument("--log-file", default="", help="Also write logs to a file path")
    args = parser.parse_args()

    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    log_path = Path(args.log_file) if args.log_file else None
    configure_root_logger(level=log_level, log_file=log_path)

    keywords = args.keywords or None
    cfg = load_config(
        keywords=keywords,
        dry_run=args.dry_run,
        news_only=args.news_only,
        log_level=args.log_level,
        log_file=args.log_file,
    )

    logger.info(
        "Knowledge updater started | dry_run=%s news_only=%s log_level=%s",
        cfg.dry_run,
        cfg.news_only,
        cfg.log_level,
    )

    result = run_pipeline(cfg)

    logger.info(
        "Knowledge updater finished | candidates=%d appended=%d errors=%d",
        result["candidates"],
        result["appended"],
        len(result["errors"]),
    )

    if result["errors"]:
        logger.warning("Errors encountered during run:")
        for err in result["errors"]:
            logger.warning("  - %s", err)

    if result["appended"] == 0 and not result["dry_run"]:
        logger.info("No new entries were appended. The knowledge base is up to date.")


if __name__ == "__main__":
    main()
