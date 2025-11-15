from __future__ import annotations

from statistics import mean

from app.models import PersonalityMetrics, PersonalityResult, Track
from app.services.library_service import LibraryService
from app.services.recommendation_service import RecommendationService


class PersonalityService:
    def __init__(self) -> None:
        self.library_service = LibraryService()
        self.recommendation_service = RecommendationService()

    def generate(self, username: str) -> PersonalityResult:
        library_tracks = self.library_service.get_library_tracks(username)
        if not library_tracks:
            raise ValueError("Library is empty. Add songs to unlock your personality profile.")

        metrics = self._compute_metrics(library_tracks)
        top_genres = self.recommendation_service.compute_library_based_top_genres(library_tracks)
        representative_tracks = self._select_representative_tracks(library_tracks, top_genres)
        archetype = self._determine_archetype(metrics)

        return PersonalityResult(
            archetype_id=archetype["id"],
            title=archetype["title"],
            one_liner=archetype["one_liner"],
            summary=archetype["summary"],
            metrics=metrics,
            top_genres=top_genres,
            representative_tracks=representative_tracks,
        )

    def _compute_metrics(self, tracks: list[Track]) -> PersonalityMetrics:
        def collect(field: str) -> list[float]:
            values: list[float] = []
            for track in tracks:
                value = getattr(track, field, None)
                if value is not None:
                    values.append(float(value))
            return values

        energy_values = collect("energy")
        mood_values = collect("valence")
        mainstream_values = collect("popularity_norm")

        genres = [track.track_genre or track.track_genre_group for track in tracks if track.track_genre or track.track_genre_group]
        unique_genres = len(set(genres))
        diversity = unique_genres / max(len(tracks), 1)
        diversity = min(diversity, 1.0)

        metrics = PersonalityMetrics(
            energy=_safe_mean(energy_values),
            mood=_safe_mean(mood_values),
            mainstream=_safe_mean(mainstream_values),
            diversity=diversity,
        )
        return metrics

    def _determine_archetype(self, metrics: PersonalityMetrics) -> dict[str, str]:
        if metrics.energy > 0.65 and metrics.diversity > 0.5:
            return {
                "id": "VIBRANT_EXPLORER",
                "title": "Vibrant Explorer",
                "one_liner": "You chase energy and chase new genres nonstop.",
                "summary": "High-energy sounds and adventurous taste define you. You thrive on bold beats and unexpected finds.",
            }

        if metrics.mood < 0.4 and metrics.energy < 0.5:
            return {
                "id": "CHILL_DREAMER",
                "title": "Chill Dreamer",
                "one_liner": "Soft pulses and mellow moods are your comfort zone.",
                "summary": "Lush pads, lo-fi textures, and dreamy vocals are your go-to ingredients for deep focus and reflection.",
            }

        if metrics.mainstream > 0.7:
            return {
                "id": "MAINSTREAM_MAVEN",
                "title": "Mainstream Maven",
                "one_liner": "You love the crowd-pleasers and turn them into anthems.",
                "summary": "You dig the tunes everyone sings along to, but the way you curate them feels distinctly yours.",
            }

        return {
            "id": "BALANCED_CURATOR",
            "title": "Balanced Curator",
            "one_liner": "A blend of moods, eras, and vibes keeps your playlists timeless.",
            "summary": "You know how to mix upbeat gems with introspective favorites, making you the dependable DJ for any room.",
        }

    def _select_representative_tracks(self, tracks: list[Track], top_genres: list[str], limit: int = 4) -> list[Track]:
        def sort_key(track: Track) -> tuple[float, float]:
            return (float(track.popularity_norm or 0), float(track.popularity or 0))

        preferred = [track for track in tracks if (track.track_genre or track.track_genre_group) in top_genres]
        preferred.sort(key=sort_key, reverse=True)

        if len(preferred) < limit:
            remaining = [track for track in tracks if track not in preferred]
            remaining.sort(key=sort_key, reverse=True)
            preferred.extend(remaining[: limit - len(preferred)])

        return preferred[:limit]


def _safe_mean(values: list[float]) -> float:
    return float(mean(values)) if values else 0.0
