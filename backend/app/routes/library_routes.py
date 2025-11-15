from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.services.library_service import LibraryService

library_bp = Blueprint("library", __name__)


@library_bp.get("/library")
def get_library():
    username = request.args.get("username", "").strip()
    if not username:
        return jsonify({"error": "username is required"}), 400

    library_service = LibraryService()
    tracks = library_service.get_library_tracks(username)
    return jsonify({"tracks": [track.to_dict() for track in tracks]})


@library_bp.post("/library/add")
def add_to_library():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username") or "").strip()
    track_id = str(payload.get("trackId") or "").strip()
    source = str(payload.get("source") or "manual")
    search_event_id = payload.get("searchEventId")

    if not username or not track_id:
        return jsonify({"error": "username and trackId are required"}), 400

    library_service = LibraryService()
    try:
        track = library_service.add_to_library(username, track_id, source=source, search_event_id=search_event_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"track": track.to_dict()})
