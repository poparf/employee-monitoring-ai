// Pages
import LoginPage from "./pages/LoginPage.jsx";
import HomePage from "./pages/HomePage.jsx";
import AboutPage from "./pages/AboutPage.jsx";

import "./style/main.css";
import { BrowserRouter, Routes, Route } from "react-router";
import { LoginRequiredComponent } from "./components/protected/LoginRequired.jsx";
import { useUser } from "./context/UserContext.jsx";
import { LoadingComponent } from "./components/LoadingComponent.jsx";
import NotFoundPage from "./pages/NotFoundPage.jsx";
import { AlreadyAuthenticated } from "./components/protected/AlreadyAuthenticated.jsx";

export const App = () => {
  const { isAuthenticated, loading } = useUser();

  if (loading) {
    return <div
    style={{
        backgroundColor: "#2C2C2C",
        backgroundSize: "cover",
        backgroundPosition: "center",
        width: "100vw",
        height: "100vh",
        
    }}
    className="flex items-center justify-center h-screen relative"
    >
      <LoadingComponent/>
    </div>
     }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="*" element={<NotFoundPage isAuthenticated={isAuthenticated()}/>}/>
        <Route path="/about" element={<AboutPage />} />
        <Route element={<AlreadyAuthenticated isAuthenticated={isAuthenticated()} />}>
          <Route path="/login" element={<LoginPage />} />
        </Route>
        <Route element={<LoginRequiredComponent isAuthenticated={isAuthenticated()} />}>
          <Route path="/home" element={<HomePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};
