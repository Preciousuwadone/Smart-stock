import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import client from "../api/client";
import RiskBadge from "../components/RiskBadge";
import AddCreditModal from "../components/AddCreditModal";

export default function CustomerDetail() {
  const { id } = useParams();
  const [customer, setCustomer] = useState(null);
  const [score, setScore] = useState(null);
  const [scoring, setScoring] = useState(false);
  const [reminding, setReminding] = useState(false);
  const [reminderResult, setReminderResult] = useState(null);
  const [showAddCredit, setShowAddCredit] = useState(false);

  const load = async () => {
    const res = await client.get(`/api/customers/${id}`);
    setCustomer(res.data);
  };

  useEffect(() => { load(); }, [id]);

  const runScore = async () => {
    setScoring(true);
    try {
      const res = await client.post(`/api/customers/${id}/score`);
      setScore(res.data);
    } catch (err) {
      alert(err.response?.data?.error || "Scoring failed");
    } finally {
      setScoring(false);
    }
  };

  const sendReminder = async () => {
    setReminding(true);
    setReminderResult(null);
    try {
      const res = await client.post(`/api/customers/${id}/remind`);
      setReminderResult(res.data);
    } catch (err) {
      setReminderResult({ error: err.response?.data?.error || "Failed to send reminder" });
    } finally {
      setReminding(false);
    }
  };

  if (!customer) return <p>Loading...</p>;

  return (
    <div style={{ maxWidth: 700, margin: "40px auto", fontFamily: "sans-serif" }}>
      <Link to="/">← Back</Link>
      <h2>{customer.full_name}</h2>
      <p>{customer.phone}</p>

      <div style={{ background: "#f3f4f6", padding: 16, borderRadius: 8, margin: "16px 0" }}>
        <p><strong>Outstanding:</strong> ₦{parseFloat(customer.balance.outstanding).toLocaleString()}</p>
        <p><strong>Total Credit:</strong> ₦{parseFloat(customer.balance.total_credit).toLocaleString()}</p>
        <p><strong>Total Paid:</strong> ₦{parseFloat(customer.balance.total_paid).toLocaleString()}</p>
        {customer.virtual_account && (
          <p><strong>Repayment account:</strong> {customer.virtual_account.account_number} ({customer.virtual_account.bank_name})
            {/*customer.virtual_account.status === "simulated" && <em> — simulated</em>*/}
          </p>
        )}
      </div>

      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        <button onClick={() => setShowAddCredit(true)}>+ Record Credit Sale</button>
        <button onClick={runScore} disabled={scoring}>{scoring ? "Scoring..." : "Run AI Credit Score"}</button>
        <button onClick={sendReminder} disabled={reminding || customer.balance.outstanding <= 0}>
          {reminding ? "Sending..." : "Send Reminder"}
        </button>
      </div>

      {score && (
        <div style={{ border: "1px solid #e5e7eb", padding: 16, borderRadius: 8, marginBottom: 16 }}>
          <p><strong>Risk Score:</strong> {score.score}/100 <RiskBadge tier={score.risk_tier} /></p>
          <p><strong>Default probability:</strong> {(score.default_probability * 100).toFixed(1)}%</p>
        </div>
      )}

      {reminderResult && (
        <div style={{ border: "1px solid #e5e7eb", padding: 16, borderRadius: 8, marginBottom: 16 }}>
          {reminderResult.error ? (
            <p style={{ color: "red" }}>{reminderResult.error}</p>
          ) : (
            <>
              <p>Checkout link: <a href={reminderResult.checkout_link} target="_blank" rel="noreferrer">{reminderResult.checkout_link}</a></p>
              <p>Email sent: {reminderResult.email_sent ? "Yes" : `No (${reminderResult.email_error || "unknown"})`}</p>
              <p>SMS sent: {reminderResult.sms_sent ? "Yes" : `No (${reminderResult.sms_error || "not configured"})`}</p>
            </>
          )}
        </div>
      )}

      <h3>Transaction History</h3>
      <ul>
        {customer.transactions.map((t) => (
          <li key={t.id}>{t.description} — ₦{parseFloat(t.amount).toLocaleString()} ({new Date(t.created_at).toLocaleDateString()})</li>
        ))}
      </ul>

      <h3>Payment History</h3>
      <ul>
        {customer.payments.map((p) => (
          <li key={p.id}>₦{parseFloat(p.amount).toLocaleString()} via {p.source} ({p.paid_at ? new Date(p.paid_at).toLocaleDateString() : "pending"})</li>
        ))}
      </ul>

      {showAddCredit && (
        <AddCreditModal
          customerId={id}
          onClose={() => setShowAddCredit(false)}
          onCreated={() => { setShowAddCredit(false); load(); }}
        />
      )}
    </div>
  );
}