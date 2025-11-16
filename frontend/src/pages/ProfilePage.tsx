import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "../App.css";

import exploreWhite from "../assets/explore-white.png";
import profileBlack from "../assets/profile-black.png";
import searchWhite from "../assets/search-white.png";
import background from "../assets/profile-background.png";
import fallbackCover from "../assets/albumCover-1.png";
import removeIcon from "../assets/remove-icon.png";
import { useUserId } from "../useUserId";

const API_BASE = "http://127.0.0.1:5000/api";
const CARD_HEIGHT_PX = 670; // keep both rectangles same height

type PersonalityMetrics = {
  avg_energy: number;
  avg_valence: number;
  avg_popularity_norm: number;
  genre_diversity: number;
  top_genres: string[];
};

type PersonalityResponse = {
  username: string;
  archetypeId: string;
  title: string;
  shortDescription: string;
  longDescription: string;
  metrics: PersonalityMetrics;
  representativeTrackIds: string[];
};

type BackendTrack = {
  track_id: string;
  track_name: string;
  artists: string[];
  album_name?: string | null;
};

type LibrarySong = {
  trackId: string;
  title: string;
  artist: string;
  album: string;
  coverUrl: string;
};

function ProfilePage() {
  const [activeTab, setActiveTab] =
    useState<"explore" | "search" | "profile">("profile");

  const [personality, setPersonality] = useState<PersonalityResponse | null>(
    null
  );
  const [personalityLoading, setPersonalityLoading] = useState(false);
  const [personalityError, setPersonalityError] = useState<string | null>(null);

  const [library, setLibrary] = useState<LibrarySong[]>([]);
  const [libraryLoading, setLibraryLoading] = useState(false);
  const [libraryError, setLibraryError] = useState<string | null>(null);

  const [removedTrackIds, setRemovedTrackIds] = useState<Set<string>>(
  () => new Set());

  
  // useUserId returns { userId, setUserId }
  const rawUser = useUserId() as any;
  const username: string | null =
    typeof rawUser === "string" ? rawUser : rawUser?.userId ?? null;

  console.log("ProfilePage user debug:", { rawUser, username });

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

  // Load personality + library when username is available
  useEffect(() => {
    if (!username) return;

    const fetchPersonality = async () => {
      setPersonalityLoading(true);
      setPersonalityError(null);
      try {
        const res = await fetch(`${API_BASE}/personality`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username }),
        });

        if (!res.ok) {
          throw new Error(`Personality failed (${res.status})`);
        }

        const data = (await res.json()) as PersonalityResponse;
        setPersonality(data);
      } catch (err) {
        console.error("Failed to fetch personality:", err);
        setPersonalityError("Could not load your personality yet.");
      } finally {
        setPersonalityLoading(false);
      }
    };

    const fetchLibrary = async () => {
      setLibraryLoading(true);
      setLibraryError(null);
      try {
        const res = await fetch(
          `${API_BASE}/library?username=${encodeURIComponent(username)}`
        );
        if (!res.ok) {
          throw new Error(`Library failed (${res.status})`);
        }

        const data = await res.json();
        // Expecting { username, tracks: BackendTrack[] }
        const tracks = (data.tracks || []) as BackendTrack[];

        const enriched: LibrarySong[] = [];
        for (const t of tracks) {
          try {
            const enrRes = await fetch(
              `${API_BASE}/tracks/enriched?trackId=${encodeURIComponent(
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

        setLibrary(enriched);
      } catch (err) {
        console.error("Failed to fetch library:", err);
        setLibraryError("Could not load your library.");
      } finally {
        setLibraryLoading(false);
      }
    };

    fetchPersonality();
    fetchLibrary();
  }, [username]);

  // Optional: remove from UI only (no backend delete wired)
const handleRemoveFromLibrary = async (trackId: string) => {
  if (!username) {
    console.error("No username; cannot remove from library.", { username });
    alert("No username set — cannot remove from library.");
    return;
  }

  try {
    const res = await fetch(
      `${API_BASE}/library/${encodeURIComponent(
        trackId
      )}?username=${encodeURIComponent(username)}`,
      { method: "DELETE" }
    );

    if (!res.ok) {
      console.error("Remove from library failed with status", res.status);
      return;
    }

    // Mark as removed in UI (checkmark) – we keep the row but disable the button
    setRemovedTrackIds((prev) => {
      const next = new Set(prev);
      next.add(trackId);
      return next;
    });
  } catch (err) {
    console.error("Failed to remove from library:", err);
  }
};


  const displayName = username ?? "Username";

  // Turn longDescription with \n\n into paragraphs
  const renderLongDescription = () => {
    if (!personality?.longDescription) return null;
    return personality.longDescription.split("\n\n").map((chunk, idx) => (
      <p key={idx} style={{ marginBottom: "12px" }}>
        {chunk}
      </p>
    ));
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
        <h1 className="lexend">{displayName}</h1>

        <div
          className="profile-row"
          style={{
            display: "flex",
            gap: "40px",
            alignItems: "flex-start", // ensure both cards start at same top line
            justifyContent: "center",
            marginTop: "32px",
          }}
        >
          {/* Personality card */}
          <div
            className="personality-card"
            style={{
              flex: 1,
              minHeight: CARD_HEIGHT_PX,
              maxHeight: CARD_HEIGHT_PX,
              display: "flex",
              flexDirection: "column",
              padding: "24px 32px",
              borderRadius: "32px",
              backdropFilter: "blur(20px)",
              marginTop: 0, // override any global margin
            }}
          >
            {personalityLoading && (
              <div className="personality-text">Loading your vibes…</div>
            )}

            {!personalityLoading && personalityError && (
              <div className="personality-text">{personalityError}</div>
            )}

            {!personalityLoading && personality && (
              <>
                <div className="personality-title">{personality.title}</div>
                <div
                  className="personality-text"
                  style={{
                    marginTop: "16px",
                    overflowY: "hidden",
                    maxHeight: "100%",
                    paddingRight: "8px",
                    maxWidth: "540px",       // narrower text column
                    marginLeft: "auto",
                    marginRight: "auto",     // centers the column in the card
                    textAlign: "justify",
                  }}
                >
                  {renderLongDescription()}
                  {/* Optional: small metrics summary */}
                  <div style={{ marginTop: "16px", fontSize: "14px" }}>
                    <strong>Energy:</strong>{" "}
                    {personality.metrics.avg_energy.toFixed(2)} ·{" "}
                    <strong>Mood (valence):</strong>{" "}
                    {personality.metrics.avg_valence.toFixed(2)} ·{" "}
                    <strong>Mainstream:</strong>{" "}
                    {personality.metrics.avg_popularity_norm.toFixed(2)}
                    <br />
                    <strong>Genre diversity:</strong>{" "}
                    {personality.metrics.genre_diversity.toFixed(2)}
                    <br />
                    <strong>Top genres:</strong>{" "}
                    {personality.metrics.top_genres.join(", ")}
                  </div>
                </div>
              </>
            )}

            {!personalityLoading && !personality && !personalityError && (
              <div className="personality-text">
                Add a few songs to your library to unlock your music
                personality.
              </div>
            )}
          </div>

          {/* Library card */}
          <div
            className="library-card"
            style={{
              flex: 1,
              minHeight: CARD_HEIGHT_PX,
              maxHeight: CARD_HEIGHT_PX,
              display: "flex",
              flexDirection: "column",
              padding: "24px 32px",
              borderRadius: "32px",
              backdropFilter: "blur(20px)",
              marginTop: 0, // override any global margin
            }}
          >
            <div className="personality-title">Library</div>

            <div className="library-list">
              {libraryLoading && (
                <div className="personality-text">Loading your library…</div>
              )}

              {!libraryLoading && libraryError && (
                <div className="personality-text">{libraryError}</div>
              )}

              {!libraryLoading && !libraryError && library.length === 0 && (
                <div className="personality-text">
                  You don&apos;t have any saved tracks yet.
                </div>
              )}

                {!libraryLoading &&
                !libraryError &&
                library.length > 0 &&
                library.map((song) => {
                    const isRemoved = removedTrackIds.has(song.trackId);

                    return (
                    <div className="library-row" key={song.trackId}>
                        <img
                        src={song.coverUrl}
                        width="65px"
                        style={{ borderRadius: "10px", margin: "10px" }}
                        />
                        <div className="library-title">{song.title}</div>
                        <div className="library-text">{song.artist}</div>
                        <button
                        className={`button-white remove-button ${isRemoved ? "removed" : ""}`}
                        onClick={() => !isRemoved && handleRemoveFromLibrary(song.trackId)}
                        disabled={isRemoved}
                        >
                        {isRemoved ? (
                            <>
                            <span style={{ marginRight: 8 }}>✔</span>
                            Removed
                            </>
                        ) : (
                            <>
                            <img src={removeIcon} width="20" />
                            Remove
                            </>
                        )}
                        </button>
                    </div>
    );
  })}

            </div>
          </div>
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
              src={searchWhite}
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
              src={profileBlack}
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

export default ProfilePage;
