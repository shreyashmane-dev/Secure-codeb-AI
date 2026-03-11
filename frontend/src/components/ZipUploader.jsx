import { useState } from "react";

const ZipUploader = ({ onSubmit, loading, aiMode }) => {
  const [file, setFile] = useState(null);
  const [includeExtensions, setIncludeExtensions] = useState(".py,.js,.jsx,.ts,.tsx");
  const [excludePaths, setExcludePaths] = useState("node_modules,.git,dist,build,.venv");
  const [maxFiles, setMaxFiles] = useState(1200);

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!file || loading) return;
    onSubmit({
      file,
      aiMode,
      includeExtensions,
      excludePaths,
      maxFiles: Number(maxFiles),
    });
  };

  return (
    <form className="panel" onSubmit={handleSubmit}>
      <div className="panel-header">
        <h3>Upload ZIP Source</h3>
        <p>Safe ZIP extraction with size validation and static-only analysis.</p>
      </div>
      <label className="input-label">
        Source ZIP (max 25MB)
        <input
          type="file"
          accept=".zip"
          onChange={(event) => setFile(event.target.files?.[0] || null)}
          required
        />
      </label>
      <label className="input-label">
        Include Extensions
        <input type="text" value={includeExtensions} onChange={(event) => setIncludeExtensions(event.target.value)} />
      </label>
      <label className="input-label">
        Exclude Paths
        <input type="text" value={excludePaths} onChange={(event) => setExcludePaths(event.target.value)} />
      </label>
      <label className="input-label">
        Max Files
        <input
          type="number"
          min={100}
          max={5000}
          value={maxFiles}
          onChange={(event) => setMaxFiles(event.target.value)}
        />
      </label>
      <button type="submit" className="primary-btn" disabled={!file || loading}>
        {loading ? "Scanning..." : "Start ZIP Scan"}
      </button>
    </form>
  );
};

export default ZipUploader;
