import { Routes, Route } from "react-router-dom";
import LoginPage from "./pages/LoginPage.tsx";
import ExplorePage from "./pages/ExplorePage.tsx";
import SearchPage from "./pages/SearchPage.tsx";
import ProfilePage from "./pages/ProfilePage.tsx";

function App() {
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