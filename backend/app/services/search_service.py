# app/services/search_service.py
import os
import time
from typing import List, Dict

import requests
from firebase_admin import firestore as admin_firestore

from app.firebase_client import get_firestore_client, server_timestamp

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_MARKET = os.getenv("SPOTIFY_MARKET", "US")

# In-memory cache for Spotify app token
_spotify_token_cache: Dict[str, object] = {
    "access_token": None,
    "expires_at": 0.0,
}

# ---------- Scoring helpers ----------

def _compute_relevance_score(doc: Dict, query_terms: List[str]) -> float:
    """
    Simple local scoring based on:
    - track_name_lowercase
    - artists
    - genre
    - popularity_norm
    """
    name = (doc.get("track_name_lowercase") or "").lower()
    artists_text = " ".join(doc.get("artists") or []).lower()
    genre = (doc.get("track_genre") or "").lower()
    popularity_norm = float(doc.get("popularity_norm") or 0.0)

    score = 0.0

    for term in query_terms:
        if not term:
            continue

        # Track name: strong weight
        if name.startswith(term):
            score += 4.0
        elif term in name:
            score += 2.5

        # Artist: medium
        if term in artists_text:
            score += 1.5

        # Genre: small
        if term in genre:
            score += 0.5

    score += popularity_norm * 1.0
    return score


def _log_search_event(user_id: str, raw_query: str, normalized_query: str, results: List[Dict]) -> None:
    db = get_firestore_client()

    user_ref = db.collection("users").document(user_id)
    events_ref = user_ref.collection("search_events")

    top_ids = [r["trackId"] for r in results[:5]]

    events_ref.add(
        {
            "query": raw_query,
            "normalized_query": normalized_query,
            "num_results": len(results),
            "top_track_ids": top_ids,
            "created_at": server_timestamp(),
        }
    )

# ---------- Spotify helpers ----------

def _get_spotify_access_token() -> str:
    """
    Client credentials flow – used only by backend.
    Token is cached in memory.
    """
    now = time.time()
    cached_token = _spotify_token_cache.get("access_token")
    expires_at = float(_spotify_token_cache.get("expires_at") or 0.0)

    if cached_token and now < expires_at:
        return cached_token  # type: ignore[arg-type]

    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        raise RuntimeError("Missing SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET env vars")

    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    access_token = data["access_token"]
    expires_in = int(data.get("expires_in", 3600))

    _spotify_token_cache["access_token"] = access_token
    _spotify_token_cache["expires_at"] = now + expires_in - 60

    return access_token


def _spotify_search_tracks(query: str, limit: int = 10) -> List[Dict]:
    """
    Call Spotify /v1/search?type=track.
    Returns our unified track shape (source='spotify').
    """
    token = _get_spotify_access_token()

    resp = requests.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "q": query,
            "type": "track",
            "limit": limit,
            "market": SPOTIFY_MARKET,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    items = (data.get("tracks") or {}).get("items") or []

    results: List[Dict] = []

    for item in items:
        track_id = item["id"]
        name = item["name"]
        artists = [a["name"] for a in item.get("artists", [])]

        album = item.get("album") or {}
        images = album.get("images") or []
        image_url = images[0]["url"] if images else None

        popularity = item.get("popularity")
        popularity_norm = None
        if isinstance(popularity, (int, float)):
            popularity_norm = popularity / 100.0

        results.append(
            {
                "trackId": track_id,
                "trackName": name,
                "artists": artists,
                "albumName": album.get("name"),
                "imageUrl": image_url,
                "popularity": popularity,
                "popularityNorm": popularity_norm,
                "genre": None,
                "genreGroup": None,
                "score": 0.0,             # will set later
                "source": "spotify",
                "spotifyUrl": f"https://open.spotify.com/track/{track_id}",
            }
        )

    return results

# ---------- Main search orchestration ----------

def search_tracks(user_id: str, raw_query: str, limit: int = 20) -> List[Dict]:
    """
    Hybrid search:
      1) Firestore track_name_lowercase prefix search (+local scoring)
      2) If not enough results, fallback to Spotify
      3) Log search_events
    """
    db = get_firestore_client()

    q = (raw_query or "").strip()
    if not q:
        return []

    q_norm = q.lower()
    query_terms = q_norm.split()

    tracks_ref = db.collection("tracks")
    fs_query = (
        tracks_ref.where("track_name_lowercase", ">=", q_norm)
        .where("track_name_lowercase", "<=", q_norm + "\uf8ff")
        .limit(limit * 3)
    )

    snap = fs_query.get()

    firestore_results: List[Dict] = []
    existing_ids: set[str] = set()

    for doc in snap:
        data = doc.to_dict() or {}
        track_id = data.get("track_id") or doc.id
        existing_ids.add(track_id)

        score = _compute_relevance_score(data, query_terms)

        firestore_results.append(
            {
                "trackId": track_id,
                "trackName": data.get("track_name"),
                "artists": data.get("artists") or [],
                "albumName": data.get("album_name"),
                "imageUrl": data.get("image_url") or None,   # if you imported this
                "popularity": data.get("popularity"),
                "popularityNorm": data.get("popularity_norm"),
                "genre": data.get("track_genre"),
                "genreGroup": data.get("track_genre_group"),
                "score": score,
                "source": "firestore",
                "spotifyUrl": f"https://open.spotify.com/track/{track_id}",
            }
        )

    firestore_results.sort(key=lambda r: r["score"], reverse=True)

    results: List[Dict] = firestore_results[:limit]

    # 2) Spotify fallback for extra results
    if len(results) < limit:
        try:
            spotify_candidates = _spotify_search_tracks(q, limit=limit)
        except Exception:
            spotify_candidates = []

        spotify_results: List[Dict] = []
        for item in spotify_candidates:
            if item["trackId"] in existing_ids:
                continue
            item["score"] = 1.0  # below strong FS hits, above weak ones
            spotify_results.append(item)

        results.extend(spotify_results)
        results.sort(key=lambda r: r["score"], reverse=True)
        results = results[:limit]

    # 3) Log search event
    _log_search_event(user_id=user_id, raw_query=raw_query, normalized_query=q_norm, results=results)

    return results
