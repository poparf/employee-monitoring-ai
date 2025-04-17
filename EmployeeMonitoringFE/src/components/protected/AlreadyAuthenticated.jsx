import { Navigate, Outlet } from "react-router"

export const AlreadyAuthenticated = ({isAuthenticated, redirectPath="/dashboard"}) => {
    return !isAuthenticated ? <Outlet/> : <Navigate 
        to={redirectPath}
        replace 
      />;
};