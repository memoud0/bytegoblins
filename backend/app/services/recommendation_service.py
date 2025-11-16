# app/services/recommendation_service.py
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Set

from app.models.user import UserProfile
from app.models.track import Track, NUMERIC_FEATURES
from app.services.track_service import TrackService


class RecommendationService:
    """
    Builds refined recommendations based on:
    - User genre preferences
    - User feature preferences (energy, valence, etc.)
    - Candidate tracks from TrackService.get_candidate_tracks
    """

    def __init__(self) -> None:
        self.track_service = TrackService()

    # ---------- Genre preference helpers ----------

    def compute_library_based_top_genres(
        self,
        library_tracks: Iterable[Track],
        top_n: int = 5,
    ) -> List[str]:
        """
        Fallback: infer top genres just from the user's library.

        Count track_genre_group first, then track_genre.
        """
        counts: Dict[str, int] = {}
        for track in library_tracks:
            genre = track.track_genre_group or track.track_genre
            if not genre:
                continue
            counts[genre] = counts.get(genre, 0) + 1

        if not counts:
            return []

        sorted_genres = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
        return [g for g, _ in sorted_genres[:top_n]]

    def _build_genre_weight_map(self, top_genres: List[str]) -> Dict[str, float]:
        """
        Turn ordered top_genres into a simple weight map.
        First genre gets highest weight, last gets lowest.

        Example:
          ["pop", "rock", "hip hop"] -> {"pop": 1.0, "rock": 0.66, "hip hop": 0.33}
        """
        if not top_genres:
            return {}

        n = len(top_genres)
        weights: Dict[str, float] = {}
        for i, genre in enumerate(top_genres):
            # higher rank -> higher weight
            rank = n - i
            weights[genre] = rank / n
        return weights

    # ---------- Feature preference ----------

    def build_feature_preferences(self, profile: UserProfile) -> Dict[str, float]:
        """
        Compute a target value for each numeric feature based on the user's
        liked/disliked feature sums.

        Rough idea:
        - liked_mean = feature_sums_liked / likes_count
        - disliked_mean = feature_sums_disliked / dislikes_count
        - preference leans toward liked and away from disliked
        """
        prefs: Dict[str, float] = {}

        likes_n = max(profile.likes_count, 0)
        dislikes_n = max(profile.dislikes_count, 0)

        for feature in NUMERIC_FEATURES:
            liked_sum = profile.feature_sums_liked.get(feature, 0.0)
            disliked_sum = profile.feature_sums_disliked.get(feature, 0.0)

            liked_mean: float | None = None
            disliked_mean: float | None = None

            if likes_n > 0:
                liked_mean = liked_sum / likes_n
            if dislikes_n > 0:
                disliked_mean = disliked_sum / max(dislikes_n, 1)

            if liked_mean is None and disliked_mean is None:
                # No data: neutral preference
                prefs[feature] = 0.5
                continue

            if liked_mean is not None and disliked_mean is None:
                # Only liked data
                prefs[feature] = float(liked_mean)
            elif liked_mean is None and disliked_mean is not None:
                # Only disliked data -> prefer the opposite region
                prefs[feature] = float(1.0 - disliked_mean)
            else:
                # Both liked and disliked: bias toward liked, away from disliked
                # Simple blend: 0.7 * liked + 0.3 * (1 - disliked)
                prefs[feature] = float(0.7 * liked_mean + 0.3 * (1.0 - disliked_mean))

            # Clamp to [0, 1] range
            prefs[feature] = max(0.0, min(1.0, prefs[feature]))

        return prefs

    # ---------- Scoring & refined candidates ----------

    def build_refined_track_ids(
        self,
        top_genres: List[str],
        feature_preferences: Dict[str, float],
        exclude_track_ids: Set[str],
        candidate_limit: int = 300,
        final_limit: int = 200,
    ) -> List[str]:
        """
        Pick refined candidate tracks and score them, returning a sorted list of track_ids.

        - Fetch candidates via TrackService.get_candidate_tracks
        - Score each track using genre + feature similarity + popularity bonus
        - Sort descending and return top N ids
        """
        # Fetch candidate tracks from Firestore
        candidates = self.track_service.get_candidate_tracks(
            top_genres=top_genres,
            exclude_track_ids=exclude_track_ids,
            limit=candidate_limit,
        )

        genre_weights = self._build_genre_weight_map(top_genres)

        scored: List[tuple[float, Track]] = []

        for track in candidates:
            score = self._score_track(
                track=track,
                feature_preferences=feature_preferences,
                genre_weights=genre_weights,
            )
            scored.append((score, track))

        # Sort by score descending
        scored.sort(key=lambda pair: pair[0], reverse=True)

        # Return only the track_ids, limited to final_limit
        return [t.track_id for score, t in scored[:final_limit]]

    def _score_track(
        self,
        track: Track,
        feature_preferences: Dict[str, float],
        genre_weights: Dict[str, float],
    ) -> float:
        """
        Combined score for a track:
        - genre alignment
        - feature similarity
        - small popularity bonus
        """
        # Genre score
        genre_key = track.track_genre_group or track.track_genre or "misc"
        genre_score = genre_weights.get(genre_key, 0.0)

        # Feature similarity: 0–1, based on distance from preferred values
        feat_score = self._feature_similarity(track, feature_preferences)

        # Popularity bonus: normalized popularity if available
        popularity = track.popularity_norm or 0.0

        # Weights are arbitrary but sensible; tweak as needed
        total = 0.45 * genre_score + 0.45 * feat_score + 0.10 * popularity
        return float(total)

    def _feature_similarity(
        self,
        track: Track,
        feature_preferences: Dict[str, float],
    ) -> float:
        """
        Compute how close this track is to the user's preferred feature vector.

        Features are assumed normalized to [0, 1] (tempo_norm, energy, etc.).
        Similarity per feature = 1 - |track_value - pref_value|.
        """
        if not feature_preferences:
            return 0.0

        sim_sum = 0.0
        weight_sum = 0.0

        for feature, pref_val in feature_preferences.items():
            track_val = getattr(track, feature, None)
            if track_val is None:
                continue

            # Basic similarity: closer value -> higher score
            diff = abs(float(track_val) - float(pref_val))
            similarity = max(0.0, 1.0 - diff)  # 1 when identical, 0 when diff >= 1

            weight = 1.0  # Could customize per feature later
            sim_sum += similarity * weight
            weight_sum += weight

        if weight_sum == 0.0:
            return 0.0

        return sim_sum / weight_sum
