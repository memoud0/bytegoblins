import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../App.css";

import exploreWhite from "../assets/explore-white.png";
import profileWhite from "../assets/profile-white.png";
import searchBlack from "../assets/search-black.png";
import background from "../assets/search-background.png";
import addIcon from "../assets/add-icon-black.png";
import fallbackCover from "../assets/albumCover-1.png";
import { useUserId } from "../useUserId";

const API_BASE = import.meta.env.VITE_API_BASE;

type BackendTrack = {
  track_id: string;
  track_name: string;
  artists: string[];
  album_name?: string | null;
  popularity_norm?: number | null;
};

type SearchResponse = {
  username: string | null;
  query: string;
  searchEventId: string | null;
  tracks: BackendTrack[];
};

type EnrichedSong = {
  trackId: string;
  title: string;
  artist: string;
  album: string;
  coverUrl: string;
};

function SearchPage() {
  const [activeTab, setActiveTab] =
    useState<"explore" | "search" | "profile">("search");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<EnrichedSong[]>([]);
  const [searchEventId, setSearchEventId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [addedTrackIds, setAddedTrackIds] = useState<Set<string>>(
    () => new Set()
  );

  // useUserId returns { userId, setUserId }
  const rawUser = useUserId() as any;
  const username: string | null =
    typeof rawUser === "string" ? rawUser : rawUser?.userId ?? null;

  console.log("SearchPage user debug:", { rawUser, username });

  const navigate = useNavigate();

  const goToExplore = () => {
    setActiveTab("explore");
    navigate("/explore");
  };

  const goToSearch = () => {
    setActiveTab("search");
    navigate("/search");
  };

  const goToProfile = () => {
    setActiveTab("profile");
    navigate("/profile");
  };

  const handleSearch = async () => {
    const q = query.trim();
    if (!q) return;

    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (username) params.set("username", username);
      params.set("q", q);
      params.set("limit", "4");

      const res = await fetch(`${API_BASE}/api/songs/search?${params.toString()}`);
      if (!res.ok) {
        throw new Error(`Search failed (${res.status})`);
      }

      const data = (await res.json()) as SearchResponse;
      setSearchEventId(data.searchEventId);

      const enriched: EnrichedSong[] = [];
      for (const t of data.tracks) {
        try {
          const enrRes = await fetch(
            `${API_BASE}/api/tracks/enriched?trackId=${encodeURIComponent(
              t.track_id
            )}`
          );
          const enrData = await enrRes.json();
          const cover =
            enrData?.spotify?.album_image_url ??
            enrData?.track?.album_image_url ??
            fallbackCover;

          enriched.push({
            trackId: t.track_id,
            title: t.track_name,
            artist: (t.artists && t.artists.join(", ")) || "Unknown artist",
            album: t.album_name || "",
            coverUrl: cover,
          });
        } catch {
          enriched.push({
            trackId: t.track_id,
            title: t.track_name,
            artist: (t.artists && t.artists.join(", ")) || "Unknown artist",
            album: t.album_name || "",
            coverUrl: fallbackCover,
          });
        }
      }

      setResults(enriched);
      setAddedTrackIds(new Set());
    } catch (err: any) {
      console.error("Search error:", err);
      setError("Something went wrong searching. Try again.");
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

    const handleAddToLibrary = async (song: EnrichedSong) => {
    if (!username) {
        console.error("No username; cannot like / add to library.", {
        rawUser,
        username,
        });
        alert("No username set — cannot like this song.");
        return;
    }

    if (addedTrackIds.has(song.trackId)) {
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/api/match/like`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            username,
            trackId: song.trackId,
            source: "search", // or "manual" if you want
        }),
        });

        if (!res.ok) {
        console.error("Like-from-search failed with status", res.status);
        return;
        }

        // Mark as added/liked in UI
        setAddedTrackIds((prev) => {
        const next = new Set(prev);
        next.add(song.trackId);
        return next;
        });
    } catch (err) {
        console.error("Failed to like/add via /match/like:", err);
    }
    };


  return (
    <div className="page-wrapper">
      <div
        style={{
          backgroundImage: `url(${background})`,
          backgroundSize: "cover",
          backgroundRepeat: "no-repeat",
          backgroundPosition: "center",
          position: "absolute",
          top: 0,
          left: 0,
          height: "100vh",
          width: "100vw",
          zIndex: -1,
        }}
      ></div>

      <div className="content">
        <h1 className="lexend">Search</h1>

        <div className="search-row">
          <input
            id="searchBar"
            className="lexend"
            type="text"
            placeholder="Look for your favourite songs . . ."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            style={{
              width: "100%",
            }}
          />

          <button
            className="button-white"
            style={{ padding: "12px" }}
            onClick={handleSearch}
            disabled={loading || !query.trim()}
          >
            <img src={searchBlack} style={{ width: "24px" }} />
          </button>
        </div>

        {error && (
          <div style={{ marginTop: "16px", color: "#ffd2d2" }}>{error}</div>
        )}

        <div className="results-grid-search">
          {results.map((song) => {
            const isAdded = addedTrackIds.has(song.trackId);
            return (
              <div
                key={song.trackId}
                className="music-card-search"
                style={{ borderRadius: "40px" }}
              >
                <img
                  className="album-cover-search"
                  src={song.coverUrl}
                  style={{
                    width: "220px",
                    margin: "25px",
                  }}
                />
                <div className="song-title-search">{song.title}</div>
                <div className="song-artist-search">{song.artist}</div>
                <button
                  className={`button-white add-button ${
                    isAdded ? "added" : ""
                  }`}
                  onClick={() => !isAdded && handleAddToLibrary(song)}
                  disabled={isAdded}
                >
                  {isAdded ? (
                    <>
                      <span style={{ marginRight: 8 }}>✔</span>
                      Added
                    </>
                  ) : (
                    <>
                      <img
                        src={addIcon}
                        width="20"
                        style={{ paddingRight: "10px" }}
                      />
                      Add to library
                    </>
                  )}
                </button>
              </div>
            );
          })}
        </div>

        <div className="menu">
          <button
            id="exploreButton"
            className={`menu-button ${
              activeTab !== "explore" ? "not-current" : ""
            }`}
            onClick={goToExplore}
          >
            <img
              src={exploreWhite}
              width="20"
              style={{ paddingRight: "10px" }}
            />
            Explore
          </button>

          <button
            id="searchButton"
            className={`menu-button ${
              activeTab !== "search" ? "not-current" : ""
            }`}
            onClick={goToSearch}
          >
            <img
              src={searchBlack}
              width="20"
              style={{ paddingRight: "10px" }}
            />
            Search
          </button>

          <button
            id="profileButton"
            className={`menu-button ${
              activeTab !== "profile" ? "not-current" : ""
            }`}
            onClick={goToProfile}
          >
            <img
              src={profileWhite}
              width="20"
              style={{ paddingRight: "10px" }}
            />
            My profile
          </button>
        </div>
      </div>
    </div>
  );
}

export default SearchPage;
