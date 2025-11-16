from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask.typing import ResponseReturnValue

from app.services.spotify_service import SpotifyService
from app.services.track_service import TrackService

spotify_bp = Blueprint("spotify", __name__, url_prefix="/api/tracks")


@spotify_bp.get("/enriched")
def get_enriched_track() -> ResponseReturnValue:
    """
    GET /api/tracks/enriched?trackId=SPOTIFY_TRACK_ID

    Returns:
    {
      "track": { ... our Track model ... },
      "spotify": {
        "spotify_id": string,
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

    # 1) Get our track from Firestore
    track = track_service.get_track(track_id)
    if not track:
        return jsonify({"error": "Track not found"}), 404

    try:
        # 2) Enrich with Spotify metadata
        spotify_info = spotify_service.get_track_details(track_id, track_metadata=track)
    except Exception as exc:  # requests errors, auth errors, etc.
        return (
            jsonify(
                {
                    "track": track.to_dict(),
                    "spotify": None,
                    "warning": f"Failed to fetch Spotify data: {exc}",
                }
            ),
            502,
        )

    return jsonify({"track": track.to_dict(), "spotify": spotify_info}), 200
