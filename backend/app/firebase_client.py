from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from flask import Flask, current_app

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:  # pragma: no cover - firebase optional for early dev
    firebase_admin = None
    credentials = None
    firestore = None

_FIREBASE_APP_KEY = "firebase_app"


def init_firebase_app(app: Flask) -> None:
    """Initialize the Firebase Admin app and store it on Flask's extensions."""
    if firebase_admin is None or credentials is None:
        app.logger.warning("firebase-admin not installed; skipping Firebase init.")
        return

    if not app.config.get("FIREBASE_CLIENT_EMAIL"):
        app.logger.warning("Firebase credentials missing; skipping Firebase init.")
        return

    if firebase_admin._apps:  # type: ignore[attr-defined]
        firebase_app = firebase_admin.get_app()
    else:
        cred_payload = _build_cred_payload(app)
        options: dict[str, Any] = {}
        if db_url := app.config.get("FIREBASE_DATABASE_URL"):
            options["databaseURL"] = db_url
        credential = credentials.Certificate(cred_payload)
        firebase_app = firebase_admin.initialize_app(credential, options)

    app.extensions[_FIREBASE_APP_KEY] = firebase_app
    app.logger.info("Firebase app ready: %s", firebase_app.name)


def get_firestore_client(app: Flask | None = None):
    """Return the Firestore client for the configured Firebase app."""
    if firestore is None:
        raise RuntimeError("firebase-admin is not installed; cannot access Firestore.")

    app = app or current_app
    firebase_app = app.extensions.get(_FIREBASE_APP_KEY)
    if firebase_app is None:
        raise RuntimeError("Firebase app is not configured. Did you call init_firebase_app?")

    return firestore.client(firebase_app)


def server_timestamp() -> datetime:
    """Consistent UTC timestamps for Firestore documents."""
    return datetime.now(timezone.utc)


def _build_cred_payload(app: Flask) -> dict[str, str]:
    private_key = app.config.get("FIREBASE_PRIVATE_KEY") or ""
    if "\\n" in private_key:
        private_key = private_key.replace("\\n", "\n")

    return {
        "type": "service_account",
        "project_id": app.config.get("FIREBASE_PROJECT_ID") or "",
        "private_key_id": "placeholder",
        "private_key": private_key,
        "client_email": app.config.get("FIREBASE_CLIENT_EMAIL") or "",
        "client_id": "placeholder",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "",
    }
