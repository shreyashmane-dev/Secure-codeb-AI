import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark, oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import { useTheme } from "../context/ThemeContext";

const AIExplanationPanel = ({ issue }) => {
  const { theme } = useTheme();

  if (!issue) {
    return (
      <section className="panel ai-panel">
        <div className="panel-header">
          <h3>AI Explanation Panel</h3>
        </div>
        <p>Select an issue from the table to view risk reasoning and refactoring suggestions.</p>
      </section>
    );
  }

  return (
    <section className="panel ai-panel">
      <div className="panel-header">
        <h3>{issue.issue_type}</h3>
        <p>
          Severity: {issue.severity.toUpperCase()} | Confidence: {Math.round(issue.confidence || 0)}%
        </p>
      </div>
      <div className="ai-item">
        <h4>Risk Explanation</h4>
        <p>{issue.risk_explanation}</p>
      </div>
      <div className="ai-item">
        <h4>Real-World Attack Scenario</h4>
        <p>{issue.real_world_attack_scenario || "No scenario generated."}</p>
      </div>
      <div className="ai-item">
        <h4>Why This Is Dangerous</h4>
        <p>{issue.why_this_is_dangerous || issue.why_dangerous}</p>
      </div>
      <div className="ai-item">
        <h4>Secure Fix Explanation</h4>
        <p>{issue.secure_fix_explanation || issue.suggested_code}</p>
      </div>
      <div className="ai-item">
        <h4>Best Practice Reference</h4>
        <p>{issue.best_practice_reference || issue.best_practice}</p>
      </div>
      <div className="ai-item">
        <h4>Performance Impact</h4>
        <p>{issue.performance_impact || "No material performance impact expected."}</p>
      </div>
      <div className="ai-item">
        <h4>Refactored Code</h4>
        <SyntaxHighlighter language="python" style={theme === "dark" ? oneDark : oneLight}>
          {issue.refactored_code || issue.refactored_example || "# No suggestion generated"}
        </SyntaxHighlighter>
      </div>
      <div className="ai-item">
        <h4>Before / After Comparison</h4>
        <SyntaxHighlighter language="javascript" style={theme === "dark" ? oneDark : oneLight}>
          {`// Before\n${issue.before_code || issue.code_snippet || "// N/A"}\n\n// After\n${
            issue.after_code || issue.refactored_code || "// N/A"
          }`}
        </SyntaxHighlighter>
      </div>
      <div className="ai-item">
        <h4>Improvement Reasoning</h4>
        <p>{issue.improvement_reasoning || issue.secure_fix_explanation || issue.suggested_code}</p>
      </div>
      <div className="ai-item">
        <h4>Suggested Improved Code</h4>
        <SyntaxHighlighter language="python" style={theme === "dark" ? oneDark : oneLight}>
          {issue.suggested_code || issue.secure_fix_explanation || "# No secure fix generated"}
        </SyntaxHighlighter>
      </div>
      {issue.code_snippet && (
        <div className="ai-item">
          <h4>Detected Code Snippet</h4>
          <SyntaxHighlighter language="javascript" style={theme === "dark" ? oneDark : oneLight}>
            {issue.code_snippet}
          </SyntaxHighlighter>
        </div>
      )}
      <p className="ai-confidence">Confidence: {issue.confidence_score || `${Math.round(issue.confidence || 0)}%`}</p>
    </section>
  );
};

export default AIExplanationPanel;
