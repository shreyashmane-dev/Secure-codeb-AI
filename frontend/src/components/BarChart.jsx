import {
  Bar,
  BarChart as RBarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const BarChart = ({ distribution = {} }) => {
  const data = [
    { severity: "Critical", count: distribution.critical || 0 },
    { severity: "High", count: distribution.high || 0 },
    { severity: "Medium", count: distribution.medium || 0 },
    { severity: "Low", count: distribution.low || 0 },
  ];

  return (
    <section className="panel chart-panel">
      <div className="panel-header">
        <h3>Severity Distribution</h3>
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={280}>
          <RBarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.2)" />
            <XAxis dataKey="severity" stroke="var(--text-muted)" />
            <YAxis stroke="var(--text-muted)" />
            <Tooltip />
            <Bar dataKey="count" fill="var(--accent)" radius={[6, 6, 0, 0]} />
          </RBarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
};

export default BarChart;
