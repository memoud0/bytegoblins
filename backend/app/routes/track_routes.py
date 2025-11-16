from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.services.spotify_service import SpotifyService
from app.services.track_service import TrackService

tracks_bp = Blueprint("tracks", __name__, url_prefix="/api/tracks")


@tracks_bp.get("/enriched")
def get_enriched_track():
    """
    GET /api/tracks/enriched?trackId=SPOTIFY_TRACK_ID

    Returns:
    {
      "track": { ... our Track model ... },
      "spotify": {
        "preview_url": string | null,
        "album_image_url": string | null,
        "spotify_url": string | null
      }
    }
    """
    track_id = (request.args.get("trackId") or "").strip()
    if not track_id:
        return jsonify({"error": "trackId is required"}), 400

    track_service = TrackService()
    spotify_service = SpotifyService()

    track = track_service.get_track(track_id)
    if not track:
        return jsonify({"error": "Track not found"}), 404

    spotify_info = spotify_service.get_track_details(track_id, track_metadata=track)

    return jsonify(
        {
            "track": track.to_dict(),
            "spotify": spotify_info,
        }
    ), 200
