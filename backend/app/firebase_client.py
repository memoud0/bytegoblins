from __future__ import annotations

from typing import Any

from flask import Flask, current_app

import json
import os

from dotenv import load_dotenv

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:  # pragma: no cover - firebase optional for early dev
    firebase_admin = None
    credentials = None
    firestore = None

# Key under which we store the firebase app on Flask's extensions
_FIREBASE_APP_KEY = "firebase_app"

load_dotenv()


def init_firebase_app(app: Flask) -> None:
    """
    Initialize the Firebase Admin app and store it on Flask's extensions.

    - Preferred: service account JSON pointed to by GOOGLE_APPLICATION_CREDENTIALS
    - Fallback: build credentials from FIREBASE_* config vars
    """
    if firebase_admin is None or credentials is None:
        app.logger.warning("firebase-admin not installed; skipping Firebase init.")
        return

    # If we don't even have a client email configured, bail out early
    if not app.config.get("FIREBASE_CLIENT_EMAIL") and not os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS"
    ):
        app.logger.warning("Firebase credentials missing; skipping Firebase init.")
        return

    # Reuse existing app if already initialized
    if firebase_admin._apps:  # type: ignore[attr-defined]
        firebase_app = firebase_admin.get_app()
    else:
        cred_payload = _build_cred_payload(app)

        # Options: RTDB URL (rarely used here) and optional project ID
        options: dict[str, Any] = {}
        if db_url := app.config.get("FIREBASE_DATABASE_URL"):
            options["databaseURL"] = db_url

        project_id = (
            app.config.get("FIREBASE_PROJECT_ID")
            or os.getenv("FIREBASE_PROJECT_ID")
            or cred_payload.get("project_id")
        )
        if project_id:
            options["projectId"] = project_id

        credential = credentials.Certificate(cred_payload)
        firebase_app = firebase_admin.initialize_app(credential, options)

    app.extensions[_FIREBASE_APP_KEY] = firebase_app
    app.logger.info("Firebase app ready: %s", firebase_app.name)


def get_firestore_client(app: Flask | None = None):
    """
    Return the Firestore client for the configured Firebase app.

    Usage in services (with app context active):

        from app.firebase_client import get_firestore_client

        db = get_firestore_client()
        users_ref = db.collection("users")

    """
    if firestore is None:
        raise RuntimeError("firebase-admin is not installed; cannot access Firestore.")

    app = app or current_app
    firebase_app = app.extensions.get(_FIREBASE_APP_KEY)
    if firebase_app is None:
        raise RuntimeError(
            "Firebase app is not configured. Did you call init_firebase_app() in create_app()?"
        )

    return firestore.client(firebase_app)


def server_timestamp() -> Any:
    """
    Convenience wrapper for Firestore's server timestamp sentinel.

    Use instead of importing firestore directly in services:

        from app.firebase_client import server_timestamp

        doc_ref.set({ "created_at": server_timestamp() })
    """
    if firestore is None:
        raise RuntimeError(
            "firebase-admin is not installed; cannot create server timestamps."
        )
    return firestore.SERVER_TIMESTAMP


def _build_cred_payload(app: Flask) -> dict[str, str]:
    """
    Build the credential payload for Firebase.

    Preferred: load from GOOGLE_APPLICATION_CREDENTIALS JSON file.
    Fallback: build from individual env vars / Flask config (FIREBASE_*).
    """
    keyfile_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    # Preferred path: load the real service account JSON
    if keyfile_path and os.path.exists(keyfile_path):
        with open(keyfile_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # Fallback to env/config-based construction
    private_key = app.config.get("FIREBASE_PRIVATE_KEY") or os.getenv(
        "FIREBASE_PRIVATE_KEY", ""
    )
    if "\\n" in private_key:
        private_key = private_key.replace("\\n", "\n")

    project_id = (
        app.config.get("FIREBASE_PROJECT_ID")
        or os.getenv("FIREBASE_PROJECT_ID")
        or ""
    )
    client_email = (
        app.config.get("FIREBASE_CLIENT_EMAIL")
        or os.getenv("FIREBASE_CLIENT_EMAIL")
        or ""
    )

    return {
        "type": "service_account",
        "project_id": project_id,
        "private_key_id": "placeholder",
        "private_key": private_key,
        "client_email": client_email,
        "client_id": "placeholder",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "",
    }
