from __future__ import annotations

import uuid

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

    def create_session(self, username: str, seed_limit: int = 12) -> tuple[MatchSession, list[Track]]:
        profile = self.user_service.ensure_user(username)
        library_ids = set(self.user_service.get_library_track_ids(username))
        swiped_ids = self.user_service.get_swiped_track_ids(username)
        exclude_ids = library_ids | swiped_ids

        seed_tracks = self.track_service.get_seed_tracks(exclude_ids, limit=seed_limit)
        if not seed_tracks:
            raise ValueError("No seed tracks are available. Please try again later.")

        session_id = uuid.uuid4().hex
        now = server_timestamp()
        payload = {
            "session_id": session_id,
            "username": username,
            "status": "active",
            "phase": "seed",
            "seed_track_ids": [track.track_id for track in seed_tracks],
            "refined_track_ids": [],
            "current_index": 0,
            "seed_swipes_completed": 0,
            "created_at": now,
            "updated_at": now,
        }

        session_ref = self._session_ref(username, session_id)
        session_ref.set(payload)
        session = MatchSession.from_mapping(payload)
        return session, seed_tracks

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
        self.user_service.record_swipe(username, session.session_id, track, liked, session.phase)
        if liked:
            self.library_service.add_to_library(username, track.track_id, source="swipe")

        if session.phase == "seed":
            session.seed_swipes_completed += 1

        session.updated_at = server_timestamp()
        self._save_session(username, session)

        if self._should_transition_to_refined(session):
            session = self._transition_to_refined(username, session)
        return session

    def get_next_track(self, username: str, session: MatchSession) -> tuple[Track | None, MatchSession]:
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

        if session.phase == "seed":
            session = self._transition_to_refined(username, session)
            return self.get_next_track(username, session)

        session.status = "completed"
        session.updated_at = server_timestamp()
        self._save_session(username, session)
        return None, session

    def _should_transition_to_refined(self, session: MatchSession) -> bool:
        return (
            session.phase == "seed"
            and session.seed_track_ids
            and session.seed_swipes_completed >= len(session.seed_track_ids)
        )

    def _transition_to_refined(self, username: str, session: MatchSession) -> MatchSession:
        profile = self.user_service.get_user(username) or self.user_service.ensure_user(username)
        top_genres = self.user_service.get_top_genres(profile)
        if not any(top_genres):
            library_tracks = self.library_service.get_library_tracks(username)
            top_genres = self.recommendation_service.compute_library_based_top_genres(library_tracks)
        if not top_genres:
            top_genres = ["pop", "rock", "hip hop"]

        preferences = self.recommendation_service.build_feature_preferences(profile)
        library_ids = set(self.user_service.get_library_track_ids(username))
        swiped_ids = self.user_service.get_swiped_track_ids(username)
        exclude_ids = library_ids | swiped_ids

        refined_ids = self.recommendation_service.build_refined_track_ids(top_genres, preferences, exclude_ids)
        session.refined_track_ids = refined_ids
        session.phase = "refined"
        session.current_index = 0
        session.updated_at = server_timestamp()
        self._save_session(username, session)
        return session

    def _session_ref(self, username: str, session_id: str):
        return self.db.collection("users").document(username).collection("sessions").document(session_id)

    def _save_session(self, username: str, session: MatchSession) -> None:
        payload = session.to_dict()
        payload["updated_at"] = server_timestamp()
        self._session_ref(username, session.session_id).set(payload, merge=True)
