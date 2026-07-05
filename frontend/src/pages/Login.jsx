import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const [isSignup, setIsSignup] = useState(false);
  const [form, setForm] = useState({ email: "", password: "", business_name: "", owner_name: "", phone: "" });
  const [error, setError] = useState("");
  const { login, signup } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      if (isSignup) {
        await signup(form);
      } else {
        await login(form.email, form.password);
      }
      navigate("/");
    } catch (err) {
      // Surface the backend's actual error message, not a generic one —
      // the Flask routes already return specific, useful error text.
      setError(err.response?.data?.error || "Something went wrong");
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: "80px auto", fontFamily: "sans-serif" }}>
      <h2>SmartStock {isSignup ? "Sign Up" : "Login"}</h2>
      <form onSubmit={handleSubmit}>
        {isSignup && (
          <>
            <input placeholder="Business name" value={form.business_name}
              onChange={(e) => setForm({ ...form, business_name: e.target.value })} required />
            <input placeholder="Owner name" value={form.owner_name}
              onChange={(e) => setForm({ ...form, owner_name: e.target.value })} required />
            <input placeholder="Phone" value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })} required />
          </>
        )}
        <input placeholder="Email" type="email" value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        <input placeholder="Password" type="password" value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })} required />
        {error && <p style={{ color: "red" }}>{error}</p>}
        <button type="submit">{isSignup ? "Sign Up" : "Login"}</button>
      </form>
      <p onClick={() => setIsSignup(!isSignup)} style={{ cursor: "pointer", color: "#2563eb" }}>
        {isSignup ? "Already have an account? Login" : "Need an account? Sign up"}
      </p>
    </div>
  );
}