from __future__ import annotations

from flask import Blueprint, jsonify, request
from app.firebase_client import get_firestore_client, server_timestamp

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
    db = get_firestore_client()
    user_ref = db.collection("users").document(username_norm)
    snap = user_ref.get()

    if not snap.exists:
        user_ref.set(
            {
                "username": username_norm,
                "created_at": server_timestamp(),
                "last_active_at": server_timestamp(),
            }
        )
        created = True
    else:
        user_ref.update(
            {
                "last_active_at": server_timestamp(),
            }
        )
        created = False


    # You can expand this response later with aggregates, preferences, etc.
    return jsonify(
        {
            "username": username_norm,
            "created": created,
        }
    ), 200
