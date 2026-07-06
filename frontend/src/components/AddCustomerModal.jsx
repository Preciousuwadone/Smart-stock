import { useState } from "react";
import client from "../api/client";
import "../styles/AppShell.css";

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
    <div className="app-modal-overlay" onClick={onClose}>
      <div className="app-modal" onClick={(e) => e.stopPropagation()}>
        <h3>Add Customer</h3>
        <form onSubmit={handleSubmit}>
          <input placeholder="Full name" value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
          <input placeholder="Phone (e.g. 08011111111)" value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })} required />
          <input placeholder="Email (for reminders)" type="email" value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })} />
          {error && <p className="app-modal-error">{error}</p>}
          <div className="app-modal-actions">
            <button type="button" className="app-btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" disabled={saving}>{saving ? "Creating…" : "Create"}</button>
          </div>
        </form>
      </div>
    </div>
  );
}