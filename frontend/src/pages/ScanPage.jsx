import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getScanStatus, startGithubScan, startUploadScan } from "../api/client";
import AIModeToggle from "../components/AIModeToggle";
import GitHubLinkInput from "../components/GitHubLinkInput";
import ProgressTracker from "../components/ProgressTracker";
import ZipUploader from "../components/ZipUploader";

const ScanPage = () => {
  const navigate = useNavigate();
  const [aiMode, setAiMode] = useState("basic");
  const [activeScanId, setActiveScanId] = useState("");
  const [scanStatus, setScanStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [completedScanId, setCompletedScanId] = useState("");

  useEffect(() => {
    if (!activeScanId) return;
    let alive = true;
    const poll = async () => {
      try {
        const data = await getScanStatus(activeScanId);
        if (!alive) return;
        setScanStatus(data);
        if (data.status === "completed") {
          setCompletedScanId(activeScanId);
          setLoading(false);
          setActiveScanId("");
        }
        if (data.status === "failed") {
          setLoading(false);
          setActiveScanId("");
          const err = data.error?.message || data.error || "Scan failed.";
          setError(err);
        }
      } catch (err) {
        if (!alive) return;
        setLoading(false);
        setError(err.response?.data?.error?.message || err.message || "Unable to fetch scan status.");
      }
    };
    poll();
    const timer = setInterval(poll, 2200);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [activeScanId]);

  const handleUploadScan = async ({ file, aiMode: mode, includeExtensions, excludePaths, maxFiles }) => {
    try {
      setLoading(true);
      setError("");
      setCompletedScanId("");
      const formData = new FormData();
      formData.append("file", file);
      formData.append("ai_mode", mode);
      formData.append("include_extensions", includeExtensions);
      formData.append("exclude_paths", excludePaths);
      formData.append("max_files", String(maxFiles));
      const data = await startUploadScan(formData);
      setActiveScanId(data.scan_id);
      setScanStatus({ status: data.status, progress: 0, message: data.message });
    } catch (err) {
      setLoading(false);
      setError(err.response?.data?.error?.message || err.message || "Upload scan request failed.");
    }
  };

  const handleGithubScan = async (payload) => {
    try {
      setLoading(true);
      setError("");
      setCompletedScanId("");
      const data = await startGithubScan(payload);
      setActiveScanId(data.scan_id);
      setScanStatus({ status: data.status, progress: 0, message: data.message });
    } catch (err) {
      setLoading(false);
      setError(err.response?.data?.error?.message || err.message || "GitHub scan request failed.");
    }
  };

  return (
    <main className="page">
      <section className="dashboard-header">
        <h1>Scan Workspace</h1>
        <p>Run authenticated scans with Basic offline engine or Advanced OpenAI-assisted analysis.</p>
      </section>

      <AIModeToggle aiMode={aiMode} onChange={setAiMode} />

      <section className="scan-form-grid">
        <ZipUploader onSubmit={handleUploadScan} loading={loading} aiMode={aiMode} />
        <GitHubLinkInput onSubmit={handleGithubScan} loading={loading} aiMode={aiMode} />
      </section>

      <ProgressTracker status={scanStatus} />

      {completedScanId && (
        <section className="panel success-panel">
          <p>Scan complete: {completedScanId}</p>
          <button type="button" className="primary-btn" onClick={() => navigate(`/results/${completedScanId}`)}>
            Open Results
          </button>
        </section>
      )}

      {error && <p className="error-text">{error}</p>}
    </main>
  );
};

export default ScanPage;
