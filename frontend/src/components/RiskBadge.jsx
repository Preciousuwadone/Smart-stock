export default function RiskBadge({ tier }) {
  const colors = {
    low: { bg: "#E7F6EC", text: "#1F9254" },
    medium: { bg: "#FDF0DA", text: "#D6900F" },
    high: { bg: "#FBEAEA", text: "#D64545" },
  };
  const c = colors[tier] || { bg: "#EEF0F2", text: "#5B6472" };

  return (
    <span style={{
      backgroundColor: c.bg, color: c.text, padding: "3px 11px", borderRadius: "999px",
      fontSize: 12, fontWeight: 700, textTransform: "capitalize", whiteSpace: "nowrap",
    }}>
      {tier || "Unscored"}
    </span>
  );
}