from __future__ import annotations

import re

WHITESPACE_RE = re.compile(r"\s+")


def normalize_query(value: str) -> str:
    """Normalize search queries for consistent Firestore comparisons."""
    lowered = value.strip().lower()
    lowered = WHITESPACE_RE.sub(" ", lowered)
    return lowered
