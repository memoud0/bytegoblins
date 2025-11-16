import { useCallback, useEffect, useMemo, useRef, useState, type ChangeEvent } from "react";

interface AudioPreviewBarProps {
  previewUrl: string | null;
  disabled?: boolean;
}

const formatTime = (seconds: number): string => {
  if (!Number.isFinite(seconds) || seconds <= 0) {
    return "0:00";
  }
  const rounded = Math.floor(seconds);
  const mins = Math.floor(rounded / 60);
  const secs = rounded % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};

function AudioPreviewBar({ previewUrl, disabled = false }: AudioPreviewBarProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isSeeking, setIsSeeking] = useState(false);
  const canPlay = Boolean(previewUrl) && !disabled;

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) {
      return;
    }
    if (!previewUrl) {
      audio.pause();
      audio.removeAttribute("src");
      setIsPlaying(false);
      setProgress(0);
      setDuration(0);
      return;
    }
    audio.src = previewUrl;
    audio.currentTime = 0;
    setProgress(0);
    setIsPlaying(false);
    const playAfterLoad = () => {
      audio
        .play()
        .then(() => setIsPlaying(true))
        .catch(() => setIsPlaying(false));
    };
    if (audio.readyState >= 2) {
      playAfterLoad();
    } else {
      audio.load();
      audio.addEventListener("canplay", playAfterLoad, { once: true });
    }

    return () => {
      audio.removeEventListener("canplay", playAfterLoad);
    };
  }, [previewUrl]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) {
      return undefined;
    }

    const handleLoaded = () => setDuration(audio.duration || 0);
    const handleTimeUpdate = () => {
      if (!isSeeking) {
        setProgress(audio.currentTime);
      }
    };
    const handleEnded = () => {
      setIsPlaying(false);
      setProgress(audio.duration || 0);
    };

    audio.addEventListener("loadedmetadata", handleLoaded);
    audio.addEventListener("timeupdate", handleTimeUpdate);
    audio.addEventListener("ended", handleEnded);

    return () => {
      audio.removeEventListener("loadedmetadata", handleLoaded);
      audio.removeEventListener("timeupdate", handleTimeUpdate);
      audio.removeEventListener("ended", handleEnded);
    };
  }, [isSeeking]);

  const progressPercent = useMemo(() => {
    if (!duration) {
      return 0;
    }
    return Math.min(100, Math.max(0, (progress / duration) * 100));
  }, [duration, progress]);

  const togglePlayback = useCallback(() => {
    const audio = audioRef.current;
    if (!audio || !canPlay) {
      return;
    }
    if (audio.paused) {
      audio
        .play()
        .then(() => setIsPlaying(true))
        .catch(() => setIsPlaying(false));
    } else {
      audio.pause();
      setIsPlaying(false);
    }
  }, [canPlay]);

  const handleSeek = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      const audio = audioRef.current;
      if (!audio || !canPlay) {
        return;
      }
      const value = Number(event.target.value);
      const newTime = (value / 100) * (duration || 0);
      setProgress(newTime);
      if (audio.readyState >= 1) {
        audio.currentTime = newTime;
      }
    },
    [canPlay, duration]
  );

  const startSeeking = useCallback(() => {
    setIsSeeking(true);
  }, []);

  const endSeeking = useCallback(() => {
    const audio = audioRef.current;
    setIsSeeking(false);
    if (audio && canPlay && audio.paused && progress > 0) {
      audio
        .play()
        .then(() => setIsPlaying(true))
        .catch(() => setIsPlaying(false));
    }
  }, [canPlay, progress]);

  return (
    <div className="audio-preview lexend">
      <button
        type="button"
        className="audio-preview__play"
        onClick={togglePlayback}
        disabled={!canPlay}
        aria-label={isPlaying ? "Pause preview" : "Play preview"}
      >
        <span className={`audio-preview__icon ${isPlaying ? "pause" : "play"}`} />
      </button>
      <div className="audio-preview__timeline">
        <input
          type="range"
          min={0}
          max={100}
          step={0.1}
          value={progressPercent}
          onChange={handleSeek}
          onMouseDown={startSeeking}
          onTouchStart={startSeeking}
          onMouseUp={endSeeking}
          onTouchEnd={endSeeking}
          disabled={!canPlay}
        />
        <div className="audio-preview__time-row">
          <span>{formatTime(progress)}</span>
          <span>{formatTime(duration)}</span>
        </div>
        {!canPlay && <div className="audio-preview__empty">Preview not available</div>}
      </div>
      <audio ref={audioRef} hidden />
    </div>
  );
}

export default AudioPreviewBar;
