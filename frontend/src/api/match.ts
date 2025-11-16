import { API_URL } from "../api";

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
  }
  return (await response.json()) as T;
}

export async function createMatchSession(username: string): Promise<MatchSessionDto> {
  // use absolute API URL from environment
  const response = await fetch(`${API_URL}/api/match/sessions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username }),
  });
  return handleJson<MatchSessionDto>(response);
}

export async function fetchNextTrack(username: string, sessionId: string): Promise<NextTrackResponse> {
  const url = `${API_URL}/api/match/next?username=${encodeURIComponent(username)}&sessionId=${encodeURIComponent(
    sessionId
  )}`;
  const response = await fetch(url, { method: "GET" });
  return handleJson<NextTrackResponse>(response);
}

export async function submitSwipe(payload: SwipePayload): Promise<void> {
  const response = await fetch(`${API_URL}/api/match/swipe`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  await handleJson<unknown>(response);
}

export async function fetchTrackPreview(trackId: string): Promise<TrackPreviewPayload | null> {
  const url = `${API_URL}/api/tracks/enriched?trackId=${encodeURIComponent(trackId)}`;
  const response = await fetch(url);
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const message = typeof payload.error === "string" ? payload.error : `Preview failed with ${response.status}`;
    throw new Error(message);
  }
  const payload = (await response.json()) as EnrichedTrackResponse;
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
}
