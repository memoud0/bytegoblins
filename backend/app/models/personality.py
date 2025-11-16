from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping, List


@dataclass(slots=True)
class PersonalityMetrics:
    avg_energy: float
    avg_valence: float
    avg_popularity_norm: float
    genre_diversity: float  # 0–1
    top_genres: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["top_genres"] = list(self.top_genres)
        return payload

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "PersonalityMetrics":
        payload = dict(data)
        payload.setdefault("top_genres", [])
        return cls(**payload)


@dataclass(slots=True)
class PersonalityResult:
    username: str
    archetype_id: str
    title: str
    short_description: str
    long_description: str
    metrics: PersonalityMetrics
    representative_track_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "username": self.username,
            "archetypeId": self.archetype_id,
            "title": self.title,
            "shortDescription": self.short_description,
            "longDescription": self.long_description,
            "metrics": self.metrics.to_dict(),
            "representativeTrackIds": list(self.representative_track_ids),
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "PersonalityResult":
        metrics_data = data.get("metrics") or {}
        metrics = PersonalityMetrics.from_mapping(metrics_data)
        return cls(
            username=data.get("username", ""),
            archetype_id=data.get("archetypeId", ""),
            title=data.get("title", ""),
            short_description=data.get("shortDescription", ""),
            long_description=data.get("longDescription", ""),
            metrics=metrics,
            representative_track_ids=list(data.get("representativeTrackIds") or []),
        )
