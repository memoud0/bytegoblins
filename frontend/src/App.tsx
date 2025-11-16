import { Routes, Route } from "react-router-dom";
import LoginPage from "./pages/LoginPage.tsx";
import ExplorePage from "./pages/ExplorePage.tsx";
import SearchPage from "./pages/SearchPage.tsx";
import ProfilePage from "./pages/ProfilePage.tsx";
import { useEffect } from "react";

const API_URL = import.meta.env.VITE_API_URL;

function App() {
  useEffect(() => {
    async function pingBackend() {
      try {
        const res = await fetch(`${API_URL}/api/health`);
        const data = await res.json();
        console.log("Health check:", data);
      } catch (err) {
        console.error("Health check failed:", err);
      }
    }
    pingBackend();
  }, []);

  return (
    <Routes>
      <Route path="/" element={<LoginPage />} />
      <Route path="/explore" element={<ExplorePage />} />
      <Route path="/search" element={<SearchPage />} />
      <Route path="/profile" element={<ProfilePage />} />
    </Routes>
  );
}

export default App;