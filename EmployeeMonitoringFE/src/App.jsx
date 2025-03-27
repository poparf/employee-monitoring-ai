import Login from "./components/login-component/step1-login-component.jsx";
import "./style/main.css";
import { BrowserRouter, Routes, Route } from "react-router";
import About from "./components/about-component/About.jsx";
import { LoginRequiredComponent } from "./components/protected-components/login-required-component/LoginRequiredComponent.jsx";
import { useUser } from "./context/UserContext.jsx";
import Home from "./components/home-component/HomeComponent.jsx";
import { LoadingComponent } from "./components/loading-component/loading-component.jsx";

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
        <Route path="/about" element={<About />} />
        <Route path="/loading" element={<LoadingComponent/>}/>
        <Route path="/login" element={<Login />} />
        <Route element={<LoginRequiredComponent isAuthenticated={isAuthenticated()} />}>
          <Route path="/home" element={<Home />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};
