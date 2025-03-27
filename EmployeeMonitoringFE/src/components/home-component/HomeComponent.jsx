import { useUser } from "../../context/UserContext";

const Home = () => {
    const {logout} = useUser()
    return <div>HOME
        <button onClick={logout}>logout</button>
    </div>
}
export default Home;