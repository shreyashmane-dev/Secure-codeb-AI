const riskColor = (score) => {
  if (score >= 80) return "rgba(239, 68, 68, 0.9)";
  if (score >= 60) return "rgba(245, 158, 11, 0.85)";
  if (score >= 35) return "rgba(251, 191, 36, 0.75)";
  return "rgba(34, 197, 94, 0.75)";
};

const HeatMapGrid = ({ files = [] }) => {
  return (
    <section className="panel">
      <div className="panel-header">
        <h3>File Risk Heatmap</h3>
      </div>
      <div className="heatmap-grid">
        {files.slice(0, 120).map((item) => (
          <article
            key={`${item.file_path}-${item.risk_score}`}
            className="heat-cell"
            style={{ borderColor: riskColor(Number(item.risk_score || 0)) }}
            title={`${item.file_path} | risk: ${item.risk_score}`}
          >
            <p className="heat-path">{item.file_path}</p>
            <p className="heat-meta">
              Risk {Math.round(Number(item.risk_score || 0))} | Issues {item.issue_count || 0}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
};

export default HeatMapGrid;
