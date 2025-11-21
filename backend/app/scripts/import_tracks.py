import os
import math
import pandas as pd

from dotenv import load_dotenv
from firebase_admin import credentials, firestore, initialize_app

load_dotenv()

SERVICE_ACCOUNT_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./byte.json")
PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
DATASET_PATH = os.getenv("DATASET_PATH", "./dataset.csv")

cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
app = initialize_app(cred, {"projectId": PROJECT_ID} if PROJECT_ID else None)
db = firestore.client()

def to_list_from_artists(raw):  # turn artists column into a Python list
    if isinstance(raw, list):
        return raw
    if not isinstance(raw, str):
        return []
    
    s = raw.strip()

    # crude parse
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
        parts = [p.strip().strip("'").strip('"') for p in s.split(",")]
        return [p for p in parts if p]
    else:
        # assume single artist name
        return [s]
    
def infer_genre_group(genre: str | None) -> str:

    if not genre:
        return "other"
    
    g = genre.lower()

    if "rock" in g:
        return "rock"
    if "metal" in g:
        return "metal"
    if "pop" in g:
        return "pop"
    if "hip hop" in g or "rap" in g or "trap" in g or "hop" in g:
        return "hiphop"
    if "r&b" in g or "soul" in g:
        return "rnb"
    if "electronic" in g or "edm" in g or "house" in g or "techno" in g or "dance" in g:
        return "electronic"
    if "jazz" in g:
        return "jazz"
    if "classical" in g or "orchestra" in g:
        return "classical"
    if "country" in g:
        return "country"
    if "latin" in g or "reggaeton" in g or "salsa" in g:
        return "latin"
    
    return "other"
    
def normalize_popularity(pop):    
    """
    Spotify popularity is usually 0–100. Normalize to 0–1.
    """

    try:
        if math.isnan(pop):
            return None
    except TypeError:
        pass

    try:
        p = float(pop)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, p / 100.0))


def normalize_tempo(tempo):
    """
    Rough 0–1 normalization for tempo.
    Assumes typical range ~60–200 BPM.
    """
    try:
        if math.isnan(tempo):
            return None
    except TypeError:
        pass

    try:
        t = float(tempo)
    except (TypeError, ValueError):
        return None

    # clamp 60–200 bpm to [0, 1]
    t_clamped = max(60.0, min(200.0, t))
    return (t_clamped - 60.0) / (200.0 - 60.0)


def import_tracks(limit: int | None = None, batch_size: int = 400):
    print(f"Loading dataset from: {DATASET_PATH}")
    df = pd.read_csv(DATASET_PATH)

    # If your column names differ, tweak these mappings:
    col_id = "id" if "id" in df.columns else "track_id"
    col_name = "name" if "name" in df.columns else "track_name"
    col_artists = "artists"
    col_album = "album" if "album" in df.columns else "album_name"
    col_pop = "popularity" if "popularity" in df.columns else None
    col_tempo = "tempo" if "tempo" in df.columns else None
    col_genre = "genre" if "genre" in df.columns else "track_genre"

    if limit:
        df = df.head(limit)

    total = len(df)
    print(f"Preparing to import {total} tracks…")

    batch = db.batch()
    batch_count = 0
    written = 0

    for idx, row in df.iterrows():
        track_id = str(row[col_id])

        track_name = str(row[col_name]) if not pd.isna(row[col_name]) else ""
        track_name_lowercase = track_name.lower()

        artists = to_list_from_artists(row[col_artists]) if col_artists in df.columns else []
        album_name = str(row[col_album]) if col_album in df.columns and not pd.isna(row[col_album]) else None

        popularity = row[col_pop] if col_pop and col_pop in df.columns else None
        popularity_norm = normalize_popularity(popularity) if popularity is not None else None

        tempo = row[col_tempo] if col_tempo and col_tempo in df.columns else None
        tempo_norm = normalize_tempo(tempo) if tempo is not None else None

        genre = str(row[col_genre]) if col_genre in df.columns and not pd.isna(row[col_genre]) else None
        genre_group = infer_genre_group(genre)

        doc_data = {
            "track_id": track_id,
            "track_name": track_name,
            "track_name_lowercase": track_name_lowercase,
            "artists": artists,
            "album_name": album_name,
            "popularity": float(popularity) if popularity is not None and not pd.isna(popularity) else None,
            "popularity_norm": popularity_norm,
            "tempo": float(tempo) if tempo is not None and not pd.isna(tempo) else None,
            "tempo_norm": tempo_norm,
            "track_genre": genre,
            "track_genre_group": genre_group,
        }

        # copy over all numeric audio features if present
        for col in [
            "duration_ms",
            "explicit",
            "danceability",
            "energy",
            "key",
            "loudness",
            "mode",
            "speechiness",
            "acousticness",
            "instrumentalness",
            "liveness",
            "valence",
            "time_signature",
        ]:
            if col in df.columns and not pd.isna(row[col]):
                # explicit is usually bool/int, keep it as is
                if col == "explicit":
                    doc_data[col] = bool(row[col]) if row[col] in [0, 1, True, False] else row[col]
                else:
                    doc_data[col] = float(row[col])

        doc_ref = db.collection("tracks").document(track_id)
        batch.set(doc_ref, doc_data)
        batch_count += 1
        written += 1

        if batch_count >= batch_size:
            print(f"Committing batch at row {idx} (total written: {written})…")
            batch.commit()
            batch = db.batch()
            batch_count = 0

    # Commit remaining
    if batch_count > 0:
        print(f"Committing final batch (total written: {written})…")
        batch.commit()

    print(f"Done. Total tracks written: {written}")


if __name__ == "__main__":
    # Change limit=None to import all rows.
    # Start with a small limit (like 50) to test first.
    import_tracks(limit=None)