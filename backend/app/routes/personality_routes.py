from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.services.personality_service import PersonalityService

personality_bp = Blueprint("personality", __name__, url_prefix="/api/personality")


@personality_bp.post("")
def compute_personality():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip().lower()

    if not username:
        return jsonify({"error": "username is required"}), 400

    service = PersonalityService()
    try:
        result = service.compute_for_user(username)
    except Exception as exc:  # noqa: BLE001
        print("Error computing personality:", exc)
        return jsonify({"error": "Failed to compute personality"}), 500

    return jsonify(result.to_dict()), 200
