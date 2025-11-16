import { useEffect, useState } from 'react'
import { useNavigate } from "react-router-dom";
import "../App.css";

import albumCover1 from "../assets/albumCover-1.png";
import albumCover2 from "../assets/albumCover-2.png";
import albumCover3 from "../assets/albumCover-3.png";
import exploreWhite from "../assets/explore-white.png";
import profileBlack from "../assets/profile-black.png";
import searchWhite from "../assets/search-white.png";
import background from "../assets/profile-background.png";
import addIcon from "../assets/add-icon-black.png";
import removeIcon from "../assets/remove-icon.png";

interface Song {
  id: string;
  title: string;
  artist: string;
  album: string;
}

function ProfilePage() {

    const [activeTab, setActiveTab] = useState<"explore" | "search" | "profile">("profile");

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
                <h1 className="lexend">Username</h1>

                <div className='profile-row'>
                    <div className='personality-card'>
                        <div className='personality-title'>
                            Dreamy Rhythm Alchemist
                        </div>
                        <div className='personality-text'>
                            You're someone who feels deeply and sees beauty in the details. You move between 
                            moody, world-building artists like Tyler, Radiohead, and Tame Impala, and the warm 
                            nostalgia of salsa romántica, city pop, and timeless classics. That mix isn't random 
                            — it shows a person who's grounded in emotion, open to new textures, and unafraid to 
                            sit with complexity. You're drawn to songs that make you feel something real — 
                            grooves that carry memory, colors, and yearning. You like music with personality: 
                            soulful, a little off-center, expressive, and full of heart. Your playlist reads like 
                            someone who understands both intensity and softness, who values depth but still loves 
                            rhythm, movement, and warmth. <br></br>
                            In short: you have taste that's intentional, emotionally 
                            intuitive, and quietly bold — and it shows.
                        </div>
                    </div>

                    <div className='library-card'>
                        <div className='personality-title'>
                            Library
                        </div>
                        <div className="library-row">
                            <img src={albumCover1} width="65px" style={{ borderRadius: "10px", margin: "10px"}} />
                            <div className="library-title">Sienna</div>
                            <div className="library-text">The Marías</div>
                            <button className="button-white">
                                <img src={removeIcon} width="20" />
                                Remove
                            </button>
                        </div>

                        <div className="library-row">
                            <img src={albumCover1} width="65px" style={{ borderRadius: "10px", margin: "10px"}} />
                            <div className="library-title">Sienna</div>
                            <div className="library-text">The Marías</div>
                            <button className="button-white">
                                <img src={removeIcon} width="20" />
                                Remove
                            </button>
                        </div>

                        <div className="library-row">
                            <img src={albumCover1} width="65px" style={{ borderRadius: "10px", margin: "10px"}} />
                            <div className="library-title">Sienna</div>
                            <div className="library-text">The Marías</div>
                            <button className="button-white">
                                <img src={removeIcon} width="20" />
                                Remove
                            </button>
                        </div>

                        <div className="library-row">
                            <img src={albumCover1} width="65px" style={{ borderRadius: "10px", margin: "10px"}} />
                            <div className="library-title">Sienna</div>
                            <div className="library-text">The Marías</div>
                            <button className="button-white">
                                <img src={removeIcon} width="20" />
                                Remove
                            </button>
                        </div>
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
                        <img src={searchWhite} width="20" style={{ paddingRight: "10px" }} />
                        Search
                    </button>

                    <button
                        id="profileButton"
                        className={`menu-button ${activeTab !== "profile" ? "not-current" : ""}`}
                        onClick={goToProfile}
                    >
                        <img src={profileBlack} width="20" style={{ paddingRight: "10px" }} />
                        My profile
                    </button>
                </div>
            </div>
        </div>
    );
}

export default ProfilePage;
