import { useEffect, useState } from 'react'
import { useNavigate } from "react-router-dom";
import "../App.css";

import albumCover1 from "../assets/albumCover-1.png";
import albumCover2 from "../assets/albumCover-2.png";
import albumCover3 from "../assets/albumCover-3.png";
import exploreWhite from "../assets/explore-white.png";
import profileWhite from "../assets/profile-white.png";
import searchBlack from "../assets/search-black.png";
import background from "../assets/search-background.png";
import addIcon from "../assets/add-icon-black.png";

interface Song {
  id: string;
  title: string;
  artist: string;
  album: string;
}

function SearchPage() {
  const [activeTab, setActiveTab] = useState<"explore" | "search" | "profile">("search");

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

  const search = () => {}

  const songs = [
    { title: "Sienna", artist: "The Marías", image: albumCover1 },
    { title: "All I Need", artist: "Radiohead", image: albumCover2 },
    { title: "Selfless", artist: "The Strokes", image: albumCover3 },
  ];

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
                    className='lexend'
                    type="text"
                    placeholder="Look for your favourite songs . . ."
                    style={{
                        width: "100%",
                    }}
                />

                <button className="button-white" style={{ padding: "12px" }}>
                    <img src={searchBlack} style={{ width: "24px" }} />
                </button>
            </div>
            
            <div className='results-grid-search'>
                <div className='music-card-search' style={{borderRadius: "40px"}}>
                    <img className="album-cover-search" src={albumCover1} 
                        style={{ 
                            width: "220px",
                            margin: "25px" 
                        }} />
                    <div className="song-title-search">All I Need</div>
                    <div className="song-artist-search">Radiohead</div>
                    <button className='button-white'>
                        <img src={addIcon} width="20" style={{ paddingRight: "10px" }} />
                        Add to library
                    </button>
                </div>

                <div className='music-card-search' style={{borderRadius: "40px"}}>
                    <img className="album-cover-search" src={albumCover2} 
                        style={{ 
                            width: "220px",
                            margin: "25px" 
                        }} />
                    <div className="song-title-search" style={{fontSize: "20px"}}>All I Need</div>
                    <div className="song-artist-search">Radiohead</div>
                    <button className='button-white'>
                        <img src={addIcon} width="20" style={{ paddingRight: "10px" }} />
                        Add to library
                    </button>
                </div>

                <div className='music-card-search' style={{borderRadius: "40px"}}>
                    <img className="album-cover-search" src={albumCover3} 
                        style={{ 
                            width: "220px",
                            margin: "25px" 
                        }} />
                    <div className="song-title-search" style={{fontSize: "20px"}}>All I Need</div>
                    <div className="song-artist-search">Radiohead</div>
                    <button className='button-white'>
                        <img src={addIcon} width="20" style={{ paddingRight: "10px" }} />
                        Add to library
                    </button>
                </div>
                
                <div className='music-card-search' style={{borderRadius: "40px"}}>
                    <img className="album-cover-search" src={albumCover1} 
                        style={{ 
                            width: "220px",
                            margin: "25px" 
                        }} />
                    <div className="song-title-search">All I Need</div>
                    <div className="song-artist-search">Radiohead</div>
                    <button className='button-white'>
                        <img src={addIcon} width="20" style={{ paddingRight: "10px" }} />
                        Add to library
                    </button>
                </div>
            </div>
            

            <div className="menu"> 
                <button
                    id="exploreButton"
                    className={`menu-button ${activeTab !== "explore" ? "not-current" : ""}`}
                    onClick={goToExplore}
                >
                    <img src={exploreWhite} width="20" style={{ paddingRight: "10px" }} />
                    Explore
                </button>

                <button
                    id="searchButton"
                    className={`menu-button ${activeTab !== "search" ? "not-current" : ""}`}
                    onClick={goToSearch}
                >
                    <img src={searchBlack} width="20" style={{ paddingRight: "10px" }} />
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

export default SearchPage;
