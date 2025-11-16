from __future__ import annotations

import random
from typing import Iterable

from firebase_admin import firestore

from app.firebase_client import get_firestore_client
from app.models import Track


class TrackService:
    def __init__(self) -> None:
        self.db = get_firestore_client()

    def get_track(self, track_id: str) -> Track | None:
        doc = self.db.collection("tracks").document(track_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        return Track.from_mapping(doc.id, data)

    def get_tracks_by_ids(self, track_ids: Iterable[str]) -> list[Track]:
        track_ids = list(track_ids)
        if not track_ids:
            return []
        refs = [self.db.collection("tracks").document(track_id) for track_id in track_ids]
        docs = list(self.db.get_all(refs))
        results: list[Track] = []
        for doc in docs:
            if not doc.exists:
                continue
            data = doc.to_dict() or {}
            results.append(Track.from_mapping(doc.id, data))
        return results

    def get_seed_tracks(self, exclude_track_ids: set[str], limit: int = 12) -> list[Track]:
        query = (
            self.db.collection("tracks")
            .where("popularity_norm", ">=", 0.75)
            .order_by("popularity_norm", direction=firestore.Query.DESCENDING)
            .limit(400)
        )
        docs = list(query.stream())

        buckets: dict[str, list[Track]] = {}
        for doc in docs:
            data = doc.to_dict() or {}
            track = Track.from_mapping(doc.id, data)
            if track.track_id in exclude_track_ids:
                continue
            genre_key = track.track_genre_group or track.track_genre or "misc"
            buckets.setdefault(genre_key, []).append(track)

        for genre_tracks in buckets.values():
            random.shuffle(genre_tracks)

        selected: list[Track] = []
        while len(selected) < limit and buckets:
            for genre, tracks in list(buckets.items()):
                if not tracks:
                    buckets.pop(genre, None)
                    continue
                selected.append(tracks.pop())
                if len(selected) >= limit:
                    break
        return selected

    def get_candidate_tracks(
        self,
        top_genres: list[str],
        exclude_track_ids: set[str],
        limit: int = 300,
    ) -> list[Track]:
        query = (
            self.db.collection("tracks")
            .where("popularity_norm", ">=", 0.6)
            .order_by("popularity_norm", direction=firestore.Query.DESCENDING)
            .limit(800)
        )
        docs = list(query.stream())
        allowed_genres = [genre for genre in top_genres if genre]

        candidates: list[Track] = []
        exploration: list[Track] = []
        for doc in docs:
            data = doc.to_dict() or {}
            track = Track.from_mapping(doc.id, data)
            if track.track_id in exclude_track_ids:
                continue

            track_genre = track.track_genre or track.track_genre_group
            if track_genre in allowed_genres:
                candidates.append(track)
            else:
                exploration.append(track)

            if len(candidates) >= limit:
                break

        if len(candidates) < limit and exploration:
            random.shuffle(exploration)
            candidates.extend(exploration[: limit - len(candidates)])
        return candidates

    def search_tracks(self, query_norm: str, limit: int = 20) -> list[Track]:
        upper_bound = f"{query_norm}\uf8ff"
        docs = (
            self.db.collection("tracks")
            .where("track_name_lowercase", ">=", query_norm)
            .where("track_name_lowercase", "<=", upper_bound)
            .order_by("track_name_lowercase")
            .limit(limit)
            .stream()
        )
        tracks: list[Track] = []
        for doc in docs:
            data = doc.to_dict() or {}
            tracks.append(Track.from_mapping(doc.id, data))
        return tracks
