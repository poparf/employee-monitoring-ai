import { Navigate, Outlet } from "react-router"

export const AlreadyAuthenticated = ({isAuthenticated, redirectPath="/home"}) => {
    return !isAuthenticated ? <Outlet/> : <Navigate 
        to={redirectPath}
        replace 
      />;
};