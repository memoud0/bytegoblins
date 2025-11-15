# app/routes/users_routes.py
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

    if not snap.exists:
        # new user
        user_ref.set(
            {
                "username": username_norm,
                "created_at": server_timestamp(),
                "last_login_at": server_timestamp(),
            }
        )
        created = True
    else:
        # existing user
        user_ref.update(
            {
                "last_login_at": server_timestamp(),
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
