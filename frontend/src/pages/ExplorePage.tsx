import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import "../App.css";
import { useUserId } from "../useUserId";
import { createMatchSession, fetchNextTrack, fetchTrackPreview, submitSwipe } from "../api/match";
import type { TrackDto } from "../api/match";
import AudioPreviewBar from "../components/AudioPreviewBar";

// import exploreBackground1 from "../assets/exploreBackground1.png";
// import exploreBackground2 from "../assets/exploreBackground2.png";
// import exploreBackground3 from "../assets/exploreBackground3.png";
import albumCover1 from "../assets/albumCover-1.png";
import albumCover2 from "../assets/albumCover-2.png";
import albumCover3 from "../assets/albumCover-3.png";
import dislikeDefault from "../assets/dislike-button-default.png";
import likeDefault from "../assets/like-button-default.png";
import exploreBlack from "../assets/explore-black.png";
import profileWhite from "../assets/profile-white.png";
import searchWhite from "../assets/search-white.png";

interface MatchSessionState {
  sessionId: string;
  phase: "seed" | "refined";
  status: "active" | "completed";
}

function ExplorePage() {
  const fallbackSongs = [
    { title: "Sienna", artist: "The Marías", image: albumCover1 },
    { title: "All I Need", artist: "Radiohead", image: albumCover2 },
    { title: "Selfless", artist: "The Strokes", image: albumCover3 },
  ];
  const fallbackDefaultImage = fallbackSongs[0].image;

  const { userId } = useUserId();
  const navigate = useNavigate();

  const [session, setSession] = useState<MatchSessionState | null>(null);
  const [currentTrack, setCurrentTrack] = useState<TrackDto | null>(null);
  const [albumArtUrl, setAlbumArtUrl] = useState<string | null>(null);
  const [previewSrc, setPreviewSrc] = useState<string | null>(null);
  const [swipeDirection, setSwipeDirection] = useState<"left" | "right" | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"explore" | "search" | "profile">("explore");
  const [isInitializing, setIsInitializing] = useState(false);
  const [isFetchingNext, setIsFetchingNext] = useState(false);
  const [isSwipePending, setIsSwipePending] = useState(false);
  const [cardVisible, setCardVisible] = useState(false);
  const [backgroundState, setBackgroundState] = useState<{
    sources: [string, string];
    activeIndex: 0 | 1;
  }>({
    sources: [fallbackDefaultImage, fallbackDefaultImage],
    activeIndex: 0,
  });
  const [isBgRemixing, setIsBgRemixing] = useState(false);

  const toastTimerRef = useRef<number | null>(null);
  const bgRemixTimerRef = useRef<number | null>(null);
  const latestTrackIdRef = useRef<string | null>(null);

  const showToast = useCallback((message: string) => {
    if (toastTimerRef.current) {
      window.clearTimeout(toastTimerRef.current);
    }
    setToastMessage(message);
    toastTimerRef.current = window.setTimeout(() => {
      setToastMessage(null);
      toastTimerRef.current = null;
    }, 3000);
  }, []);

  useEffect(() => {
    return () => {
      if (toastTimerRef.current) {
        window.clearTimeout(toastTimerRef.current);
      }
    };
  }, []);

  const runSwipeAnimation = useCallback(
    (dir: "left" | "right") =>
      new Promise<void>((resolve) => {
        setSwipeDirection(dir);
        window.setTimeout(() => {
          resolve();
        }, 400);
      }),
    []
  );

  const fetchPreviewForTrack = useCallback(async (track: TrackDto) => {
    const requestingTrackId = track.track_id;
    try {
      const preview = await fetchTrackPreview(requestingTrackId);
      if (latestTrackIdRef.current !== requestingTrackId) {
        return;
      }
      setPreviewSrc(preview?.previewUrl || null);
      if (preview?.albumArtUrl) {
        setAlbumArtUrl(preview.albumArtUrl);
      } else {
        setAlbumArtUrl(null);
      }
    } catch (err) {
      console.warn("Failed to load preview:", err);
      if (latestTrackIdRef.current === requestingTrackId) {
        setPreviewSrc(null);
        setAlbumArtUrl(null);
      }
    }
  }, []);

  const loadNextTrack = useCallback(
    async (sessionId: string) => {
      if (!userId) {
        return;
      }
      setIsFetchingNext(true);
      setCardVisible(false);
      try {
        const next = await fetchNextTrack(userId, sessionId);
        const nextSession: MatchSessionState = {
          sessionId: next.sessionId,
          phase: next.phase,
          status: next.status,
        };
        setSession(nextSession);

        if (!next.track) {
          setCurrentTrack(null);
          latestTrackIdRef.current = null;
          setPreviewSrc(null);
          setAlbumArtUrl(null);
          showToast("You're caught up for now. Start a new session soon!");
          setSwipeDirection(null);
          setCardVisible(true);
          return;
        }

        setCurrentTrack(next.track);
        latestTrackIdRef.current = next.track.track_id;
        setPreviewSrc(null);
        setAlbumArtUrl(null);
        await fetchPreviewForTrack(next.track);
        requestAnimationFrame(() => {
          setSwipeDirection(null);
          setCardVisible(true);
        });
      } catch (err) {
        console.error("Failed to load next track:", err);
        showToast(err instanceof Error ? err.message : "Unable to load the next song.");
        setSwipeDirection(null);
        setCardVisible(true);
      } finally {
        setIsFetchingNext(false);
      }
    },
    [userId, fetchPreviewForTrack, showToast]
  );

  const initializeSession = useCallback(async () => {
    if (!userId) {
      return;
    }
    setIsInitializing(true);
    try {
      const created = await createMatchSession(userId);
      const initialSession: MatchSessionState = {
        sessionId: created.sessionId,
        phase: created.phase || "seed",
        status: "active",
      };
      setSession(initialSession);
      setCardVisible(false);
      await loadNextTrack(created.sessionId);
    } catch (err) {
      console.error("Failed to start session:", err);
      showToast(err instanceof Error ? err.message : "Unable to start a session right now.");
    } finally {
      setIsInitializing(false);
    }
  }, [userId, loadNextTrack, showToast]);

  useEffect(() => {
    if (!userId) {
      navigate("/", { replace: true });
      return;
    }
    initializeSession();
  }, [userId, navigate, initializeSession]);

  const handleSwipeAction = useCallback(
    async (direction: "like" | "dislike") => {
      if (!session || !currentTrack || !userId || isSwipePending) {
        return;
      }
      setIsSwipePending(true);
      setCardVisible(false);
      const swipeDir = direction === "like" ? "right" : "left";
      const animationPromise = runSwipeAnimation(swipeDir);
      const swipePromise = submitSwipe({
        username: userId,
        sessionId: session.sessionId,
        trackId: currentTrack.track_id,
        direction,
      });

      try {
        await Promise.all([swipePromise, animationPromise]);
        if (direction === "like") {
          showToast(`${currentTrack.track_name} was added to your library!`);
        }
        await loadNextTrack(session.sessionId);
      } catch (err) {
        console.error("Swipe failed:", err);
        showToast(err instanceof Error ? err.message : "Unable to process that swipe. Try again.");
        setSwipeDirection(null);
        setCardVisible(true);
      } finally {
        setIsSwipePending(false);
      }
    },
    [session, currentTrack, userId, isSwipePending, runSwipeAnimation, showToast, loadNextTrack]
  );

  const handleDislike = () => {
    if (isInitializing || isFetchingNext || isSwipePending || !currentTrack || !session) {
      return;
    }
    handleSwipeAction("dislike");
  };

  const handleLike = () => {
    if (isInitializing || isFetchingNext || isSwipePending || !currentTrack || !session) {
      return;
    }
    handleSwipeAction("like");
  };

  const normalizeArtistNames = useCallback((artists?: string[]) => {
    if (!artists || artists.length === 0) {
      return "";
    }
    const normalized: string[] = [];
    artists.forEach((artist) => {
      if (!artist) {
        return;
      }
      const segments = artist.split(";").map((segment) => segment.trim()).filter(Boolean);
      if (segments.length) {
        normalized.push(...segments);
      } else {
        normalized.push(artist.trim());
      }
    });
    return normalized.join(", ");
  }, []);

  const currentFallbackIndex = currentTrack ? currentTrack.track_id.length % fallbackSongs.length : 0;
  const fallbackImage = fallbackSongs[currentFallbackIndex].image;
  const songTitle = currentTrack ? currentTrack.track_name : "";
  const songArtist = currentTrack ? normalizeArtistNames(currentTrack.artists) : "";
  const nextBgImage = albumArtUrl || fallbackImage;
  const hasTrackLoaded = Boolean(currentTrack);
  const cardClassName = [
    "music-card",
    "explore-card",
    swipeDirection ? (swipeDirection === "left" ? "left" : "right") : "",
    hasTrackLoaded ? (cardVisible ? "card-visible" : "card-hidden") : "music-card--empty",
  ]
    .filter(Boolean)
    .join(" ");
    const isInteractionDisabled = !hasTrackLoaded || isInitializing || isFetchingNext || isSwipePending;

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

  useEffect(() => {
    const resolvedBgImage = nextBgImage;
    setBackgroundState((prev) => {
      const nextIndex = prev.activeIndex === 0 ? 1 : 0;
      const nextSources = [...prev.sources] as [string, string];
      nextSources[nextIndex] = resolvedBgImage;
      return {
        sources: nextSources,
        activeIndex: nextIndex,
      };
    });

    setIsBgRemixing(true);
    if (bgRemixTimerRef.current) {
      window.clearTimeout(bgRemixTimerRef.current);
    }
    bgRemixTimerRef.current = window.setTimeout(() => {
      setIsBgRemixing(false);
      bgRemixTimerRef.current = null;
    }, 1100);

    return () => {
      if (bgRemixTimerRef.current) {
        window.clearTimeout(bgRemixTimerRef.current);
        bgRemixTimerRef.current = null;
      }
    };
  }, [nextBgImage]);

  return (
    <div className="page-wrapper explore-page" data-remixing={isBgRemixing ? "true" : "false"}>
      <div className="explore-background">
        {backgroundState.sources.map((src, index) => (
          <img
            key={`bg-layer-${index}`}
            className="explore-bg-layer"
            data-active={backgroundState.activeIndex === index ? "true" : "false"}
            data-remixing={isBgRemixing && backgroundState.activeIndex === index ? "true" : "false"}
            src={src}
            alt=""
          />
        ))}
      </div>

      {toastMessage && <div className="toast lexend">{toastMessage}</div>}

      <div className="content-explorer">
        <h1 className="lexend-explorer">Explore</h1>

        <div className={`${cardClassName} explore-card`}>
          {hasTrackLoaded ? (
            <>
              <div className="explore-card__cover">
                <img className="album-cover explore-album" src={nextBgImage} alt={`${songTitle} album cover`} />
              </div>

              <div className="explore-card__details">
                <div className="song-title">{songTitle}</div>
                <div className="song-artist">{songArtist}</div>

                <AudioPreviewBar previewUrl={previewSrc} disabled={isInteractionDisabled} />
              </div>

              <div className="action-button-row-explorer">
                <div className="dislike-button-explorer" onClick={handleDislike} aria-disabled={isInteractionDisabled}>
                  <img src={dislikeDefault} width="100" />
                </div>

                <div className="like-button" onClick={handleLike} aria-disabled={isInteractionDisabled}>
                  <img src={likeDefault} width="100" />
                </div>
              </div>
            </>
          ) : (
            <div className="music-card__loading">
              <div className="music-card__spinner" />
              <p className="music-card__loading-text lexend">Finding your next match...</p>
            </div>
          )}
        </div>

        <div className="menu">
          <button
            id="exploreButton"
            className={`menu-button ${activeTab !== "explore" ? "not-current" : ""}`}
            onClick={goToExplore}
          >
            <img src={exploreBlack} width="20" style={{ paddingRight: "10px" }} />
            Explore
          </button>

          <button
            id="searchButton"
            className={`menu-button ${activeTab !== "search" ? "not-current" : ""}`}
            onClick={goToSearch}
          >
            <img src={searchWhite} width="20" style={{ paddingRight: "10px" }} />
            Search
          </button>

          <button
            id="profileButton"
            className={`menu-button ${activeTab !== "profile" ? "not-current" : ""}`}
            onClick={goToProfile}
          >
            <img src={profileWhite} width="20" style={{ paddingRight: "10px" }} />
            My profile
          </button>
        </div>
      </div>
    </div>
  );
}


export default ExplorePage;
