from __future__ import annotations

import math
from typing import Iterable, Mapping

from app.models import NUMERIC_FEATURES


def genre_rank_score(genre: str | None, top_genres: list[str]) -> float:
    if not genre:
        return 0.0
    if not top_genres:
        return 0.3

    if genre == top_genres[0]:
        return 1.0
    if len(top_genres) > 1 and genre == top_genres[1]:
        return 0.8
    if len(top_genres) > 2 and genre == top_genres[2]:
        return 0.6
    return 0.3


def compute_feature_similarity(track_payload: Mapping[str, float], preferences: Mapping[str, float]) -> float:
    total = 0.0
    used = 0
    for feature in NUMERIC_FEATURES:
        pref_value = preferences.get(feature)
        track_value = track_payload.get(feature)
        if pref_value is None or track_value is None:
            continue
        diff = float(track_value) - float(pref_value)
        total += diff * diff
        used += 1

    if used == 0:
        return 0.0

    distance = math.sqrt(total)
    return 1.0 / (1.0 + distance)


def score_search_result(track_payload: Mapping[str, object], query_norm: str, top_genres: Iterable[str]) -> float:
    track_name = str(track_payload.get("track_name") or "")
    track_name_lower = track_name.lower()
    artists = [str(artist).lower() for artist in track_payload.get("artists") or []]
    genre = (track_payload.get("track_genre") or "").lower()
    top_genres_lower = [genre.lower() for genre in top_genres]

    score = 0.0
    if track_name_lower.startswith(query_norm):
        score += 2.0
    elif query_norm in track_name_lower:
        score += 1.0

    if any(query_norm in artist for artist in artists):
        score += 1.0

    if genre and genre in top_genres_lower:
        score += 0.5

    return score
