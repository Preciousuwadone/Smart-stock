import { createContext, useContext, useState } from "react";
import client from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [shop, setShop] = useState(null);

  const login = async (email, password) => {
    const res = await client.post("/api/auth/login", { email, password });
    localStorage.setItem("token", res.data.access_token);
    setShop(res.data.shop);
    return res.data.shop;
  };

  const signup = async (data) => {
    const res = await client.post("/api/auth/signup", data);
    localStorage.setItem("token", res.data.access_token);
    setShop(res.data.shop);
    return res.data.shop;
  };

  const logout = () => {
    localStorage.removeItem("token");
    setShop(null);
  };

  return (
    <AuthContext.Provider value={{ shop, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);