from __future__ import annotations

import ast
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .complexity import calculate_python_cyclomatic

BRANCH_TYPES = (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.Match)
SNAKE_CASE_PATTERN = re.compile(r"^[a-z_][a-z0-9_]{2,}$")
MAGIC_NUMBER_PATTERN = re.compile(r"(?<![\w.])(-?\d+(?:\.\d+)?)(?![\w.])")
JS_IMPORT_PATTERN = re.compile(r"^\s*import\s+(.+?)\s+from\s+['\"].+['\"]", re.MULTILINE)
JS_FUNCTION_PATTERN = re.compile(
    r"^\s*(?:function\s+([A-Za-z_]\w*)\s*\(([^)]*)\)|(?:const|let|var)\s+([A-Za-z_]\w*)\s*=\s*\(([^)]*)\)\s*=>\s*\{)",
    re.MULTILINE,
)


def _snippet_for_line(content: str, line: int) -> str:
    lines = content.splitlines()
    if 1 <= line <= len(lines):
        return lines[line - 1].strip()[:260]
    return ""


@dataclass
class FunctionMeta:
    name: str
    start_line: int
    end_line: int
    param_count: int = 0
    risky_calls: int = 0
    has_try: bool = False
    complexity: int = 1
    max_nesting: int = 0
    magic_numbers: int = 0

    @property
    def length(self) -> int:
        return max(1, self.end_line - self.start_line + 1)


def _max_nesting(node: ast.AST, depth: int = 0) -> int:
    current = depth
    for child in ast.iter_child_nodes(node):
        next_depth = depth + 1 if isinstance(child, BRANCH_TYPES) else depth
        current = max(current, _max_nesting(child, next_depth))
    return current


class PythonASTAnalyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.functions: Dict[str, FunctionMeta] = {}
        self.function_stack: List[str] = []
        self.called_functions: set[str] = set()
        self.null_checks = 0
        self.has_logging = False
        self.branch_count = 0
        self.imports: Dict[str, int] = {}
        self.used_names: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = (alias.asname or alias.name.split(".")[0]).strip()
            if name:
                self.imports[name] = getattr(node, "lineno", 1)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            name = (alias.asname or alias.name).strip()
            if name and name != "*":
                self.imports[name] = getattr(node, "lineno", 1)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._register_function(node.name, node)
        self._touch_current("param_count", value=len(node.args.args) + len(node.args.kwonlyargs) + len(node.args.posonlyargs))
        self._touch_current("max_nesting", value=_max_nesting(node))
        self._touch_current("magic_numbers", value=_count_magic_numbers_ast(node))
        self.generic_visit(node)
        self.function_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._register_function(node.name, node)
        self._touch_current("param_count", value=len(node.args.args) + len(node.args.kwonlyargs) + len(node.args.posonlyargs))
        self._touch_current("max_nesting", value=_max_nesting(node))
        self._touch_current("magic_numbers", value=_count_magic_numbers_ast(node))
        self.generic_visit(node)
        self.function_stack.pop()

    def _register_function(self, name: str, node: ast.AST) -> None:
        start = getattr(node, "lineno", 1)
        end = getattr(node, "end_lineno", start)
        self.functions[name] = FunctionMeta(name=name, start_line=start, end_line=end)
        self.function_stack.append(name)

    def visit_Call(self, node: ast.Call) -> None:
        func_name = self._call_name(node.func)
        if func_name:
            plain = func_name.split(".")[-1]
            self.called_functions.add(plain)
            if any(token in func_name for token in ("logging", "logger", "print")):
                self.has_logging = True
            if any(token in func_name for token in ("open", "read", "write", "requests", "urlopen", "subprocess")):
                self._touch_current("risky_calls")
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        self._touch_current("has_try", value=True)
        self.branch_count += 1
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        self.branch_count += 1
        if self._contains_none_check(node.test):
            self.null_checks += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.branch_count += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self.branch_count += 1
        self.generic_visit(node)

    def _contains_none_check(self, expr: ast.AST) -> bool:
        return any(isinstance(node, ast.Constant) and node.value is None for node in ast.walk(expr))

    def _touch_current(self, field: str, value=None) -> None:
        if not self.function_stack:
            return
        current = self.function_stack[-1]
        meta = self.functions.get(current)
        if not meta:
            return
        if value is None:
            setattr(meta, field, getattr(meta, field) + 1)
        else:
            setattr(meta, field, value)

    @staticmethod
    def _call_name(func: ast.AST) -> str:
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            base = PythonASTAnalyzer._call_name(func.value)
            return f"{base}.{func.attr}" if base else func.attr
        return ""


def _count_magic_numbers_ast(node: ast.AST) -> int:
    count = 0
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, (int, float)):
            if child.value not in {0, 1, -1}:
                count += 1
    return count


def analyze_python_ast(file_path: str, content: str) -> Tuple[List[dict], Dict[str, float], Optional[ast.AST]]:
    issues: List[dict] = []
    metrics: Dict[str, float] = defaultdict(float)

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return issues, dict(metrics), None

    visitor = PythonASTAnalyzer()
    visitor.visit(tree)
    metrics["function_count"] = float(len(visitor.functions))
    metrics["null_checks"] = float(visitor.null_checks)
    metrics["has_logging"] = 1.0 if visitor.has_logging else 0.0
    metrics["cyclomatic_complexity"] = float(calculate_python_cyclomatic(tree))

    for function in visitor.functions.values():
        if function.length > 50:
            issues.append(
                {
                    "rule_id": "LONG_FUNCTION",
                    "issue_type": "Long Function",
                    "category": "quality",
                    "severity": "medium",
                    "file_path": file_path,
                    "line": function.start_line,
                    "message": f"Function '{function.name}' has {function.length} lines (>50).",
                    "code_snippet": _snippet_for_line(content, function.start_line),
                    "confidence": 87.0,
                    "tags": ["code-smell", "maintainability"],
                }
            )

        if function.param_count > 5:
            issues.append(
                {
                    "rule_id": "TOO_MANY_PARAMETERS",
                    "issue_type": "Too Many Parameters",
                    "category": "quality",
                    "severity": "medium",
                    "file_path": file_path,
                    "line": function.start_line,
                    "message": f"Function '{function.name}' has {function.param_count} parameters.",
                    "code_snippet": _snippet_for_line(content, function.start_line),
                    "confidence": 81.0,
                    "tags": ["code-smell", "readability"],
                }
            )

        if function.max_nesting > 4:
            issues.append(
                {
                    "rule_id": "DEEP_NESTING",
                    "issue_type": "Deep Nesting",
                    "category": "maintainability",
                    "severity": "medium",
                    "file_path": file_path,
                    "line": function.start_line,
                    "message": f"Function '{function.name}' nesting depth is {function.max_nesting}.",
                    "code_snippet": _snippet_for_line(content, function.start_line),
                    "confidence": 79.0,
                    "tags": ["nesting", "complexity"],
                }
            )

        if function.magic_numbers >= 4:
            issues.append(
                {
                    "rule_id": "MAGIC_NUMBERS",
                    "issue_type": "Magic Numbers",
                    "category": "quality",
                    "severity": "low",
                    "file_path": file_path,
                    "line": function.start_line,
                    "message": f"Function '{function.name}' contains {function.magic_numbers} unexplained numeric literals.",
                    "code_snippet": _snippet_for_line(content, function.start_line),
                    "confidence": 75.0,
                    "tags": ["code-smell", "readability"],
                }
            )

        if not SNAKE_CASE_PATTERN.match(function.name):
            issues.append(
                {
                    "rule_id": "POOR_NAMING_CONVENTION",
                    "issue_type": "Poor Naming Convention",
                    "category": "quality",
                    "severity": "low",
                    "file_path": file_path,
                    "line": function.start_line,
                    "message": f"Function name '{function.name}' does not follow recommended snake_case style.",
                    "code_snippet": _snippet_for_line(content, function.start_line),
                    "confidence": 73.0,
                    "tags": ["naming", "maintainability"],
                }
            )

        if function.risky_calls > 0 and not function.has_try:
            issues.append(
                {
                    "rule_id": "MISSING_EXCEPTION_HANDLING",
                    "issue_type": "Missing Exception Handling",
                    "category": "reliability",
                    "severity": "high",
                    "file_path": file_path,
                    "line": function.start_line,
                    "message": f"Function '{function.name}' performs risky operations without try/except.",
                    "code_snippet": _snippet_for_line(content, function.start_line),
                    "confidence": 85.0,
                    "tags": ["exceptions", "reliability"],
                }
            )

    unused_imports = [name for name in visitor.imports if name not in visitor.used_names]
    for import_name in unused_imports[:30]:
        issues.append(
            {
                "rule_id": "UNUSED_IMPORT",
                "issue_type": "Unused Import",
                "category": "quality",
                "severity": "low",
                "file_path": file_path,
                "line": visitor.imports.get(import_name, 1),
                "message": f"Imported symbol '{import_name}' is never used.",
                "code_snippet": _snippet_for_line(content, visitor.imports.get(import_name, 1)),
                "confidence": 88.0,
                "tags": ["cleanup", "quality"],
            }
        )

    defined = set(visitor.functions.keys())
    called = visitor.called_functions
    dead_functions = sorted(name for name in defined if name not in called and not name.startswith("_"))
    for function_name in dead_functions[:20]:
        meta = visitor.functions.get(function_name)
        if not meta:
            continue
        issues.append(
            {
                "rule_id": "DEAD_CODE_FUNCTION",
                "issue_type": "Potential Dead Code",
                "category": "quality",
                "severity": "low",
                "file_path": file_path,
                "line": meta.start_line,
                "message": f"Function '{function_name}' is defined but never called in file scope.",
                "code_snippet": _snippet_for_line(content, meta.start_line),
                "confidence": 70.0,
                "tags": ["dead-code", "cleanup"],
            }
        )

    return issues, dict(metrics), tree


def _extract_js_function_ranges(content: str) -> List[Tuple[str, int, int, int]]:
    lines = content.splitlines()
    results: List[Tuple[str, int, int, int]] = []
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        match = JS_FUNCTION_PATTERN.match(line)
        if not match:
            idx += 1
            continue
        name = match.group(1) or match.group(3) or f"anonymous_{idx + 1}"
        params = (match.group(2) or match.group(4) or "").strip()
        param_count = len([token for token in params.split(",") if token.strip()])
        start = idx + 1
        brace_delta = line.count("{") - line.count("}")
        end = start
        cursor = idx + 1
        while cursor < len(lines) and brace_delta > 0:
            brace_delta += lines[cursor].count("{") - lines[cursor].count("}")
            end = cursor + 1
            cursor += 1
        results.append((name, start, max(end, start), param_count))
        idx = cursor
    return results


def _js_deep_nesting(block: str) -> int:
    depth = 0
    max_depth = 0
    for char in block:
        if char == "{":
            depth += 1
            max_depth = max(max_depth, depth)
        elif char == "}":
            depth = max(0, depth - 1)
    return max_depth


def analyze_js_ast_like(file_path: str, content: str) -> Tuple[List[dict], Dict[str, float]]:
    issues: List[dict] = []
    metrics: Dict[str, float] = defaultdict(float)
    functions = _extract_js_function_ranges(content)
    metrics["function_count"] = float(len(functions))

    has_logging = bool(re.search(r"\b(console\.(log|error|warn)|logger\.)", content))
    metrics["has_logging"] = 1.0 if has_logging else 0.0
    metrics["null_checks"] = float(
        len(re.findall(r"(\?\.|!=\s*null|!==\s*null|typeof\s+\w+\s*!==?\s*['\"]undefined['\"])", content))
    )
    metrics["cyclomatic_complexity"] = float(
        1 + len(re.findall(r"\b(if|for|while|switch|case|catch)\b|\?\s*", content))
    )

    imports = {}
    for match in JS_IMPORT_PATTERN.finditer(content):
        group = match.group(1).strip()
        for token in re.split(r"[{},\s]+", group):
            cleaned = token.strip()
            if not cleaned or cleaned in {"as", "default"}:
                continue
            imports[cleaned] = content[: match.start()].count("\n") + 1
    used_names = set(re.findall(r"\b([A-Za-z_]\w+)\b", content))

    for name, start, end, param_count in functions:
        length = end - start + 1
        block = "\n".join(content.splitlines()[start - 1 : end])
        function_complexity = 1 + len(re.findall(r"\b(if|for|while|switch|case|catch)\b|\?\s*", block))
        nesting = _js_deep_nesting(block)
        magic_numbers = len([num for num in MAGIC_NUMBER_PATTERN.findall(block) if num not in {"0", "1", "-1"}])

        if length > 50:
            issues.append(
                {
                    "rule_id": "LONG_FUNCTION_JS",
                    "issue_type": "Long Function",
                    "category": "quality",
                    "severity": "medium",
                    "file_path": file_path,
                    "line": start,
                    "message": f"Function '{name}' has {length} lines (>50).",
                    "code_snippet": _snippet_for_line(content, start),
                    "confidence": 83.0,
                    "tags": ["code-smell", "javascript"],
                }
            )

        if param_count > 5:
            issues.append(
                {
                    "rule_id": "TOO_MANY_PARAMETERS_JS",
                    "issue_type": "Too Many Parameters",
                    "category": "quality",
                    "severity": "medium",
                    "file_path": file_path,
                    "line": start,
                    "message": f"Function '{name}' has {param_count} parameters.",
                    "code_snippet": _snippet_for_line(content, start),
                    "confidence": 78.0,
                    "tags": ["code-smell", "javascript"],
                }
            )

        if function_complexity > 14:
            issues.append(
                {
                    "rule_id": "HIGH_COMPLEXITY_JS",
                    "issue_type": "High Cyclomatic Complexity",
                    "category": "maintainability",
                    "severity": "high",
                    "file_path": file_path,
                    "line": start,
                    "message": f"Function '{name}' has estimated complexity {function_complexity}.",
                    "code_snippet": _snippet_for_line(content, start),
                    "confidence": 80.0,
                    "tags": ["complexity", "javascript"],
                }
            )

        if nesting > 5:
            issues.append(
                {
                    "rule_id": "DEEP_NESTING_JS",
                    "issue_type": "Deep Nesting",
                    "category": "maintainability",
                    "severity": "medium",
                    "file_path": file_path,
                    "line": start,
                    "message": f"Function '{name}' has deep nesting level {nesting}.",
                    "code_snippet": _snippet_for_line(content, start),
                    "confidence": 76.0,
                    "tags": ["nesting", "javascript"],
                }
            )

        if magic_numbers >= 4:
            issues.append(
                {
                    "rule_id": "MAGIC_NUMBERS_JS",
                    "issue_type": "Magic Numbers",
                    "category": "quality",
                    "severity": "low",
                    "file_path": file_path,
                    "line": start,
                    "message": f"Function '{name}' contains {magic_numbers} unexplained numeric literals.",
                    "code_snippet": _snippet_for_line(content, start),
                    "confidence": 72.0,
                    "tags": ["code-smell", "javascript"],
                }
            )

        if len(name) < 3:
            issues.append(
                {
                    "rule_id": "POOR_NAMING_JS",
                    "issue_type": "Poor Naming Convention",
                    "category": "quality",
                    "severity": "low",
                    "file_path": file_path,
                    "line": start,
                    "message": f"Function name '{name}' is not descriptive.",
                    "code_snippet": _snippet_for_line(content, start),
                    "confidence": 69.0,
                    "tags": ["naming", "javascript"],
                }
            )

        risky = bool(re.search(r"\b(fetch|axios|fs\.readFile|fs\.writeFile|JSON\.parse)\b", block))
        has_try = bool(re.search(r"\btry\s*\{", block))
        if risky and not has_try:
            issues.append(
                {
                    "rule_id": "MISSING_EXCEPTION_HANDLING_JS",
                    "issue_type": "Missing Exception Handling",
                    "category": "reliability",
                    "severity": "high",
                    "file_path": file_path,
                    "line": start,
                    "message": f"Function '{name}' performs risky operations without try/catch.",
                    "code_snippet": _snippet_for_line(content, start),
                    "confidence": 82.0,
                    "tags": ["exceptions", "javascript"],
                }
            )

    definitions = [name for name, _, _, _ in functions if not name.startswith("anonymous_")]
    for name in definitions:
        usage_count = len(re.findall(rf"\b{name}\b", content))
        if usage_count <= 1:
            start = next((s for fname, s, _, _ in functions if fname == name), 1)
            issues.append(
                {
                    "rule_id": "DEAD_CODE_JS",
                    "issue_type": "Potential Dead Code",
                    "category": "quality",
                    "severity": "low",
                    "file_path": file_path,
                    "line": start,
                    "message": f"Function '{name}' appears unused in file scope.",
                    "code_snippet": _snippet_for_line(content, start),
                    "confidence": 66.0,
                    "tags": ["dead-code", "javascript"],
                }
            )

    unused_imports = [name for name in imports if name not in used_names]
    for import_name in unused_imports[:30]:
        issues.append(
            {
                "rule_id": "UNUSED_IMPORT_JS",
                "issue_type": "Unused Import",
                "category": "quality",
                "severity": "low",
                "file_path": file_path,
                "line": imports.get(import_name, 1),
                "message": f"Imported symbol '{import_name}' appears unused.",
                "code_snippet": _snippet_for_line(content, imports.get(import_name, 1)),
                "confidence": 79.0,
                "tags": ["cleanup", "javascript"],
            }
        )

    return issues, dict(metrics)
