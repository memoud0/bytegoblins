import { useEffect, useState } from 'react'
// import reactLogo from './assets/react.svg'
// import viteLogo from '/vite.svg'
import "../App.css";
import { useUserId } from "../useUserId";
import { db } from "../firebase";
import {
  collection,
  addDoc,
  getDocs,
  query,
  where,
  Timestamp,
} from "firebase/firestore";

// import exploreBackground1 from "../assets/exploreBackground1.png";
// import exploreBackground2 from "../assets/exploreBackground2.png";
// import exploreBackground3 from "../assets/exploreBackground3.png";
import albumCover1 from "../assets/albumCover-1.png";
import albumCover2 from "../assets/albumCover-2.png";
import albumCover3 from "../assets/albumCover-3.png";
import dislikeDefault from "../assets/dislike-button-default.png";
import likeDefault from "../assets/like-button-default.png";

interface Song {
  id: string;
  title: string;
  artist: string;
  album: string;
}
 function ExplorePage() {
  
  const songs = [
    { title: "Sienna", artist: "The Marías", image: albumCover1 },
    { title: "All I Need", artist: "Radiohead", image: albumCover2 },
    { title: "Selfless", artist: "The Strokes", image: albumCover3 },
  ];

  const [currentIndex, setCurrentIndex] = useState(0);
  const [swipeDirection, setSwipeDirection] = useState<"left" | "right" | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const handleSwipe = (dir: "left" | "right") => {
    setSwipeDirection(dir);

    // Wait until animation finishes
    setTimeout(() => {
      setCurrentIndex((prev) => (prev + 1) % songs.length);
      setSwipeDirection(null);
    }, 400);
  };

  const handleLike = () => {
  const song = songs[currentIndex];
    setToastMessage(`${song.title} was added to your library!`);
    setTimeout(() => setToastMessage(null), 3000);
    handleSwipe("right");
  };

  const currentSong = songs[currentIndex];

  return (
    <div className="page-wrapper">
      <img className="bg-blur" src={currentSong.image} alt="background" />

      {toastMessage && (
        <div className="toast lexend">{toastMessage}</div>
      )}

      <div className="content">
        <h1 className="lexend">Explore</h1>

        <div className={`music-card ${swipeDirection ?? ""}`}>
          <img className="album-cover" src={currentSong.image} style={{ width: "300px" }} />

          <div className="song-title">{currentSong.title}</div>
          <div className="song-artist">{currentSong.artist}</div>

          <div className="dislike-button" onClick={() => handleSwipe("left")}>
            <img src={dislikeDefault} width="100" />
          </div>

          <div className="like-button" onClick={handleLike}>
            <img src={likeDefault} width="100" />
          </div>
        </div>

        <div className='music-card'> 
          <button>Explore</button>
          <button>Search</button>
          <button>My profile</button>
        </div>

      </div>
    </div>
  );
}


export default ExplorePage;