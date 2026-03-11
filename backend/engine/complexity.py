from __future__ import annotations

import ast
import math
import re
from typing import Optional


PYTHON_BRANCH_NODES = (
    ast.If,
    ast.For,
    ast.While,
    ast.Try,
    ast.ExceptHandler,
    ast.With,
    ast.BoolOp,
    ast.IfExp,
    ast.Match,
)


def calculate_python_cyclomatic(tree: ast.AST) -> int:
    complexity = 1
    for node in ast.walk(tree):
        if isinstance(node, PYTHON_BRANCH_NODES):
            complexity += 1
    return complexity


def estimate_js_cyclomatic(content: str) -> int:
    keywords = re.findall(r"\b(if|for|while|catch|case|\?\s*|&&|\|\|)\b", content)
    return 1 + len(keywords)


def maintainability_index(loc: int, complexity: float, comment_lines: int = 0) -> float:
    loc = max(loc, 1)
    complexity = max(complexity, 1.0)
    comment_ratio = min(comment_lines / loc, 1.0)
    volume = max(loc * complexity, 1.0)
    raw = 171.0 - 5.2 * math.log(volume) - 0.23 * complexity - 16.2 * math.log(loc)
    with_comments = raw + 50 * math.sin(math.sqrt(2.4 * comment_ratio))
    normalized = max(0.0, min(100.0, with_comments * 100.0 / 171.0))
    return round(normalized, 2)


def file_complexity(language: str, content: str, tree: Optional[ast.AST] = None) -> float:
    if language == "python" and tree is not None:
        return float(calculate_python_cyclomatic(tree))
    if language in {"javascript", "typescript"}:
        return float(estimate_js_cyclomatic(content))
    return float(1 + len(re.findall(r"\b(if|for|while|switch|catch)\b", content)))
