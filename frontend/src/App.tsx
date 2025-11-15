import { useEffect, useState } from 'react'
// import reactLogo from './assets/react.svg'
// import viteLogo from '/vite.svg'
import "./App.css";
import { useUserId } from "./useUserId";
import { db } from "./firebase";
import {
  collection,
  doc,
  setDoc,
  addDoc,
  getDocs,
  query,
  where,
  Timestamp,
} from "firebase/firestore";

interface Song {
  id: string;
  title: string;
  artist: string;
  album: string;
}

function App() {
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

     if (!userId) return;

    const libraryRef = collection(db, "users", userId, "library");
    const snap = await getDocs(libraryRef);

    const data: Song[] = snap.docs.map((docSnap) => ({
      id: docSnap.id,
      title: docSnap.data().track_name ?? "(unknown)",
      artist: (docSnap.data().artists || ["Unknown Artist"])[0],
      album: docSnap.data().album_name ?? "(unknown)",
  }));

  setSongs(data);
};

  //   try {
  //     const userSongsRef = collection(db, "usersongs");
  //     const q = query(
  //       userSongsRef,
  //       where("userId", "==", userId),
  //       where("liked", "==", true)
  //     );

  //     const snap = await getDocs(q);
  //     console.log("loadSongs: got", snap.size, "docs");

  //     const data: Song[] = snap.docs.map((doc) => ({
  //       id: doc.id,
  //       title: doc.data().songTitle,
  //       artist: doc.data().songArtist,
  //       album: doc.data().songAlbum,
  //     }));

  //     setSongs(data);
  //   } catch (err) {
  //     console.error("loadSongs ERROR:", err);
  //   } finally {
  //     console.log("loadSongs: FINALLY -> setLoading(false)");
  //     setLoading(false);
  //   }
  // };

  const addFakeSong = async () => {
    if (!userId) {
      console.log("addFakeSong: no userId yet");
      return;
    }

    console.log("addFakeSong: CLICKED, userId =", userId);

    const libraryRef = collection(db, "users", userId, "library");
    const trackId = "test-track-1";

    await setDoc(doc(libraryRef, trackId), {
      track_id: trackId,
      added_at: Timestamp.now(),
      source: "test",
    });

    await loadSongs();
  };

//     const userSongsRef = collection(db, "usersongs");
//     addDoc(userSongsRef, {
//     userId,
//     songId: "test-song-1",
//     songTitle: "Test Song",
//     songArtist: "Test Artist",
//     songAlbum: "Test Album",
//     liked: true,
//     createdAt: Timestamp.now(),
//   })
//     .then((docRef) => {
//       console.log("addFakeSong: SAVED with id =", docRef.id);
//       // reload songs after save
//       return loadSongs();
//     })
//     .catch((err) => {
//       console.error("addFakeSong ERROR:", err);
//     });
// };

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
    <div className="App">
      <h1>Song Swipe Firebase Test</h1>
      <p>Your user id: {userId}</p>

      <p>Loading state: {loading ? "true" : "false"}</p>

      {/* NOTE: no disabled={loading} while debugging */}
      <button onClick={addFakeSong}>
        Add Fake Liked Song
      </button>

      <h2>Your liked songs</h2>
      {songs.length === 0 ? (
        <p>No songs yet.</p>
      ) : (
        <ul>
          {songs.map((s) => (
            <li key={s.id}>
              {s.title} – {s.artist} ({s.album})
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default App;


//   return (
//     <>
//       <div>
//         <a href="https://vite.dev" target="_blank">
//           <img src={viteLogo} className="logo" alt="Vite logo" />
//         </a>
//         <a href="https://react.dev" target="_blank">
//           <img src={reactLogo} className="logo react" alt="React logo" />
//         </a>
//       </div>
//       <h1>Vite + React</h1>
//       <div className="card">
//         <button onClick={() => setCount((count) => count + 1)}>
//           count is {count}
//         </button>
//         <p>
//           Edit <code>src/App.tsx</code> and save to test HMR
//         </p>
//       </div>
//       <p className="read-the-docs">
//         Click on the Vite and React logos to learn more
//       </p>
//     </>
//   )
// }

// export default App
