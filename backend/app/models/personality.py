from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from .track import Track


@dataclass(slots=True)
class PersonalityMetrics:
    energy: float = 0.0
    mood: float = 0.0
    diversity: float = 0.0
    mainstream: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(slots=True)
class PersonalityResult:
    archetype_id: str
    title: str
    one_liner: str
    summary: str
    metrics: PersonalityMetrics = field(default_factory=PersonalityMetrics)
    top_genres: list[str] = field(default_factory=list)
    representative_tracks: list[Track] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "archetypeId": self.archetype_id,
            "title": self.title,
            "oneLiner": self.one_liner,
            "summary": self.summary,
            "metrics": self.metrics.to_dict(),
            "topGenres": list(self.top_genres),
            "representativeTracks": [track.to_dict() for track in self.representative_tracks],
        }
