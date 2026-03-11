from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple


def dependency_risk_score(issues: List[dict]) -> int:
    severity_weight = {"critical": 14, "high": 10, "medium": 5, "low": 2}
    dep_issues = [item for item in issues if item.get("category") == "dependency"]
    weighted = sum(severity_weight.get(str(item.get("severity", "low")).lower(), 2) for item in dep_issues)
    score = max(0, 100 - weighted)
    return int(score)


def architecture_validator(file_content_map: Dict[str, str]) -> Tuple[List[dict], Dict[str, int]]:
    issues: List[dict] = []
    diagnostics = {
        "missing_input_validation_signals": 0,
        "auth_layer_missing": 0,
        "insecure_cors": 0,
        "debug_enabled": 0,
    }

    all_content = "\n".join(file_content_map.values()).lower()
    backend_files = [path for path in file_content_map if path.endswith(".py") or path.endswith(".js")]

    has_auth_layer = any(
        token in all_content
        for token in ["verify_id_token", "jwt", "oauth", "authentication", "authorize", "firebase_admin.auth"]
    )
    if not has_auth_layer and backend_files:
        diagnostics["auth_layer_missing"] = 1
        issues.append(
            {
                "rule_id": "NO_AUTH_LAYER_DETECTED",
                "issue_type": "Missing Authentication Layer",
                "category": "security",
                "severity": "high",
                "file_path": backend_files[0],
                "line": 1,
                "message": "No authentication or token verification pattern detected in backend sources.",
                "confidence": 72.0,
                "tags": ["architecture", "auth"],
            }
        )

    for file_path, content in file_content_map.items():
        lower = content.lower()
        if "cors" in lower and ("allow_origins=['*']" in lower or 'allow_origins=["*"]' in lower):
            diagnostics["insecure_cors"] += 1
            issues.append(
                {
                    "rule_id": "INSECURE_CORS_WILDCARD",
                    "issue_type": "Insecure CORS Configuration",
                    "category": "security",
                    "severity": "high",
                    "file_path": file_path,
                    "line": 1,
                    "message": "CORS wildcard origin detected. Restrict origins for production.",
                    "confidence": 90.0,
                    "tags": ["cors", "security"],
                }
            )
        if re.search(r"\bdebug\s*=\s*true\b", lower):
            diagnostics["debug_enabled"] += 1
            issues.append(
                {
                    "rule_id": "DEBUG_MODE_ENABLED",
                    "issue_type": "Debug Mode Enabled",
                    "category": "security",
                    "severity": "medium",
                    "file_path": file_path,
                    "line": 1,
                    "message": "Debug mode appears enabled in production code path.",
                    "confidence": 84.0,
                    "tags": ["debug", "hardening"],
                }
            )
        if re.search(r"(request\.(args|json|form)|input\()", lower):
            has_validation = bool(
                re.search(
                    r"(pydantic|validator|validate|schema|marshmallow|zod|joi|typedict|BaseModel)",
                    lower,
                )
            )
            if not has_validation:
                diagnostics["missing_input_validation_signals"] += 1
                issues.append(
                    {
                        "rule_id": "MISSING_INPUT_VALIDATION_ARCH",
                        "issue_type": "Missing Input Validation",
                        "category": "security",
                        "severity": "medium",
                        "file_path": file_path,
                        "line": 1,
                        "message": "Input handling detected without clear validation pattern.",
                        "confidence": 65.0,
                        "tags": ["validation", "architecture"],
                    }
                )

    return issues, diagnostics


def analyze_test_coverage(file_content_map: Dict[str, str]) -> Dict[str, int | bool]:
    file_paths = list(file_content_map.keys())
    has_test_folder = any("/tests/" in f"/{path.lower()}/" or path.lower().startswith("tests/") for path in file_paths)
    has_pytest = any("pytest" in content.lower() for content in file_content_map.values())
    has_unittest = any("unittest" in content.lower() for content in file_content_map.values())
    test_file_count = sum(
        1
        for path in file_paths
        if path.lower().startswith("tests/") or path.lower().endswith("_test.py") or path.lower().endswith(".spec.js")
    )

    score = 25
    if has_test_folder:
        score += 30
    if has_pytest or has_unittest:
        score += 25
    if test_file_count >= 5:
        score += 20
    elif test_file_count >= 2:
        score += 10

    return {
        "has_test_folder": has_test_folder,
        "has_pytest_or_unittest": has_pytest or has_unittest,
        "test_file_count": test_file_count,
        "test_coverage_score": min(100, score),
    }


def code_maturity_index(source_dir: Path, file_content_map: Dict[str, str]) -> Dict[str, int | bool]:
    readme_content = ""
    for filename in ["README.md", "readme.md", "Readme.md"]:
        target = source_dir / filename
        if target.exists():
            readme_content = target.read_text(encoding="utf-8", errors="ignore")
            break

    has_license = any((source_dir / name).exists() for name in ["LICENSE", "LICENSE.md", "COPYING"])
    has_docs = bool(readme_content)
    readme_quality = 0
    if has_docs:
        length = len(readme_content.strip())
        headings = len(re.findall(r"^\s*#+\s+", readme_content, flags=re.MULTILINE))
        readme_quality = min(100, int(length / 30) + headings * 5)

    folder_depth = max((len(Path(path).parts) for path in file_content_map.keys()), default=1)
    modular_structure = folder_depth >= 3 and len({Path(path).parts[0] for path in file_content_map.keys()}) >= 3
    has_logging = any("logging" in content.lower() or "logger" in content.lower() for content in file_content_map.values())

    score = 20
    if has_docs:
        score += 20
    if has_license:
        score += 15
    if modular_structure:
        score += 20
    if has_logging:
        score += 15
    score += int(min(30, readme_quality * 0.3))
    score = min(100, score)

    return {
        "has_readme": has_docs,
        "readme_quality": readme_quality,
        "has_license": has_license,
        "modular_structure": modular_structure,
        "logging_detected": has_logging,
        "code_maturity_index": score,
    }
