import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart as RRadarChart,
  ResponsiveContainer,
} from "recharts";

const RadarChart = ({ scores = {} }) => {
  const data = [
    { metric: "Security", value: scores.security_score || 0 },
    { metric: "Trust", value: scores.trust_score || 0 },
    { metric: "Reliability", value: scores.reliability_score || 0 },
    { metric: "Quality", value: scores.quality_score || 0 },
    { metric: "Improvement", value: scores.improvement_potential || 0 },
  ];

  return (
    <section className="panel chart-panel">
      <div className="panel-header">
        <h3>Score Radar</h3>
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={280}>
          <RRadarChart data={data}>
            <PolarGrid stroke="rgba(148, 163, 184, 0.25)" />
            <PolarAngleAxis dataKey="metric" stroke="var(--text-muted)" />
            <PolarRadiusAxis stroke="var(--text-muted)" />
            <Radar name="Score" dataKey="value" stroke="var(--accent)" fill="var(--accent)" fillOpacity={0.4} />
          </RRadarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
};

export default RadarChart;
