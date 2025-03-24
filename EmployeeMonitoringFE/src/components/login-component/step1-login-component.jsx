import background from "../../assets/imgs/login1bg.png";
import LogoName from "../logo-component/Logo-name-component";
import { Link, useNavigate } from "react-router"; // Use react-router-dom if applicable
import axios from "axios";
import { SERVER_URL } from "../../utils/constants";
import { useState } from "react";
import { CiUser } from "react-icons/ci";


const Login = () => {
  const [step, setStep] = useState("step1-login");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState("")
  const navigate = useNavigate()

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setError("")
    const formData = new FormData(e.target);
    const password = formData.get("password");

    if (!password) {
      setError("Please enter your password.");
      return;
    }

    try {
      setLoading(true);
      const res = await axios.post(`${SERVER_URL}/users/login`, {email, password})
      if(res.status == 200) {
        const data = res.data;
        localStorage.setItem("token", data["token"])
        navigate("/home") 
      } else {
        setError("Password is not correct.")
      }
    } catch(err) {
      console.error(err);
      setError("An error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const handleEmailSubmit = async (e) => {
    e.preventDefault();
    setError(""); // reset error state
    const formData = new FormData(e.target);
    const email = formData.get("email");

    if (!email) {
      setError("Please enter your email.");
      return;
    }

    try {
      setLoading(true);
      const res = await axios.post(`${SERVER_URL}/users/check-email`, { email });
      if (res.data["exists"]) {
        setEmail(email)
        setStep("step2-login");

      } else {
        // Optionally, route to register if the email doesn't exist
        setStep("step1-register");
      }
    } catch (err) {
      console.error(err);
      setError("An error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        backgroundImage: `url(${background})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
      className="w-screen h-screen flex items-center justify-center relative overflow-hidden"
    >
      <div className="bg-neutral-600 w-80 p-6 flex flex-col items-center justify-center rounded-lg shadow-lg min-h-[55vh]">
        <LogoName />

        {step === "step1-login" && (
          <form onSubmit={handleEmailSubmit} className="w-full">
            <label className="text-neutral-200 mt-8 mb-2 text-sm block">
              Enter your email address
            </label>
            <input
              name="email"
              type="email"
              className="bg-neutral-700 w-full p-2 rounded text-white outline-none border border-stone-800"
            />
            {error && <p className="text-red-500 text-xs mt-2">{error}</p>}
            <button
              type="submit"
              className="bg-neutral-900 text-neutral-200 w-full mt-8 p-2 rounded hover:bg-neutral-800 hover:cursor-pointer"
              disabled={loading}
            >
              {loading ? "Loading..." : "Continue"}
            </button>
            <p className="text-neutral-300 text-xs text-center mt-8">
              Don't worry if you don't have an account
              <br />
              you can create one in the next step
            </p>
          </form>
        )}

        {step === "step2-login" && (<>
          <div className="mt-8 rounded-full w-24 h-24 bg-neutral-200"><CiUser className="w-24 h-22" /></div>
          <p className="text-neutral-300 mt-2">{email}</p>
          <form onSubmit={handlePasswordSubmit} className="w-full">
            <label className="text-neutral-200 mt-8 mb-2 text-sm block">
              Enter your password
            </label>
            <input
              name="password"
              type="password"
              className="bg-neutral-700 w-full p-2 rounded text-white outline-none border border-stone-800"
            />
            {error && <p className="text-red-500 text-xs mt-2">{error}</p>}
            <button
              type="submit"
              className="bg-neutral-900 text-neutral-200 w-full mt-8 p-2 rounded hover:bg-neutral-800 hover:cursor-pointer"
              disabled={loading}
            >
              {loading ? "Loading..." : "Continue"}
            </button>
            <div></div><p className="mt-2 text-right text-neutral-300">Forgot password?</p>
          </form></>
        )}

        {step === "step1-register" && (
          <form className="w-full">
            {/* Placeholder for Step 1 Register Form */}
            <p className="text-neutral-200 text-sm text-center">Step 1 Register Form</p>
          </form>
        )}

        {step === "step2-register" && (
          <form className="w-full">
            {/* Placeholder for Set Password Form */}
            <p className="text-neutral-200 text-sm text-center">Set Password Form</p>
          </form>
        )}

        {step === "step3-register" && (
          <form className="w-full">
            {/* Placeholder for Email Verification Form */}
            <p className="text-neutral-200 text-sm text-center">Verify Email Form</p>
          </form>
        )}

        {step === "step4-register" && (
          <form className="w-full">
            {/* Placeholder for Organization Registration Form */}
            <p className="text-neutral-200 text-sm text-center">Organization Registration Form</p>
          </form>
        )}
      </div>

      <div className="absolute bottom-4 right-4">
        <p className="text-neutral-400 text-xs">
          <Link to="/about">About</Link> | © 2025 VISION
        </p>
      </div>
    </div>
  );
};

export default Login;
