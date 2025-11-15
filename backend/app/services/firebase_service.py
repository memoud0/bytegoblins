from __future__ import annotations

import logging
from typing import Any

from flask import Flask

try:
    import firebase_admin
    from firebase_admin import credentials
except ImportError:  # pragma: no cover - firebase optional during early dev
    firebase_admin = None
    credentials = None


def init_firebase_app(app: Flask) -> None:
    """Initialize Firebase Admin if credentials are present."""
    if firebase_admin is None or credentials is None:
        app.logger.info("firebase-admin not installed; skipping Firebase init")
        return

    if app.config.get("FIREBASE_CLIENT_EMAIL") is None:
        app.logger.info("Firebase env vars missing; skipping Firebase init")
        return

    if firebase_admin._apps:  # type: ignore[attr-defined]
        app.extensions["firebase_app"] = firebase_admin.get_app()
        return

    cred_payload = _build_cred_payload(app)
    options: dict[str, Any] = {}
    if db_url := app.config.get("FIREBASE_DATABASE_URL"):
        options["databaseURL"] = db_url

    cred = credentials.Certificate(cred_payload)
    firebase_app = firebase_admin.initialize_app(cred, options)
    app.extensions["firebase_app"] = firebase_app
    logging.getLogger(__name__).info("Initialized Firebase app %s", firebase_app.name)


def _build_cred_payload(app: Flask) -> dict[str, str]:
    private_key = app.config["FIREBASE_PRIVATE_KEY"]
    if private_key:
        private_key = private_key.replace("\\n", "\n")

    return {
        "type": "service_account",
        "project_id": app.config.get("FIREBASE_PROJECT_ID") or "",
        "private_key_id": "placeholder",
        "private_key": private_key or "",
        "client_email": app.config.get("FIREBASE_CLIENT_EMAIL") or "",
        "client_id": "placeholder",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "",
    }
