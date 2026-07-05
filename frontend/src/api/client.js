import axios from "axios";

const client = axios.create({
  baseURL: "https://smart-stock-production.up.railway.app", // swap to localhost:5000 for local dev
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