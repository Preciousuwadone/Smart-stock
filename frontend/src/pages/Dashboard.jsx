import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client";
import RiskBadge from "../components/RiskBadge";
import AddCustomerModal from "../components/AddCustomerModal";
import AppHeader from "../components/AppHeader";
import "../styles/AppShell.css";

export default function Dashboard() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [search, setSearch] = useState("");

  const loadCustomers = async () => {
    setLoading(true);
    const res = await client.get("/api/customers");
    setCustomers(res.data);
    setLoading(false);
  };

  useEffect(() => { loadCustomers(); }, []);

  const totalOutstanding = customers.reduce((sum, c) => sum + parseFloat(c.outstanding_balance), 0);
  const atRiskCount = customers.filter((c) => c.risk_tier === "high").length;

  const filtered = useMemo(() => {
    if (!search.trim()) return customers;
    const q = search.trim().toLowerCase();
    return customers.filter((c) => c.full_name.toLowerCase().includes(q));
  }, [customers, search]);

  return (
    <div>
      <AppHeader />
      <div className="app-page">
        <div className="app-page-head">
          <h1>Customers</h1>
          <button onClick={() => setShowAddModal(true)}>+ Add Customer</button>
        </div>

        <div className="app-stats">
          <div className="app-stat-card">
            <div className="app-stat-label">Total Outstanding</div>
            <div className="app-stat-value accent">₦{totalOutstanding.toLocaleString()}</div>
          </div>
          <div className="app-stat-card">
            <div className="app-stat-label">Total Customers</div>
            <div className="app-stat-value">{customers.length}</div>
          </div>
          <div className="app-stat-card">
            <div className="app-stat-label">High Risk Customers</div>
            <div className="app-stat-value" style={{ color: atRiskCount ? "var(--color-danger)" : undefined }}>
              {atRiskCount}
            </div>
          </div>
        </div>

        <div className="app-search">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <circle cx="11" cy="11" r="7" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input placeholder="Search customers..." value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>

        <div className="app-card">
          {loading ? (
            <div className="app-loading">Loading customers…</div>
          ) : filtered.length === 0 ? (
            <div className="app-empty">
              <div className="app-empty-icon">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <circle cx="9" cy="8" r="3" /><path d="M4 20c0-3 2.5-5 5-5s5 2 5 5" />
                </svg>
              </div>
              <p>{search ? "No customers match that search." : "No customers yet. Add your first one to get started."}</p>
            </div>
          ) : (
            <table className="app-table">
              <thead>
                <tr><th>Name</th><th>Outstanding</th><th>Risk</th><th></th></tr>
              </thead>
              <tbody>
                {filtered.map((c) => (
                  <tr key={c.id}>
                    <td className="app-row-name">{c.full_name}</td>
                    <td>₦{parseFloat(c.outstanding_balance).toLocaleString()}</td>
                    <td><RiskBadge tier={c.risk_tier} /></td>
                    <td><Link to={`/customers/${c.id}`} className="app-row-link">View →</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {showAddModal && (
        <AddCustomerModal
          onClose={() => setShowAddModal(false)}
          onCreated={() => { setShowAddModal(false); loadCustomers(); }}
        />
      )}
    </div>
  );
}