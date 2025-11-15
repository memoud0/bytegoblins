# Backend Overview

This directory hosts the ByteGoblin Flask API plus all Firebase/Spotify integrations. The structure keeps HTTP routes, business logic, and data helpers split into discrete packages:

```
backend/
├── app/
│   ├── __init__.py          # App factory & blueprint registration
│   ├── config.py            # Environment-aware settings
│   ├── firebase_client.py   # Firebase Admin bootstrap + helpers
│   ├── models/              # Dataclasses shared between layers
│   ├── routes/              # Flask blueprints (health, users, match, etc.)
│   ├── services/            # Business logic (sessions, search, library, Spotify)
│   └── utils/               # Scoring, serialization, validation helpers
├── requirements.txt
├── run.py                   # Local entry point (flask --app run.py run)
├── .env.example
└── README.md
```

## Getting Started

1. **Install Python** – 3.11+ is recommended for long-term support.
2. **Create a virtual environment**
   ```bash
   cd backend
   python -m venv .venv
   .\.venv\Scripts\activate  # or source .venv/bin/activate on macOS/Linux
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure environment variables**
   - Copy `.env.example` to `.env` and fill in secrets for Spotify and Firebase.
   - When using service account JSON for Firebase, paste the private key as-is (include literal `\n` sequences).
5. **Run the API**
   ```bash
   flask --app run.py --debug run
   ```

## Spotify Integration Notes

- `SpotifyService` implements the Client Credentials grant and exposes `/api/songs/preview`.
- Provide `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, and `SPOTIFY_REDIRECT_URI` in the environment.
- Extend `app/routes/spotify_routes.py` for additional endpoints (playlists, recommendations, etc.).

## Firebase Integration Notes

- `app/firebase_client.py` initializes Firebase Admin once per process and exposes helpers for Firestore + server timestamps.
- Services access Firestore via `get_firestore_client()` and rely on server-side timestamps for consistent ordering.
- Data access lives inside `app/services/*` and can be expanded with repositories as needed.
