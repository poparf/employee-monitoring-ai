import { useUser } from "../context/UserContext";

const HomePage = () => {
    const {logout} = useUser()
    return <div>HOME
        <button onClick={logout}>logout</button>
    </div>
}
export default HomePage;