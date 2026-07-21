"""
scripts/seed_knowledge_base.py - Seed SECOND-KNOWLEDGE-BRAIN.md from references.

Idempotent: only appends entries whose DOI/URL hash is not already present in
the brain. Uses the same SHA256 dedup as tools/knowledge_updater.py. This is a
local setup / ingestion routine for bootstrapping a fresh brain from the
curated references in references/ and config/sources.yaml.

Usage:
    python -m scripts.seed_knowledge_base            # append curated seed entries
    python -m scripts.seed_knowledge_base --dry-run  # show what would be appended
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.config_loader import load_system_config
from tools.knowledge_updater import compute_hash, format_entry, load_existing_hashes
from tools.logger import setup_logger

logger = setup_logger("seed_knowledge_base")

ROOT = Path(__file__).resolve().parent.parent
BRAIN = ROOT / "SECOND-KNOWLEDGE-BRAIN.md"


def build_seed_entries() -> list[dict]:
    """Build curated seed entries from config/sources.yaml."""
    cfg = load_system_config()
    sources = cfg.sources
    entries: list[dict] = []
    for s in sources.get("domain_authoritative", []):
        entries.append(
            {
                "title": f"[Seed] {s['name']} (authoritative source)",
                "authors": ["Curated"],
                "year": datetime.now().year,
                "venue": s.get("url", ""),
                "doi_or_url": s.get("url", ""),
                "abstract": f"Tier {s.get('tier', 3)} authoritative source: {s['name']}.",
                "published_date": datetime.now(),
                "citation_count": 0,
                "source": "seed",
            }
        )
    for s in sources.get("academic", []):
        entries.append(
            {
                "title": f"[Seed] {s['name']} ({s.get('venue', '')})",
                "authors": ["Curated"],
                "year": datetime.now().year,
                "venue": s.get("venue", ""),
                "doi_or_url": s.get("venue", "") or s.get("name", ""),
                "abstract": f"Tier {s.get('tier', 2)} academic source: {s['name']}.",
                "published_date": datetime.now(),
                "citation_count": 0,
                "source": "seed",
            }
        )
    return entries


def seed(dry_run: bool, brain_path: Path = BRAIN) -> int:
    if not brain_path.exists():
        logger.error("brain not found: %s", brain_path)
        return 0
    existing = load_existing_hashes(brain_path)
    candidates = build_seed_entries()
    new = []
    for e in candidates:
        if not e.get("doi_or_url"):
            continue
        h = compute_hash(e["doi_or_url"])
        if h in existing:
            continue
        existing.add(h)
        new.append(e)
    if not new:
        logger.info("no new seed entries (all %d already present)", len(candidates))
        return 0
    md = "".join(format_entry(e, 0.0) for e in new)
    if dry_run:
        logger.info("DRY RUN: would append %d seed entries", len(new))
        for e in new:
            logger.info("  [DRY] %s", e["title"][:80])
        return len(new)
    content = brain_path.read_text(encoding="utf-8")
    if "## 7. Knowledge Update Log" not in content:
        content += "\n## 7. Knowledge Update Log\n"
    content += md
    brain_path.write_text(content, encoding="utf-8")
    logger.info("seeded %d new entries into %s", len(new), brain_path)
    return len(new)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the knowledge brain from curated references")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    n = seed(dry_run=args.dry_run)
    print(f"seeded={n} dry_run={args.dry_run}")


if __name__ == "__main__":
    main()
