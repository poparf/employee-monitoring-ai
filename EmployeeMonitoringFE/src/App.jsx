// Pages
import LoginPage from "./pages/LoginPage.jsx";
import HomePage from "./pages/HomePage.jsx";
import AboutPage from "./pages/AboutPage.jsx";

import "./style/main.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router";
import { LoginRequiredComponent } from "./components/protected/LoginRequired.jsx";
import { useUser } from "./context/UserContext.jsx";
import { LoadingComponent } from "./components/LoadingComponent.jsx";
import NotFoundPage from "./pages/NotFoundPage.jsx";
import { AlreadyAuthenticated } from "./components/protected/AlreadyAuthenticated.jsx";
import EmployeeRegistration from "./pages/employees/EmployeeRegistration.jsx";
import EmployeesList from "./pages/employees/EmployeesList.jsx";
import SecurityRegistration from "./pages/security/SecurityRegistration.jsx";
import SecurityList from "./pages/security/SecurityList.jsx";
import ObserverPage from "./pages/ObserverPage.jsx";
import AlertsPage from "./pages/alerts/AlertsPage.jsx";
import VideoCamerasPage from "./pages/video-cameras/VideoCamerasPage.jsx";
import IndividualVideoCameraPage from "./pages/video-cameras/IndividualVideoCameraPage.jsx";
import ZonesPage from "./pages/video-cameras/zones/ZonesPage.jsx";
import IndividualZonePage from "./pages/video-cameras/zones/IndividualZonePage.jsx";
import ZoneRegistration from "./pages/video-cameras/zones/ZoneRegsistration.jsx";

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
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<HomePage />} />
          
          <Route path="/employees/register" element={<EmployeeRegistration/>} />
          <Route path="/employees" element={<EmployeesList/>} />

          <Route path="/security/register" element={<SecurityRegistration />} />
          <Route path="/security" element={<SecurityList />} />

          <Route path="/alerts" element={<AlertsPage/>}/>
          
          <Route path="/video-cameras" element={<VideoCamerasPage/>}/>
          <Route path="/video-cameras/:cameraId" element={<IndividualVideoCameraPage />} />
          <Route path="/video-cameras/:cameraId/zones" element={<ZonesPage/>}/>
          <Route path="/video-cameras/:cameraId/zones/:zoneId" element={<IndividualZonePage/>}/>
          <Route path="/video-cameras/:cameraId/zones/register" element={<ZoneRegistration/>}/>

          <Route path="/settings" element={<div>Settings</div>} />

          <Route path="/observer" element={<ObserverPage/>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};
