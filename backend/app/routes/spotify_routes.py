from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.services.spotify_service import SpotifyService, SpotifyServiceError

spotify_bp = Blueprint("spotify", __name__)


@spotify_bp.get("/songs/preview")
def get_song_preview():
    track_id = request.args.get("trackId", "").strip()
    if not track_id:
        return jsonify({"error": "trackId is required"}), 400

    try:
        service = SpotifyService()
        payload = service.get_track_preview(track_id)
    except SpotifyServiceError as exc:
        return jsonify({"error": str(exc)}), 502

    return jsonify(payload)
