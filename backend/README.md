# Backend Overview

This folder hosts a small Flask skeleton that will grow into the ByteGoblin's backend. The structure focuses on keeping the core layers
separated so future Firebase and Spotify work can slot in cleanly.

```
backend/
├── app/
│   ├── __init__.py          # App factory & blueprint registration
│   ├── config.py            # Environment-aware settings
│   ├── blueprints/
│   │   ├── __init__.py
│   │   ├── health.py        # /api/health status check
│   │   └── spotify.py       # Spotify-facing endpoints
│   └── services/
│       ├── __init__.py
│       ├── firebase_service.py
│       └── spotify_service.py
├── run.py                   # Local entry point (flask --app run.py run)
├── requirements.txt
└── .env.example
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
   - When using service account JSON for Firebase, paste the private key as-is (including literal `\n` sequences) so it can be reconstructed.
5. **Run the API**
   ```bash
   flask --app run.py --debug run
   ```

## Spotify Integration Plan

- `SpotifyService` implements the Client Credentials grant for server-to-server calls (search is stubbed as the first API).
- Use `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` environment values.
- Extend the blueprint in `app/blueprints/spotify.py` for additional resources (playlists, top tracks, etc.).

## Firebase Integration Plan

- `firebase_service.py` configures Firebase Admin SDK once and attaches the initialized app to Flask's `g` context for easy reuse.
- Expect to store Firebase credentials in environment variables rather than committing JSON.
- Future data-access helpers can live alongside `firebase_service.py` or in a dedicated `repositories/` package.

## Testing

At minimum, wire up pytest with a simple smoke test against the app factory:

```bash
pip install pytest
pytest
```

As functionality grows, add integration tests for each blueprint and service.
