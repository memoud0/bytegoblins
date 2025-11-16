import { Routes, Route } from "react-router-dom";
import LoginPage from "./pages/LoginPage.tsx";
import ExplorePage from "./pages/ExplorePage.tsx";
import SearchPage from "./pages/SearchPage.tsx";

function App() {
  return (
    <Routes>
      <Route path="/" element={<LoginPage />} />
      <Route path="/explore" element={<ExplorePage />} />
      <Route path="/search" element={<SearchPage />} />
    </Routes>
  );
}

export default App;