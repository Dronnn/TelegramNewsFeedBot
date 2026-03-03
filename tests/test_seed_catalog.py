"""Tests for scripts/seed_catalog.py — catalog JSON loading."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from bot.db.models import CatalogEntry

# Allow importing the script even though it lives outside the bot package.
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.seed_catalog import load_entries


SAMPLE_CATALOG = {
    "topics": [
        {
            "id": "tech",
            "name": "Технологии",
            "emoji": "💻",
            "channels": [
                {"username": "chan_a", "title": "Channel A"},
                {"username": "chan_b", "title": "Channel B", "tags": "ai,ml", "language": "en"},
            ],
        },
        {
            "id": "news",
            "name": "Новости",
            "emoji": "📰",
            "channels": [
                {"username": "chan_c", "title": "Channel C"},
            ],
        },
    ],
}


def _write_catalog(data: dict) -> Path:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(data, tmp, ensure_ascii=False)
    tmp.close()
    return Path(tmp.name)


def test_load_entries_count():
    path = _write_catalog(SAMPLE_CATALOG)
    entries = load_entries(path)
    assert len(entries) == 3
    path.unlink()


def test_load_entries_fields():
    path = _write_catalog(SAMPLE_CATALOG)
    entries = load_entries(path)

    tech_entries = [e for e in entries if e.category == "tech"]
    assert len(tech_entries) == 2
    assert tech_entries[0].channel_username == "chan_a"
    assert tech_entries[0].title == "Channel A"
    assert tech_entries[0].tags is None
    assert tech_entries[0].language == "ru"

    assert tech_entries[1].tags == "ai,ml"
    assert tech_entries[1].language == "en"

    news_entries = [e for e in entries if e.category == "news"]
    assert len(news_entries) == 1
    assert news_entries[0].channel_username == "chan_c"

    path.unlink()


def test_load_entries_returns_catalog_entry_instances():
    path = _write_catalog(SAMPLE_CATALOG)
    entries = load_entries(path)
    for entry in entries:
        assert isinstance(entry, CatalogEntry)
    path.unlink()


def test_load_entries_real_catalog():
    """Verify the actual project catalog file parses without errors."""
    catalog_path = PROJECT_ROOT / "data" / "channel_catalog.json"
    if not catalog_path.exists():
        pytest.skip("catalog file not found")
    entries = load_entries(catalog_path)
    assert len(entries) > 0
    categories = {e.category for e in entries}
    assert len(categories) >= 2
