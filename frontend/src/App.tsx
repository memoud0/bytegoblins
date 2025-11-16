import { Routes, Route } from "react-router-dom";
import LoginPage from "./pages/LoginPage.tsx";
import ExplorePage from "./pages/ExplorePage.tsx";
import SearchPage from "./pages/SearchPage.tsx";
import ProfilePage from "./pages/ProfilePage.tsx";
import { useEffect } from "react";
import { api } from "./api/api";

function App() {
  useEffect(() => {
    async function pingBackend() {
      try {
        const res = await api.get(`/api/health`);
        console.log("Health check:", res.data);
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