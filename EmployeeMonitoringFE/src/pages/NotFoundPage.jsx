import { useEffect } from "react";

const NotFoundPage = ({isAuthenticated}) => {

    useEffect(() => {
        setTimeout(() => {
            if(isAuthenticated) {
                window.location.href = "/login"
            } else {
                window.location.href = "/dashboard"
            }
        }, 5000)
    }, [])

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
    <div className="text-white">
        <p>404 Page not found</p>
        <p>You will be redirected to home page in a few seconds...</p>

    </div>
</div>
}

export default NotFoundPage;