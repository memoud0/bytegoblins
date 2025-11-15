from __future__ import annotations

from app.firebase_client import get_firestore_client, server_timestamp
from app.models import Track
from app.services.track_service import TrackService
from app.services.user_service import UserService
from app.utils.scoring import score_search_result
from app.utils.text import normalize_query


class SearchService:
    def __init__(self) -> None:
        self.db = get_firestore_client()
        self.track_service = TrackService()
        self.user_service = UserService()

    def search(self, username: str, query: str, limit: int = 20) -> tuple[list[Track], str]:
        normalized = normalize_query(query)
        if not normalized:
            raise ValueError("Query is empty.")

        event_id = self._record_search_event(username, query, normalized)
        profile = self.user_service.ensure_user(username)
        top_genres = self.user_service.get_top_genres(profile)

        tracks = self.track_service.search_tracks(normalized, limit=limit)
        scored = [
            (score_search_result(track.to_dict(), normalized, top_genres), track)
            for track in tracks
        ]
        scored.sort(key=lambda item: item[0], reverse=True)
        ordered_tracks = [track for _, track in scored]
        return ordered_tracks, event_id

    def _record_search_event(self, username: str, query: str, normalized_query: str) -> str:
        user_ref = self.db.collection("users").document(username)
        now = server_timestamp()
        event_ref = user_ref.collection("search_events").document()
        event_ref.set(
            {
                "query": query,
                "normalized_query": normalized_query,
                "created_at": now,
            }
        )
        return event_ref.id
