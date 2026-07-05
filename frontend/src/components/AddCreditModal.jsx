import { useState } from "react";
import client from "../api/client";

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
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ background: "white", padding: 24, borderRadius: 8, width: 320 }}>
        <h3>Record Credit Sale</h3>
        <form onSubmit={handleSubmit}>
          <input placeholder="Description (e.g. 2 bags of rice)" value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })} required />
          <input placeholder="Amount (₦)" type="number" value={form.amount}
            onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
          {error && <p style={{ color: "red" }}>{error}</p>}
          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <button type="submit" disabled={saving}>{saving ? "Saving..." : "Save"}</button>
            <button type="button" onClick={onClose}>Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
}