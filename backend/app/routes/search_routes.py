from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.services.search_service import SearchService

search_bp = Blueprint("search", __name__)


@search_bp.get("/songs/search")
def search_songs():
    username = request.args.get("username", "").strip()
    query = request.args.get("q", "").strip()
    limit_param = request.args.get("limit", "20")

    if not username or not query:
        return jsonify({"error": "username and q are required"}), 400

    try:
        limit = max(1, min(50, int(limit_param)))
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400

    search_service = SearchService()
    try:
        tracks, event_id = search_service.search(username, query, limit=limit)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"tracks": [track.to_dict() for track in tracks], "searchEventId": event_id})
