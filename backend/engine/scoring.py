from __future__ import annotations

from collections import Counter
from typing import Dict, List, Tuple

from .quality_engine import calculate_quality_score
from .reliability_engine import calculate_reliability_score
from .trust_engine import calculate_trust_score


SEVERITY_WEIGHT = {"critical": 12, "high": 8, "medium": 4, "low": 1}


def severity_distribution(issues: List[dict]) -> Dict[str, int]:
    counter = Counter(str(issue.get("severity", "low")).lower() for issue in issues)
    return {
        "critical": counter.get("critical", 0),
        "high": counter.get("high", 0),
        "medium": counter.get("medium", 0),
        "low": counter.get("low", 0),
    }


def security_score(issues: List[dict], lines: int) -> int:
    security_issues = [issue for issue in issues if issue.get("category") in {"security", "dependency"}]
    weighted = sum(SEVERITY_WEIGHT.get(str(issue.get("severity", "low")).lower(), 1) for issue in security_issues)
    density = weighted / max(lines / 100.0, 1.0)
    score = max(0.0, 100.0 - (density * 3.3))
    return int(round(min(100.0, score)))


def _compute_improvement_potential(
    security: int,
    trust: int,
    reliability: int,
    quality: int,
    issues_count: int,
    files_count: int,
) -> int:
    health = security * 0.35 + trust * 0.2 + reliability * 0.2 + quality * 0.25
    issue_density = issues_count / max(files_count, 1)
    potential = (100.0 - health) + min(18.0, issue_density * 4.0)
    return int(max(0, min(100, round(potential))))


def calculate_all_scores(
    issues: List[dict],
    file_metrics: List[dict],
    aggregate_metrics: Dict[str, float],
    total_lines: int,
    total_files: int,
) -> Tuple[Dict[str, int], Dict[str, Dict[str, float | int]]]:
    security = security_score(issues, total_lines)
    trust, trust_details = calculate_trust_score(issues, total_files)
    reliability, reliability_details = calculate_reliability_score(issues, aggregate_metrics)
    quality, quality_details = calculate_quality_score(issues, file_metrics)
    improvement = _compute_improvement_potential(
        security=security,
        trust=trust,
        reliability=reliability,
        quality=quality,
        issues_count=len(issues),
        files_count=total_files,
    )

    scores = {
        "security_score": security,
        "trust_score": trust,
        "reliability_score": reliability,
        "quality_score": quality,
        "improvement_potential": improvement,
    }
    diagnostics = {
        "trust_engine": trust_details,
        "reliability_engine": reliability_details,
        "quality_engine": quality_details,
    }
    return scores, diagnostics
