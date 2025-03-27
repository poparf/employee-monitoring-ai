import { Navigate, Outlet } from "react-router"

export const LoginRequiredComponent = ({isAuthenticated, redirectPath="/"}) => {
    console.log(isAuthenticated)
    return isAuthenticated ? <Outlet/> : <Navigate 
        to="/login"
        replace 
      />;
};