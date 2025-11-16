from __future__ import annotations

import time
from typing import Any

import requests
from flask import current_app

from app.models.track import Track
from app.services.itunes_preview_service import ItunesPreviewService


class SpotifyService:
    def __init__(self) -> None:
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    def _get_access_token(self) -> str:
        # Cached token using Client Credentials flow
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        client_id = current_app.config.get("SPOTIFY_CLIENT_ID")
        client_secret = current_app.config.get("SPOTIFY_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise RuntimeError("Spotify client ID/secret not configured")

        resp = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data["expires_in"]
        return self._access_token

    def get_track_details(self, spotify_track_id: str, track_metadata: Track | None = None) -> dict[str, Any]:
        """
        Fetch preview_url + album cover for a track.
        """
        token = self._get_access_token()
        resp = requests.get(
            f"https://api.spotify.com/v1/tracks/{spotify_track_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        album = data.get("album") or {}
        images = album.get("images") or []
        image_url = images[0]["url"] if images else None

        preview_url = data.get("preview_url")
        preview_source = "spotify"
        spotify_url = data.get("external_urls", {}).get("spotify")
        if not preview_url and track_metadata is not None:
            itunes_service = ItunesPreviewService()
            fallback_url, fallback_source = itunes_service.get_preview(track_metadata)
            if fallback_url:
                preview_url = fallback_url
                preview_source = fallback_source or "itunes"

        return {
            "spotify_id": spotify_track_id,
            "preview_url": preview_url,
            "album_image_url": image_url,
            "spotify_url": spotify_url,
            "preview_source": preview_source,
        }
