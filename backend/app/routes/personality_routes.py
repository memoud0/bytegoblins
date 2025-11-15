from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.services.personality_service import PersonalityService

personality_bp = Blueprint("personality", __name__)


@personality_bp.post("/personality")
def generate_personality():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username") or "").strip()
    if not username:
        return jsonify({"error": "username is required"}), 400

    service = PersonalityService()
    try:
        result = service.generate(username)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(result.to_dict())
