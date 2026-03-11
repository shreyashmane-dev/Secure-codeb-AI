from __future__ import annotations

from statistics import mean
from typing import Dict, List


def calculate_quality_score(issues: List[dict], file_metrics: List[dict]) -> tuple[int, Dict[str, float]]:
    score = 100
    duplication_hits = sum(1 for issue in issues if "DUPLICATION" in str(issue.get("rule_id", "")))
    long_functions = sum(1 for issue in issues if "LONG_FUNCTION" in str(issue.get("rule_id", "")))
    dead_code_hits = sum(1 for issue in issues if "DEAD_CODE" in str(issue.get("rule_id", "")))
    complexity_hits = sum(1 for issue in issues if "COMPLEXITY" in str(issue.get("rule_id", "")))

    avg_complexity = mean(metric.get("cyclomatic_complexity", 0.0) for metric in file_metrics) if file_metrics else 0.0
    avg_maintainability = (
        mean(metric.get("maintainability_index", 0.0) for metric in file_metrics) if file_metrics else 100.0
    )

    score -= duplication_hits * 4
    score -= long_functions * 3
    score -= dead_code_hits * 2
    score -= complexity_hits * 4

    if avg_complexity > 20:
        score -= 8
    elif avg_complexity > 12:
        score -= 4

    if avg_maintainability < 45:
        score -= 10
    elif avg_maintainability < 65:
        score -= 5

    score = max(0, min(100, score))
    details = {
        "duplication_hits": float(duplication_hits),
        "long_function_hits": float(long_functions),
        "dead_code_hits": float(dead_code_hits),
        "complexity_hits": float(complexity_hits),
        "avg_complexity": round(avg_complexity, 2),
        "avg_maintainability": round(avg_maintainability, 2),
    }
    return int(score), details
