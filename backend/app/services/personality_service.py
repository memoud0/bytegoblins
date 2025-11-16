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
        """Build the exact prompt to send to the LLM based on the user's spec.

        The prompt instructs the model to return only the required JSON and to
        avoid mentioning numbers, algorithms, or how the inference was done.
        """
        # Build track lines
        track_lines: list[str] = []
        for t in top_tracks:
            artists = ", ".join(t.get("artists", [])) if t.get("artists") else "unknown artist"
            name = t.get("track_name", "unknown track")
            track_lines.append(f"{name} — {artists}")

        top_genres_str = ", ".join(metrics.get("top_genres", [])) if metrics.get("top_genres") else ", ".join([])

        prompt = """
You are generating a music-based personality profile for a user.

I still wanna keep the avg at the end, BUT DO NOT MENTION THEM IN THE PARAGRAPH
Tone:
- like a close friend reading their Spotify receipts out loud at 2 AM
- playful, a little teasing, very human
- funny without being cringe
- concise but vivid — QUALITY over quantity

Do NOT mention:
- numbers, scores, stats, averages, metrics, algorithms, or “your data”
- how anything was calculated or inferred
- “representative tracks” as a concept; just use them naturally

Base everything on:
- the genres
- the emotional vibe of the specific songs and artists
- the archetype seed (vibe direction, not a script)

You’re starting from this seed archetype:
- archetype_id: {archetype_id}
- title: {title}
- base_short: {base_short}
- base_long: {base_long}

You may slightly rename/refine the archetypeId and title if the vibe suggests it — keep it spiritually aligned.

Write a personality portrait that feels intuitive, warm, and eerily accurate. Focus on emotional tendencies, habits, little quirks, contradictions, “you seem like the kind of person who…” observations. Let the songs guide you. Stay concise and punchy.

Think: “you definitely have a soft spot for songs that feel like X,” “you give off ‘main character walking home at night’ energy,” “you pretend you’re chill but your playlist says otherwise,” etc.

Avoid long paragraphs; keep it tight and high-quality.

-----------------------------------------------------
USER: {username}

TRACKS THEY LOVE:
{tracks_block}

TOP GENRES:
{top_genres}

(You see the metrics below but NEVER reference them directly.)
- avg_energy: {avg_energy:.2f}
- avg_valence: {avg_valence:.2f}
- avg_popularity_norm: {avg_pop:.2f}
- genre_diversity: {genre_div:.2f}
-----------------------------------------------------

RETURN ONLY THIS JSON:

{{
  "archetypeId": "STRING_ID_LIKE_SUNLIT_GROOVE_PILOT",
  "title": "Short archetype name (2–5 words)",
  "shortDescription": "A fun, sharp 1-sentence vibe read.",
  "longDescription": "3–6 sentences describing their personality and emotional aesthetic based purely on the feel of their songs and genres. No stats. Funny, familiar, specific, but concise."
}}
    """.format(
            username=username,
            tracks_block="\n".join(track_lines),
            top_genres=top_genres_str,
            avg_energy=metrics.get("avg_energy", 0.5),
            avg_valence=metrics.get("avg_valence", 0.5),
            avg_pop=metrics.get("avg_popularity_norm", 0.5),
            genre_div=metrics.get("genre_diversity", 0.0),
            archetype_id=archetype_id,
            title=title,
            base_short=base_short,
            base_long=base_long,
        )
        return prompt

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
            # No LLM key available — produce a compact, friendly fallback that
            # follows the requested constraints (no numbers in prose, concise, playful).
            return self._fallback_personality(
                username=username,
                archetype_id=archetype_id,
                title=title,
                base_short=base_short,
                base_long=base_long,
                representative_tracks=representative_tracks,
                metrics=metrics,
            )

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
            return self._fallback_personality(
                username=username,
                archetype_id=archetype_id,
                title=title,
                base_short=base_short,
                base_long=base_long,
                representative_tracks=representative_tracks,
                metrics=metrics,
            )

    def _fallback_personality(
        self,
        username: str,
        archetype_id: str,
        title: str,
        base_short: str,
        base_long: str,
        representative_tracks: list[Track],
        metrics: PersonalityMetrics,
    ) -> PersonalityResult:
        """Rule-based fallback that respects the user's constraints.

        - No numeric stats in prose
        - Tone: close friend, playful, concise
        - Use genres and representative tracks naturally
        """
        # Build a punchy short description
        genres = metrics.top_genres or []
        genre_phrase = ", ".join(genres[:2]) if genres else None

        artists = [a for t in representative_tracks for a in (t.artists or [])][:3]
        artist_phrase = ", ".join(artists) if artists else None

        short_candidates: list[str] = []
        if genre_phrase and artist_phrase:
            short_candidates.append(f"A midnight mixtape person — {genre_phrase} leanings with a soft spot for {artist_phrase}.")
        if genre_phrase:
            short_candidates.append(f"You’ve got a {genre_phrase}-tilted heart with sneaky main-character energy.")
        if artist_phrase:
            short_candidates.append(f"You nod along to {artist_phrase} like it's a private joke.")
        short_description = short_candidates[0] if short_candidates else base_short

        # Build a 3-5 sentence long description without numbers
        sentences: list[str] = []
        # opener
        sentences.append(short_description)

        # habit/quirk line using tracks
        if representative_tracks:
            t = representative_tracks[0]
            s = f"You bookmark songs that feel like small scenes — {t.track_name} shows up when you want to feel seen."
            sentences.append(s)

        if genre_phrase:
            sentences.append(f"There’s a clear flavour in your queue: {genre_phrase}, which shows up when you need to switch moods fast.")
        else:
            sentences.append("Your taste slips between moods in a way that never feels random.")

        # little contradiction / tease
        sentences.append("You pretend you’re chill, but your playlist keeps giving away the part of you that never sleeps.")

        # close with a warm line
        sentences.append("Short, sharp, and oddly comforting — the kind of music that reads like a good late-night conversation.")

        # Keep it concise: 3-6 sentences (we already built several)
        long_description = " ".join(sentences[:6])

        representative_track_ids = [t.track_id for t in representative_tracks]

        return PersonalityResult(
            username=username,
            archetype_id=archetype_id,
            title=title,
            short_description=short_description,
            long_description=long_description,
            metrics=metrics,
            representative_track_ids=representative_track_ids,
        )
