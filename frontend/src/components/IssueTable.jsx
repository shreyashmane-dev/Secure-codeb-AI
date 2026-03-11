import { useMemo, useState } from "react";
import { severityColor } from "../utils/format";

const IssueTable = ({ issues = [], onSelectIssue, selectedIssueId }) => {
  const [severityFilter, setSeverityFilter] = useState("all");
  const [fileFilter, setFileFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");

  const filtered = useMemo(() => {
    return issues.filter((item) => {
      if (severityFilter !== "all" && item.severity !== severityFilter) {
        return false;
      }
      if (categoryFilter !== "all" && item.category !== categoryFilter) {
        return false;
      }
      if (fileFilter && !item.file_path.toLowerCase().includes(fileFilter.toLowerCase())) {
        return false;
      }
      return true;
    });
  }, [issues, severityFilter, fileFilter, categoryFilter]);

  return (
    <section className="panel">
      <div className="panel-header">
        <h3>Issue Table</h3>
        <p>{filtered.length} issues matched</p>
      </div>
      <div className="issue-filters">
        <select value={severityFilter} onChange={(event) => setSeverityFilter(event.target.value)}>
          <option value="all">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select value={categoryFilter} onChange={(event) => setCategoryFilter(event.target.value)}>
          <option value="all">All Categories</option>
          <option value="security">Security</option>
          <option value="dependency">Dependency</option>
          <option value="reliability">Reliability</option>
          <option value="quality">Quality</option>
          <option value="maintainability">Maintainability</option>
        </select>
        <input
          type="text"
          placeholder="Filter by file path"
          value={fileFilter}
          onChange={(event) => setFileFilter(event.target.value)}
        />
      </div>
      <div className="table-wrap">
        <table className="issue-table">
          <thead>
            <tr>
              <th>Severity</th>
              <th>Type</th>
              <th>Category</th>
              <th>File</th>
              <th>Line</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {filtered.slice(0, 600).map((issue) => (
              <tr
                key={issue.issue_id}
                onClick={() => onSelectIssue(issue)}
                className={issue.issue_id === selectedIssueId ? "row-selected" : ""}
              >
                <td>
                  <span className="severity-pill" style={{ background: severityColor(issue.severity) }}>
                    {issue.severity}
                  </span>
                </td>
                <td>{issue.issue_type}</td>
                <td>{issue.category}</td>
                <td title={issue.file_path}>{issue.file_path}</td>
                <td>{issue.line}</td>
                <td>{Math.round(issue.confidence || 0)}%</td>
              </tr>
            ))}
            {!filtered.length && (
              <tr>
                <td colSpan={6} className="empty-cell">
                  No issues match the selected filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
};

export default IssueTable;
