const AIModeToggle = ({ aiMode, onChange }) => {
  const advanced = aiMode === "advanced";
  return (
    <section className="panel ai-mode-panel">
      <div className="panel-header">
        <h3>AI Mode</h3>
        <p>{advanced ? "Advanced GPT reasoning enabled" : "Basic offline engine enabled"}</p>
      </div>
      <div className="ai-mode-toggle">
        <button
          type="button"
          className={advanced ? "ghost-btn" : "primary-btn"}
          onClick={() => onChange("basic")}
        >
          Basic Mode
        </button>
        <button
          type="button"
          className={advanced ? "primary-btn" : "ghost-btn"}
          onClick={() => onChange("advanced")}
        >
          Advanced AI Mode
        </button>
      </div>
      <p className="ai-mode-note">
        Basic: Regex + AST + scoring only. Advanced: adds OpenAI vulnerability reasoning and refactor simulations.
      </p>
    </section>
  );
};

export default AIModeToggle;
