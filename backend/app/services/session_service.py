from __future__ import annotations

import uuid
from typing import Any

from app.firebase_client import get_firestore_client, server_timestamp
from app.models import MatchSession, Track
from app.services.library_service import LibraryService
from app.services.recommendation_service import RecommendationService
from app.services.track_service import TrackService
from app.services.user_service import UserService


class SessionService:
    def __init__(self) -> None:
        self.db = get_firestore_client()
        self.user_service = UserService()
        self.track_service = TrackService()
        self.library_service = LibraryService()
        self.recommendation_service = RecommendationService()

    def create_session(self, username: str, seed_limit: int = 12) -> dict[str, Any]:
        """
        Create a new match session with seed tracks.

        Returns a JSON-safe DTO:
        {
          "sessionId": string,
          "username": string,
          "seedTrackIds": string[],
          "seedCount": number
        }
        """
        username = username.lower()

        # Make sure the user profile exists
        self.user_service.ensure_user(username)

        user_ref = self.db.collection("users").document(username)

        # Exclude tracks already in user's library from seeds
        library_tracks = self.library_service.get_library_tracks(username)
        exclude_track_ids = {t.track_id for t in library_tracks}

        seed_tracks = self.track_service.get_seed_tracks(
            exclude_track_ids=exclude_track_ids,
            limit=seed_limit,
        )
        seed_ids = [t.track_id for t in seed_tracks]

        session_ref = user_ref.collection("sessions").document()  # auto ID
        session_id = session_ref.id

        now = server_timestamp()
        session_data = {
            "session_id": session_id,
            "username": username,
            "created_at": now,
            "updated_at": now,
            "is_active": True,
            "phase": "seed",          # matches your later logic (session.phase)
            "status": "active",       # optional, used in get_next_track completion
            "seed_track_ids": seed_ids,
            "refined_track_ids": [],
            "current_index": 0,
            "seed_swipes_completed": 0,
        }
        session_ref.set(session_data)

        # Return JSON-safe data (no Firestore sentinel objects)
        return {
            "sessionId": session_id,
            "username": username,
            "seedTrackIds": seed_ids,
            "seedCount": len(seed_ids),
            "phase": "seed",
        }

    def get_session(self, username: str, session_id: str) -> MatchSession:
        snapshot = self._session_ref(username, session_id).get()
        if not snapshot.exists:
            raise ValueError("Session not found.")
        data = snapshot.to_dict() or {}
        data["session_id"] = session_id
        data["username"] = username
        return MatchSession.from_mapping(data)

    def register_swipe(
        self,
        username: str,
        session: MatchSession,
        track: Track,
        liked: bool,
    ) -> MatchSession:
        # Record swipe on user aggregates / swipes collection
        self.user_service.record_swipe(
            username=username,
            session_id=session.session_id,
            track=track,
            liked=liked,
            phase=session.phase,
        )

        # Add to library if liked
        if liked:
            self.library_service.add_to_library(
                username=username,
                track_id=track.track_id,
                source="swipe",
            )

        # Update session fields
        if session.phase == "seed":
            session.seed_swipes_completed += 1

        session.updated_at = server_timestamp()
        self._save_session(username, session)

        # Transition to refined if needed
        if self._should_transition_to_refined(session):
            session = self._transition_to_refined(username, session)

        return session

    def get_next_track(self, username: str, session: MatchSession) -> tuple[Track | None, MatchSession]:
        """
        Returns (track, session).

        - If there is a next track, track is a Track instance.
        - If session is exhausted, track is None and session.status is set to "completed".
        """
        # Decide which universe of tracks we’re pulling from
        universe = session.seed_track_ids if session.phase == "seed" else session.refined_track_ids

        library_ids = set(self.user_service.get_library_track_ids(username))
        swiped_ids = self.user_service.get_swiped_track_ids(username)
        skip_ids = library_ids | swiped_ids

        index = session.current_index
        while index < len(universe):
            track_id = universe[index]
            index += 1

            if track_id in skip_ids:
                continue

            track = self.track_service.get_track(track_id)
            if not track:
                continue

            session.current_index = index
            session.updated_at = server_timestamp()
            self._save_session(username, session)
            return track, session

        # If we’re out of seeds, try to transition to refined
        if session.phase == "seed":
            session = self._transition_to_refined(username, session)
            return self.get_next_track(username, session)

        # If we’re in refined and still out of tracks, mark completed
        session.status = "completed"
        session.updated_at = server_timestamp()
        self._save_session(username, session)
        return None, session

    def _should_transition_to_refined(self, session: MatchSession) -> bool:
        return (
            session.phase == "seed"
            and bool(session.seed_track_ids)
            and session.seed_swipes_completed >= len(session.seed_track_ids)
        )

    def _transition_to_refined(self, username: str, session: MatchSession) -> MatchSession:
        # Get user profile; ensure it exists
        profile = self.user_service.get_user(username) or self.user_service.ensure_user(username)

        # Get top genres from profile
        top_genres = self.user_service.get_top_genres(profile)

        # Fallback to library-based genres if no profile genres yet
        if not any(top_genres):
            library_tracks = self.library_service.get_library_tracks(username)
            top_genres = self.recommendation_service.compute_library_based_top_genres(library_tracks)

        # Final fallback default genres
        if not top_genres:
            top_genres = ["pop", "rock", "hip hop"]

        # Build feature preferences
        preferences = self.recommendation_service.build_feature_preferences(profile)

        library_ids = set(self.user_service.get_library_track_ids(username))
        swiped_ids = self.user_service.get_swiped_track_ids(username)
        exclude_ids = library_ids | swiped_ids

        # Get refined candidate track IDs
        refined_ids = self.recommendation_service.build_refined_track_ids(
            top_genres=top_genres,
            preferences=preferences,
            exclude_track_ids=exclude_ids,
        )

        session.refined_track_ids = refined_ids
        session.phase = "refined"
        session.current_index = 0
        session.updated_at = server_timestamp()
        self._save_session(username, session)
        return session

    def _session_ref(self, username: str, session_id: str):
        return (
            self.db.collection("users")
            .document(username)
            .collection("sessions")
            .document(session_id)
        )

    def _save_session(self, username: str, session: MatchSession) -> None:
        payload = session.to_dict()
        # Always update updated_at on save
        payload["updated_at"] = server_timestamp()
        self._session_ref(username, session.session_id).set(payload, merge=True)
