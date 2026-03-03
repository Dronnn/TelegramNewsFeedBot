from __future__ import annotations

import json


def load_topics(catalog_path: str) -> list[dict]:
    """Read topics from the channel catalog JSON file."""
    with open(catalog_path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("topics", [])
