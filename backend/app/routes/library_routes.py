from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.services.library_service import LibraryService

# Single blueprint, all routes under /api/...
library_bp = Blueprint("library", __name__)


@library_bp.get("/library")
def get_library():
    """
    GET /api/library?username=mo

    Returns the user's library as Track[].
    """
    username = (request.args.get("username") or "").strip()
    if not username:
        return jsonify({"error": "username is required"}), 400

    # keep consistent with /users/login behavior (lowercase)
    username_norm = username.lower()

    service = LibraryService()
    tracks = service.get_library_tracks(username_norm)

    # Assuming Track has a .to_dict() method.
    return jsonify(
        {
            "username": username_norm,
            "tracks": [t.to_dict() for t in tracks],
        }
    ), 200


@library_bp.post("/library/add")
def add_to_library():
    """
    POST /api/library/add

    Two supported payload shapes:

    1) Legacy (Firestore-only track already exists):
       {
         "username": "mo",
         "trackId": "spotifyTrackId",
         "source": "manual" | "match" | "search",
         "searchEventId": "..."   // optional
       }

    2) Hybrid (track object from /songs/search, including Spotify results):
       {
         "username": "mo",
         "track": {
           "trackId": "...",
           "trackName": "...",
           "artists": ["Artist"],
           "albumName": "...",
           "imageUrl": "...",
           "popularity": 73,
           "popularityNorm": 0.73,
           "genre": "pop",
           "genreGroup": "pop",
           "source": "firestore" | "spotify"
         }
       }
    """
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or "").strip()
    if not username:
        return jsonify({"error": "username is required"}), 400

    username_norm = username.lower()
    service = LibraryService()

    track_payload = data.get("track")

    # ---- New hybrid path: full track object (e.g., from Spotify search) ----
    if isinstance(track_payload, dict):
        track_id = (track_payload.get("trackId") or "").strip()
        if not track_id:
            return jsonify({"error": "track.trackId is required"}), 400

        try:
            track = service.add_track_object_to_library(
                username=username_norm,
                track_payload=track_payload,
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 404

        return jsonify(
            {
                "username": username_norm,
                "track": track.to_dict(),
            }
        ), 200

    # ---- Legacy path: add by trackId only ----
    track_id = (data.get("trackId") or "").strip()
    source = (data.get("source") or "manual").strip() or "manual"
    search_event_id = data.get("searchEventId")

    if not track_id:
        return jsonify({"error": "trackId is required"}), 400

    try:
        track = service.add_to_library(
            username=username_norm,
            track_id=track_id,
            source=source,
            search_event_id=search_event_id,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404

    return jsonify(
        {
            "username": username_norm,
            "track": track.to_dict(),
        }
    ), 200
