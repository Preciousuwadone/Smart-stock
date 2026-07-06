import { useState } from "react";
import client from "../api/client";

export default function AddCustomerModal({ onClose, onCreated }) {
  const [form, setForm] = useState({ full_name: "", phone: "", email: "" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await client.post("/api/customers", form);
      onCreated();
    } catch (err) {
      setError(err.response?.data?.error || "Failed to add customer");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={overlayStyle}>
      <div style={modalStyle}>
        <h3>Add Customer</h3>
        <form onSubmit={handleSubmit}>
          <input placeholder="Full name" value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
          <input placeholder="Phone (e.g. 08011111111)" value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })} required />
          <input placeholder="Email (for reminders)" type="email" value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })} />
          {error && <p style={{ color: "red" }}>{error}</p>}
          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <button type="submit" disabled={saving}>{saving ? "Creating..." : "Create"}</button>
            <button type="button" onClick={onClose}>Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
}

const overlayStyle = { position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", display: "flex", alignItems: "center", justifyContent: "center" };
const modalStyle = { background: "white", padding: 24, borderRadius: 8, width: 320 };