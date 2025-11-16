from __future__ import annotations

import random
from typing import Any

from app.firebase_client import get_firestore_client, server_timestamp
from app.models import MatchSession, Track
from app.services.library_service import LibraryService
from app.services.recommendation_service import RecommendationService
from app.services.track_service import TrackService
from app.services.user_service import UserService

MIN_SEED_SWIPES = 3  # trigger refinement after this many seed swipes (or all seeds if fewer)


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
            "status": "active",       # used in completion logic
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

        Behavior:
        - While in pure seed phase and below MIN_SEED_SWIPES:
            - Serve only from seed_track_ids (like before).
        - Once refined is available (after threshold or seeds exhausted):
            - Blend sources: ~2/3 of the time pick from seeds, ~1/3 from refined.
            - Still skip anything in library or already swiped.
        """
        username = username.lower()

        library_ids = set(self.user_service.get_library_track_ids(username))
        swiped_ids = self.user_service.get_swiped_track_ids(username)
        skip_ids = library_ids | swiped_ids

        # --- Pure seed phase: before we generate refined recs ---
        if session.phase == "seed":
            # If not enough swipes yet, just use seed-only behavior with current_index
            if not self._should_transition_to_refined(session):
                return self._next_from_seed_only(username, session, skip_ids)

            # Otherwise, generate refined_track_ids and switch to blended mode
            session = self._transition_to_refined(username, session)

        # --- Blended mode: seeds + refined (phase "refined") ---
        track = self._next_mixed_track(username, session, skip_ids)

        if track is None:
            # No tracks left from either source
            session.status = "completed"
            session.updated_at = server_timestamp()
            self._save_session(username, session)
            return None, session

        return track, session

    # ---------- helpers ----------

    def _should_transition_to_refined(self, session: MatchSession) -> bool:
        if session.phase != "seed":
            return False
        if not session.seed_track_ids:
            return False
        threshold = min(len(session.seed_track_ids), MIN_SEED_SWIPES)
        return session.seed_swipes_completed >= threshold

    def _next_from_seed_only(
        self,
        username: str,
        session: MatchSession,
        skip_ids: set[str],
    ) -> tuple[Track | None, MatchSession]:
        """Seed-only behavior while we're still below the refinement threshold."""
        universe = session.seed_track_ids or []
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

        # Ran out of seed tracks: force refinement and then blend
        session = self._transition_to_refined(username, session)
        return self.get_next_track(username, session)

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

        refined_ids = self.recommendation_service.build_refined_track_ids(
            top_genres=top_genres,
            feature_preferences=preferences,
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

    def _next_mixed_track(
        self,
        username: str,
        session: MatchSession,
        skip_ids: set[str],
    ) -> Track | None:
        """
        After refinement: mix seeds & refined.

        Approximate ratio:
          - 1/3 of requests -> refined_track_ids
          - 2/3 of requests -> seed_track_ids

        We always skip:
          - tracks already in library
          - tracks already swiped
        """
        seed_ids = session.seed_track_ids or []
        refined_ids = session.refined_track_ids or []

        has_seed = bool(seed_ids)
        has_refined = bool(refined_ids)

        if not has_seed and not has_refined:
            return None

        # Helper to pull next usable track from a list of IDs
        def pick_from_ids(ids: list[str]) -> Track | None:
            for tid in ids:
                if tid in skip_ids:
                    continue
                track = self.track_service.get_track(tid)
                if track:
                    return track
            return None

        # We’ll do up to 2 attempts:
        #  1) preferred source (based on ratio)
        #  2) fallback to the other source if first was empty/exhausted
        for _ in range(2):
            use_refined = False

            if has_seed and has_refined:
                # Both available: 1/3 chance refined, 2/3 chance seed
                use_refined = random.random() < (1.0 / 3.0)
            elif has_refined:
                use_refined = True
            else:
                use_refined = False  # only seeds left

            if use_refined:
                candidate = pick_from_ids(refined_ids)
            else:
                candidate = pick_from_ids(seed_ids)

            if candidate is not None:
                # We don't rely on current_index in blended mode; treat it as a simple counter
                session.current_index += 1
                session.updated_at = server_timestamp()
                self._save_session(username, session)
                return candidate

            # If the chosen source had nothing usable, disable it and try the other on next loop
            if use_refined:
                has_refined = False
            else:
                has_seed = False

        # Neither source could produce a new track
        return None
