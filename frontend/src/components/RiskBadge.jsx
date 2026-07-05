export default function RiskBadge({ tier }) {
  const colors = {
    low: { bg: "#dcfce7", text: "#166534" },
    medium: { bg: "#fef9c3", text: "#854d0e" },
    high: { bg: "#fee2e2", text: "#991b1b" },
  };
  const c = colors[tier] || { bg: "#e5e7eb", text: "#374151" };

  return (
    <span
      style={{
        backgroundColor: c.bg,
        color: c.text,
        padding: "2px 10px",
        borderRadius: "999px",
        fontSize: "12px",
        fontWeight: 600,
        textTransform: "capitalize",
      }}
    >
      {tier || "unscored"}
    </span>
  );
}