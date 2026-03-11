from __future__ import annotations

from collections import Counter
from typing import Dict, List


def calculate_trust_score(issues: List[dict], files_analyzed: int) -> tuple[int, Dict[str, int]]:
    counter = Counter()
    for issue in issues:
        rule = str(issue.get("rule_id", ""))
        severity = str(issue.get("severity", "low")).lower()
        category = str(issue.get("category", "quality")).lower()

        if "SECRET" in rule:
            counter["secret_exposure"] += 1
        if "AUTH" in rule or "authentication" in str(issue.get("issue_type", "")).lower():
            counter["auth_safety"] += 1
        if "INPUT_VALIDATION" in rule:
            counter["input_validation"] += 1
        if category == "reliability" and severity in {"high", "critical"}:
            counter["error_handling"] += 1

    score = 100
    score -= counter["secret_exposure"] * 11
    score -= counter["auth_safety"] * 9
    score -= counter["input_validation"] * 4
    score -= counter["error_handling"] * 6

    if files_analyzed > 0 and counter["input_validation"] == 0:
        score += 4

    score = max(0, min(100, score))
    diagnostics = {
        "secret_exposure_hits": counter["secret_exposure"],
        "auth_safety_hits": counter["auth_safety"],
        "input_validation_hits": counter["input_validation"],
        "error_handling_hits": counter["error_handling"],
    }
    return int(score), diagnostics
