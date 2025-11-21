import os
import math
import json
import pandas as pd

# -------------------------------
# CONFIG
# -------------------------------
DATASET_PATH = "./dataset.csv"
OUTPUT_PATH = "./tracks_prepared.jsonl"


# -------------------------------
# HELPERS
# -------------------------------
def to_list_from_artists(raw):
    if isinstance(raw, list):
        return raw
    if not isinstance(raw, str):
        return []

    s = raw.strip()

    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
        parts = [p.strip().strip("'").strip('"') for p in s.split(",")]
        return [p for p in parts if p]
    return [s]


def infer_genre_group(g):
    if not g:
        return "other"

    g = g.lower()
    if "rock" in g: return "rock"
    if "metal" in g: return "metal"
    if "pop" in g: return "pop"
    if "hip hop" in g or "rap" in g or "trap" in g: return "hiphop"
    if "r&b" in g or "soul" in g: return "rnb"
    if any(w in g for w in ["electronic", "edm", "house", "techno", "dance"]): return "electronic"
    if "jazz" in g: return "jazz"
    if any(w in g for w in ["classical", "orchestra"]): return "classical"
    if "country" in g: return "country"
    if any(w in g for w in ["latin", "reggaeton", "salsa"]): return "latin"
    return "other"


def normalize_popularity(p):
    try:
        if math.isnan(p): return None
    except Exception:
        pass

    try:
        p = float(p)
        return max(0.0, min(1.0, p / 100.0))
    except:
        return None


def normalize_tempo(t):
    try:
        if math.isnan(t): return None
    except:
        pass

    try:
        t = float(t)
    except:
        return None

    t_clamped = max(60.0, min(200.0, t))
    return (t_clamped - 60.0) / 140.0


# -------------------------------
# MAIN EXPORT
# -------------------------------
def export_jsonl():
    df = pd.read_csv(DATASET_PATH)
    print(f"Loaded {len(df)} rows from {DATASET_PATH}")

    col_id = "id" if "id" in df.columns else "track_id"
    col_name = "name" if "name" in df.columns else "track_name"
    col_album = "album" if "album" in df.columns else "album_name"
    col_pop = "popularity"
    col_tempo = "tempo"
    col_genre = "genre" if "genre" in df.columns else "track_genre"

    with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
        for _, row in df.iterrows():
            track_id = str(row[col_id])
            name = str(row[col_name]) if not pd.isna(row[col_name]) else ""
            artists = to_list_from_artists(row["artists"]) if "artists" in df.columns else []

            popularity_norm = normalize_popularity(row[col_pop]) if col_pop in df.columns else None
            tempo_norm = normalize_tempo(row[col_tempo]) if col_tempo in df.columns else None
            genre = str(row[col_genre]) if col_genre in df.columns and not pd.isna(row[col_genre]) else None
            genre_group = infer_genre_group(genre)

            doc = {
                "track_id": track_id,
                "track_name": name,
                "track_name_lowercase": name.lower(),
                "artists": artists,
                "album_name": str(row[col_album]) if not pd.isna(row[col_album]) else None,
                "popularity": float(row[col_pop]) if col_pop in df.columns else None,
                "popularity_norm": popularity_norm,
                "tempo": float(row[col_tempo]) if col_tempo in df.columns else None,
                "tempo_norm": tempo_norm,
                "track_genre": genre,
                "track_genre_group": genre_group,
            }

            # copy numeric audio features if present
            numeric = [
                "duration_ms", "explicit", "danceability", "energy", "key",
                "loudness", "mode", "speechiness", "acousticness",
                "instrumentalness", "liveness", "valence", "time_signature"
            ]

            for col in numeric:
                if col in df.columns and not pd.isna(row[col]):
                    if col == "explicit":
                        doc[col] = bool(row[col])
                    else:
                        doc[col] = float(row[col])

            out.write(json.dumps(doc) + "\n")

    print(f"\nExport complete → {OUTPUT_PATH}")


if __name__ == "__main__":
    export_jsonl()
