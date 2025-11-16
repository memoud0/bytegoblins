import { Routes, Route } from "react-router-dom";
import LoginPage from "./pages/LoginPage.tsx";
import ExplorePage from "./pages/ExplorePage.tsx";

function App() {
  return (
    <Routes>
      <Route path="/" element={<LoginPage />} />
      <Route path="/home" element={<ExplorePage />} />
    </Routes>
  );
}

export default App;