from __future__ import annotations

import base64
import time
from dataclasses import dataclass
from typing import Any

import requests
from flask import current_app


class SpotifyServiceError(RuntimeError):
    """Raised when Spotify returns an error response."""


@dataclass
class _TokenCache:
    access_token: str
    expires_at: float

    def is_valid(self) -> bool:
        return time.time() < self.expires_at - 30  # refresh 30s early


class SpotifyService:
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    API_BASE_URL = "https://api.spotify.com/v1"
    _token_cache: _TokenCache | None = None

    def __init__(self) -> None:
        config = current_app.config
        self.client_id: str | None = config.get("SPOTIFY_CLIENT_ID")
        self.client_secret: str | None = config.get("SPOTIFY_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise SpotifyServiceError("Spotify credentials are not configured.")

    def search(self, query: str, search_type: str = "track", limit: int = 10) -> dict[str, Any]:
        token = self._get_access_token()
        response = requests.get(
            f"{self.API_BASE_URL}/search",
            params={"q": query, "type": search_type, "limit": limit},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if not response.ok:
            raise SpotifyServiceError(f"Spotify search failed: {response.text}")
        return response.json()

    def _get_access_token(self) -> str:
        if self._token_cache and self._token_cache.is_valid():
            return self._token_cache.access_token

        token = self._request_new_token()
        return token

    def _request_new_token(self) -> str:
        credentials_b64 = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()

        response = requests.post(
            self.TOKEN_URL,
            data={"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {credentials_b64}"},
            timeout=10,
        )

        if not response.ok:
            raise SpotifyServiceError(f"Failed to acquire Spotify token: {response.text}")

        payload = response.json()
        expires_in = payload.get("expires_in", 3600)
        access_token = payload.get("access_token")

        if not access_token:
            raise SpotifyServiceError("Spotify token payload missing `access_token`.")

        self.__class__._token_cache = _TokenCache(access_token=access_token, expires_at=time.time() + expires_in)
        return access_token
