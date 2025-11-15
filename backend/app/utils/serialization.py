from __future__ import annotations

from datetime import datetime


def to_iso(dt: datetime | None) -> str | None:
    if not dt:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)
