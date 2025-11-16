from __future__ import annotations

from collections import Counter
from typing import Any, Iterable
import math
import os
import json

from openai import OpenAI

from app.firebase_client import get_firestore_client, server_timestamp
from app.models.personality import PersonalityMetrics, PersonalityResult
from app.models.track import Track
from app.services.library_service import LibraryService


class PersonalityService:
    def __init__(self) -> None:
        self.db = get_firestore_client()
        self.library_service = LibraryService()

        api_key = os.getenv("OPENAI_API_KEY")
        # if no key, client will raise on use; we guard before calling
        self._openai_client = OpenAI(api_key=api_key) if api_key else None

    # ---------- public API ----------

    def compute_for_user(self, username: str) -> PersonalityResult:
        username = username.lower()

        tracks = self.library_service.get_library_tracks(username)
        if not tracks:
            metrics = PersonalityMetrics(
                avg_energy=0.5,
                avg_valence=0.5,
                avg_popularity_norm=0.5,
                genre_diversity=0.0,
                top_genres=[],
            )
            result = self._build_archetype(username, metrics, [], use_llm=False)
            return result

        metrics = self._compute_metrics(tracks)
        representative_tracks = self._pick_representative_tracks(tracks)

        result = self._build_archetype(
            username=username,
            metrics=metrics,
            representative_tracks=representative_tracks,
            use_llm=True,
        )
        self._save_personality(username, result)
        return result

    # ---------- core logic ----------

    def _compute_metrics(self, tracks: Iterable[Track]) -> PersonalityMetrics:
        energies: list[float] = []
        valences: list[float] = []
        pops: list[float] = []
        genres: list[str] = []

        for t in tracks:
            if t.energy is not None:
                energies.append(float(t.energy))
            if t.valence is not None:
                valences.append(float(t.valence))
            if t.popularity_norm is not None:
                pops.append(float(t.popularity_norm))
            g = t.track_genre_group or t.track_genre
            if g:
                genres.append(g)

        def _avg(xs: list[float], default: float = 0.5) -> float:
            return sum(xs) / len(xs) if xs else default

        avg_energy = _avg(energies)
        avg_valence = _avg(valences)
        avg_pop_norm = _avg(pops)

        if genres:
            counts = Counter(genres)
            total = sum(counts.values())
            entropy = 0.0
            for c in counts.values():
                p = c / total
                entropy -= p * math.log(p + 1e-12)
            max_entropy = math.log(len(counts))
            diversity = entropy / max_entropy if max_entropy > 0 else 0.0
            top_genres = [g for g, _ in counts.most_common(3)]
        else:
            diversity = 0.0
            top_genres = []

        return PersonalityMetrics(
            avg_energy=avg_energy,
            avg_valence=avg_valence,
            avg_popularity_norm=avg_pop_norm,
            genre_diversity=diversity,
            top_genres=top_genres,
        )

    def _pick_representative_tracks(self, tracks: Iterable[Track]) -> list[Track]:
        """
        Pick a small set of representative tracks (as full Track objects),
        biased towards higher popularity so they're recognizable.
        """
        sorted_tracks = sorted(
            tracks,
            key=lambda t: (t.popularity_norm or 0.0),
            reverse=True,
        )
        return list(sorted_tracks[:6])

    def _build_archetype(
        self,
        username: str,
        metrics: PersonalityMetrics,
        representative_tracks: list[Track],
        use_llm: bool = True,
    ) -> PersonalityResult:
        energy = metrics.avg_energy
        valence = metrics.avg_valence
        mainstream = metrics.avg_popularity_norm
        diversity = metrics.genre_diversity

        if energy >= 0.65 and valence >= 0.55:
            archetype_id = "sunlit_groove_pilot"
            title = "Sunlit Groove Pilot"
            base_short = (
                "You move through life with warmth, momentum, and a taste for big, bright moments."
            )
        elif energy <= 0.45 and diversity >= 0.6:
            archetype_id = "dreamy_rhythm_alchemist"
            title = "Dreamy Rhythm Alchemist"
            base_short = (
                "You’re drawn to textured, emotional worlds — songs that feel like scenes, not just sounds."
            )
        elif mainstream >= 0.7:
            archetype_id = "chart_savvy_conductor"
            title = "Chart-Savvy Conductor"
            base_short = (
                "You have a radar for what hits — polished, catchy tracks that land instantly."
            )
        else:
            archetype_id = "midnight_side_streets"
            title = "Midnight Side Streets Curator"
            base_short = (
                "You live in the in-between: not fully mainstream, not fully obscure — just tastefully off-center."
            )

        base_long = self._build_base_long_description(title, base_short, metrics)

        if use_llm:
            llm_result = self._maybe_call_llm(
                username=username,
                metrics=metrics,
                archetype_id=archetype_id,
                title=title,
                base_short=base_short,
                base_long=base_long,
                representative_tracks=representative_tracks,
            )
            if llm_result is not None:
                return llm_result

        representative_track_ids = [t.track_id for t in representative_tracks]

        return PersonalityResult(
            username=username,
            archetype_id=archetype_id,
            title=title,
            short_description=base_short,
            long_description=base_long,
            metrics=metrics,
            representative_track_ids=representative_track_ids,
        )

    def _build_base_long_description(
        self,
        title: str,
        base_short: str,
        metrics: PersonalityMetrics,
    ) -> str:
        lines: list[str] = []
        lines.append(
            f"{title} fits you because of how your library balances mood, energy, and variety."
        )
        lines.append("")
        lines.append(
            f"Your average energy sits around {metrics.avg_energy:.2f}, "
            f"with a valence of {metrics.avg_valence:.2f}, which points to a mix of "
            f"{'uplifting' if metrics.avg_valence > 0.55 else 'moody, reflective'} textures."
        )
        if metrics.top_genres:
            top = ", ".join(metrics.top_genres)
            lines.append(f"Your top genres lean towards {top}, giving your listening a clear flavor.")
        lines.append(
            f"Your genre diversity score of {metrics.genre_diversity:.2f} "
            f"means you "
            f"{'wander widely across different sounds' if metrics.genre_diversity > 0.6 else 'tend to go deep within a few lanes you love'}."
        )
        lines.append("")
        lines.append(base_short)
        return "\n".join(lines)

    # ---------- persistence ----------

    def _save_personality(self, username: str, result: PersonalityResult) -> None:
        doc_ref = (
            self.db.collection("users")
            .document(username)
            .collection("analytics")
            .document("personality")
        )
        payload = result.to_dict()
        payload["computed_at"] = server_timestamp()
        doc_ref.set(payload, merge=True)

    # ---------- LLM integration ----------

    def _build_personality_prompt(
        self,
        username: str,
        metrics: dict[str, Any],
        top_tracks: list[dict[str, Any]],
        archetype_id: str,
        title: str,
        base_short: str,
        base_long: str,
    ) -> str:
        """
        Build a highly relatable, modern, personality-focused prompt for the LLM.

        metrics: {
            "avg_energy": float,
            "avg_valence": float,
            "avg_popularity_norm": float,
            "genre_diversity": float,
            "top_genres": [str, ...]
        }

        top_tracks: list of {
            "track_name": str,
            "artists": [str, ...],
            "genre": str | None
        }
        """
        avg_energy = metrics.get("avg_energy")
        avg_valence = metrics.get("avg_valence")
        avg_pop = metrics.get("avg_popularity_norm")
        genre_div = metrics.get("genre_diversity")
        top_genres = metrics.get("top_genres") or []

        track_lines: list[str] = []
        for t in top_tracks:
            name = t.get("track_name", "Unknown title")
            artists = ", ".join(t.get("artists") or [])
            genre = t.get("genre")
            if genre:
                track_lines.append(f"- {name} — {artists} (genre: {genre})")
            else:
                track_lines.append(f"- {name} — {artists}")

        top_genres_str = ", ".join(top_genres) if top_genres else "none"

        return f"""
You are generating a music-based personality profile for a user.

Your tone should feel like:
- a close friend psychoanalyzing their Spotify at 2 AM,
- a mix of Spotify Wrapped energy, astrology memes, and warm insight,
- playful but never cringe,
- modern, internet-aware, and specific.

Do NOT mention algorithms, math, scores, or how metrics were computed.
Do NOT moralize or judge taste.
Do NOT add markdown or extra commentary around the JSON.

Ground everything in:
- the numeric metrics,
- the top genres,
- and especially the specific tracks and artists below.

You are starting from this seed archetype:
- archetype_id: {archetype_id}
- title: {title}
- base_short: {base_short}
- base_long: {base_long}

It's OK to slightly rename/refine the archetypeId and title if the vibe suggests a better fit,
but keep it in the same spirit.

-----------------------------------------
USER: {username}

LISTENING PROFILE:
- Average energy: {avg_energy:.2f}
- Average mood / valence: {avg_valence:.2f}
- Mainstream level (popularity_norm): {avg_pop:.2f}
- Genre diversity (0–1): {genre_div:.2f}
- Top genres: {top_genres_str}

Representative tracks (these are strong signals of their taste):
{chr(10).join(track_lines)}

-----------------------------------------

Write a personality profile that feels emotionally intuitive and extremely relatable.
Interpret the *vibe* behind these metrics and songs — not just the numbers.
Make subtle, specific observations (e.g., “you definitely have a walking-home-at-night playlist”
or “you like songs that sound like they were recorded in a bedroom at 2 AM”).

Tone guidelines:
- casual, warm, slightly teasing, but respectful
- hyper-specific and vibe-driven
- confident, poetic in small doses, but not overdramatic
- feel like you're actually describing a real person’s musical identity
- celebrate contradictions (people love this)

-----------------------------------------
RETURN ONLY THIS JSON OBJECT, NOTHING ELSE:

{{
  "archetypeId": "STRING_ID_LIKE_SUNLIT_GROOVE_PILOT",
  "title": "Short human-readable archetype name (2–5 words)",
  "shortDescription": "1 sentence summarizing their vibe.",
  "longDescription": "3–6 sentences deeply interpreting their taste. Reference genres, mood, energy, mainstream-ness, and some of the representative tracks."
}}
-----------------------------------------
"""

    def _maybe_call_llm(
        self,
        username: str,
        metrics: PersonalityMetrics,
        archetype_id: str,
        title: str,
        base_short: str,
        base_long: str,
        representative_tracks: list[Track],
    ) -> PersonalityResult | None:
        """
        Use OpenAI chat completions to rewrite/upgrade the personality description.
        If no API key or if the call fails, return None and fall back to rule-based text.
        """
        if self._openai_client is None:
            return None

        metrics_dict = metrics.to_dict()

        # Build lightweight track payloads for the prompt
        top_tracks_payload: list[dict[str, Any]] = []
        for t in representative_tracks:
            top_tracks_payload.append(
                {
                    "track_name": t.track_name,
                    "artists": list(t.artists or []),
                    "genre": t.track_genre_group or t.track_genre,
                }
            )

        prompt = self._build_personality_prompt(
            username=username,
            metrics=metrics_dict,
            top_tracks=top_tracks_payload,
            archetype_id=archetype_id,
            title=title,
            base_short=base_short,
            base_long=base_long,
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a music psychologist who writes short, vivid, friendly, "
                    "highly relatable personality blurbs based on a user's listening habits. "
                    "You must respond with clean JSON only, following the requested schema exactly."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        try:
            resp = self._openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.8,
            )
            content = resp.choices[0].message.content or ""
            data = json.loads(content)

            final_archetype_id = data.get("archetypeId", archetype_id)
            final_title = data.get("title", title)
            final_short = data.get("shortDescription", base_short)
            final_long = data.get("longDescription", base_long)

            representative_track_ids = [t.track_id for t in representative_tracks]

            return PersonalityResult(
                username=username,
                archetype_id=final_archetype_id,
                title=final_title,
                short_description=final_short,
                long_description=final_long,
                metrics=metrics,
                representative_track_ids=representative_track_ids,
            )
        except Exception as exc:  # noqa: BLE001
            print("LLM personality generation failed:", exc)
            return None
