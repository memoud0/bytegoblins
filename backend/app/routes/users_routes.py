from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.firebase_client import get_firestore_client, server_timestamp

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


@users_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()

    if not username:
        return jsonify({"error": "username is required"}), 400

    # normalize username (optional: lowercase to avoid duplicates)
    username_norm = username.lower()

    db = get_firestore_client()
    user_ref = db.collection("users").document(username_norm)
    snap = user_ref.get()

    created = False  # <-- define default

    if not snap.exists:
        created = True
        user_ref.set(
            {
                "username": username_norm,
                "created_at": server_timestamp(),
                "last_active_at": server_timestamp(),
                # optional: initialize aggregates for consistency with UserProfile
                "likes_count": 0,
                "dislikes_count": 0,
                "liked_genres": {},
                "disliked_genres": {},
                "feature_sums_liked": {},
                "feature_sums_disliked": {},
            },
            merge=True,
        )
    else:
        user_ref.update(
            {
                "last_active_at": server_timestamp(),
            }
        )

    return jsonify(
        {
            "username": username_norm,
            "created": created,
        }
    ), 200
