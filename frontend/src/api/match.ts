// Clean, single-definition match API helpers using central axios `api`.
import { api } from "./api";

export interface TrackDto {
  track_id: string;
  track_name: string;
  artists: string[];
  album_name?: string | null;
  track_genre?: string | null;
  track_genre_group?: string | null;
  popularity?: number | null;
  previewUrl?: string | null;
}

export interface MatchSessionDto {
  sessionId: string;
  username: string;
  seedTrackIds?: string[];
  seedCount?: number;
  phase: "seed" | "refined";
}

export interface NextTrackResponse {
  sessionId: string;
  phase: "seed" | "refined";
  status: "active" | "completed";
  done: boolean;
  track: TrackDto | null;
}

export interface SwipePayload {
  username: string;
  sessionId: string;
  trackId: string;
  direction: "like" | "dislike";
}

export interface TrackPreviewPayload {
  trackId: string;
  previewUrl: string | null;
  albumArtUrl?: string | null;
  previewSource?: string | null;
}

export interface SpotifyTrackMetadata {
  spotify_id: string;
  preview_url: string | null;
  album_image_url: string | null;
  spotify_url: string | null;
  preview_source?: string | null;
}

export interface EnrichedTrackResponse {
  track: TrackDto | null;
  spotify: SpotifyTrackMetadata | null;
  warning?: string;
}

export async function createMatchSession(username: string): Promise<MatchSessionDto> {
  const resp = await api.post<MatchSessionDto>(`/api/match/sessions`, { username });
  return resp.data;
}

export async function fetchNextTrack(username: string, sessionId: string): Promise<NextTrackResponse> {
  const resp = await api.get<NextTrackResponse>(`/api/match/next`, {
    params: { username, sessionId },
  });
  return resp.data;
}

export async function submitSwipe(payload: SwipePayload): Promise<void> {
  await api.post(`/api/match/swipe`, payload);
}

export async function fetchTrackPreview(trackId: string): Promise<TrackPreviewPayload | null> {
  try {
    const resp = await api.get<EnrichedTrackResponse>(`/api/tracks/enriched`, {
      params: { trackId },
    });
    const payload = resp.data;
    if (!payload.spotify) {
      return {
        trackId: payload.track?.track_id ?? trackId,
        previewUrl: null,
        albumArtUrl: null,
        previewSource: null,
      };
    }
    return {
      trackId: payload.track?.track_id ?? trackId,
      previewUrl: payload.spotify.preview_url,
      albumArtUrl: payload.spotify.album_image_url,
      previewSource: payload.spotify.preview_source ?? null,
    };
  } catch (err: any) {
    // If the backend returns 404 for missing preview, return null
    if (err?.response?.status === 404) {
      return null;
    }
    throw err;
  }
}
export interface TrackDto {
  track_id: string;
  track_name: string;
  artists: string[];
  album_name?: string | null;
  track_genre?: string | null;
  track_genre_group?: string | null;
  popularity?: number | null;
  previewUrl?: string | null;
}

export interface MatchSessionDto {
  sessionId: string;
  username: string;
  seedTrackIds?: string[];
  seedCount?: number;
  phase: "seed" | "refined";
}

export interface NextTrackResponse {
  sessionId: string;
  phase: "seed" | "refined";
  status: "active" | "completed";
  done: boolean;
  track: TrackDto | null;
}

export interface SwipePayload {
  username: string;
  sessionId: string;
  trackId: string;
  direction: "like" | "dislike";
}

export interface TrackPreviewPayload {
  trackId: string;
  previewUrl: string | null;
  albumArtUrl?: string | null;
  previewSource?: string | null;
}

export interface SpotifyTrackMetadata {
  spotify_id: string;
  preview_url: string | null;
  album_image_url: string | null;
  spotify_url: string | null;
  preview_source?: string | null;
}

export interface EnrichedTrackResponse {
  track: TrackDto | null;
  spotify: SpotifyTrackMetadata | null;
  warning?: string;
}

async function handleJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const message = typeof payload.error === "string" ? payload.error : `Request failed with ${response.status}`;
    throw new Error(message);

import { api, API_URL } from "./api";

export async function createMatchSession(username: string): Promise<MatchSessionDto> {
  const resp = await api.post<MatchSessionDto>(`/api/match/sessions`, { username });
  return resp.data;
}

export async function fetchNextTrack(username: string, sessionId: string): Promise<NextTrackResponse> {
import { api } from "./api";
    params: { username, sessionId },
  });
  return resp.data;
}

export async function submitSwipe(payload: SwipePayload): Promise<void> {
  await api.post(`/api/match/swipe`, payload);
}

export async function fetchTrackPreview(trackId: string): Promise<TrackPreviewPayload | null> {
  try {
    const resp = await api.get<EnrichedTrackResponse>(`/api/tracks/enriched`, {
      params: { trackId },
    });
    const payload = resp.data;
    if (!payload.spotify) {
      return {
        trackId: payload.track?.track_id ?? trackId,
        previewUrl: null,
        albumArtUrl: null,
        previewSource: null,
      };
    }
    return {
      trackId: payload.track?.track_id ?? trackId,
      previewUrl: payload.spotify.preview_url,
      albumArtUrl: payload.spotify.album_image_url,
      previewSource: payload.spotify.preview_source ?? null,
    };
  } catch (err: any) {
    // If the backend returns 404 for missing preview, return null
    if (err?.response?.status === 404) {
      return null;
    }
    throw err;
  }
}
