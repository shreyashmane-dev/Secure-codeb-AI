import { useState } from "react";

const GitHubLinkInput = ({ onSubmit, loading, aiMode }) => {
  const [repoUrl, setRepoUrl] = useState("");
  const [branch, setBranch] = useState("");
  const [includeExtensions, setIncludeExtensions] = useState(".py,.js,.jsx,.ts,.tsx");
  const [excludePaths, setExcludePaths] = useState("node_modules,.git,dist,build,.venv");
  const [maxFiles, setMaxFiles] = useState(1200);

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!repoUrl || loading) {
      return;
    }
    onSubmit({
      repo_url: repoUrl.trim(),
      branch: branch.trim() || null,
      ai_mode: aiMode,
      include_extensions: includeExtensions
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      exclude_paths: excludePaths
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      max_files: Number(maxFiles),
    });
  };

  return (
    <form className="panel" onSubmit={handleSubmit}>
      <div className="panel-header">
        <h3>Scan GitHub Repository</h3>
        <p>Clone repository locally, perform static-only scanning, then cleanup temp folders.</p>
      </div>
      <label className="input-label">
        Repository URL
        <input
          type="url"
          value={repoUrl}
          onChange={(event) => setRepoUrl(event.target.value)}
          placeholder="https://github.com/org/repo"
          required
        />
      </label>
      <label className="input-label">
        Branch (Optional)
        <input
          type="text"
          value={branch}
          onChange={(event) => setBranch(event.target.value)}
          placeholder="main"
        />
      </label>
      <label className="input-label">
        Include Extensions
        <input
          type="text"
          value={includeExtensions}
          onChange={(event) => setIncludeExtensions(event.target.value)}
        />
      </label>
      <label className="input-label">
        Exclude Paths
        <input
          type="text"
          value={excludePaths}
          onChange={(event) => setExcludePaths(event.target.value)}
        />
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
      <button type="submit" className="primary-btn" disabled={loading || !repoUrl}>
        {loading ? "Scanning..." : "Start GitHub Scan"}
      </button>
    </form>
  );
};

export default GitHubLinkInput;
