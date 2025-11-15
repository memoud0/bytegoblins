from datetime import datetime, timezone

from flask import Blueprint, jsonify


health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    """Lightweight readiness endpoint."""
    now = datetime.now(timezone.utc)
    return jsonify(
        {
            "status": "ok",
            "timestamp": now.isoformat(),
        }
    )
