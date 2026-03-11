const ProgressTracker = ({ status }) => {
  if (!status) {
    return null;
  }

  return (
    <section className="panel progress-panel">
      <div className="panel-header">
        <h3>Real-Time Scan Progress</h3>
        <p>{status.status.toUpperCase()}</p>
      </div>
      <div className="progress-track">
        <div className="progress-bar" style={{ width: `${status.progress || 0}%` }} />
      </div>
      <div className="progress-meta">
        <span>{status.progress || 0}%</span>
        <span>{status.message}</span>
      </div>
    </section>
  );
};

export default ProgressTracker;
