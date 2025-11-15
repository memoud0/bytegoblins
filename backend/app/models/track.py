from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Mapping


NUMERIC_FEATURES = [
    "danceability",
    "energy",
    "acousticness",
    "valence",
    "tempo_norm",
    "instrumentalness",
    "liveness",
    "speechiness",
]


@dataclass(slots=True)
class Track:
    track_id: str
    track_name: str
    artists: list[str] = field(default_factory=list)
    album_name: str | None = None
    popularity: int | None = None
    popularity_norm: float | None = None
    duration_ms: int | None = None
    explicit: bool | None = None
    danceability: float | None = None
    energy: float | None = None
    key: int | None = None
    loudness: float | None = None
    mode: int | None = None
    speechiness: float | None = None
    acousticness: float | None = None
    instrumentalness: float | None = None
    liveness: float | None = None
    valence: float | None = None
    tempo: float | None = None
    tempo_norm: float | None = None
    time_signature: int | None = None
    track_genre: str | None = None
    track_genre_group: str | None = None
    track_name_lowercase: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["artists"] = list(self.artists)
        return payload

    @classmethod
    def from_mapping(cls, track_id: str, data: Mapping[str, Any]) -> "Track":
        payload = dict(data)
        payload["track_id"] = track_id
        artists = payload.get("artists") or []
        payload["artists"] = list(artists)
        return cls(**payload)
