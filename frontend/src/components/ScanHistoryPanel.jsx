const ScanHistoryPanel = ({ items = [], onOpen }) => {
  return (
    <section className="panel">
      <div className="panel-header">
        <h3>Scan History</h3>
        <p>{items.length} recent scans</p>
      </div>
      <div className="history-list">
        {items.map((item) => (
          <article key={item.scan_id} className="history-item">
            <div>
              <p className="history-title">{item.source_label}</p>
              <p className="history-meta">
                {item.source_type.toUpperCase()} | Issues: {item.totals?.total_issues_found ?? "-"} | Security:{" "}
                {item.scores?.security_score ?? "-"}
              </p>
            </div>
            <button type="button" className="ghost-btn" onClick={() => onOpen(item.scan_id)}>
              Open
            </button>
          </article>
        ))}
        {!items.length && <p>No previous scans found.</p>}
      </div>
    </section>
  );
};

export default ScanHistoryPanel;
