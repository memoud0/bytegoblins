# 🎶 Tuneder

A production-structured Flask + Firebase backend powering a Tinder-style music discovery experience.

<p align="center">
  <img src="https://github.com/user-attachments/assets/7ee2becb-b3db-47c5-bc46-bf41953739de" width="750" />
  <br/><br/>
  <img src="https://github.com/user-attachments/assets/c68b4ef9-e2b8-4fca-b54c-54803ce184d8" width="750" />
  <br/><br/>
  <img src="https://github.com/user-attachments/assets/b0e4abbd-49c8-4a64-9359-9572958df1e9" width="750" />
</p>


---

## Overview

Byte Goblins is a backend system designed for a music-matching web app where users swipe through songs, build a personal library, and receive hyper-personalized music recommendations generated from real Spotify audio features.

The project is intentionally structured like a real product backend: modular services, clean data models, scalable architecture, and a recommendation engine built on interpretable signals instead of opaque ML.

---

## Core Capabilities

### 🎧 Swipe-Based Music Recommender

Users swipe on an initial “seed” set of genre-diverse tracks. The backend learns preferences by analyzing:

- Genre affinity (likes vs. dislikes)
- Audio features such as energy, valence, tempo, danceability, acousticness, etc.
- Weighted positive and negative signals
- Search queries that hint at user intent

After enough swipes, the system transitions into a refined recommendation mode that generates a ranked list of tracks tailored to the user.

### Music Personality Profile

From the user’s library and aggregates, the system computes:

- Energy (average energy)
- Mood (average valence)
- Mainstream score (average popularity_norm)
- Genre diversity
- Top genres
- Representative tracks

These metrics feed into a personality archetype (e.g., “Vibrant Explorer”, “Chill Dreamer”), creating a compact summary of the user’s music identity.

### Intelligent Music Search

The backend includes a lightweight ranking engine that scores search matches using:

- Prefix match strength on track name
- Artist relevance
- Genre alignment with the user’s preferences
- Popularity as a tie-breaker

All searches are logged and can be used as additional taste signals.

### Persistent Music Library

Every liked or added track is stored in a structured user library. This library is used for:

- Displaying saved tracks
- Computing personality metrics
- Powering recommendations

---

## High-Level Architecture

Frontend: React + TypeScript  
Backend: Flask (Python)  
Database: Firebase Firestore (users, swipes, sessions, library, search history)  
Data: Spotify track dataset pre-ingested into Firestore (`tracks` collection)

The architecture is intentionally modular and mirrors modern backend design patterns.

---

## Backend Structure

Backend layout (service-oriented, app-factory style):

- backend/
  - app/
    - __init__.py – Flask app factory, CORS, Firestore initialization
    - config.py – Environment configuration
    - firebase_client.py – Firestore connection
    - models/ – Track, User, Session, Personality schemas/helpers
    - services/ – Core logic
    - routes/ – Flask blueprints (users, match, library, search, personality)
    - utils/ – validation, scoring helpers, small utilities
  - run.py – Application entry point
  - requirements.txt – Python dependencies

This structure separates routing, business logic, data access, and utilities, making the codebase easier to reason about and extend.

---

## Recommendation Engine

The refined recommender uses a blended scoring model:

- Genre affinity: derived from liked vs. disliked genres (positives weighted more than negatives)
- Feature similarity: Euclidean distance across normalized Spotify audio features
- Optional search bonus: small boost for tracks related to frequent user searches

Conceptually:

- Final score = 0.6 × genre_affinity + 0.4 × feature_similarity + search_bonus

This delivers surprisingly accurate music-taste modeling without requiring a dedicated ML model.

---

## Live Demo

**https://bytegoblins.vercel.app/**

