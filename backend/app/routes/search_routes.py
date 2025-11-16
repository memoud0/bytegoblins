from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.services.search_service import SearchService

# This is what routes/__init__.py imports:
# from .search_routes import search_bp
search_bp = Blueprint("search", __name__, url_prefix="/api/songs")


@search_bp.get("/search")
def search_songs():
    """
    GET /api/songs/search?username=<username>&q=<query>&limit=<n>

    Response:
    {
      "username": "gomgomu",
      "query": "love",
      "searchEventId": "abcd123",
      "tracks": [ Track, ... ]
    }
    """
    query = (request.args.get("q") or "").strip()
    username = (request.args.get("username") or "").strip().lower() or None
    limit_raw = (request.args.get("limit") or "").strip()

    try:
        limit = int(limit_raw) if limit_raw else 20
    except ValueError:
        limit = 20

    if not query:
        return jsonify({"error": "q (query) is required"}), 400

    service = SearchService()
    try:
        tracks, search_event_id = service.search_songs(
            query=query,
            username=username,
            limit=limit,
        )
    except Exception as exc:  # basic safety
        print("Error during search:", exc)
        return jsonify({"error": "Search failed"}), 500

    return jsonify(
        {
            "username": username,
            "query": query,
            "searchEventId": search_event_id,
            "tracks": [t.to_dict() for t in tracks],
        }
    ), 200
