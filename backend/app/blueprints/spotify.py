from flask import Blueprint, jsonify, request

from ..services.spotify_service import SpotifyService, SpotifyServiceError


spotify_bp = Blueprint("spotify", __name__, url_prefix="/spotify")


@spotify_bp.get("/search")
def search_tracks():
    """
    Prototype endpoint showing how Spotify's Web API will be called.
    Accepts ?q= and ?type= params, defaulting to track search.
    """
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Missing query parameter `q`"}), 400

    search_type = request.args.get("type", "track")
    try:
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return jsonify({"error": "`limit` must be an integer"}), 400

    service = SpotifyService()

    try:
        payload = service.search(query=query, search_type=search_type, limit=limit)
        return jsonify(payload)
    except SpotifyServiceError as err:
        return jsonify({"error": str(err)}), 502
