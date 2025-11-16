import { useEffect, useState } from "react";
import "../App.css";
import { useNavigate } from "react-router-dom";
import { useUserId } from "../useUserId";
// import { db } from "../firebase";
// import {
//   collection,
//   addDoc,
//   getDocs,
//   query,
//   where,
//   Timestamp,
// } from "firebase/firestore";

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

  const navigate = useNavigate();

  const handleSignIn = () => {
    navigate("/explore");
  };

  return (
    <div 
      style={{
        backgroundImage: `url(${loginBackground})`,
        backgroundSize: "cover",
        backgroundRepeat: "no-repeat",
        backgroundPosition: "center",
        height: "100vh",
        width: "100vw",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div className="App">
        <h1 className="lexend" 
            style={{
              fontSize : "96px", 
              margin: '0', 
              paddingTop:"120px",
              textShadow: "0px 5px 10px rgba(0, 0, 0, 0.35)"
            }}>
          tuneder
        </h1>

        <div style={{ display:"flex", flexDirection:"column", alignItems:"center" }}>
          <input
            id="userIdInput"
            className='lexend'
            type="text"
            placeholder="Enter your user ID . . ."
            style={{marginTop: "75px"}}
          />

          <button className="button-white" onClick={handleSignIn}>
            Sign in
          </button>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
