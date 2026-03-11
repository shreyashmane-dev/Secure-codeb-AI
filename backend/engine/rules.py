from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Pattern


@dataclass(frozen=True)
class Rule:
    rule_id: str
    issue_type: str
    category: str
    severity: str
    pattern: Pattern[str]
    message: str
    tags: tuple[str, ...]
    confidence: float


RULES: List[Rule] = [
    Rule(
        rule_id="HARDCODED_SECRET",
        issue_type="Hardcoded Secret",
        category="security",
        severity="critical",
        pattern=re.compile(
            r"(?i)\b(api[_-]?key|secret|token|password|passwd|private[_-]?key)\b\s*[:=]\s*['\"][^'\"]{6,}['\"]"
        ),
        message="Potential hardcoded secret detected in source.",
        tags=("secret", "credential", "security"),
        confidence=95.0,
    ),
    Rule(
        rule_id="SQL_INJECTION_STRING_BUILD",
        issue_type="Possible SQL Injection",
        category="security",
        severity="high",
        pattern=re.compile(r"(?i)(select|insert|update|delete).*(\+|%s|f['\"]).*(from|where)"),
        message="SQL query appears to be dynamically concatenated.",
        tags=("injection", "sql", "security"),
        confidence=89.0,
    ),
    Rule(
        rule_id="COMMAND_INJECTION",
        issue_type="Command Injection Risk",
        category="security",
        severity="critical",
        pattern=re.compile(r"(?i)\b(os\.system|subprocess\.(run|popen|call))\s*\("),
        message="Command execution API used. Ensure strict input sanitization.",
        tags=("command-exec", "injection", "security"),
        confidence=88.0,
    ),
    Rule(
        rule_id="EVAL_USAGE",
        issue_type="Dynamic Code Execution",
        category="security",
        severity="high",
        pattern=re.compile(r"(?i)\b(eval|exec|new Function)\s*\("),
        message="Dynamic code execution call detected.",
        tags=("rce", "dynamic-code", "security"),
        confidence=92.0,
    ),
    Rule(
        rule_id="INSECURE_HASH",
        issue_type="Weak Cryptographic Hash",
        category="security",
        severity="high",
        pattern=re.compile(r"(?i)\b(hashlib\.)?(md5|sha1)\s*\("),
        message="Weak hash function detected. Prefer SHA-256 or stronger algorithms.",
        tags=("crypto", "hash", "security"),
        confidence=90.0,
    ),
    Rule(
        rule_id="INSECURE_HTTP",
        issue_type="Insecure Transport",
        category="security",
        severity="medium",
        pattern=re.compile(r"(?i)http://[a-z0-9]"),
        message="Plain HTTP URL detected in code. Use HTTPS in production flows.",
        tags=("transport", "network"),
        confidence=82.0,
    ),
    Rule(
        rule_id="INSECURE_AUTH_LOGIC",
        issue_type="Insecure Authentication Logic",
        category="security",
        severity="high",
        pattern=re.compile(r"(?i)(password\s*==|if\s+user\s*==\s*['\"].+['\"])"),
        message="Possible insecure authentication check with plaintext comparison.",
        tags=("auth", "identity"),
        confidence=87.0,
    ),
    Rule(
        rule_id="UNSAFE_FILE_HANDLING",
        issue_type="Unsafe File Handling",
        category="security",
        severity="medium",
        pattern=re.compile(r"(?i)\bopen\s*\([^)]*['\"]w\+?['\"]\)|\bFileWriter\s*\("),
        message="File write operation detected. Validate file paths and permissions.",
        tags=("file-io", "path-traversal"),
        confidence=76.0,
    ),
    Rule(
        rule_id="BROAD_EXCEPTION",
        issue_type="Broad Exception Handling",
        category="reliability",
        severity="medium",
        pattern=re.compile(r"(?i)except\s*:\s*$|except\s+Exception"),
        message="Broad exception clause can hide production failures.",
        tags=("exceptions", "reliability"),
        confidence=79.0,
    ),
    Rule(
        rule_id="EMPTY_EXCEPTION_HANDLER",
        issue_type="Swallowed Exception",
        category="reliability",
        severity="high",
        pattern=re.compile(r"(?is)except[^\n]*:\s*(pass|return\s+None|continue)\b"),
        message="Exception block suppresses errors without diagnostics.",
        tags=("exceptions", "observability"),
        confidence=84.0,
    ),
    Rule(
        rule_id="MISSING_INPUT_VALIDATION_HINT",
        issue_type="Potential Missing Input Validation",
        category="security",
        severity="medium",
        pattern=re.compile(r"(?i)(request\.(args|json|form)|input\()"),
        message="User input usage detected. Validate and sanitize before processing.",
        tags=("input-validation", "security"),
        confidence=62.0,
    ),
    Rule(
        rule_id="TODO_HACK_MARKER",
        issue_type="Code Smell Marker",
        category="maintainability",
        severity="low",
        pattern=re.compile(r"(?i)\b(TODO|FIXME|HACK|XXX)\b"),
        message="Temporary marker found; unresolved technical debt may accumulate.",
        tags=("debt", "maintainability"),
        confidence=73.0,
    ),
]


def apply_regex_rules(file_path: str, content: str) -> List[dict]:
    issues: List[dict] = []
    lines = content.splitlines()

    for rule in RULES:
        for line_no, line in enumerate(lines, start=1):
            if rule.pattern.search(line):
                issues.append(
                    {
                        "rule_id": rule.rule_id,
                        "issue_type": rule.issue_type,
                        "category": rule.category,
                        "severity": rule.severity,
                        "file_path": file_path,
                        "line": line_no,
                        "message": rule.message,
                        "code_snippet": line.strip()[:260],
                        "confidence": rule.confidence,
                        "tags": list(rule.tags),
                    }
                )
    return issues
