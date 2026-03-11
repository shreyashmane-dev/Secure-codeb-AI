import { useEffect, useState } from "react";
import { generateReport, getScanHistory } from "../api/client";

const ReportsPage = () => {
  const [history, setHistory] = useState([]);
  const [selectedScanId, setSelectedScanId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getScanHistory(50)
      .then((items) => {
      setHistory(items);
      if (items[0]) setSelectedScanId(items[0].scan_id);
    })
      .catch((err) => setError(err.response?.data?.error?.message || err.message || "Failed to load scan history."));
  }, []);

  const triggerDownload = (blobData, filename) => {
    const url = URL.createObjectURL(blobData);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const downloadPdf = async () => {
    if (!selectedScanId) return;
    try {
      setLoading(true);
      const blob = await generateReport(selectedScanId, "pdf");
      triggerDownload(blob, `SecureCodeAI-Report-${selectedScanId}.pdf`);
    } catch (err) {
      setError(err.response?.data?.error?.message || err.message || "Failed to generate PDF.");
    } finally {
      setLoading(false);
    }
  };

  const downloadJson = async () => {
    if (!selectedScanId) return;
    try {
      setLoading(true);
      const payload = await generateReport(selectedScanId, "json");
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
      triggerDownload(blob, `SecureCodeAI-Report-${selectedScanId}.json`);
    } catch (err) {
      setError(err.response?.data?.error?.message || err.message || "Failed to generate JSON report.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page">
      <section className="dashboard-header">
        <h1>Report Center</h1>
        <p>Generate enterprise PDF and JSON reports from completed scan history.</p>
      </section>
      <section className="panel">
        <label className="input-label">
          Select Scan
          <select value={selectedScanId} onChange={(event) => setSelectedScanId(event.target.value)}>
            {history.map((item) => (
              <option key={item.scan_id} value={item.scan_id}>
                {item.scan_id.slice(0, 8)} | {item.source_label} | Security {item.scores?.security_score}
              </option>
            ))}
          </select>
        </label>
        <div className="report-actions">
          <button type="button" className="primary-btn" onClick={downloadPdf} disabled={loading || !selectedScanId}>
            Download PDF
          </button>
          <button type="button" className="ghost-btn" onClick={downloadJson} disabled={loading || !selectedScanId}>
            Download JSON
          </button>
        </div>
        {error && <p className="error-text">{error}</p>}
      </section>
    </main>
  );
};

export default ReportsPage;
