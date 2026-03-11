import { humanizeKey } from "../utils/format";

const scoreKeys = [
  "security_score",
  "trust_score",
  "reliability_score",
  "quality_score",
  "improvement_potential",
];

const scoreTone = (value) => {
  if (value >= 85) return "score-good";
  if (value >= 65) return "score-mid";
  return "score-bad";
};

const ScoreCards = ({ scores = {}, totals = {} }) => {
  return (
    <section className="score-grid">
      {scoreKeys.map((key) => (
        <article key={key} className="score-card glass-card">
          <p className="score-label">{humanizeKey(key)}</p>
          <p className={`score-value ${scoreTone(Number(scores[key] || 0))}`}>{Math.round(scores[key] || 0)}</p>
        </article>
      ))}
      <article className="score-card glass-card">
        <p className="score-label">Total Issues</p>
        <p className="score-value">{totals.total_issues_found || 0}</p>
      </article>
      <article className="score-card glass-card">
        <p className="score-label">Files Scanned</p>
        <p className="score-value">{totals.total_files_scanned || 0}</p>
      </article>
      <article className="score-card glass-card">
        <p className="score-label">Lines Analyzed</p>
        <p className="score-value">{totals.total_lines_analyzed || 0}</p>
      </article>
    </section>
  );
};

export default ScoreCards;
