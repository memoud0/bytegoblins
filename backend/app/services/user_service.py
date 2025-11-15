from __future__ import annotations

from app.firebase_client import get_firestore_client, server_timestamp
from app.models import UserProfile
from app.models.track import NUMERIC_FEATURES, Track


class UserService:
    def __init__(self) -> None:
        self.db = get_firestore_client()
        self.users_ref = self.db.collection("users")

    def ensure_user(self, username: str) -> UserProfile:
        doc_ref = self.users_ref.document(username)
        snapshot = doc_ref.get()
        if snapshot.exists:
            return UserProfile.from_mapping(username, snapshot.to_dict() or {})

        now = server_timestamp()
        profile = UserProfile(username=username, created_at=now, last_active_at=now)
        doc_ref.set(
            {
                **profile.to_dict(),
                "created_at": now,
                "last_active_at": now,
            }
        )
        return profile

    def get_user(self, username: str) -> UserProfile | None:
        snapshot = self.users_ref.document(username).get()
        if not snapshot.exists:
            return None
        return UserProfile.from_mapping(username, snapshot.to_dict() or {})

    def update_last_active(self, username: str) -> None:
        self.users_ref.document(username).set({"last_active_at": server_timestamp()}, merge=True)

    def get_swiped_track_ids(self, username: str) -> set[str]:
        swipes_ref = self.users_ref.document(username).collection("swipes")
        track_ids: set[str] = set()
        for doc in swipes_ref.stream():
            payload = doc.to_dict() or {}
            track_id = payload.get("track_id")
            if track_id:
                track_ids.add(track_id)
        return track_ids

    def record_swipe(
        self,
        username: str,
        session_id: str,
        track: Track,
        liked: bool,
        phase: str,
    ) -> None:
        user_ref = self.users_ref.document(username)
        now = server_timestamp()
        swipe_ref = user_ref.collection("swipes").document()
        swipe_ref.set(
            {
                "track_id": track.track_id,
                "liked": liked,
                "session_id": session_id,
                "phase": phase,
                "created_at": now,
            }
        )

        snapshot = user_ref.get()
        profile = UserProfile.from_mapping(username, snapshot.to_dict() or {})

        if liked:
            profile.likes_count += 1
        else:
            profile.dislikes_count += 1

        genre_key = track.track_genre_group or track.track_genre
        if genre_key:
            genre_map = profile.liked_genres if liked else profile.disliked_genres
            genre_map[genre_key] = genre_map.get(genre_key, 0) + 1

        feature_map = profile.feature_sums_liked if liked else profile.feature_sums_disliked
        for feature in NUMERIC_FEATURES:
            track_value = getattr(track, feature, None)
            if track_value is None:
                continue
            feature_map[feature] = feature_map.get(feature, 0.0) + float(track_value)

        user_ref.set(
            {
                "likes_count": profile.likes_count,
                "dislikes_count": profile.dislikes_count,
                "liked_genres": profile.liked_genres,
                "disliked_genres": profile.disliked_genres,
                "feature_sums_liked": profile.feature_sums_liked,
                "feature_sums_disliked": profile.feature_sums_disliked,
                "last_active_at": now,
            },
            merge=True,
        )

    def get_top_genres(self, profile: UserProfile, limit: int = 3) -> list[str]:
        scores: dict[str, float] = {}
        for genre, count in profile.liked_genres.items():
            if not genre:
                continue
            scores[genre] = scores.get(genre, 0.0) + float(count)
        for genre, count in profile.disliked_genres.items():
            if not genre:
                continue
            scores[genre] = scores.get(genre, 0.0) - 0.5 * float(count)

        sorted_genres = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return [genre for genre, _ in sorted_genres[:limit] if genre]

    def get_library_track_ids(self, username: str) -> list[str]:
        user_ref = self.users_ref.document(username)
        library_ref = user_ref.collection("library")
        track_ids: list[str] = []
        for doc in library_ref.stream():
            payload = doc.to_dict() or {}
            track_id = payload.get("track_id") or doc.id
            if track_id:
                track_ids.append(track_id)
        return track_ids
