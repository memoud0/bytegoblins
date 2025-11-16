# app/routes/users_routes.py
from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request

from app.firebase_client import server_timestamp
from app.services.user_service import UserService

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


def _serialize_timestamp(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


@users_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()

    if not username:
        return jsonify({"error": "username is required"}), 400

    username_norm = username.lower()
    service = UserService()
    user_ref = service.db.collection("users").document(username_norm)
    snap = user_ref.get()
    created = not snap.exists
    profile = service.ensure_user(username_norm)

    user_ref.update({"last_active_at": server_timestamp()})

    return (
        jsonify(
            {
                "username": profile.username,
                "created_at": _serialize_timestamp(profile.created_at),
                "likes_count": profile.likes_count,
                "dislikes_count": profile.dislikes_count,
                "created": created,
            }
        ),
        200,
    )
