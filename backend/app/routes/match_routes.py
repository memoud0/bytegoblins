from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.models import MatchSession
from app.services.session_service import SessionService
from app.services.track_service import TrackService

match_bp = Blueprint("match", __name__)


@match_bp.post("/match/sessions")
def create_session():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username") or "").strip()
    if not username:
        return jsonify({"error": "username is required"}), 400

    try:
        seed_limit = int(payload.get("seedLimit") or 12)
    except (TypeError, ValueError):
        return jsonify({"error": "seedLimit must be an integer"}), 400
    session_service = SessionService()
    try:
        session, tracks = session_service.create_session(username, seed_limit=seed_limit)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(
        {
            "session": _session_payload(session),
            "seedTracks": [track.to_dict() for track in tracks],
        }
    )


@match_bp.post("/match/swipe")
def swipe_track():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username") or "").strip()
    session_id = str(payload.get("sessionId") or "").strip()
    track_id = str(payload.get("trackId") or "").strip()
    liked = payload.get("liked")

    if not username or not session_id or not track_id:
        return jsonify({"error": "username, sessionId, and trackId are required"}), 400
    if liked is None or not isinstance(liked, bool):
        return jsonify({"error": "liked must be a boolean"}), 400

    session_service = SessionService()
    track_service = TrackService()

    try:
        session = session_service.get_session(username, session_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404

    track = track_service.get_track(track_id)
    if not track:
        return jsonify({"error": "track not found"}), 404

    before_phase = session.phase
    session = session_service.register_swipe(username, session, track, liked)
    phase_changed = before_phase != session.phase

    return jsonify(
        {
            "trackId": track_id,
            "liked": liked,
            "session": _session_payload(session),
            "phaseChanged": phase_changed,
        }
    )


@match_bp.get("/match/next")
def next_track():
    username = request.args.get("username", "").strip()
    session_id = request.args.get("sessionId", "").strip()
    if not username or not session_id:
        return jsonify({"error": "username and sessionId are required"}), 400

    session_service = SessionService()
    try:
        session = session_service.get_session(username, session_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404

    track, session = session_service.get_next_track(username, session)
    if track is None:
        return jsonify({"session": _session_payload(session), "track": None, "status": "completed"}), 200

    return jsonify(
        {
            "session": _session_payload(session),
            "track": track.to_dict(),
        }
    )


def _session_payload(session: MatchSession) -> dict[str, object]:
    return {
        "sessionId": session.session_id,
        "phase": session.phase,
        "status": session.status,
        "seedTrackIds": session.seed_track_ids,
        "refinedTrackIds": session.refined_track_ids,
        "currentIndex": session.current_index,
        "seedSwipesCompleted": session.seed_swipes_completed,
    }
