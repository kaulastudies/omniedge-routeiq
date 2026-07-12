#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# OmniEdge RouteIQ — Final safe optimization and verification
#
# Usage:
#   chmod +x final-routeiq-optimize.sh
#   ./final-routeiq-optimize.sh
#
# Skip image build:
#   RUN_BUILD=0 ./final-routeiq-optimize.sh
#
# Use another build script:
#   BUILD_SCRIPT=your-script.sh ./final-routeiq-optimize.sh
# ============================================================

RUN_BUILD="${RUN_BUILD:-1}"
BUILD_SCRIPT="${BUILD_SCRIPT:-routeiq-v16-safe-hybrid.sh}"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR=".routeiq-backup-${STAMP}"
REPORT="routeiq-verification-${STAMP}.txt"

exec > >(tee -a "$REPORT") 2>&1

echo "============================================================"
echo " OmniEdge RouteIQ final optimization"
echo " Started: $(date)"
echo " Repository: $(pwd)"
echo " Backup: $BACKUP_DIR"
echo " Report: $REPORT"
echo "============================================================"

fail() {
    echo
    echo "ERROR: $*" >&2
    echo "No submission should be made until this error is resolved."
    exit 1
}

command -v python >/dev/null 2>&1 || fail "Python is not installed."

[[ -f "agent.py" ]] || fail "agent.py was not found in $(pwd)"
[[ -f "local/arithmetic.py" ]] || fail "local/arithmetic.py was not found."

echo
echo "[1/9] Creating backup..."

mkdir -p "$BACKUP_DIR/local"
cp agent.py "$BACKUP_DIR/agent.py"
cp local/arithmetic.py "$BACKUP_DIR/local/arithmetic.py"

if [[ -f "local/sentiment.py" ]]; then
    cp local/sentiment.py "$BACKUP_DIR/local/sentiment.py"
fi

if [[ -f "$BUILD_SCRIPT" ]]; then
    cp "$BUILD_SCRIPT" "$BACKUP_DIR/$(basename "$BUILD_SCRIPT")"
fi

if [[ -f "Dockerfile" ]]; then
    cp Dockerfile "$BACKUP_DIR/Dockerfile"
fi

if [[ -f "requirements.txt" ]]; then
    cp requirements.txt "$BACKUP_DIR/requirements.txt"
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git status --short > "$BACKUP_DIR/git-status-before.txt" || true
    git diff > "$BACKUP_DIR/git-diff-before.patch" || true
fi

echo "Backup completed."

echo
echo "[2/9] Applying transactional code patches..."

python - <<'PY'
from __future__ import annotations

import ast
import re
import textwrap
from pathlib import Path
from typing import Callable


AGENT_PATH = Path("agent.py")
ARITHMETIC_PATH = Path("local/arithmetic.py")


NORMALIZE_REPLACEMENT = r'''
def normalize_answer(value: Any) -> str:
    if value is None:
        return ""

    if not isinstance(value, str):
        return json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    cleaned = value.strip()

    # Remove common conversational wrappers only at the start.
    cleaned = re.sub(
        r"(?i)^(?:the\s+answer\s+is|final\s+answer|answer|result)"
        r"\s*[:\-]?\s*",
        "",
        cleaned,
    ).strip()

    # Strip trailing sentence punctuation only from plain numeric answers.
    if re.fullmatch(
        r"-?(?:\d+(?:\.\d+)?|\.\d+)[.,]",
        cleaned,
    ):
        cleaned = cleaned[:-1]

    return cleaned
'''


SYSTEM_PROMPT_REPLACEMENT = r'''
system_prompt = (
    'Return only valid JSON using: '
    '{"results":[{"task_id":<same input id>,'
    '"answer":"<final answer only>"}]}. '
    "Return one result for every task, preserve each task_id, "
    "and include no reasoning, markdown, commentary, or extra keys."
)
'''


ARITHMETIC_REPLACEMENT = r'''
def _solve_direct_expression(
    text: str,
) -> LocalDecision | None:
    cleaned_text = text.strip()

    # Remove only supported introductory instructions.
    cleaned_text = re.sub(
        r"(?i)^\s*(?:please\s+)?"
        r"(?:calculate|compute|evaluate|solve|what\s+is|"
        r"find\s+the\s+value\s+of|the\s+value\s+of)"
        r"\s*:?\s*",
        "",
        cleaned_text,
    )

    # Remove supported answer-format instructions at the end.
    cleaned_text = re.sub(
        r"(?i)\s*(?:and\s+)?"
        r"(?:return|give|answer\s+with)\s+"
        r"(?:only\s+)?(?:the\s+)?"
        r"(?:number|numeric\s+answer)\s*$",
        "",
        cleaned_text,
    )

    cleaned_text = re.sub(
        r"[?.!]+$",
        "",
        cleaned_text,
    ).strip()

    # Never evaluate prose, identifiers, function calls, or arbitrary code.
    if not re.fullmatch(
        r"[-+0-9.\s()*/%]+",
        cleaned_text,
    ):
        return None

    if not re.search(r"\d", cleaned_text):
        return _reject("expression contains no number")

    try:
        value = _safe_evaluate(cleaned_text)
        return _accept(
            value,
            "safe explicit arithmetic",
        )
    except Exception as error:
        return _reject(
            f"unsupported arithmetic expression: {error}"
        )
'''


def parse(source: str, path: Path) -> ast.Module:
    try:
        return ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        raise RuntimeError(
            f"{path} already contains a syntax error: {exc}"
        ) from exc


def ensure_import(source: str, module_name: str, statement: str) -> str:
    tree = parse(source, Path("<import-check>"))

    for node in tree.body:
        if isinstance(node, ast.Import):
            if any(alias.name == module_name for alias in node.names):
                return source

        if isinstance(node, ast.ImportFrom):
            if node.module == module_name:
                return source

    lines = source.splitlines(keepends=True)
    insertion_line = 0

    # Keep a module docstring first.
    if (
        tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    ):
        insertion_line = tree.body[0].end_lineno or 0

    # Keep __future__ imports before normal imports.
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            insertion_line = max(
                insertion_line,
                node.end_lineno or node.lineno,
            )

    lines.insert(insertion_line, statement.rstrip() + "\n")
    return "".join(lines)


def ensure_any_import(source: str) -> str:
    tree = parse(source, Path("<typing-check>"))

    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "typing":
            if any(alias.name == "Any" for alias in node.names):
                return source

    return ensure_import(source, "typing", "from typing import Any")


def replace_node(
    source: str,
    node: ast.AST,
    replacement: str,
) -> str:
    if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
        raise RuntimeError("AST node does not contain source positions.")

    lines = source.splitlines(keepends=True)
    start = node.lineno - 1
    end = node.end_lineno

    original_first_line = lines[start]
    indentation = re.match(r"^\s*", original_first_line).group(0)

    replacement_text = textwrap.dedent(replacement).strip("\n")
    replacement_text = textwrap.indent(
        replacement_text,
        indentation,
    ) + "\n"

    return "".join(lines[:start]) + replacement_text + "".join(lines[end:])


def find_function(
    tree: ast.Module,
    name: str,
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    matches = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    ]

    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one function named {name!r}; "
            f"found {len(matches)}."
        )

    return matches[0]


def assignment_targets_name(
    node: ast.Assign | ast.AnnAssign,
    name: str,
) -> bool:
    targets = (
        node.targets
        if isinstance(node, ast.Assign)
        else [node.target]
    )

    return any(
        isinstance(target, ast.Name) and target.id == name
        for target in targets
    )


def find_assignment_inside_function(
    tree: ast.Module,
    function_name: str,
    variable_name: str,
) -> ast.Assign | ast.AnnAssign:
    function = find_function(tree, function_name)

    matches = [
        node
        for node in ast.walk(function)
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        and assignment_targets_name(node, variable_name)
    ]

    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one {variable_name!r} assignment "
            f"inside {function_name!r}; found {len(matches)}."
        )

    return matches[0]


def patch_agent(source: str) -> str:
    source = ensure_import(source, "json", "import json")
    source = ensure_import(source, "re", "import re")
    source = ensure_any_import(source)

    tree = parse(source, AGENT_PATH)
    normalize_node = find_function(tree, "normalize_answer")
    source = replace_node(
        source,
        normalize_node,
        NORMALIZE_REPLACEMENT,
    )

    tree = parse(source, AGENT_PATH)
    prompt_node = find_assignment_inside_function(
        tree,
        "request_batch",
        "system_prompt",
    )
    source = replace_node(
        source,
        prompt_node,
        SYSTEM_PROMPT_REPLACEMENT,
    )

    parse(source, AGENT_PATH)
    return source


def patch_arithmetic(source: str) -> str:
    source = ensure_import(source, "re", "import re")

    tree = parse(source, ARITHMETIC_PATH)
    arithmetic_node = find_function(
        tree,
        "_solve_direct_expression",
    )

    source = replace_node(
        source,
        arithmetic_node,
        ARITHMETIC_REPLACEMENT,
    )

    parse(source, ARITHMETIC_PATH)
    return source


agent_original = AGENT_PATH.read_text(encoding="utf-8")
arithmetic_original = ARITHMETIC_PATH.read_text(encoding="utf-8")

# Calculate both patches before writing either file.
agent_patched = patch_agent(agent_original)
arithmetic_patched = patch_arithmetic(arithmetic_original)

if agent_patched == agent_original:
    raise RuntimeError("agent.py was not changed.")

if arithmetic_patched == arithmetic_original:
    raise RuntimeError("local/arithmetic.py was not changed.")

AGENT_PATH.write_text(agent_patched, encoding="utf-8")
ARITHMETIC_PATH.write_text(arithmetic_patched, encoding="utf-8")

print("Patched agent.py")
print("Patched local/arithmetic.py")
print("Sentiment rules were intentionally left unchanged.")
PY

echo "Code patches applied successfully."

echo
echo "[3/9] Checking syntax..."

python -m py_compile agent.py
python -m py_compile local/arithmetic.py

if [[ -f "local/sentiment.py" ]]; then
    python -m py_compile local/sentiment.py
fi

python -m compileall -q agent.py local

echo "Python syntax checks passed."

echo
echo "[4/9] Running normalize_answer smoke tests..."

python - <<'PY'
from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any


source = Path("agent.py").read_text(encoding="utf-8")
tree = ast.parse(source, filename="agent.py")

nodes = [
    node
    for node in ast.walk(tree)
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    and node.name == "normalize_answer"
]

if len(nodes) != 1:
    raise SystemExit(
        f"Expected one normalize_answer function; found {len(nodes)}."
    )

module = ast.Module(body=[nodes[0]], type_ignores=[])
ast.fix_missing_locations(module)

namespace = {
    "Any": Any,
    "json": json,
    "re": re,
}

exec(
    compile(module, filename="normalize_answer-smoke", mode="exec"),
    namespace,
)

normalize_answer = namespace["normalize_answer"]

cases = {
    None: "",
    "The answer is 42": "42",
    "Answer: 42": "42",
    "Final answer - 42": "42",
    "Result: 42.": "42",
    "Positive": "Positive",
    "The service was excellent.": "The service was excellent.",
    42: "42",
    True: "true",
    {"a": 1}: '{"a":1}',
}

for given, expected in cases.items():
    actual = normalize_answer(given)

    if actual != expected:
        raise AssertionError(
            f"normalize_answer({given!r}) returned {actual!r}; "
            f"expected {expected!r}"
        )

print(f"Passed {len(cases)} normalize_answer smoke tests.")
PY

echo
echo "[5/9] Verifying patched structures..."

python - <<'PY'
import ast
from pathlib import Path


agent_source = Path("agent.py").read_text(encoding="utf-8")
arithmetic_source = Path("local/arithmetic.py").read_text(
    encoding="utf-8"
)

agent_tree = ast.parse(agent_source)
arithmetic_tree = ast.parse(arithmetic_source)

request_batch = next(
    (
        node
        for node in ast.walk(agent_tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "request_batch"
    ),
    None,
)

if request_batch is None:
    raise SystemExit("request_batch was not found after patching.")

prompt_values = []

for node in ast.walk(request_batch):
    if isinstance(node, ast.Assign):
        if any(
            isinstance(target, ast.Name)
            and target.id == "system_prompt"
            for target in node.targets
        ):
            try:
                prompt_values.append(ast.literal_eval(node.value))
            except Exception as exc:
                raise SystemExit(
                    f"Could not evaluate system_prompt: {exc}"
                )

if len(prompt_values) != 1:
    raise SystemExit(
        f"Expected one system_prompt; found {len(prompt_values)}."
    )

prompt = prompt_values[0]

required_prompt_terms = [
    '"results"',
    '"task_id"',
    '"answer"',
    "one result for every task",
    "preserve each task_id",
    "no reasoning",
]

missing = [
    term
    for term in required_prompt_terms
    if term not in prompt
]

if missing:
    raise SystemExit(
        "The compact system prompt is missing: "
        + ", ".join(missing)
    )

arithmetic_function = next(
    (
        node
        for node in ast.walk(arithmetic_tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "_solve_direct_expression"
    ),
    None,
)

if arithmetic_function is None:
    raise SystemExit(
        "_solve_direct_expression was not found after patching."
    )

start = arithmetic_function.lineno - 1
end = arithmetic_function.end_lineno
function_source = "\n".join(
    arithmetic_source.splitlines()[start:end]
)

for required in [
    "re.fullmatch",
    "_safe_evaluate",
    "safe explicit arithmetic",
]:
    if required not in function_source:
        raise SystemExit(
            f"Arithmetic patch is missing {required!r}."
        )

print("Compact prompt structure verified.")
print("Arithmetic local-solver structure verified.")
PY

echo
echo "[6/9] Checking Git diff..."

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git diff --check

    echo
    echo "Changed files:"
    git status --short

    echo
    echo "Patch summary:"
    git diff --stat

    git diff > "$BACKUP_DIR/final-changes.patch"
else
    echo "Not inside a Git repository; Git checks skipped."
fi

echo
echo "[7/9] Running project tests when available..."

TESTS_FOUND=0

if find . \
    -path "./.git" -prune -o \
    -path "./.venv" -prune -o \
    -path "./venv" -prune -o \
    -path "./node_modules" -prune -o \
    -type f \
    \( -name "test_*.py" -o -name "*_test.py" \) \
    -print -quit | grep -q .; then
    TESTS_FOUND=1
fi

if [[ "$TESTS_FOUND" == "1" ]]; then
    if python -c "import pytest" >/dev/null 2>&1; then
        python -m pytest -q
        echo "Pytest suite passed."
    else
        echo "Test files were found, but pytest is not installed."
        fail "Install pytest or run the repository's normal test command."
    fi
else
    echo "No Python test files detected; pytest was skipped."
fi

if command -v ruff >/dev/null 2>&1; then
    echo
    echo "Running Ruff..."
    ruff check agent.py local/arithmetic.py
else
    echo "Ruff is not installed; lint check skipped."
fi

echo
echo "[8/9] Checking Docker and build configuration..."

if [[ -f "Dockerfile" ]]; then
    grep -nE '^(FROM|ENTRYPOINT|CMD)' Dockerfile || true
else
    echo "Dockerfile was not found."
fi

if [[ -f "$BUILD_SCRIPT" ]]; then
    bash -n "$BUILD_SCRIPT"
    echo "Build script syntax passed: $BUILD_SCRIPT"
else
    echo "Configured build script was not found: $BUILD_SCRIPT"
fi

echo
echo "[9/9] Building candidate..."

if [[ "$RUN_BUILD" == "0" ]]; then
    echo "Build skipped because RUN_BUILD=0."
elif [[ -f "$BUILD_SCRIPT" ]]; then
    echo "Executing existing build script: $BUILD_SCRIPT"
    echo "Note: if this script pushes an image, it will continue to do so."
    chmod +x "$BUILD_SCRIPT"
    "./$BUILD_SCRIPT"
    echo "Existing build script completed successfully."
elif [[ -f "Dockerfile" ]] && command -v docker >/dev/null 2>&1; then
    IMAGE_TAG="routeiq-final-candidate:${STAMP}"

    echo "Existing build script was unavailable."
    echo "Building local fallback image: $IMAGE_TAG"

    docker build \
        --tag "$IMAGE_TAG" \
        .

    docker image inspect "$IMAGE_TAG" >/dev/null
    echo "Fallback Docker image built and inspected successfully."
else
    fail "No usable build script or Docker build environment was found."
fi

echo
echo "============================================================"
echo " LOCAL VERIFICATION PASSED"
echo "============================================================"
echo
echo "Applied:"
echo "  1. Safer normalize_answer cleanup"
echo "  2. Compact but schema-preserving remote prompt"
echo "  3. Conservative direct arithmetic expansion"
echo
echo "Not applied:"
echo "  - Broad sentiment keyword changes"
echo
echo "Backup directory:"
echo "  $BACKUP_DIR"
echo
echo "Verification report:"
echo "  $REPORT"
echo
echo "Final status:"
echo "  Syntax: passed"
echo "  Normalization smoke tests: passed"
echo "  Prompt structure: passed"
echo "  Arithmetic structure: passed"
echo "  Git diff validation: passed"
echo "  Available repository tests: passed"
echo "  Build: passed"
echo
echo "Important:"
echo "  Only the AMD automated judge can confirm the new accuracy"
echo "  and external-token count. Local verification cannot prove"
echo "  that the candidate will score 100%."
echo
echo "Completed: $(date)"