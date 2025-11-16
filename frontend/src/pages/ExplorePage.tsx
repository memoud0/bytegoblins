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

import loginBackground from "../assets/loginBackground.png";

interface Song {
  id: string;
  title: string;
  artist: string;
  album: string;
}

function ExplorePage() {
    return (
        <h1 className='lexend'>Search</h1>
    );
}

export default ExplorePage;