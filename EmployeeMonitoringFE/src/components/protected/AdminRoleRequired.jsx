import { Navigate, Outlet } from "react-router"

export const AdminRoleRequired = ({isAdmin, redirectPath="/404"}) => {
    return isAdmin ? <Outlet/> : <Navigate 
        to={redirectPath}
        replace 
      />;
};