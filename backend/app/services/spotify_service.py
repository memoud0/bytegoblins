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
        # Simple in-memory cache: spotify_track_id -> (timestamp, payload)
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._cache_ttl = 60 * 60  # 1 hour

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
        Fetch preview_url + album cover for a track. Simple caching + retry on 429 (honor Retry-After) + best-effort fallback.
        """
        # Return cached value if fresh
        cached = self._cache.get(spotify_track_id)
        if cached and (time.time() - cached[0]) < self._cache_ttl:
            return cached[1]

        token = self._get_access_token()
        url = f"https://api.spotify.com/v1/tracks/{spotify_track_id}"
        max_attempts = 3
        backoff_base = 0.5
        data: dict[str, Any] = {}

        for attempt in range(1, max_attempts + 1):
            try:
                resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=10)
            except requests.RequestException:
                # network error: small backoff then retry
                time.sleep(backoff_base * attempt)
                continue

            if resp.status_code == 429:
                # Rate limited: respect Retry-After header if present
                retry_after = resp.headers.get("Retry-After")
                try:
                    wait = int(retry_after) if retry_after is not None else backoff_base * attempt
                except ValueError:
                    wait = backoff_base * attempt
                time.sleep(wait)
                continue

            try:
                resp.raise_for_status()
                data = resp.json()
                break
            except requests.HTTPError:
                # Non-429 HTTP error: give up and fall back
                data = {}
                break

        album = (data.get("album") if isinstance(data, dict) else {}) or {}
        images = album.get("images") or []
        image_url = images[0]["url"] if images else None

        preview_url = data.get("preview_url") if isinstance(data, dict) else None
        preview_source = "spotify" if preview_url else None
        spotify_url = data.get("external_urls", {}).get("spotify") if isinstance(data, dict) else None

        # If Spotify didn't provide a preview, try iTunes fallback
        if not preview_url and track_metadata is not None:
            itunes_service = ItunesPreviewService()
            fallback_url, fallback_source = itunes_service.get_preview(track_metadata)
            if fallback_url:
                preview_url = fallback_url
                preview_source = fallback_source or "itunes"

        result: dict[str, Any] = {
            "spotify_id": spotify_track_id,
            "preview_url": preview_url,
            "album_image_url": image_url,
            "spotify_url": spotify_url,
            "preview_source": preview_source,
        }

        # Cache best-effort result
        try:
            self._cache[spotify_track_id] = (time.time(), result)
        except Exception:
            # Never fail because of caching problems
            pass

        return result
    
    def get_tracks_details(self, spotify_ids: list[str], track_metadata_map: dict[str, Track] | None = None) -> dict[str, dict[str, Any]]:
        """
        Fetch details for multiple Spotify track IDs using /v1/tracks?ids=id1,id2,... (max 50 ids per request).
        Returns a mapping spotify_id -> details dict (same shape as get_track_details returns).
        Uses caching, respects Spotify rate-limits (Retry-After) and applies small exponential backoff on 429s/network errors.
        """
        # normalize & dedupe preserving order
        seen = set()
        ids = [i for i in spotify_ids if isinstance(i, str) and not (i in seen or seen.add(i))]
        result: dict[str, dict[str, Any]] = {}

        # fast-return for cached items
        to_fetch: list[str] = []
        now = time.time()
        for sid in ids:
            cached = self._cache.get(sid)
            if cached and (now - cached[0]) < self._cache_ttl:
                result[sid] = cached[1]
            else:
                to_fetch.append(sid)

        if not to_fetch:
            return {sid: result.get(sid, {}) for sid in ids}

        token = self._get_access_token()
        # Spotify allows up to 50 ids per request
        CHUNK = 50
        max_attempts = int(current_app.config.get("SPOTIFY_BATCH_ATTEMPTS", 3))
        base_backoff = float(current_app.config.get("SPOTIFY_BASE_BACKOFF", 0.5))

        for i in range(0, len(to_fetch), CHUNK):
            chunk = to_fetch[i : i + CHUNK]
            url = "https://api.spotify.com/v1/tracks"
            params = {"ids": ",".join(chunk)}
            attempt = 1
            while attempt <= max_attempts:
                try:
                    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params, timeout=10)
                except requests.RequestException:
                    wait = base_backoff * (2 ** (attempt - 1))
                    time.sleep(wait)
                    attempt += 1
                    continue

                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    try:
                        wait = int(retry_after) if (retry_after and retry_after.isdigit()) else base_backoff * (2 ** (attempt - 1))
                    except Exception:
                        wait = base_backoff * (2 ** (attempt - 1))
                    time.sleep(wait)
                    attempt += 1
                    continue

                if not resp.ok:
                    # non-retryable HTTP error: break and treat as missing
                    current_app.logger.debug("Spotify batch request failed: %s %s", resp.status_code, resp.text)
                    break

                data = resp.json()
                tracks = data.get("tracks") or []
                for item in tracks:
                    if not item:
                        continue
                    sid = item.get("id")
                    album = item.get("album") or {}
                    images = album.get("images") or []
                    image_url = images[0]["url"] if images else None
                    preview_url = item.get("preview_url")
                    spotify_url = item.get("external_urls", {}).get("spotify")
                    preview_source = "spotify" if preview_url else None

                    # fallback to provided track metadata for preview if needed will be handled below
                    result[sid] = {
                        "spotify_id": sid,
                        "preview_url": preview_url,
                        "album_image_url": image_url,
                        "spotify_url": spotify_url,
                        "preview_source": preview_source,
                    }

                # break retry loop on success
                break

            # if after attempts we still have missing items in this chunk, fill with best-effort (itunes fallback)
            for sid in chunk:
                if sid in result and result[sid].get("preview_url"):
                    continue
                # best-effort: try iTunes fallback using provided track metadata if available
                tb_meta = (track_metadata_map or {}).get(sid) if track_metadata_map else None
                preview_url = None
                preview_source = None
                if tb_meta:
                    itunes = ItunesPreviewService()
                    fb_url, fb_src = itunes.get_preview(tb_meta)
                    if fb_url:
                        preview_url = fb_url
                        preview_source = fb_src or "itunes"

                # ensure at least an empty shape exists
                result.setdefault(sid, {
                    "spotify_id": sid,
                    "preview_url": preview_url,
                    "album_image_url": None,
                    "spotify_url": None,
                    "preview_source": preview_source,
                })

                # cache best-effort result
                try:
                    self._cache[sid] = (time.time(), result[sid])
                except Exception:
                    pass

        # preserve original requested order in returned mapping
        ordered = {sid: result.get(sid, {}) for sid in spotify_ids if sid in result}
        return ordered
