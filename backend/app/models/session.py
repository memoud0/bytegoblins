from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Mapping


@dataclass(slots=True)
class MatchSession:
    session_id: str
    username: str
    status: str
    phase: str
    seed_track_ids: list[str] = field(default_factory=list)
    refined_track_ids: list[str] = field(default_factory=list)
    current_index: int = 0
    seed_swipes_completed: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["seed_track_ids"] = list(self.seed_track_ids)
        payload["refined_track_ids"] = list(self.refined_track_ids)
        return payload

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "MatchSession":
        payload = dict(data)
        payload.setdefault("seed_track_ids", [])
        payload.setdefault("refined_track_ids", [])
        payload.setdefault("status", "active")
        payload.setdefault("phase", "seed")
        payload.setdefault("current_index", 0)
        payload.setdefault("seed_swipes_completed", 0)
        return cls(**payload)
