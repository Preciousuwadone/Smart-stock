import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client";
import RiskBadge from "../components/RiskBadge";
import AddCustomerModal from "../components/AddCustomerModal";

export default function Dashboard() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  const loadCustomers = async () => {
    setLoading(true);
    const res = await client.get("/api/customers");
    setCustomers(res.data);
    setLoading(false);
  };

  useEffect(() => { loadCustomers(); }, []);

  const totalOutstanding = customers.reduce((sum, c) => sum + parseFloat(c.outstanding_balance), 0);

  return (
    <div style={{ maxWidth: 900, margin: "40px auto", fontFamily: "sans-serif" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Customers</h2>
        <button onClick={() => setShowAddModal(true)}>+ Add Customer</button>
      </div>

      <div style={{ background: "#f3f4f6", padding: 16, borderRadius: 8, margin: "16px 0" }}>
        <strong>Total Outstanding:</strong> ₦{totalOutstanding.toLocaleString()}
        <span style={{ marginLeft: 24 }}><strong>Customers:</strong> {customers.length}</span>
      </div>

      {loading ? <p>Loading...</p> : (
        <table width="100%" cellPadding="10" style={{ borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "2px solid #e5e7eb" }}>
              <th>Name</th><th>Outstanding</th><th></th>
            </tr>
          </thead>
          <tbody>
            {customers.map((c) => (
              <tr key={c.id} style={{ borderBottom: "1px solid #e5e7eb" }}>
                <td>{c.full_name}</td>
                <td>₦{parseFloat(c.outstanding_balance).toLocaleString()}</td>
                <td><Link to={`/customers/${c.id}`}>View →</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {showAddModal && (
        <AddCustomerModal
          onClose={() => setShowAddModal(false)}
          onCreated={() => { setShowAddModal(false); loadCustomers(); }}
        />
      )}
    </div>
  );
}