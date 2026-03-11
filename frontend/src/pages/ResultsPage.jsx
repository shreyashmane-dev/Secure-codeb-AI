import { useEffect, useMemo, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import { exportScanJson, generateReport, getScanStatus } from "../api/client";
import AIExplanationPanel from "../components/AIExplanationPanel";
import BarChart from "../components/BarChart";
import HeatMapGrid from "../components/HeatMapGrid";
import IssueTable from "../components/IssueTable";
import RadarChart from "../components/RadarChart";
import ScoreCards from "../components/ScoreCards";

const ResultsPage = () => {
  const { scanId } = useParams();
  const location = useLocation();
  const [result, setResult] = useState(location.state?.result || null);
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [loading, setLoading] = useState(!location.state?.result);
  const [error, setError] = useState("");
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    if (!scanId) {
      return;
    }
    if (result) {
      return;
    }
    let alive = true;
    const loadResult = async () => {
      try {
        setLoading(true);
        const status = await getScanStatus(scanId);
        if (!alive) return;
        if (status.status !== "completed" || !status.result) {
          setError("Scan is not completed yet. Return to dashboard for live progress.");
          return;
        }
        setResult(status.result);
      } catch (err) {
        if (alive) {
          setError(err.response?.data?.error?.message || err.message || "Unable to load scan result.");
        }
      } finally {
        if (alive) {
          setLoading(false);
        }
      }
    };
    loadResult();
    return () => {
      alive = false;
    };
  }, [scanId, result]);

  useEffect(() => {
    if (result?.issues?.length && !selectedIssue) {
      setSelectedIssue(result.issues[0]);
    }
  }, [result, selectedIssue]);

  const topRisks = useMemo(() => (result?.file_risk_heatmap || []).slice(0, 60), [result]);

  const triggerDownload = (blobData, filename) => {
    const url = URL.createObjectURL(blobData);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const handleJsonExport = async () => {
    if (!scanId) return;
    try {
      setDownloading(true);
      const jsonData = await exportScanJson(scanId);
      const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: "application/json" });
      triggerDownload(blob, `securecode-ai-scan-${scanId}.json`);
    } catch (err) {
      setError(err.response?.data?.error?.message || err.message || "JSON export failed.");
    } finally {
      setDownloading(false);
    }
  };

  const handlePdfReport = async () => {
    if (!scanId) return;
    try {
      setDownloading(true);
      const pdfBlob = await generateReport(scanId, "pdf");
      triggerDownload(pdfBlob, `SecureCodeAI-Report-${scanId}.pdf`);
    } catch (err) {
      setError(err.response?.data?.error?.message || err.message || "PDF generation failed.");
    } finally {
      setDownloading(false);
    }
  };

  if (loading) {
    return (
      <main className="page">
        <p>Loading scan result...</p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="page">
        <p className="error-text">{error}</p>
      </main>
    );
  }

  if (!result) {
    return (
      <main className="page">
        <p>No result found.</p>
      </main>
    );
  }

  return (
    <main className="page">
      <section className="results-header">
        <div>
          <h1>Scan Results</h1>
          <p>
            Scan ID: {result.scan_id} | Source: {result.source_label}
          </p>
        </div>
        <div className="results-actions">
          <button type="button" className="ghost-btn" onClick={handleJsonExport} disabled={downloading}>
            Export JSON
          </button>
          <button type="button" className="primary-btn" onClick={handlePdfReport} disabled={downloading}>
            Download PDF Report
          </button>
        </div>
      </section>

      <ScoreCards scores={result.scores} totals={result.totals} />

      <section className="panel">
        <div className="panel-header">
          <h3>Advanced Metrics</h3>
          <p>AI Mode: {result.metadata?.ai_mode_applied || "basic"}</p>
        </div>
        <div className="analytics-grid">
          <article className="glass-card metric-card">
            <p>Dependency Risk Score</p>
            <h3>{result.metadata?.dependency_risk_score ?? "-"}</h3>
          </article>
          <article className="glass-card metric-card">
            <p>Test Coverage Score</p>
            <h3>{result.metadata?.test_coverage?.test_coverage_score ?? "-"}</h3>
          </article>
          <article className="glass-card metric-card">
            <p>Code Maturity Index</p>
            <h3>{result.metadata?.code_maturity?.code_maturity_index ?? "-"}</h3>
          </article>
          <article className="glass-card metric-card">
            <p>AI Enriched Issues</p>
            <h3>{result.metadata?.ai_diagnostics?.processed ?? 0}</h3>
          </article>
        </div>
      </section>

      <section className="chart-grid">
        <BarChart distribution={result.severity_distribution} />
        <RadarChart scores={result.scores} />
      </section>

      <HeatMapGrid files={topRisks} />

      <section className="results-grid">
        <IssueTable
          issues={result.issues}
          selectedIssueId={selectedIssue?.issue_id}
          onSelectIssue={(issue) => setSelectedIssue(issue)}
        />
        <AIExplanationPanel issue={selectedIssue} />
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3>Improvement Recommendations</h3>
        </div>
        <ol className="recommendation-list">
          {(result.recommendations || []).map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ol>
      </section>
    </main>
  );
};

export default ResultsPage;
