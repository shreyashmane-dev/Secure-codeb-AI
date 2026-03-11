import { useState } from "react";
import { compareScans } from "../api/client";
import { humanizeKey } from "../utils/format";

const ScanComparison = ({ history = [] }) => {
  const [scanA, setScanA] = useState("");
  const [scanB, setScanB] = useState("");
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleCompare = async () => {
    if (!scanA || !scanB) {
      return;
    }
    try {
      setLoading(true);
      setError("");
      const data = await compareScans(scanA, scanB);
      setComparison(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Comparison failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel">
      <div className="panel-header">
        <h3>Scan Comparison Mode</h3>
      </div>
      <div className="comparison-controls">
        <select value={scanA} onChange={(event) => setScanA(event.target.value)}>
          <option value="">Baseline scan</option>
          {history.map((item) => (
            <option key={item.scan_id} value={item.scan_id}>
              {item.scan_id.slice(0, 8)} | {item.source_label}
            </option>
          ))}
        </select>
        <select value={scanB} onChange={(event) => setScanB(event.target.value)}>
          <option value="">Target scan</option>
          {history.map((item) => (
            <option key={item.scan_id} value={item.scan_id}>
              {item.scan_id.slice(0, 8)} | {item.source_label}
            </option>
          ))}
        </select>
        <button type="button" className="primary-btn" onClick={handleCompare} disabled={loading || !scanA || !scanB}>
          {loading ? "Comparing..." : "Compare"}
        </button>
      </div>
      {error && <p className="error-text">{error}</p>}
      {comparison?.score_difference && (
        <div className="comparison-result">
          {Object.entries(comparison.score_difference).map(([key, value]) => (
            <div key={key} className="comparison-row">
              <span>{humanizeKey(key)}</span>
              <span className={Number(value) >= 0 ? "diff-positive" : "diff-negative"}>
                {Number(value) >= 0 ? "+" : ""}
                {value}
              </span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
};

export default ScanComparison;
