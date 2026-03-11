from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from difflib import SequenceMatcher
from itertools import combinations
from typing import Dict, List, Tuple


def _normalize_line(line: str) -> str:
    line = re.sub(r"#.*$", "", line)
    line = re.sub(r"//.*$", "", line)
    line = re.sub(r"\s+", " ", line).strip()
    return line


def _extract_function_blocks(file_path: str, content: str) -> List[Tuple[str, int, str]]:
    blocks: List[Tuple[str, int, str]] = []
    lines = content.splitlines()

    py_pattern = re.compile(r"^\s*def\s+([A-Za-z_]\w*)\s*\(")
    js_pattern = re.compile(r"^\s*(?:function\s+([A-Za-z_]\w*)\s*\(|(?:const|let|var)\s+([A-Za-z_]\w*)\s*=)")

    idx = 0
    while idx < len(lines):
        line = lines[idx]
        py_match = py_pattern.match(line)
        js_match = js_pattern.match(line)
        if not py_match and not js_match:
            idx += 1
            continue

        name = ""
        if py_match:
            name = py_match.group(1)
            indent = len(line) - len(line.lstrip(" "))
            end = idx + 1
            while end < len(lines):
                current = lines[end]
                if current.strip() and (len(current) - len(current.lstrip(" "))) <= indent:
                    break
                end += 1
        else:
            name = js_match.group(1) or js_match.group(2) or f"fn_{idx+1}"
            brace_delta = line.count("{") - line.count("}")
            end = idx + 1
            while end < len(lines) and brace_delta > 0:
                brace_delta += lines[end].count("{") - lines[end].count("}")
                end += 1

        block_lines = lines[idx:end]
        cleaned = [_normalize_line(item) for item in block_lines if _normalize_line(item)]
        if len(cleaned) >= 6:
            blocks.append((f"{file_path}:{name}", idx + 1, "\n".join(cleaned)))
        idx = max(end, idx + 1)

    return blocks


def detect_duplicate_blocks(
    file_content_map: Dict[str, str],
    window_size: int = 6,
    max_reports: int = 250,
) -> List[dict]:
    block_index = defaultdict(list)
    results: List[dict] = []

    for file_path, content in file_content_map.items():
        lines = content.splitlines()
        cleaned = [_normalize_line(line) for line in lines]
        cleaned = [line for line in cleaned if line]

        if len(cleaned) < window_size:
            continue

        for idx in range(0, len(cleaned) - window_size + 1):
            block = "\n".join(cleaned[idx : idx + window_size])
            if len(block) < 40:
                continue
            fingerprint = hashlib.sha1(block.encode("utf-8")).hexdigest()
            block_index[fingerprint].append((file_path, idx + 1))

    for _, occurrences in block_index.items():
        unique_files = {item[0] for item in occurrences}
        if len(unique_files) < 2:
            continue
        first_file, first_line = occurrences[0]
        second_file, second_line = occurrences[1]
        results.append(
            {
                "issue_type": "Duplicated Code Block",
                "rule_id": "DUPLICATION_BLOCK",
                "category": "quality",
                "severity": "medium",
                "file_path": first_file,
                "line": first_line,
                "message": f"Code block duplicated with {second_file}:{second_line}.",
                "confidence": 86.0,
                "tags": ["duplication", "maintainability"],
            }
        )
        if len(results) >= max_reports:
            break

    return results


def detect_duplicate_functions(file_content_map: Dict[str, str], similarity_threshold: float = 0.86) -> List[dict]:
    function_pool: List[Tuple[str, int, str]] = []
    for file_path, content in file_content_map.items():
        function_pool.extend(_extract_function_blocks(file_path, content))

    findings: List[dict] = []
    seen_pairs = set()
    for left, right in combinations(function_pool, 2):
        left_id, left_line, left_body = left
        right_id, right_line, right_body = right
        pair_key = tuple(sorted([left_id, right_id]))
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)
        ratio = SequenceMatcher(None, left_body, right_body).ratio()
        if ratio < similarity_threshold:
            continue
        left_file = left_id.split(":", 1)[0]
        right_file = right_id.split(":", 1)[0]
        findings.append(
            {
                "issue_type": "Duplicate Function Similarity",
                "rule_id": "DUPLICATE_FUNCTION_SIMILARITY",
                "category": "quality",
                "severity": "medium",
                "file_path": left_file,
                "line": left_line,
                "message": (
                    f"Function body is {round(ratio * 100, 1)}% similar to function in {right_file}:{right_line}. "
                    "Consider modularization."
                ),
                "confidence": round(min(99.0, 65.0 + ratio * 35.0), 1),
                "tags": ["duplication", "refactor", "similarity"],
            }
        )
        if len(findings) >= 120:
            break
    return findings
