from __future__ import annotations

import json
import logging
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional

from ..utils.file_handler import count_lines, iter_source_files, read_text_file
from .ai_engine import enrich_issue
from .ast_parser import analyze_js_ast_like, analyze_python_ast
from .complexity import file_complexity, maintainability_index
from .duplication import detect_duplicate_blocks, detect_duplicate_functions
from .openai_engine import apply_advanced_ai_mode
from .project_health import analyze_test_coverage, architecture_validator, code_maturity_index, dependency_risk_score
from .rules import apply_regex_rules
from .scoring import calculate_all_scores, severity_distribution

logger = logging.getLogger(__name__)


KNOWN_DEPENDENCY_RISKS = {
    "lodash": {"safe": "4.17.21", "severity": "high"},
    "minimist": {"safe": "1.2.8", "severity": "high"},
    "axios": {"safe": "1.6.0", "severity": "medium"},
    "flask": {"safe": "2.0.0", "severity": "medium"},
    "django": {"safe": "3.2.0", "severity": "high"},
    "requests": {"safe": "2.31.0", "severity": "medium"},
    "pyyaml": {"safe": "6.0.0", "severity": "medium"},
}

SEVERITY_SCORE = {"critical": 10, "high": 7, "medium": 4, "low": 1}


def utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _language_from_suffix(suffix: str) -> str:
    suffix = suffix.lower()
    if suffix == ".py":
        return "python"
    if suffix in {".js", ".jsx"}:
        return "javascript"
    if suffix in {".ts", ".tsx"}:
        return "typescript"
    if suffix == ".java":
        return "java"
    return "other"


def _is_comment_line(language: str, line: str) -> bool:
    striped = line.strip()
    if not striped:
        return False
    if language == "python":
        return striped.startswith("#")
    return striped.startswith("//") or striped.startswith("/*") or striped.startswith("*")


def _parse_version(value: str) -> List[int]:
    numbers = re.findall(r"\d+", value or "")
    if not numbers:
        return [0]
    return [int(item) for item in numbers[:4]]


def _version_is_lower(current: str, safe: str) -> bool:
    current_parts = _parse_version(current)
    safe_parts = _parse_version(safe)
    max_len = max(len(current_parts), len(safe_parts))
    current_parts.extend([0] * (max_len - len(current_parts)))
    safe_parts.extend([0] * (max_len - len(safe_parts)))
    return current_parts < safe_parts


def _extract_line(content: str, line: int) -> str:
    lines = content.splitlines()
    if 1 <= line <= len(lines):
        return lines[line - 1].strip()[:260]
    return ""


def _dependency_findings(file_path: str, content: str) -> List[dict]:
    findings: List[dict] = []
    lower_path = file_path.lower()

    if lower_path.endswith("requirements.txt"):
        for idx, raw_line in enumerate(content.splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            package_match = re.match(r"([A-Za-z0-9_.-]+)\s*([<>=!~]+)?\s*([A-Za-z0-9_.-]+)?", line)
            if not package_match:
                continue
            package = (package_match.group(1) or "").lower()
            operator = package_match.group(2) or ""
            version = package_match.group(3) or ""

            if not operator:
                findings.append(
                    {
                        "rule_id": "UNPINNED_PY_DEPENDENCY",
                        "issue_type": "Unpinned Dependency",
                        "category": "dependency",
                        "severity": "low",
                        "file_path": file_path,
                        "line": idx,
                        "message": f"Dependency '{package}' is not version pinned.",
                        "code_snippet": line,
                        "confidence": 68.0,
                        "tags": ["dependency", "supply-chain"],
                    }
                )

            known = KNOWN_DEPENDENCY_RISKS.get(package)
            if known and version and _version_is_lower(version, known["safe"]):
                findings.append(
                    {
                        "rule_id": "OUTDATED_RISKY_DEPENDENCY",
                        "issue_type": "Potential Risky Dependency Version",
                        "category": "dependency",
                        "severity": known["severity"],
                        "file_path": file_path,
                        "line": idx,
                        "message": (
                            f"Dependency '{package}' uses {version}; recommended minimum is {known['safe']}."
                        ),
                        "code_snippet": line,
                        "confidence": 84.0,
                        "tags": ["dependency", "version-risk"],
                    }
                )

    if lower_path.endswith("package.json"):
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            return findings

        sections = ["dependencies", "devDependencies", "optionalDependencies"]
        for section in sections:
            values = payload.get(section, {})
            if not isinstance(values, dict):
                continue
            for name, version in values.items():
                version_text = str(version)
                package = name.lower()
                severity = "low"
                message = None

                if version_text.strip() in {"*", "latest"}:
                    severity = "medium"
                    message = f"Dependency '{name}' uses non-deterministic version '{version_text}'."

                known = KNOWN_DEPENDENCY_RISKS.get(package)
                stripped = version_text.lstrip("^~>=< ")
                if known and stripped and _version_is_lower(stripped, known["safe"]):
                    severity = known["severity"]
                    message = f"Dependency '{name}' uses {version_text}; recommended minimum is {known['safe']}."

                if message:
                    findings.append(
                        {
                            "rule_id": "JS_DEPENDENCY_RISK",
                            "issue_type": "Potential Risky Dependency Version",
                            "category": "dependency",
                            "severity": severity,
                            "file_path": file_path,
                            "line": 1,
                            "message": message,
                            "code_snippet": f'"{name}": "{version_text}"',
                            "confidence": 80.0,
                            "tags": ["dependency", "supply-chain", section],
                        }
                    )

    return findings


def _analyze_file(file_path: str, content: str) -> tuple[List[dict], Dict[str, float], Dict[str, float]]:
    issues = apply_regex_rules(file_path, content)
    suffix = Path(file_path).suffix
    language = _language_from_suffix(suffix)
    line_count = count_lines(content)
    comment_lines = sum(1 for line in content.splitlines() if _is_comment_line(language, line))

    ast_metrics: Dict[str, float] = defaultdict(float)
    tree = None

    if language == "python":
        ast_issues, ast_metrics, tree = analyze_python_ast(file_path, content)
        issues.extend(ast_issues)
    elif language in {"javascript", "typescript"}:
        ast_issues, ast_metrics = analyze_js_ast_like(file_path, content)
        issues.extend(ast_issues)

    complexity = file_complexity(language, content, tree=tree)
    maintainability = maintainability_index(line_count, complexity, comment_lines=comment_lines)

    if complexity > 25:
        issues.append(
            {
                "rule_id": "HIGH_COMPLEXITY_FILE",
                "issue_type": "High Cyclomatic Complexity",
                "category": "maintainability",
                "severity": "high",
                "file_path": file_path,
                "line": 1,
                "message": f"File has high estimated complexity ({complexity:.0f}).",
                "code_snippet": _extract_line(content, 1),
                "confidence": 78.0,
                "tags": ["complexity", "maintainability"],
            }
        )
    elif complexity > 16:
        issues.append(
            {
                "rule_id": "MODERATE_COMPLEXITY_FILE",
                "issue_type": "Elevated Complexity",
                "category": "maintainability",
                "severity": "medium",
                "file_path": file_path,
                "line": 1,
                "message": f"File complexity is elevated ({complexity:.0f}); consider decomposition.",
                "code_snippet": _extract_line(content, 1),
                "confidence": 72.0,
                "tags": ["complexity"],
            }
        )

    if maintainability < 45:
        issues.append(
            {
                "rule_id": "LOW_MAINTAINABILITY",
                "issue_type": "Low Maintainability Index",
                "category": "maintainability",
                "severity": "medium",
                "file_path": file_path,
                "line": 1,
                "message": f"Maintainability index is low ({maintainability}).",
                "code_snippet": _extract_line(content, 1),
                "confidence": 74.0,
                "tags": ["maintainability", "quality"],
            }
        )

    file_metric = {
        "file_path": file_path,
        "language": language,
        "lines": line_count,
        "issue_count": 0,
        "critical_count": 0,
        "high_count": 0,
        "medium_count": 0,
        "low_count": 0,
        "cyclomatic_complexity": round(complexity, 2),
        "maintainability_index": round(maintainability, 2),
        "duplication_blocks": 0,
        "risk_score": 0.0,
    }

    runtime_metrics = {
        "has_logging": float(ast_metrics.get("has_logging", 0.0)),
        "null_checks": float(ast_metrics.get("null_checks", 0.0)),
    }
    return issues, file_metric, runtime_metrics


def _build_recommendations(issues: List[dict], scores: Dict[str, int], test_score: int, maturity_score: int) -> List[str]:
    recommendations: List[str] = []
    top_security = [item for item in issues if item.get("category") in {"security", "dependency"}]
    top_reliability = [item for item in issues if item.get("category") == "reliability"]
    top_quality = [item for item in issues if item.get("category") in {"quality", "maintainability"}]

    if any("SECRET" in str(item.get("rule_id", "")) for item in top_security):
        recommendations.append("Move credentials to environment variables or a secrets manager and rotate exposed keys.")
    if any("INJECTION" in str(item.get("rule_id", "")) for item in top_security):
        recommendations.append("Use parameterized queries and strict command allowlists to block injection paths.")
    if any("MISSING_EXCEPTION_HANDLING" in str(item.get("rule_id", "")) for item in top_reliability):
        recommendations.append("Enforce targeted try/catch blocks for I/O, network, and parsing operations.")
    if any("DUPLICATION" in str(item.get("rule_id", "")) for item in top_quality):
        recommendations.append("Extract duplicate logic into shared modules and apply regression tests.")
    if scores.get("quality_score", 100) < 70:
        recommendations.append("Prioritize refactoring for long functions, deep nesting, and poor naming conventions.")
    if scores.get("security_score", 100) < 75:
        recommendations.append("Harden authentication, CORS, and validation paths before release.")
    if test_score < 50:
        recommendations.append("Increase automated tests coverage with unit and integration suites.")
    if maturity_score < 55:
        recommendations.append("Improve project documentation, licensing metadata, and modular code organization.")

    if not recommendations:
        recommendations.append("No critical risk clusters detected. Continue periodic static reviews and secure coding checks.")
    return recommendations[:12]


def _check_timeout(start_time: float, timeout_sec: int) -> None:
    if timeout_sec <= 0:
        return
    elapsed = time.monotonic() - start_time
    if elapsed > timeout_sec:
        raise TimeoutError(f"Scan exceeded timeout of {timeout_sec} seconds.")


def analyze_codebase(
    scan_id: str,
    source_type: str,
    source_label: str,
    source_dir: Path,
    ai_mode: str = "basic",
    include_extensions: Optional[List[str]] = None,
    exclude_paths: Optional[List[str]] = None,
    max_files: int = 1200,
    timeout_sec: int = 360,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> Dict:
    started_at = utc_now()
    monotonic_start = time.monotonic()

    files = iter_source_files(
        root_dir=source_dir,
        include_extensions=include_extensions,
        exclude_paths=exclude_paths,
        max_files=max_files,
    )
    if not files:
        raise ValueError("No source files found for selected filters.")

    issues: List[dict] = []
    file_metrics: List[dict] = []
    file_content_map: Dict[str, str] = {}
    runtime_aggregate = {
        "files_with_logging": 0.0,
        "files_with_null_checks": 0.0,
    }

    total_files = len(files)
    for idx, absolute_path in enumerate(files, start=1):
        _check_timeout(monotonic_start, timeout_sec)

        rel_path = str(absolute_path.relative_to(source_dir)).replace("\\", "/")
        content = read_text_file(absolute_path)
        file_content_map[rel_path] = content

        file_issues, metric, runtime = _analyze_file(rel_path, content)
        issues.extend(file_issues)
        file_metrics.append(metric)

        if runtime.get("has_logging", 0.0) > 0:
            runtime_aggregate["files_with_logging"] += 1
        if runtime.get("null_checks", 0.0) > 0:
            runtime_aggregate["files_with_null_checks"] += 1

        if progress_callback:
            base = 10
            span = 62
            progress = base + int((idx / total_files) * span)
            progress_callback(progress, f"Analyzing {rel_path}")

    _check_timeout(monotonic_start, timeout_sec)
    issues.extend(detect_duplicate_blocks(file_content_map))
    issues.extend(detect_duplicate_functions(file_content_map))

    for file_path, content in file_content_map.items():
        issues.extend(_dependency_findings(file_path, content))

    arch_issues, arch_diag = architecture_validator(file_content_map)
    issues.extend(arch_issues)

    test_diag = analyze_test_coverage(file_content_map)
    maturity_diag = code_maturity_index(source_dir, file_content_map)

    enriched_issues: List[dict] = []
    for idx, issue in enumerate(issues, start=1):
        issue["issue_id"] = f"{scan_id}-{idx:05d}"
        enriched_issues.append(enrich_issue(issue))

    ai_diag = {"mode": "basic", "reason": "offline-engine", "processed": 0}
    if ai_mode == "advanced":
        if progress_callback:
            progress_callback(82, "Running OpenAI advanced reasoning")
        enriched_issues, ai_diag = apply_advanced_ai_mode(enriched_issues)

    severity_counts = severity_distribution(enriched_issues)
    file_issue_map = defaultdict(list)
    for issue in enriched_issues:
        file_issue_map[issue["file_path"]].append(issue)

    for metric in file_metrics:
        related = file_issue_map.get(metric["file_path"], [])
        metric["issue_count"] = len(related)
        severity_counter = Counter(item.get("severity", "low") for item in related)
        metric["critical_count"] = severity_counter.get("critical", 0)
        metric["high_count"] = severity_counter.get("high", 0)
        metric["medium_count"] = severity_counter.get("medium", 0)
        metric["low_count"] = severity_counter.get("low", 0)
        metric["duplication_blocks"] = sum(1 for item in related if "DUPLICATION" in str(item.get("rule_id", "")))
        weighted = sum(SEVERITY_SCORE.get(str(item.get("severity", "low")).lower(), 1) for item in related)
        metric["risk_score"] = round(min(100.0, weighted * 2.4), 2)

    total_lines = sum(item["lines"] for item in file_metrics)
    aggregate_metrics = {
        "logging_ratio": runtime_aggregate["files_with_logging"] / max(total_files, 1),
        "null_check_ratio": runtime_aggregate["files_with_null_checks"] / max(total_files, 1),
    }

    scores, diagnostics = calculate_all_scores(
        issues=enriched_issues,
        file_metrics=file_metrics,
        aggregate_metrics=aggregate_metrics,
        total_lines=total_lines,
        total_files=total_files,
    )

    dependency_score = dependency_risk_score(enriched_issues)
    test_score = int(test_diag["test_coverage_score"])
    maturity_score = int(maturity_diag["code_maturity_index"])
    recommendations = _build_recommendations(
        enriched_issues,
        scores,
        test_score=test_score,
        maturity_score=maturity_score,
    )

    file_heatmap = sorted(
        [
            {
                "file_path": item["file_path"],
                "risk_score": item["risk_score"],
                "issue_count": item["issue_count"],
            }
            for item in file_metrics
        ],
        key=lambda row: row["risk_score"],
        reverse=True,
    )

    finished_at = utc_now()
    result = {
        "scan_id": scan_id,
        "source_type": source_type,
        "source_label": source_label,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": round((finished_at - started_at).total_seconds(), 2),
        "totals": {
            "total_files_scanned": total_files,
            "total_lines_analyzed": total_lines,
            "total_issues_found": len(enriched_issues),
            "critical": severity_counts["critical"],
            "high": severity_counts["high"],
            "medium": severity_counts["medium"],
            "low": severity_counts["low"],
        },
        "scores": scores,
        "severity_distribution": severity_counts,
        "score_radar": {
            "security": scores["security_score"],
            "trust": scores["trust_score"],
            "reliability": scores["reliability_score"],
            "quality": scores["quality_score"],
            "improvement": scores["improvement_potential"],
        },
        "file_risk_heatmap": file_heatmap,
        "recommendations": recommendations,
        "issues": enriched_issues,
        "files": file_metrics,
        "metadata": {
            "ai_mode_requested": ai_mode,
            "ai_mode_applied": ai_diag.get("mode", "basic"),
            "ai_diagnostics": ai_diag,
            "aggregate_metrics": aggregate_metrics,
            "score_diagnostics": diagnostics,
            "architecture_validator": arch_diag,
            "test_coverage": test_diag,
            "code_maturity": maturity_diag,
            "dependency_risk_score": dependency_score,
            "include_extensions": include_extensions or [],
            "exclude_paths": exclude_paths or [],
            "max_files": max_files,
            "timeout_sec": timeout_sec,
        },
    }

    if progress_callback:
        progress_callback(96, "Finalizing scan output")

    logger.info(
        "Scan %s completed. files=%s issues=%s security=%s reliability=%s quality=%s ai_mode=%s",
        scan_id,
        total_files,
        len(enriched_issues),
        scores["security_score"],
        scores["reliability_score"],
        scores["quality_score"],
        result["metadata"]["ai_mode_applied"],
    )
    return result
