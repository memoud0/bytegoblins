from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.services.session_service import SessionService
from app.services.track_service import TrackService

match_bp = Blueprint("match", __name__, url_prefix="/api/match")


@match_bp.post("/sessions")
def create_match_session():
    """
    POST /api/match/sessions
    Body: { "username": string, "seedLimit"?: number }

    Returns:
    {
      "sessionId": string,
      "username": string,
      "seedTrackIds": string[],
      "seedCount": number,
      "phase": "seed"
    }
    """
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    seed_limit = data.get("seedLimit") or 12

    if not username:
        return jsonify({"error": "username is required"}), 400

    service = SessionService()
    result = service.create_session(username=username, seed_limit=int(seed_limit))

    # result is already a JSON-safe dict returned by SessionService
    return jsonify(result), 200


@match_bp.post("/swipe")
def swipe():
    """
    POST /api/match/swipe
    Body:
    {
      "username": string,
      "sessionId": string,
      "trackId": string,
      "direction": "like" | "dislike"
    }
    """
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or "").strip()
    session_id = (data.get("sessionId") or "").strip()
    track_id = (data.get("trackId") or "").strip()
    direction = (data.get("direction") or "").strip().lower()

    if not username:
        return jsonify({"error": "username is required"}), 400
    if not session_id:
        return jsonify({"error": "sessionId is required"}), 400
    if not track_id:
        return jsonify({"error": "trackId is required"}), 400
    if direction not in {"like", "dislike"}:
        return jsonify({"error": "direction must be 'like' or 'dislike'"}), 400

    session_service = SessionService()
    track_service = TrackService()

    # Load session
    try:
        session = session_service.get_session(username, session_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404

    # Load track
    track = track_service.get_track(track_id)
    if not track:
        return jsonify({"error": "Track not found."}), 404

    liked = direction == "like"

    # This does: store swipe, update user aggregates, add to library on like, update session
    updated_session = session_service.register_swipe(
        username=username,
        session=session,
        track=track,
        liked=liked,
    )

    # Minimal JSON-safe response with updated session info
    return jsonify(
        {
            "status": "ok",
            "session": {
                "sessionId": updated_session.session_id,
                "phase": updated_session.phase,
                "status": getattr(updated_session, "status", "active"),
                "currentIndex": updated_session.current_index,
                "seedSwipesCompleted": getattr(updated_session, "seed_swipes_completed", 0),
            },
        }
    ), 200


@match_bp.get("/next")
def next_track():
    """
    GET /api/match/next?username=...&sessionId=...

    Returns:
    {
      "sessionId": string,
      "phase": "seed" | "refined",
      "status": "active" | "completed",
      "done": boolean,
      "track": Track | null
    }
    """
    username = (request.args.get("username") or "").strip()
    session_id = (request.args.get("sessionId") or "").strip()

    if not username:
        return jsonify({"error": "username is required"}), 400
    if not session_id:
        return jsonify({"error": "sessionId is required"}), 400

    session_service = SessionService()

    # Load session
    try:
        session = session_service.get_session(username, session_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404

    # Ask service for the next track (may move to refined phase internally)
    track, updated_session = session_service.get_next_track(username, session)

    status = getattr(updated_session, "status", "active")
    done = status == "completed"

    if track is None:
        # No more tracks for this session
        return jsonify(
            {
                "sessionId": updated_session.session_id,
                "phase": updated_session.phase,
                "status": status,
                "done": True,
                "track": None,
            }
        ), 200

    return jsonify(
        {
            "sessionId": updated_session.session_id,
            "phase": updated_session.phase,
            "status": status,
            "done": done,
            "track": track.to_dict(),
        }
    ), 200
