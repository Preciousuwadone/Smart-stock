import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import client from "../api/client";
import RiskBadge from "../components/RiskBadge";
import AddCreditModal from "../components/AddCreditModal";
import AppHeader from "../components/AppHeader";
import "../styles/AppShell.css";

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

  if (!customer) {
    return (
      <div>
        <AppHeader />
        <div className="app-page"><div className="app-loading">Loading customer…</div></div>
      </div>
    );
  }

  const outstanding = parseFloat(customer.balance.outstanding);

  return (
    <div>
      <AppHeader />
      <div className="app-page">
        <Link to="/dashboard" className="app-back-link">← Back to customers</Link>

        <div className="app-customer-head">
          <div>
            <h1>{customer.full_name}</h1>
            <span className="app-customer-phone">{customer.phone}</span>
          </div>
          {score && <RiskBadge tier={score.risk_tier} />}
        </div>

        <div className="app-balance-grid">
          <div className="app-balance-card outstanding">
            <div className="label">Outstanding</div>
            <div className="value">₦{outstanding.toLocaleString()}</div>
          </div>
          <div className="app-balance-card">
            <div className="label">Total Credit</div>
            <div className="value">₦{parseFloat(customer.balance.total_credit).toLocaleString()}</div>
          </div>
          <div className="app-balance-card paid">
            <div className="label">Total Paid</div>
            <div className="value">₦{parseFloat(customer.balance.total_paid).toLocaleString()}</div>
          </div>
        </div>

        {customer.virtual_account && (
          <div className="app-va-card">
            <div>
              <div className="label">Repayment Account</div>
              <div className="value">{customer.virtual_account.account_number} · {customer.virtual_account.bank_name}</div>
            </div>
            {customer.virtual_account.status === "simulated" && (
              <span className="app-va-badge">Simulated (sandbox limit)</span>
            )}
          </div>
        )}

        <div className="app-actions">
          <button onClick={() => setShowAddCredit(true)}>+ Record Credit Sale</button>
          <button className="app-btn-secondary" onClick={runScore} disabled={scoring}>
            {scoring ? "Scoring…" : "Run AI Credit Score"}
          </button>
          <button className="app-btn-secondary" onClick={sendReminder} disabled={reminding || outstanding <= 0}>
            {reminding ? "Sending…" : "Send Reminder"}
          </button>
        </div>

        {score && (
          <div className="app-result-card">
            <div className="app-result-row">
              <span>Risk Score</span>
              <strong>{score.score}/100</strong>
            </div>
            <div className="app-result-row">
              <span>Default probability</span>
              <strong>{(score.default_probability * 100).toFixed(1)}%</strong>
            </div>
          </div>
        )}

        {reminderResult && (
          <div className={`app-result-card ${reminderResult.error ? "error" : ""}`}>
            {reminderResult.error ? (
              <p style={{ margin: 0, color: "var(--color-danger)" }}>{reminderResult.error}</p>
            ) : (
              <>
                <div className="app-result-row">
                  <span>Checkout link</span>
                  <a href={reminderResult.checkout_link} target="_blank" rel="noreferrer">Open link ↗</a>
                </div>
                <div className="app-result-row">
                  <span>Email</span>
                  <span className={reminderResult.email_sent ? "app-result-ok" : "app-result-fail"}>
                    {reminderResult.email_sent ? "Sent" : `Not sent (${reminderResult.email_error || "unknown"})`}
                  </span>
                </div>
                <div className="app-result-row">
                  <span>SMS</span>
                  <span className={reminderResult.sms_sent ? "app-result-ok" : "app-result-fail"}>
                    {reminderResult.sms_sent ? "Sent" : `Not sent (${reminderResult.sms_error || "not configured"})`}
                  </span>
                </div>
              </>
            )}
          </div>
        )}

        <h3 className="app-section-title">Transaction History</h3>
        <div className="app-card">
          {customer.transactions.length === 0 ? (
            <div className="app-empty">No credit transactions yet.</div>
          ) : (
            <ul className="app-list" style={{ padding: "4px 20px" }}>
              {customer.transactions.map((t) => (
                <li className="app-list-item" key={t.id}>
                  <div>
                    <div className="desc">{t.description}</div>
                    <div className="meta">{new Date(t.created_at).toLocaleDateString()}</div>
                  </div>
                  <span className="app-list-amount">₦{parseFloat(t.amount).toLocaleString()}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <h3 className="app-section-title">Payment History</h3>
        <div className="app-card">
          {customer.payments.length === 0 ? (
            <div className="app-empty">No payments recorded yet.</div>
          ) : (
            <ul className="app-list" style={{ padding: "4px 20px" }}>
              {customer.payments.map((p) => (
                <li className="app-list-item" key={p.id}>
                  <div>
                    <div className="desc">via {p.source}</div>
                    <div className="meta">{p.paid_at ? new Date(p.paid_at).toLocaleDateString() : "Pending"}</div>
                  </div>
                  <span className="app-list-amount">₦{parseFloat(p.amount).toLocaleString()}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

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