import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getAnalytics, getScanHistory } from "../api/client";
import ScanComparison from "../components/ScanComparison";
import ScanHistoryPanel from "../components/ScanHistoryPanel";

const DashboardPage = () => {
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState("");

  const loadMeta = async () => {
    const [historyItems, analyticsData] = await Promise.all([getScanHistory(30), getAnalytics()]);
    setHistory(historyItems);
    setAnalytics(analyticsData);
  };

  useEffect(() => {
    loadMeta().catch((err) =>
      setError(err.response?.data?.error?.message || err.message || "Failed to load dashboard metadata.")
    );
  }, []);

  return (
    <main className="page">
      <section className="dashboard-header">
        <h1>Security & Reliability Dashboard</h1>
        <p>Run scans, monitor progress, and compare historical codebase risk posture.</p>
        <div>
          <button type="button" className="primary-btn" onClick={() => navigate("/scan")}>
            New Scan
          </button>
        </div>
      </section>

      {analytics && (
        <section className="analytics-grid">
          <article className="glass-card metric-card">
            <p>Total Scans</p>
            <h3>{analytics.total_scans || 0}</h3>
          </article>
          <article className="glass-card metric-card">
            <p>Avg Security</p>
            <h3>{Math.round(analytics.avg_security_score || 0)}</h3>
          </article>
          <article className="glass-card metric-card">
            <p>Avg Reliability</p>
            <h3>{Math.round(analytics.avg_reliability_score || 0)}</h3>
          </article>
          <article className="glass-card metric-card">
            <p>Avg Quality</p>
            <h3>{Math.round(analytics.avg_quality_score || 0)}</h3>
          </article>
        </section>
      )}

      {error && <p className="error-text">{error}</p>}

      <section className="dashboard-bottom">
        <ScanHistoryPanel items={history} onOpen={(scanId) => navigate(`/results/${scanId}`)} />
        <ScanComparison history={history} />
      </section>
    </main>
  );
};

export default DashboardPage;
