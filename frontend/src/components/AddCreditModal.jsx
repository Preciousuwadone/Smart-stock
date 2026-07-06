import { useState } from "react";
import client from "../api/client";
import "../styles/AppShell.css";

export default function AddCreditModal({ customerId, onClose, onCreated }) {
  const [form, setForm] = useState({ description: "", amount: "" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await client.post(`/api/customers/${customerId}/credit`, {
        description: form.description,
        amount: parseFloat(form.amount),
      });
      onCreated();
    } catch (err) {
      setError(err.response?.data?.error || "Failed to add transaction");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="app-modal-overlay" onClick={onClose}>
      <div className="app-modal" onClick={(e) => e.stopPropagation()}>
        <h3>Record Credit Sale</h3>
        <form onSubmit={handleSubmit}>
          <input placeholder="Description (e.g. 2 bags of rice)" value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })} required />
          <input placeholder="Amount (₦)" type="number" min="0" step="0.01" value={form.amount}
            onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
          {error && <p className="app-modal-error">{error}</p>}
          <div className="app-modal-actions">
            <button type="button" className="app-btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" disabled={saving}>{saving ? "Saving…" : "Save"}</button>
          </div>
        </form>
      </div>
    </div>
  );
}