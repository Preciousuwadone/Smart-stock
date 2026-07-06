import { useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Logo from "../components/Logo";

export default function Login() {
  const [searchParams] = useSearchParams();
  const [isSignup, setIsSignup] = useState(searchParams.get("mode") === "signup");
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
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.error || "Something went wrong");
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", padding: "40px 20px" }}>
      <div style={{ marginBottom: 32 }}>
        <Link to="/"><Logo size={36} /></Link>
      </div>

      <div style={{
        maxWidth: 400, width: "100%", background: "var(--color-surface)",
        border: "1px solid var(--color-border)", borderRadius: "var(--radius)",
        boxShadow: "var(--shadow-sm)", padding: 32,
      }}>
        <h2 style={{ marginTop: 0 }}>{isSignup ? "Create your account" : "Welcome back"}</h2>
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
          {error && <p style={{ color: "var(--color-danger)", fontSize: 13 }}>{error}</p>}
          <button type="submit" style={{ width: "100%", marginTop: 8 }}>
            {isSignup ? "Sign Up" : "Log in"}
          </button>
        </form>
        <p onClick={() => setIsSignup(!isSignup)} style={{ cursor: "pointer", textAlign: "center", marginTop: 16, fontSize: 14 }}>
          {isSignup ? "Already have an account? Log in" : "Need an account? Sign up"}
        </p>
      </div>

      <Link to="/" style={{ marginTop: 24, fontSize: 13, color: "var(--color-text-secondary)" }}>← Back to home</Link>
    </div>
  );
}