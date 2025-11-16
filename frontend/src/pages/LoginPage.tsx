import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "../App.css";
import { useNavigate } from "react-router-dom";
import { useUserId } from "../useUserId";
// import { db } from "../firebase";
// import {
//   collection,
//   addDoc,
//   getDocs,
//   query,
//   where,
//   Timestamp,
// } from "firebase/firestore";

import loginBackground from "../assets/loginBackground.png";

interface LoginPayload {
  username?: string;
  error?: string;
  created?: boolean;
}

interface ToastState {
  username: string;
  created: boolean;
}

function LoginPage() {
  const navigate = useNavigate();
  const { userId, setUserId } = useUserId();
  const [usernameInput, setUsernameInput] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toast, setToast] = useState<ToastState | null>(null);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    const frame = requestAnimationFrame(() => setIsMounted(true));
    return () => cancelAnimationFrame(frame);
  }, []);

  useEffect(() => {
    if (!userId) {
      return;
    }

    const redirectDelay = toast ? (toast.created ? 1200 : 1700) : 500;
    const timer = setTimeout(() => {
      navigate("/explore", { replace: true });
    }, redirectDelay);

    return () => clearTimeout(timer);
  }, [userId, toast, navigate]);

  useEffect(() => {
    if (!toast) {
      return;
    }

    const timer = setTimeout(() => setToast(null), 2500);
    return () => clearTimeout(timer);
  }, [toast]);

  const handleLogin = async () => {
    const trimmed = usernameInput.trim();
    if (!trimmed) {
      setErrorMessage("Please enter your username");
      return;
    }

    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const response = await fetch("/api/users/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username: trimmed }),
      });

      const payload = (await response.json().catch(() => null)) as LoginPayload | null;

      if (!response.ok) {
        const message = (payload && payload.error) || "Unable to sign in. Try again later.";
        throw new Error(message);
      }

      const normalized = (payload?.username || trimmed).toLowerCase();
      setUserId(normalized);
      setUsernameInput("");
      setToast({
        username: normalized,
        created: Boolean(payload?.created),
      });
    } catch (err) {
      console.error("handleLogin ERROR:", err);
      setErrorMessage(
        err instanceof Error ? `${err.message} Try again later.` : "Unexpected error signing in. Try again later."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className="login-shell"
      data-ready={isMounted}
      style={{
        backgroundImage: `url(${loginBackground})`,
        backgroundSize: "cover",
        backgroundRepeat: "no-repeat",
        backgroundPosition: "center",
        height: "100vh",
        width: "100vw",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div className="App">
        <div>

          <h1
            className="lexend login-title"
            style={{
              fontSize : "96px", 
              margin: '0', 
              paddingTop:"120px",
              textShadow: "0px 5px 10px rgba(0, 0, 0, 0.35)"
            }}>
          tuneder
        </h1>

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}>

            <input
              id="userIdInput"
              className='lexend'
              type="text"
              placeholder="Enter your user ID . . ."
              style={{marginTop: "75px"}}
              value={usernameInput}
              onChange={(event) => {
                if (errorMessage) {
                  setErrorMessage(null);
                }
                setUsernameInput(event.target.value);
              }}
              disabled={isSubmitting}
            />

            <button
              className="button-white"
              type="button"
              onClick={handleLogin}
              disabled={isSubmitting}
              data-loading={isSubmitting}
            >
              <span>{isSubmitting ? "Signing in" : "Sign in"}</span>
            </button>

            {errorMessage && (
              <p className="login-error" role="status" aria-live="polite">
                {errorMessage}
              </p>
            )}

          </div>
        </div>
        {toast && (
          <div className="login-toast">
            {toast.created ? (
              <span>Welcome to tuneder, {toast.username}!</span>
            ) : (
              <span>Welcome back, {toast.username}!</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default LoginPage;
