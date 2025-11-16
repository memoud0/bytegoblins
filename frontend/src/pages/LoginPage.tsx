import { useEffect, useState } from 'react'
import "../App.css";
import { useUserId } from "../useUserId";
import { db } from "../firebase";
import {
  collection,
  getDocs,
  query,
  where,
} from "firebase/firestore";

import loginBackground from "../assets/loginBackground.png";

interface Song {
  id: string;
  title: string;
  artist: string;
  album: string;
}

function LoginPage() {
  const userId = useUserId();
  const [songs, setSongs] = useState<Song[]>([]);
  const [loading, setLoading] = useState(false);

  const loadSongs = async () => {
    if (!userId) {
      console.log("loadSongs: no userId yet");
      return;
    }

    console.log("loadSongs: START, userId =", userId);
    setLoading(true);

    try {
      const userSongsRef = collection(db, "usersongs");
      const q = query(
        userSongsRef,
        where("userId", "==", userId),
        where("liked", "==", true)
      );

      const snap = await getDocs(q);
      console.log("loadSongs: got", snap.size, "docs");

      const data: Song[] = snap.docs.map((doc) => ({
        id: doc.id,
        title: doc.data().songTitle,
        artist: doc.data().songArtist,
        album: doc.data().songAlbum,
      }));

      setSongs(data);
    } catch (err) {
      console.error("loadSongs ERROR:", err);
    } finally {
      console.log("loadSongs: FINALLY -> setLoading(false)");
      setLoading(false);
    }
  };

  useEffect(() => {
    if (userId) {
      console.log("useEffect: userId ready, calling loadSongs()");
      loadSongs();
    }
  }, [userId]);

  if (!userId) {
    return <div>Initializing user...</div>;
  }

  return (
    <div 
      style={{
        backgroundImage: `url(${loginBackground})`,
        backgroundSize: "cover",
        backgroundRepeat: "no-repeat",
        backgroundPosition: "center",
        height: "100%",        
        width: "100%",
        display: "flex",
        justifyContent: "center", // centers the inner div horizontally
        alignItems: "center", // or "center" vertically
      }}
    >
      <div className="App">
        <div>

          <h1 className="lexend" 
            style={{
              fontSize : "96px", 
              margin: '0', 
              paddingTop:"120px",
              textShadow: "0px 5px 10px rgba(0, 0, 0, 0.35)"
            }}
            >tuneder</h1>

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}>

            <input
              id="userIdInput"
              className='lexend'
              type="text"
              placeholder="Enter your user ID . . ."
              style={{marginTop: "75px"}}
              // value={userId}
            />

            <button className="button-white">
              Sign in
            </button>

          </div>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;