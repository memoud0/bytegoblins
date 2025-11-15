# app/routes/debug_routes.py
from flask import Blueprint, jsonify
from app.firebase_client import get_firestore_client

# All routes in this blueprint will be under /api
debug_bp = Blueprint("debug", __name__, url_prefix="/api")

@debug_bp.get("/debug/firebase")
def debug_firebase():
    db = get_firestore_client()
    cols = [c.id for c in db.collections()]
    return jsonify({"status": "ok", "collections": cols})
