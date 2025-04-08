import loadingAnimation from "../assets/animations/loading_animation.webm"

export const LoadingComponent = () => {
    return <div>
                <video id="banner-video" autoPlay={true} muted playsInline={true} loop>
                    <source src={loadingAnimation} type="video/webm"/>
                    Your browser does not support the video tag.
                </video>
            </div>
} 