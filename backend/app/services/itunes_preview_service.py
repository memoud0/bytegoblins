from __future__ import annotations

from typing import Optional

import requests

from app.models.track import Track


class ItunesPreviewService:
    """Fetches preview audio snippets from the iTunes Search API."""

    API_URL = "https://itunes.apple.com/search"

    def get_preview(self, track: Track, limit: int = 1) -> tuple[Optional[str], Optional[str]]:
        primary_artist = track.artists[0] if track.artists else ""
        term_parts = [track.track_name.strip()]
        if primary_artist:
            term_parts.append(primary_artist.strip())
        term = " ".join(part for part in term_parts if part)
        if not term:
            return None, None

        try:
            response = requests.get(
                self.API_URL,
                params={
                    "media": "music",
                    "limit": limit,
                    "term": term,
                },
                timeout=6,
            )
            response.raise_for_status()
        except requests.RequestException:
            return None, "itunes-error"

        payload = response.json()
        results = payload.get("results") or []
        if not results:
            return None, "itunes-empty"

        preview_url = results[0].get("previewUrl")
        if not preview_url:
            return None, "itunes-missing"
        return preview_url, "itunes"
