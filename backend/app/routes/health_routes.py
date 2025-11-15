from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()})
