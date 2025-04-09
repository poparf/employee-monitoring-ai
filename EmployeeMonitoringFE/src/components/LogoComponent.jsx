import Logo from '../assets/logo/Logo_Vision.webp'

const LogoName = () => {
    return (
        <div className="flex items-center space-x-2">
            <img src={Logo} alt="logo" className="w-16 h-16" />
            <span className="font-serif text-6xl text-white">VISION</span>
        </div>
    )
}

export default LogoName;