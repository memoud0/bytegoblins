from __future__ import annotations

from typing import Iterable

from app.models import Track, UserProfile
from app.models.track import NUMERIC_FEATURES
from app.services.track_service import TrackService
from app.utils.scoring import compute_feature_similarity, genre_rank_score


class RecommendationService:
    def __init__(self) -> None:
        self.track_service = TrackService()

    def build_feature_preferences(self, profile: UserProfile) -> dict[str, float]:
        preferences: dict[str, float] = {}
        for feature in NUMERIC_FEATURES:
            like_sum = profile.feature_sums_liked.get(feature, 0.0)
            dislike_sum = profile.feature_sums_disliked.get(feature, 0.0)
            like_avg = like_sum / profile.likes_count if profile.likes_count else None
            dislike_avg = dislike_sum / profile.dislikes_count if profile.dislikes_count else None

            if like_avg is None and dislike_avg is None:
                preferences[feature] = 0.5
            elif like_avg is not None and dislike_avg is not None:
                preferences[feature] = like_avg - 0.5 * dislike_avg
            else:
                preferences[feature] = like_avg if like_avg is not None else 0.5
        return preferences

    def build_refined_track_ids(
        self,
        top_genres: list[str],
        preferences: dict[str, float],
        exclude_track_ids: set[str],
        limit: int = 100,
    ) -> list[str]:
        candidates = self.track_service.get_candidate_tracks(
            top_genres=top_genres, exclude_track_ids=exclude_track_ids, limit=limit * 3
        )
        scored: list[tuple[float, Track]] = []
        for track in candidates:
            genre = track.track_genre or track.track_genre_group
            genre_score = genre_rank_score(genre, top_genres)
            feature_payload = track.to_dict()
            sim = compute_feature_similarity(feature_payload, preferences)
            final_score = 0.6 * genre_score + 0.4 * sim
            scored.append((final_score, track))

        scored.sort(key=lambda item: item[0], reverse=True)
        selected = [track.track_id for item, track in scored[:limit]]
        return selected

    def compute_library_based_top_genres(self, tracks: Iterable[Track], limit: int = 3) -> list[str]:
        genre_counts: dict[str, int] = {}
        for track in tracks:
            genre = track.track_genre or track.track_genre_group
            if not genre:
                continue
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
        sorted_genres = sorted(genre_counts.items(), key=lambda item: item[1], reverse=True)
        return [genre for genre, _ in sorted_genres[:limit]]
