from __future__ import annotations

from dataclasses import dataclass, field, asdict, fields
from datetime import datetime
from typing import Any, Mapping

from .track import NUMERIC_FEATURES


def _default_feature_map() -> dict[str, float]:
    return {feature: 0.0 for feature in NUMERIC_FEATURES}


@dataclass(slots=True)
class UserProfile:
    username: str
    created_at: datetime | None = None
    last_active_at: datetime | None = None
    likes_count: int = 0
    dislikes_count: int = 0
    liked_genres: dict[str, int] = field(default_factory=dict)
    disliked_genres: dict[str, int] = field(default_factory=dict)
    feature_sums_liked: dict[str, float] = field(default_factory=_default_feature_map)
    feature_sums_disliked: dict[str, float] = field(default_factory=_default_feature_map)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["liked_genres"] = dict(self.liked_genres)
        payload["disliked_genres"] = dict(self.disliked_genres)
        payload["feature_sums_liked"] = dict(self.feature_sums_liked)
        payload["feature_sums_disliked"] = dict(self.feature_sums_disliked)
        return payload

    @classmethod
    def from_mapping(cls, username: str, data: Mapping[str, Any]) -> "UserProfile":
        payload = dict(data)
        payload["username"] = username

        # Backwards compatibility: map last_login_at -> last_active_at if present
        if "last_login_at" in payload and "last_active_at" not in payload:
            payload["last_active_at"] = payload["last_login_at"]

        # Ensure these maps are always present
        payload.setdefault("liked_genres", {})
        payload.setdefault("disliked_genres", {})
        payload.setdefault("feature_sums_liked", _default_feature_map())
        payload.setdefault("feature_sums_disliked", _default_feature_map())

        # Only keep fields that actually exist on the dataclass
        allowed_fields = {f.name for f in fields(cls)}
        filtered = {key: value for key, value in payload.items() if key in allowed_fields}

        return cls(**filtered)
