from __future__ import annotations

from typing import Dict, List


def calculate_reliability_score(issues: List[dict], aggregate_metrics: Dict[str, float]) -> tuple[int, Dict[str, float]]:
    score = 100

    missing_exception = sum(1 for issue in issues if "MISSING_EXCEPTION_HANDLING" in str(issue.get("rule_id", "")))
    swallowed_exception = sum(1 for issue in issues if "EMPTY_EXCEPTION_HANDLER" in str(issue.get("rule_id", "")))
    reliability_high = sum(
        1
        for issue in issues
        if issue.get("category") == "reliability" and issue.get("severity") in {"high", "critical"}
    )

    has_logging_ratio = float(aggregate_metrics.get("logging_ratio", 0.0))
    null_check_ratio = float(aggregate_metrics.get("null_check_ratio", 0.0))

    score -= missing_exception * 6
    score -= swallowed_exception * 5
    score -= reliability_high * 4
    score += int(has_logging_ratio * 8)
    score += int(null_check_ratio * 6)

    score = max(0, min(100, score))
    details = {
        "missing_exception_cases": float(missing_exception),
        "swallowed_exception_cases": float(swallowed_exception),
        "critical_reliability_issues": float(reliability_high),
        "logging_ratio": round(has_logging_ratio, 3),
        "null_check_ratio": round(null_check_ratio, 3),
    }
    return int(score), details
