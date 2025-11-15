from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Mapping


@dataclass(slots=True)
class MatchSession:
    session_id: str
    username: str
    created_at: Any | None = None
    updated_at: Any | None = None

    # Session state
    phase: str = "seed"          # "seed" | "refined"
    status: str = "active"       # "active" | "completed"

    # Seed phase
    seed_track_ids: list[str] = field(default_factory=list)
    seed_swipes_completed: int = 0

    # Refined phase
    refined_track_ids: list[str] = field(default_factory=list)

    # Index pointer
    current_index: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "username": self.username,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "phase": self.phase,
            "status": self.status,
            "seed_track_ids": list(self.seed_track_ids),
            "seed_swipes_completed": self.seed_swipes_completed,
            "refined_track_ids": list(self.refined_track_ids),
            "current_index": self.current_index,
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "MatchSession":
        """Safely load from Firestore and ignore extra unknown fields."""
        payload = dict(data)

        allowed = {f.name for f in fields(cls)}

        # Convert Firestore dict into valid dataclass kwargs
        filtered = {k: v for k, v in payload.items() if k in allowed}

        # Missing required fields?
        if "session_id" not in filtered or "username" not in filtered:
            raise ValueError("Invalid session document: missing id or username")

        return cls(**filtered)
