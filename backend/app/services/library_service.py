from __future__ import annotations

from firebase_admin import firestore

from app.firebase_client import get_firestore_client, server_timestamp
from app.models import Track
from app.services.track_service import TrackService


class LibraryService:
    def __init__(self) -> None:
        self.db = get_firestore_client()
        self.track_service = TrackService()

    # ---------------------------------------------
    # GET LIBRARY
    # ---------------------------------------------
    def get_library_tracks(self, username: str) -> list[Track]:
        user_ref = self.db.collection("users").document(username)
        library_ref = (
            user_ref.collection("library")
            .order_by("added_at", direction=firestore.Query.DESCENDING)
        )

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

    # -------------------------------------------------
    # ADD TO LIBRARY (HYBRID: Firestore + Spotify)
    # -------------------------------------------------
    def add_track_object_to_library(self, username: str, track_payload: dict) -> Track:
        """
        New hybrid method.
        Used when the frontend sends the track object from /songs/search.

        track_payload must include:
        {
            "trackId": "...",
            "trackName": "...",
            "artists": [...],
            "albumName": "...",
            "imageUrl": "...",
            "popularity": ...,
            "popularityNorm": ...,
            "genre": ...,
            "genreGroup": ...,
            "source": "firestore" | "spotify"
        }
        """

        track_id = track_payload["trackId"]
        source = track_payload.get("source", "manual")

        # -------------------------------------------------
        # 1. If Spotify result: ensure Firestore has this track
        # -------------------------------------------------
        track = self.track_service.get_track(track_id)

        if not track and source == "spotify":
            # Upsert Firestore track document for later personality & match calculations
            track_doc = {
                "track_id": track_id,
                "track_name": track_payload.get("trackName"),
                "track_name_lowercase": (track_payload.get("trackName") or "").lower(),
                "artists": track_payload.get("artists") or [],
                "album_name": track_payload.get("albumName"),
                "image_url": track_payload.get("imageUrl"),
                "popularity": track_payload.get("popularity"),
                "popularity_norm": track_payload.get("popularityNorm"),
                "track_genre": track_payload.get("genre"),
                "track_genre_group": track_payload.get("genreGroup"),
                "source": "spotify",
            }

            track_ref = self.db.collection("tracks").document(track_id)
            track_ref.set(track_doc, merge=True)

            # re-fetch Track model from DB so return type is consistent
            track = self.track_service.get_track(track_id)

        # Still not found?
        if not track:
            raise ValueError(
                f"Track {track_id} not found in Firestore or could not be created."
            )

        # -------------------------------------------------
        # 2. Add entry under users/{username}/library/{trackId}
        # -------------------------------------------------
        user_ref = self.db.collection("users").document(username)
        library_ref = user_ref.collection("library").document(track_id)
        now = server_timestamp()

        library_ref.set(
            {"track_id": track_id, "added_at": now, "source": source},
            merge=True,
        )

        return track

    # -----------------------------------------------------------
    # LEGACY METHOD (still supported): add by ID only
    # -----------------------------------------------------------
    def add_to_library(
        self,
        username: str,
        track_id: str,
        source: str = "manual",
        search_event_id: str | None = None,
    ) -> Track:
        """
        Existing older method: add to library by track_id.
        Only works for Firestore-existing tracks.
        """
        track = self.track_service.get_track(track_id)
        if not track:
            raise ValueError("Track not found.")

        user_ref = self.db.collection("users").document(username)
        library_ref = user_ref.collection("library").document(track_id)

        now = server_timestamp()
        library_ref.set(
            {"track_id": track_id, "added_at": now, "source": source},
            merge=True,
        )

        if search_event_id:
            user_ref.collection("search_events").document(search_event_id).set(
                {"selected_track_id": track_id, "updated_at": now}, merge=True
            )

        return track
