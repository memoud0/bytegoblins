from __future__ import annotations

from typing import Any, Iterable

from firebase_admin import firestore

from app.firebase_client import get_firestore_client, server_timestamp
from app.models.user import UserProfile
from app.models.track import Track, NUMERIC_FEATURES


class UserService:
    def __init__(self) -> None:
        self.db = get_firestore_client()

    # ---------- User profile CRUD ----------

    def get_user(self, username: str) -> UserProfile | None:
        username = username.lower()
        doc = self.db.collection("users").document(username).get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        return UserProfile.from_mapping(username, data)

    def ensure_user(self, username: str) -> UserProfile:
        """
        Make sure a user profile exists in Firestore and return it.
        """
        username = username.lower()
        profile = self.get_user(username)
        if profile is not None:
            return profile

        now = server_timestamp()
        # Create a minimal user doc; aggregates start at zero
        doc_ref = self.db.collection("users").document(username)
        doc_ref.set(
            {
                "username": username,
                "created_at": now,
                "last_active_at": now,
                "likes_count": 0,
                "dislikes_count": 0,
                "liked_genres": {},
                "disliked_genres": {},
                "feature_sums_liked": {f: 0.0 for f in NUMERIC_FEATURES},
                "feature_sums_disliked": {f: 0.0 for f in NUMERIC_FEATURES},
            },
            merge=True,
        )

        # Reload using from_mapping to get proper types/defaults
        snapshot = doc_ref.get()
        return UserProfile.from_mapping(username, snapshot.to_dict() or {})

    def save_user(self, profile: UserProfile) -> None:
        """
        Persist the UserProfile back to Firestore.
        """
        doc_ref = self.db.collection("users").document(profile.username)
        payload = profile.to_dict()
        # last_active_at as server timestamp on writes
        payload["last_active_at"] = server_timestamp()
        doc_ref.set(payload, merge=True)

    # ---------- Aggregates & helpers ----------

    def get_library_track_ids(self, username: str) -> list[str]:
        username = username.lower()
        user_ref = self.db.collection("users").document(username)
        docs = user_ref.collection("library").stream()
        return [d.id for d in docs]

    def get_swiped_track_ids(self, username: str) -> set[str]:
        username = username.lower()
        user_ref = self.db.collection("users").document(username)
        docs = user_ref.collection("swipes").stream()
        ids: set[str] = set()
        for d in docs:
            data = d.to_dict() or {}
            tid = data.get("track_id")
            if tid:
                ids.add(tid)
        return ids

    def get_top_genres(self, profile: UserProfile, top_n: int = 5) -> list[str]:
        """
        Return user's top genres based on liked_genres counts.
        """
        if not profile.liked_genres:
            return []
        sorted_genres = sorted(
            profile.liked_genres.items(),
            key=lambda kv: kv[1],
            reverse=True,
        )
        return [g for g, _ in sorted_genres[:top_n]]

    # ---------- Swipe recording ----------

    def record_swipe(
        self,
        username: str,
        session_id: str,
        track: Track,
        liked: bool,
        phase: str,
    ) -> None:
        """
        Store a swipe and update the user's aggregate preferences.
        """
        username = username.lower()
        profile = self.ensure_user(username)

        # 1) Write swipe event
        user_ref = self.db.collection("users").document(username)
        now = server_timestamp()
        swipe_ref = user_ref.collection("swipes").document()
        swipe_ref.set(
            {
                "session_id": session_id,
                "track_id": track.track_id,
                "direction": "like" if liked else "dislike",
                "phase": phase,
                "created_at": now,
                "track_genre": track.track_genre,
                "track_genre_group": track.track_genre_group,
            }
        )

        # 2) Update aggregated counters on UserProfile
        if liked:
            profile.likes_count += 1
        else:
            profile.dislikes_count += 1

        # Genre aggregate
        genre_key = track.track_genre_group or track.track_genre or "misc"

        if liked:
            profile.liked_genres[genre_key] = profile.liked_genres.get(genre_key, 0) + 1
        else:
            profile.disliked_genres[genre_key] = profile.disliked_genres.get(genre_key, 0) + 1

        # Feature aggregates (energy, valence, etc.)
        for feature in NUMERIC_FEATURES:
            value = getattr(track, feature, None)
            if value is None:
                continue
            if liked:
                profile.feature_sums_liked[feature] = profile.feature_sums_liked.get(feature, 0.0) + float(value)
            else:
                profile.feature_sums_disliked[feature] = profile.feature_sums_disliked.get(feature, 0.0) + float(value)

        # 3) Save profile back
        self.save_user(profile)
