from __future__ import annotations

import json
import logging
from typing import Dict, List, Tuple

from openai import OpenAI

from ..config import get_settings

logger = logging.getLogger(__name__)

REQUIRED_KEYS = [
    "issue_type",
    "severity",
    "risk_explanation",
    "real_world_attack_scenario",
    "why_this_is_dangerous",
    "secure_fix_explanation",
    "refactored_code",
    "best_practice_reference",
    "performance_impact",
    "confidence_score",
]


def _build_prompt(issue: dict) -> str:
    snippet = str(issue.get("code_snippet", ""))[:1600]
    return (
        "You are a cybersecurity AI reasoning engine. Return only JSON.\n\n"
        "Analyze this issue and provide enterprise-grade remediation.\n"
        f"Issue Type: {issue.get('issue_type')}\n"
        f"Severity: {issue.get('severity')}\n"
        f"File: {issue.get('file_path')}:{issue.get('line')}\n"
        f"Message: {issue.get('message')}\n"
        f"Code Snippet:\n{snippet}\n\n"
        "Output keys exactly:\n"
        + ", ".join(REQUIRED_KEYS)
        + "\nNo markdown. No prose outside JSON."
    )


def _safe_parse_json(raw: str) -> Dict[str, str]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    result: Dict[str, str] = {}
    for key in REQUIRED_KEYS:
        value = payload.get(key, "")
        result[key] = str(value).strip()
    return result


def _apply_ai_output(issue: dict, ai_output: Dict[str, str]) -> dict:
    if not ai_output:
        return issue
    issue = dict(issue)
    for key in REQUIRED_KEYS:
        if ai_output.get(key):
            issue[key] = ai_output[key]
    issue["why_dangerous"] = issue.get("why_this_is_dangerous", issue.get("why_dangerous", ""))
    issue["best_practice"] = issue.get("best_practice_reference", issue.get("best_practice", ""))
    issue["suggested_code"] = issue.get("secure_fix_explanation", issue.get("suggested_code", ""))
    issue["refactored_example"] = issue.get("refactored_code", issue.get("refactored_example", ""))
    issue["before_code"] = issue.get("code_snippet", "")
    issue["after_code"] = issue.get("refactored_code", "")
    issue["improvement_reasoning"] = issue.get("secure_fix_explanation", "")
    return issue


def apply_advanced_ai_mode(issues: List[dict]) -> Tuple[List[dict], Dict[str, str | int]]:
    settings = get_settings()
    if not settings.openai_api_key:
        return issues, {"mode": "basic_fallback", "reason": "OPENAI_API_KEY missing", "processed": 0}

    prioritized = sorted(
        issues,
        key=lambda issue: {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(str(issue.get("severity", "low")), 1),
        reverse=True,
    )
    max_issues = max(1, settings.advanced_ai_max_issues)
    target_ids = {issue["issue_id"] for issue in prioritized[:max_issues]}

    client = OpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_sec)
    enhanced: List[dict] = []
    processed = 0

    for issue in issues:
        if issue.get("issue_id") not in target_ids:
            enhanced.append(issue)
            continue
        try:
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "Return only strict JSON."},
                    {"role": "user", "content": _build_prompt(issue)},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            parsed = _safe_parse_json(content)
            enhanced.append(_apply_ai_output(issue, parsed))
            processed += 1
        except Exception as exc:
            logger.warning("Advanced AI enrichment failed for issue %s: %s", issue.get("issue_id"), exc)
            enhanced.append(issue)

    mode = "advanced" if processed > 0 else "basic_fallback"
    reason = "ok" if processed > 0 else "OpenAI call failure fallback"
    return enhanced, {"mode": mode, "reason": reason, "processed": processed}
