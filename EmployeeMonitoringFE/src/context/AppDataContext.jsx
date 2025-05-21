import { createContext, useState } from "react";
import { useContext } from "react";
import { useUser } from "../context/UserContext";

const AppDataContext = createContext(null);

export const AppDataProvider = ({ children }) => {
    const [cameras, setCameras] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [employees, setEmployees] = useState([]);
    const [security, setSecurity] = useState([]);
  const { isAdmin } = useUser(); // This is where UserContext is being used

    const loadAllAppData = (cameras, alerts, employees, security) => {
        setCameras(cameras);
        setAlerts(alerts);
        if (isAdmin()) {
      setEmployees(employees || []);
      setSecurity(security || []);
    }
    }



  return (
    <AppDataContext.Provider value={{setAlerts, setCameras, setEmployees, setSecurity, loadAllAppData, cameras, alerts, employees, security}}>
      {children}
    </AppDataContext.Provider>
  );
};

export const useAppData = () => {
  const context = useContext(AppDataContext);
  if (!context) {
    throw new Error("useAppData must be used within a AppDataProvider");
  }
  return context;
};
