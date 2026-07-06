import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Logo from "../components/Logo";

export default function Logout() {
  const { logout } = useAuth();
  const [done, setDone] = useState(false);

  useEffect(() => {
    logout();
    setDone(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div style={{
      minHeight: "100vh", display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center", padding: "40px 20px", textAlign: "center",
    }}>
      <div style={{ marginBottom: 24 }}>
        <Logo size={36} />
      </div>
      {done ? (
        <>
          <h2 style={{ margin: "0 0 8px" }}>You've been logged out</h2>
          <p style={{ color: "var(--color-text-secondary)", margin: "0 0 24px" }}>
            Your session has ended. Log back in whenever you're ready.
          </p>
          <div style={{ display: "flex", gap: 10 }}>
            <Link to="/login" style={{
              background: "var(--color-primary)", color: "#fff", padding: "10px 20px",
              borderRadius: 8, fontWeight: 600, fontSize: 14, textDecoration: "none",
            }}>Log back in</Link>
            <Link to="/" style={{
              background: "transparent", color: "var(--color-text)", padding: "10px 20px",
              borderRadius: 8, fontWeight: 600, fontSize: 14, textDecoration: "none",
              border: "1px solid var(--color-border)",
            }}>Back to home</Link>
          </div>
        </>
      ) : (
        <p style={{ color: "var(--color-text-secondary)" }}>Logging out...</p>
      )}
    </div>
  );
}