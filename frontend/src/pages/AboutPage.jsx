const AboutPage = () => {
  return (
    <main className="page">
      <section className="dashboard-header">
        <h1>About SecureCode AI</h1>
        <p>Enterprise-grade local code analysis platform for security, reliability, and maintainability.</p>
      </section>
      <section className="about-grid">
        <article className="panel">
          <h3>Authentication</h3>
          <p>
            Firebase Authentication secures frontend sessions while FastAPI verifies bearer tokens on all protected scan
            and report endpoints.
          </p>
        </article>
        <article className="panel">
          <h3>Backend Engine</h3>
          <p>
            FastAPI backend runs static scanning with regex rules, Python AST traversal, JavaScript heuristic parsing,
            duplication detection, and dependency risk analysis.
          </p>
        </article>
        <article className="panel">
          <h3>AI Reasoning Layer</h3>
          <p>
            Basic mode uses offline heuristic reasoning, while Advanced mode invokes OpenAI for deep vulnerability
            context, attack scenarios, and refactor-quality secure fixes with fallback safety.
          </p>
        </article>
        <article className="panel">
          <h3>Scoring Framework</h3>
          <p>
            Security, Trust, Reliability, Quality, and Improvement Potential scores are computed through weighted
            severity models and engineering quality signals.
          </p>
        </article>
        <article className="panel">
          <h3>Enterprise Dashboard</h3>
          <p>
            React dashboard delivers real-time scan progress, risk heatmaps, radar and severity charts, issue
            filtering, history, and comparison mode.
          </p>
        </article>
      </section>
    </main>
  );
};

export default AboutPage;
