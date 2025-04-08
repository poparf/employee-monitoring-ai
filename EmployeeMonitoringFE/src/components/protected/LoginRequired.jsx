import { Navigate, Outlet } from "react-router"

export const LoginRequiredComponent = ({isAuthenticated, redirectPath="/login"}) => {
    return isAuthenticated ? <Outlet/> : <Navigate 
        to={redirectPath}
        replace 
      />;
};