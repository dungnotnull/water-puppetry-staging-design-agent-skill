"""
test_knowledge_updater.py — Skill 167: water-puppetry-staging-design
Test suite for knowledge_updater module: dedup, scoring, formatting,
configuration, and edge cases.

Run: pytest tools/test_knowledge_updater.py -v
"""

from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools.config import AppConfig, load_config
from tools.exceptions import AppendError, BrainNotFoundError, CrawlError
from tools.knowledge_updater import (
    append_to_brain,
    compute_hash,
    fetch_arxiv,
    fetch_rss,
    fetch_with_retry,
    format_entry,
    load_existing_hashes,
    score_entry,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_entry() -> dict[str, Any]:
    return {
        "title": "Water Puppetry and Modern Stage Lighting",
        "authors": ["Nguyen, A.", "Tran, B."],
        "year": 2024,
        "venue": "Asian Theatre Journal",
        "doi_or_url": "10.1353/atj.2024.0001",
        "abstract": "This paper examines the integration of DMX-controlled LED lighting in traditional Vietnamese water puppetry.",
        "published_date": datetime.datetime(2024, 6, 15),
        "citation_count": 25,
        "source": "semantic_scholar",
    }


@pytest.fixture
def sample_keywords() -> list[str]:
    return ["water puppetry", "stage lighting", "DMX", "traditional", "puppet"]


@pytest.fixture
def sample_config() -> AppConfig:
    return load_config()


# ---------------------------------------------------------------------------
# Hash & Dedup Tests
# ---------------------------------------------------------------------------


class TestHashing:
    def test_compute_hash_consistent(self) -> None:
        a = compute_hash("https://doi.org/10.1234/example")
        b = compute_hash("https://doi.org/10.1234/example")
        assert a == b

    def test_compute_hash_different(self) -> None:
        a = compute_hash("https://doi.org/10.1234/one")
        b = compute_hash("https://doi.org/10.1234/two")
        assert a != b

    def test_compute_hash_case_insensitive(self) -> None:
        a = compute_hash("  HTTPS://DOI.ORG/10.1234/X  ")
        b = compute_hash("https://doi.org/10.1234/x")
        assert a == b, "Hash should be case/whitespace insensitive"

    def test_compute_hash_hex_format(self) -> None:
        h = compute_hash("test")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_load_existing_hashes_from_real_brain(self) -> None:
        brain_path = Path(__file__).parent.parent / "SECOND-KNOWLEDGE-BRAIN.md"
        if brain_path.exists():
            hashes = load_existing_hashes(brain_path)
            assert isinstance(hashes, set)
            dois = re.findall(r"\*\*DOI/URL:\*\*\s*(\S+)", brain_path.read_text(encoding="utf-8"))
            assert len(hashes) >= len(dois)

    def test_load_existing_hashes_missing_brain(self, tmp_path: Path) -> None:
        nonexistent = tmp_path / "not_a_brain.md"
        hashes = load_existing_hashes(nonexistent)
        assert isinstance(hashes, set)
        assert len(hashes) == 0


# ---------------------------------------------------------------------------
# Scoring Tests
# ---------------------------------------------------------------------------


class TestScoring:
    def test_score_range(self, sample_entry: dict[str, Any], sample_keywords: list[str]) -> None:
        s = score_entry(sample_entry, sample_keywords, datetime.datetime.now())
        assert 0.0 <= s <= 10.0

    def test_score_perfect_match(self, sample_keywords: list[str]) -> None:
        entry = {
            "title": "water puppetry and stage lighting",
            "abstract": "DMX traditional puppet theatre",
            "published_date": datetime.datetime.now(),
            "citation_count": 2000,
        }
        s = score_entry(entry, sample_keywords, datetime.datetime.now())
        assert s >= 7.0, f"Expected high score, got {s}"

    def test_score_no_match(self, sample_keywords: list[str]) -> None:
        entry = {
            "title": "Quantum Computing Advances",
            "abstract": "Novel algorithms for superconducting qubits",
            "published_date": datetime.datetime(2020, 1, 1),
            "citation_count": 0,
        }
        s = score_entry(entry, sample_keywords, datetime.datetime.now())
        assert s <= 3.0, f"Expected low score, got {s}"

    def test_score_old_publication_penalized(self, sample_keywords: list[str]) -> None:
        entry = {
            "title": "water puppetry traditional arts",
            "abstract": "stage lighting DMX control puppet",
            "published_date": datetime.datetime(2015, 1, 1),
            "citation_count": 100,
        }
        s_old = score_entry(entry, sample_keywords, datetime.datetime.now())
        entry["published_date"] = datetime.datetime.now()
        s_new = score_entry(entry, sample_keywords, datetime.datetime.now())
        assert s_new > s_old, f"New entry ({s_new}) should score higher than old ({s_old})"

    def test_score_no_date(self, sample_keywords: list[str]) -> None:
        entry = {
            "title": "water puppetry",
            "abstract": "stage design",
            "published_date": None,
            "citation_count": 0,
        }
        s = score_entry(entry, sample_keywords, datetime.datetime.now())
        assert 0.0 <= s <= 10.0

    def test_score_bogus_date(self, sample_keywords: list[str]) -> None:
        entry = {
            "title": "test",
            "abstract": "test",
            "published_date": "not-a-date",
            "citation_count": 0,
        }
        s = score_entry(entry, sample_keywords, datetime.datetime.now())
        assert 0.0 <= s <= 10.0


# ---------------------------------------------------------------------------
# Formatting Tests
# ---------------------------------------------------------------------------


class TestFormatting:
    def test_format_entry_structure(self, sample_entry: dict[str, Any]) -> None:
        txt = format_entry(sample_entry, 7.5)
        assert "Water Puppetry and Modern Stage Lighting" in txt
        assert "Nguyen, A., Tran, B." in txt
        assert "DOI/URL:" in txt
        assert "**Relevance Score:** 7.5/10" in txt
        assert "Key Finding:" in txt
        assert "[semantic_scholar]" in txt

    def test_format_entry_no_authors(self) -> None:
        entry = {
            "title": "Test",
            "authors": [],
            "year": 2026,
            "venue": "X",
            "doi_or_url": "https://x.com",
            "abstract": "ab",
            "source": "rss",
        }
        txt = format_entry(entry, 3.0)
        assert "Unknown" in txt

    def test_format_entry_score_float(self) -> None:
        entry = {
            "title": "T",
            "authors": [],
            "year": 2025,
            "venue": "V",
            "doi_or_url": "https://x",
            "abstract": "",
            "source": "test",
        }
        txt = format_entry(entry, 9.99)
        assert "9.99/10" in txt


# ---------------------------------------------------------------------------
# Configuration Tests
# ---------------------------------------------------------------------------


class TestConfig:
    def test_default_config_loads(self) -> None:
        cfg = load_config()
        assert cfg.domain == "Traditional Performing Arts Staging & Production Design"
        assert len(cfg.keywords) >= 5
        assert cfg.scoring_weights.recency == 0.4
        assert cfg.scoring_weights.keyword_relevance == 0.4
        assert cfg.scoring_weights.citation_count == 0.2

    def test_config_override_keywords(self) -> None:
        cfg = load_config(keywords=["custom", "test"])
        assert cfg.keywords == ["custom", "test"]

    def test_config_dry_run(self) -> None:
        cfg = load_config(dry_run=True)
        assert cfg.dry_run is True

    def test_config_brain_path(self) -> None:
        cfg = load_config()
        assert cfg.brain_path.name == "SECOND-KNOWLEDGE-BRAIN.md"

    def test_config_log_path(self) -> None:
        cfg = load_config(log_file="logs/test.log")
        assert cfg.log_path is not None
        assert cfg.log_path.name == "test.log"


# ---------------------------------------------------------------------------
# Exception Tests
# ---------------------------------------------------------------------------


class TestExceptions:
    def test_crawl_error(self) -> None:
        e = CrawlError("Test error", source="arxiv", retryable=True)
        assert e.source == "arxiv"
        assert e.retryable is True
        assert "Test error" in str(e)

    def test_brain_not_found_error(self) -> None:
        e = BrainNotFoundError("/nonexistent/file.md")
        assert e.path == "/nonexistent/file.md"

    def test_append_error(self) -> None:
        e = AppendError("Write failed", count_attempted=5)
        assert e.count_attempted == 5


# ---------------------------------------------------------------------------
# HTTP / Mock Tests
# ---------------------------------------------------------------------------


class TestFetchWithRetry:
    def test_fetch_success(self) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        with patch("tools.knowledge_updater.requests") as mock_req:
            mock_req.get.return_value = mock_resp
            result = fetch_with_retry("https://example.com", source="test")
            assert result is not None
            assert result.status_code == 200

    def test_fetch_429_with_retry(self) -> None:
        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_429.headers = {"Retry-After": "0.1"}
        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.raise_for_status = MagicMock()
        with patch("tools.knowledge_updater.requests") as mock_req, patch("time.sleep", return_value=None):
            mock_req.get.side_effect = [mock_429, mock_200]
            result = fetch_with_retry("https://example.com", source="test", base_delay=0.01)
            assert result is not None
            assert result.status_code == 200
            assert mock_req.get.call_count == 2

    def test_fetch_all_retries_exhausted(self) -> None:
        mock_500 = MagicMock()
        mock_500.status_code = 500
        with patch("tools.knowledge_updater.requests") as mock_req, patch("time.sleep", return_value=None):
            mock_req.get.return_value = mock_500
            with pytest.raises(CrawlError) as exc_info:
                fetch_with_retry("https://example.com", source="test", max_retries=2, base_delay=0.01)
            assert "503" in str(exc_info.value) or "500" in str(exc_info.value) or "test" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Append-to-Brain Tests
# ---------------------------------------------------------------------------


class TestAppendToBrain:
    def test_append_no_duplicates(self, sample_config: AppConfig, tmp_path: Path) -> None:
        brain = tmp_path / "SECOND-KNOWLEDGE-BRAIN.md"
        brain.write_text("## 7. Knowledge Update Log\n", encoding="utf-8")
        sample_config._brain_path_override = brain  # type: ignore[attr-defined]
        sample_config.dry_run = True
        entries = [
            {
                "title": "T1",
                "authors": ["A"],
                "year": 2026,
                "venue": "V",
                "doi_or_url": "https://example.com/unique1",
                "abstract": "ab",
                "published_date": datetime.datetime.now(),
                "citation_count": 5,
                "source": "test",
            }
        ]
        n = append_to_brain(entries, sample_config)
        assert n == 1

    def test_append_skips_duplicate(self, sample_config: AppConfig, tmp_path: Path) -> None:
        brain = tmp_path / "SECOND-KNOWLEDGE-BRAIN.md"
        brain.write_text(
            "## 7. Knowledge Update Log\n\n### 2026-01-01 [test] Dup Title\n- **DOI/URL:** https://example.com/dup1\n",
            encoding="utf-8",
        )
        sample_config.dry_run = True
        entries = [
            {
                "title": "T1",
                "authors": ["A"],
                "year": 2026,
                "venue": "V",
                "doi_or_url": "https://example.com/dup1",
                "abstract": "ab",
                "published_date": datetime.datetime.now(),
                "citation_count": 0,
                "source": "test",
            }
        ]
        n = append_to_brain(entries, sample_config, brain_path=brain)
        assert n == 0

    def test_append_brain_not_found(self, sample_config: AppConfig, tmp_path: Path) -> None:
        sample_config.dry_run = False
        nonexistent = tmp_path / "nonexistent_brain.md"
        entries = [
            {
                "title": "T",
                "doi_or_url": "https://x.com",
                "authors": ["A"],
                "year": 2026,
                "venue": "V",
                "abstract": "a",
                "published_date": datetime.datetime.now(),
                "citation_count": 0,
                "source": "t",
            }
        ]
        with pytest.raises(BrainNotFoundError):
            append_to_brain(entries, sample_config, brain_path=nonexistent)


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_keywords_list(self) -> None:
        entry = {
            "title": "water puppetry design",
            "abstract": "stage lighting",
            "published_date": datetime.datetime.now(),
            "citation_count": 0,
        }
        s = score_entry(entry, [], datetime.datetime.now())
        assert 0.0 <= s <= 10.0

    def test_empty_entry(self) -> None:
        entry: dict[str, Any] = {
            "title": "",
            "abstract": "",
            "published_date": None,
            "citation_count": None,
        }
        s = score_entry(entry, ["test"], datetime.datetime.now())
        assert s >= 0.0

    def test_negative_citation(self) -> None:
        entry = {
            "title": "t",
            "abstract": "t",
            "published_date": datetime.datetime.now(),
            "citation_count": -5,
        }
        s = score_entry(entry, ["t"], datetime.datetime.now())
        assert 0.0 <= s <= 10.0, f"Score {s} out of range: negative citation should be clamped to 0"

    def test_high_citation_ceiling(self) -> None:
        entry = {
            "title": "water puppetry stage design DMX",
            "abstract": "lighting traditional puppet performance",
            "published_date": datetime.datetime.now(),
            "citation_count": 100000,
        }
        s = score_entry(entry, ["water", "puppetry", "stage", "design"], datetime.datetime.now())
        assert s <= 10.0

    def test_fetch_arxiv_no_categories(self) -> None:
        cfg = load_config()
        cfg.arxiv_categories = []
        results = fetch_arxiv(cfg)
        assert isinstance(results, list)

    def test_fetch_rss_no_feeds(self) -> None:
        cfg = load_config()
        cfg.rss_feeds = []
        results = fetch_rss(cfg)
        assert isinstance(results, list)
        assert len(results) == 0
