from __future__ import annotations

from typing import Dict


DEFAULT_GUIDANCE = {
    "risk_explanation": "The detected pattern is associated with exploitable behavior or production reliability degradation.",
    "real_world_attack_scenario": "An attacker can leverage this weakness in an exposed endpoint or automation flow.",
    "why_this_is_dangerous": "It can lead to data leakage, unauthorized access, service disruption, or expensive incidents.",
    "secure_fix_explanation": "Use secure-by-default APIs, strict validation, and explicit failure handling.",
    "refactored_code": "# Replace vulnerable logic with validated and least-privilege implementation.",
    "best_practice_reference": "OWASP ASVS, OWASP Top 10, and language-specific secure coding standards.",
    "performance_impact": "Improved safety with negligible runtime overhead for most workloads.",
    "confidence_score": "78%",
}


GUIDANCE_BY_RULE: Dict[str, Dict[str, str]] = {
    "HARDCODED_SECRET": {
        "risk_explanation": "Hardcoded secrets are extractable from source control and CI/CD artifacts.",
        "real_world_attack_scenario": "If the repository is leaked, attackers can immediately access production services using exposed keys.",
        "why_this_is_dangerous": "Credential exposure enables unauthorized data access and persistent compromise.",
        "secure_fix_explanation": "Load secrets from environment variables or a secret vault and rotate compromised credentials.",
        "refactored_code": "api_key = os.getenv('SERVICE_API_KEY')\nif not api_key:\n    raise RuntimeError('Missing SERVICE_API_KEY')",
        "best_practice_reference": "OWASP Secrets Management Cheat Sheet",
        "performance_impact": "No measurable overhead; improves operational security significantly.",
        "confidence_score": "95%",
    },
    "SQL_INJECTION_STRING_BUILD": {
        "risk_explanation": "Dynamic query string construction introduces SQL injection vectors.",
        "real_world_attack_scenario": "A crafted input value manipulates query semantics to exfiltrate user records.",
        "why_this_is_dangerous": "Attackers can read, update, or delete sensitive database data.",
        "secure_fix_explanation": "Use parameterized statements or ORM-safe query APIs.",
        "refactored_code": "cursor.execute('SELECT * FROM users WHERE email = %s', (email,))",
        "best_practice_reference": "OWASP SQL Injection Prevention Cheat Sheet",
        "performance_impact": "Prepared statements can improve query-plan reuse and performance stability.",
        "confidence_score": "91%",
    },
    "COMMAND_INJECTION": {
        "risk_explanation": "Shell command construction with user-controlled data can result in command injection.",
        "real_world_attack_scenario": "An attacker appends shell operators to execute arbitrary system commands.",
        "why_this_is_dangerous": "May lead to host compromise, data destruction, and remote code execution.",
        "secure_fix_explanation": "Avoid `shell=True`, pass strict argument arrays, and enforce allowlists.",
        "refactored_code": "subprocess.run(['ls', '-la', safe_path], check=True, shell=False)",
        "best_practice_reference": "CWE-78: Improper Neutralization of Special Elements used in an OS Command",
        "performance_impact": "Direct subprocess invocation is typically faster and safer than shell parsing.",
        "confidence_score": "92%",
    },
    "MISSING_EXCEPTION_HANDLING": {
        "risk_explanation": "Risky operations without targeted exception handling degrade resilience.",
        "real_world_attack_scenario": "A malformed payload crashes request processing and creates repeated 500 errors.",
        "why_this_is_dangerous": "Unhandled failures can cause outages and data consistency issues.",
        "secure_fix_explanation": "Catch specific exceptions, log context, and return controlled error responses.",
        "refactored_code": "try:\n    payload = json.loads(raw)\nexcept json.JSONDecodeError as exc:\n    logger.error('Invalid payload: %s', exc)\n    raise ValueError('Invalid input') from exc",
        "best_practice_reference": "Google SRE Workbook - Handling Overload and Failure",
        "performance_impact": "Negligible overhead; major reliability and observability improvements.",
        "confidence_score": "86%",
    },
    "DUPLICATION_BLOCK": {
        "risk_explanation": "Duplicated logic increases maintenance cost and defect propagation risk.",
        "real_world_attack_scenario": "A security patch is applied in one duplicate block but missed in another path.",
        "why_this_is_dangerous": "Inconsistent behavior and latent vulnerabilities remain in cloned code paths.",
        "secure_fix_explanation": "Extract shared logic into reusable utilities with tests.",
        "refactored_code": "def normalize_user_payload(payload: dict) -> dict:\n    ...",
        "best_practice_reference": "DRY Principle and Secure SDLC code review practices",
        "performance_impact": "Can improve cache locality and reduce binary size in compiled stacks.",
        "confidence_score": "85%",
    },
}


def _local_ai_payload(issue: dict, guidance: Dict[str, str]) -> dict:
    payload = dict(issue)
    payload["risk_explanation"] = guidance["risk_explanation"]
    payload["real_world_attack_scenario"] = guidance["real_world_attack_scenario"]
    payload["why_this_is_dangerous"] = guidance["why_this_is_dangerous"]
    payload["secure_fix_explanation"] = guidance["secure_fix_explanation"]
    payload["refactored_code"] = guidance["refactored_code"]
    payload["best_practice_reference"] = guidance["best_practice_reference"]
    payload["performance_impact"] = guidance["performance_impact"]
    payload["confidence_score"] = guidance["confidence_score"]

    payload["why_dangerous"] = guidance["why_this_is_dangerous"]
    payload["best_practice"] = guidance["best_practice_reference"]
    payload["suggested_code"] = guidance["secure_fix_explanation"]
    payload["refactored_example"] = guidance["refactored_code"]
    payload["before_code"] = str(issue.get("code_snippet", ""))
    payload["after_code"] = guidance["refactored_code"]
    payload["improvement_reasoning"] = guidance["secure_fix_explanation"]
    return payload


def enrich_issue(issue: dict) -> dict:
    rule_id = str(issue.get("rule_id", ""))
    issue_type = str(issue.get("issue_type", ""))
    guidance = GUIDANCE_BY_RULE.get(rule_id, DEFAULT_GUIDANCE)

    if rule_id == "DEAD_CODE_FUNCTION" or "Dead Code" in issue_type:
        guidance = {
            "risk_explanation": "Unused code paths hide stale logic and increase audit complexity.",
            "real_world_attack_scenario": "A deprecated function contains insecure logic that remains reachable via legacy routes.",
            "why_this_is_dangerous": "Dead code increases attack surface and maintenance burden.",
            "secure_fix_explanation": "Delete unreachable paths and enforce coverage on active code.",
            "refactored_code": "# Remove unused function and consolidate logic in one validated implementation.",
            "best_practice_reference": "CWE-561: Dead Code",
            "performance_impact": "Reduced bundle size and faster static analysis cycles.",
            "confidence_score": "72%",
        }

    return _local_ai_payload(issue, guidance)
