# app/routes/search_routes.py
from flask import Blueprint, request, jsonify

from app.services.search_service import search_tracks

search_bp = Blueprint("search", __name__)


@search_bp.route("/songs/search")
def songs_search():
    """
    Query params:
      q: search string (required)
      username or userId: current user (required)

    Returns:
      { "results": SearchResultTrack[] }
    """
    q = request.args.get("q", type=str, default="")
    user_id = request.args.get("username") or request.args.get("userId")

    if not user_id:
        return jsonify({"error": "username is required"}), 400

    if not q.strip():
        return jsonify({"results": []}), 200

    try:
        results = search_tracks(user_id=user_id, raw_query=q)
        return jsonify({"results": results}), 200
    except Exception as e:
        return jsonify({"error": "search_failed", "message": str(e)}), 500
