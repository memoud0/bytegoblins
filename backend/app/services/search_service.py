from __future__ import annotations

from typing import Any, List, Tuple

from app.firebase_client import get_firestore_client, server_timestamp
from app.models import Track
from app.services.track_service import TrackService


class SearchService:
    def __init__(self) -> None:
        self.db = get_firestore_client()
        self.track_service = TrackService()

    def search_songs(
        self,
        query: str,
        username: str | None = None,
        limit: int = 20,
    ) -> tuple[list[Track], str | None]:
        """
        Search songs by name/artist/genre.

        - Uses Firestore prefix search on track_name_lowercase.
        - Ranks results locally.
        - If username is provided, logs a search_event and returns its ID.

        Returns:
            (tracks, search_event_id)
        """
        query_raw = (query or "").strip()
        query_norm = query_raw.lower()
        if not query_norm:
            return [], None

        # pull a bigger pool so scoring has room to work
        pool_size = max(limit * 3, 40)
        candidate_tracks = self.track_service.search_tracks(query_norm, limit=pool_size)

        scored: list[tuple[float, Track]] = []
        for t in candidate_tracks:
            score = self._score_track(t, query_norm)
            scored.append((score, t))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_tracks = [t for score, t in scored[:limit]]

        search_event_id: str | None = None
        if username:
            search_event_id = self._log_search_event(
                username=username,
                query_raw=query_raw,
                query_norm=query_norm,
                tracks=top_tracks,
            )

        return top_tracks, search_event_id

    # ---------- helpers ----------

    def _score_track(self, track: Track, query_norm: str) -> float:
        """
        Very simple scoring:
        - strong weight if track name starts with query
        - medium weight if track name contains query
        - bonus if any artist name contains query
        - bonus if genre contains query
        - small popularity bonus
        """
        name = (track.track_name_lowercase or track.track_name or "").lower()
        artists = [a.lower() for a in (track.artists or [])]
        genre = (track.track_genre or "").lower()
        genre_group = (track.track_genre_group or "").lower()
        popularity = float(track.popularity_norm or 0.0)

        score = 0.0

        if name.startswith(query_norm):
            score += 5.0
        elif query_norm in name:
            score += 3.0

        if any(query_norm in a for a in artists):
            score += 2.0

        if query_norm in genre:
            score += 1.0
        if query_norm in genre_group:
            score += 0.5

        score += popularity * 2.0  # small push for popular tracks

        return score

    def _log_search_event(
        self,
        username: str,
        query_raw: str,
        query_norm: str,
        tracks: list[Track],
    ) -> str:
        user_id = username.lower()
        user_ref = self.db.collection("users").document(user_id)
        events_ref = user_ref.collection("search_events").document()
        event_id = events_ref.id

        now = server_timestamp()
        events_ref.set(
            {
                "search_event_id": event_id,
                "query": query_raw,
                "query_norm": query_norm,
                "created_at": now,
                "results_track_ids": [t.track_id for t in tracks],
            }
        )
        return event_id
