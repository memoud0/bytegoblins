from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.services.user_service import UserService
from app.utils.serialization import to_iso

users_bp = Blueprint("users", __name__)


@users_bp.post("/users/login")
def login_user():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username") or "").strip()
    if not username:
        return jsonify({"error": "username is required"}), 400

    user_service = UserService()
    profile = user_service.ensure_user(username)

    return jsonify(
        {
            "username": profile.username,
            "createdAt": to_iso(profile.created_at),
            "lastActiveAt": to_iso(profile.last_active_at),
            "likesCount": profile.likes_count,
            "dislikesCount": profile.dislikes_count,
            "likedGenres": profile.liked_genres,
            "dislikedGenres": profile.disliked_genres,
        }
    )
