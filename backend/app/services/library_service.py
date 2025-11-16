from __future__ import annotations

from firebase_admin import firestore

from app.firebase_client import get_firestore_client, server_timestamp
from app.models import Track
from app.services.track_service import TrackService


class LibraryService:
    def __init__(self) -> None:
        self.db = get_firestore_client()
        self.track_service = TrackService()

    def get_library_tracks(self, username: str) -> list[Track]:
        user_ref = self.db.collection("users").document(username)
        library_ref = user_ref.collection("library").order_by("added_at", direction=firestore.Query.DESCENDING)
        entries = list(library_ref.stream())
        track_ids = [doc.id for doc in entries]
        tracks = self.track_service.get_tracks_by_ids(track_ids)
        track_map = {track.track_id: track for track in tracks}
        ordered_tracks: list[Track] = []
        for doc in entries:
            track_id = doc.id
            track = track_map.get(track_id)
            if track:
                ordered_tracks.append(track)
        return ordered_tracks

    def add_to_library(
        self,
        username: str,
        track_id: str,
        source: str = "manual",
        search_event_id: str | None = None,
    ) -> Track:
        track = self.track_service.get_track(track_id)
        if not track:
            raise ValueError("Track not found.")

        user_ref = self.db.collection("users").document(username)
        library_ref = user_ref.collection("library").document(track_id)
        now = server_timestamp()
        library_ref.set({"track_id": track_id, "added_at": now, "source": source}, merge=True)

        if search_event_id:
            user_ref.collection("search_events").document(search_event_id).set(
                {"selected_track_id": track_id, "updated_at": now}, merge=True
            )
        return track
    
    def remove_from_library(self, username: str, track_id: str) -> None:
        """
        Delete a track from the user's library.

        Raises:
            ValueError if the track is not in the library.
        """
        username_norm = username.lower()
        user_ref = self.db.collection("users").document(username_norm)
        doc_ref = user_ref.collection("library").document(track_id)

        snap = doc_ref.get()
        if not snap.exists:
            raise ValueError("Track not found in library.")

        doc_ref.delete()
