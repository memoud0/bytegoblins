from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.services.library_service import LibraryService

library_bp = Blueprint("library", __name__, url_prefix="/api")

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

    # Assuming Track has a .to_dict() method; if not, we can adapt later.
    return jsonify({"username": username_norm, "tracks": [t.to_dict() for t in tracks]}), 200

@library_bp.post("/library/add")
def add_to_library():
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or "").strip()
    track_id = (data.get("trackId") or "").strip()
    source = (data.get("source") or "manual").strip() or "manual"
    search_event_id = data.get("searchEventId")

    if not username:
        return jsonify({"error": "username is required"}), 400
    if not track_id:
        return jsonify({"error": "trackId is required"}), 400

    username_norm = username.lower()
    service = LibraryService()

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


@library_bp.delete("/library/<track_id>")
def remove_from_library(track_id: str):
    """
    DELETE /api/library/<track_id>?username=mo

    Removes a track from the user's library.
    """
    username = (request.args.get("username") or "").strip()
    if not username:
        return jsonify({"error": "username is required"}), 400

    service = LibraryService()
    try:
        service.remove_from_library(username=username, track_id=track_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404

    return jsonify(
        {
            "username": username.lower(),
            "trackId": track_id,
            "status": "removed",
        }
    ), 200