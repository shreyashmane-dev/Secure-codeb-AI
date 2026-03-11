import { Link } from "react-router-dom";

const LandingPage = () => {
  return (
    <main className="page page-landing">
      <section className="hero glass-card">
        <p className="hero-tag">Enterprise Secure Dev Platform</p>
        <h1>SecureCode AI</h1>
        <p>
          Intelligent offline code security and reliability analyzer with AST-driven detection, heuristic reasoning,
          multi-dimensional scoring, and remediation-grade AI guidance.
        </p>
        <div className="hero-actions">
          <Link to="/login" className="primary-btn">
            Secure Login
          </Link>
          <Link to="/signup" className="ghost-btn">
            Create Account
          </Link>
        </div>
      </section>

      <section className="landing-grid">
        <article className="glass-card">
          <h3>Security Intelligence</h3>
          <p>Detect injections, secrets, unsafe auth logic, insecure file handling, and dependency risks offline.</p>
        </article>
        <article className="glass-card">
          <h3>Reliability Analytics</h3>
          <p>Quantify exception handling quality, defensive coding patterns, and maintainability weaknesses.</p>
        </article>
        <article className="glass-card">
          <h3>Actionable Refactoring</h3>
          <p>Issue-level AI explanation panel provides risk context, best practices, and refactored snippets.</p>
        </article>
      </section>
    </main>
  );
};

export default LandingPage;
