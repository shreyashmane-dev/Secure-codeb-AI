export const formatPercent = (value) => `${Math.round(Number(value || 0))}%`;

export const severityOrder = ["critical", "high", "medium", "low"];

export const severityColor = (severity) => {
  switch ((severity || "").toLowerCase()) {
    case "critical":
      return "var(--danger)";
    case "high":
      return "#fb7185";
    case "medium":
      return "var(--warning)";
    case "low":
      return "var(--success)";
    default:
      return "var(--muted)";
  }
};

export const humanizeKey = (value) =>
  String(value || "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (m) => m.toUpperCase());
