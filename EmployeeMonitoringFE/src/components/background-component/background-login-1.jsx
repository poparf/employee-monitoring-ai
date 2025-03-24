import background from "../../assets/imgs/login1bg.png";
const BackgroundLogin1 = ({children}) => {
    return (
        <div style={{
            backgroundImage: `url(${background})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            width: '100vw',
            height: '100vh',
            overflow: 'hidden'
        }}>
            {children}
        </div>
    );
}

export default BackgroundLogin1;