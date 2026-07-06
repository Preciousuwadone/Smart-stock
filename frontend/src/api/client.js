import axios from "axios";

// Reads from frontend/.env (local dev) or the platform's env vars (Railway).
// Falls back to the deployed backend if the variable isn't set, so nothing
// breaks if it's missing — but production deploys should always set it explicitly.
const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "https://smart-stock-production.up.railway.app",
});

// Attach the JWT to every request automatically — no repeating this in every call.
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// If a token expires (matches the backend's real behavior), bounce to login
// instead of leaving the user staring at a broken screen.
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 || err.response?.data?.msg === "Token has expired") {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default client;