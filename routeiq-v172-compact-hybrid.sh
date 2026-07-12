#!/usr/bin/env bash
set -Eeuo pipefail

BASE_SHA="${ROUTEIQ_BASE_SHA:-368908aec0e6f698ccfaadd4084998711f6b3ba2}"
REPO="${ROUTEIQ_REPO:-$(pwd)}"
SOURCE_DIR="${ROUTEIQ_SOURCE_DIR:-track1-v171-agent}"
CANDIDATE_DIR="${ROUTEIQ_CANDIDATE_DIR:-track1-v172-agent}"
WORKFLOW_FILE=".github/workflows/publish-track1-v172.yml"
WORKFLOW_NAME="Publish RouteIQ v1.7.2 Compact Hybrid"
LOCAL_IMAGE="routeiq-v172-compact-hybrid:test"
PUBLISH="${ROUTEIQ_PUBLISH:-0}"
SKIP_DOCKER="${ROUTEIQ_SKIP_DOCKER:-0}"
STAMP="$(date +%Y%m%d-%H%M%S)"
REPORT="routeiq-v172-verification-${STAMP}.txt"

exec > >(tee -a "$REPORT") 2>&1

say() { printf '\n==> %s\n' "$*"; }
die() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }

MOCK_NAME=""
NETWORK_NAME=""
TMP_ROOT=""
cleanup() {
  set +e
  [[ -n "$MOCK_NAME" ]] && docker rm -f "$MOCK_NAME" >/dev/null 2>&1
  [[ -n "$NETWORK_NAME" ]] && docker network rm "$NETWORK_NAME" >/dev/null 2>&1
  [[ -n "$TMP_ROOT" && -d "$TMP_ROOT" ]] && rm -rf "$TMP_ROOT"
  return 0
}
trap cleanup EXIT
trap 'printf "\nFAILED at line %s. Nothing was submitted to the ACT II portal.\n" "$LINENO" >&2' ERR

printf '%s\n' "============================================================"
printf '%s\n' " OmniEdge RouteIQ v1.7.2 compact-hybrid candidate"
printf '%s\n' "============================================================"
printf 'Repository: %s\n' "$REPO"
printf 'Protected base: %s\n' "$BASE_SHA"
printf 'Publish image: %s\n' "$PUBLISH"
printf 'Skip Docker: %s\n' "$SKIP_DOCKER"
printf 'Report: %s\n' "$REPORT"

for command in git python3; do
  command -v "$command" >/dev/null 2>&1 || die "$command is required"
done

cd "$REPO"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "not a Git repository: $REPO"
[[ -f "$SOURCE_DIR/agent.py" ]] || die "missing $SOURCE_DIR/agent.py"
[[ -f "$SOURCE_DIR/local/arithmetic.py" ]] || die "missing arithmetic solver"
[[ -f "$SOURCE_DIR/local/sentiment.py" ]] || die "missing sentiment solver"
[[ -f "$SOURCE_DIR/Dockerfile" ]] || die "missing Dockerfile"

git cat-file -e "${BASE_SHA}^{commit}" 2>/dev/null || die "protected base commit is unavailable: $BASE_SHA"
git merge-base --is-ancestor "$BASE_SHA" HEAD || die "current branch does not descend from the protected v1.7.1 commit"
BRANCH="$(git branch --show-current)"
[[ -n "$BRANCH" ]] || die "detached HEAD is not supported"

say "Preparing a separate candidate folder"
rm -rf "$CANDIDATE_DIR"
cp -a "$SOURCE_DIR" "$CANDIDATE_DIR"
find "$CANDIDATE_DIR" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$CANDIDATE_DIR" -type f -name '*.pyc' -delete

say "Applying four guarded optimizations"
CANDIDATE_DIR="$CANDIDATE_DIR" python3 - <<'PY'
from __future__ import annotations

import ast
import os
import re
import textwrap
from pathlib import Path

root = Path(os.environ["CANDIDATE_DIR"])
agent_path = root / "agent.py"
arithmetic_path = root / "local" / "arithmetic.py"
sentiment_path = root / "local" / "sentiment.py"


def parse(source: str, path: Path) -> ast.Module:
    return ast.parse(source, filename=str(path))


def replace_function(source: str, path: Path, name: str, replacement: str) -> str:
    tree = parse(source, path)
    matches = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one function {name!r}; found {len(matches)}")
    node = matches[0]
    lines = source.splitlines(keepends=True)
    indentation = re.match(r"^\s*", lines[node.lineno - 1]).group(0)
    block = textwrap.indent(textwrap.dedent(replacement).strip("\n"), indentation) + "\n"
    return "".join(lines[: node.lineno - 1]) + block + "".join(lines[node.end_lineno :])


agent = agent_path.read_text(encoding="utf-8")
agent = replace_function(
    agent,
    agent_path,
    "normalize_answer",
    r'''
def normalize_answer(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if not isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

    cleaned = value.strip()
    cleaned = re.sub(
        r"(?i)^(?:the\s+answer\s+is\s*[:\-]?\s+|"
        r"final\s+answer\s*[:\-]\s*|answer\s*[:\-]\s*)",
        "",
        cleaned,
    ).strip()

    sentiment = re.fullmatch(
        r"(?i)(?:sentiment\s*[:\-]\s*)?"
        r"(positive|negative|neutral)[.!]?",
        cleaned,
    )
    if sentiment:
        return sentiment.group(1).lower()

    if re.fullmatch(r"-?(?:\d+(?:\.\d+)?|\.\d+)[.,]", cleaned):
        cleaned = cleaned[:-1]

    return cleaned
''',
)
anchor = '"max_tokens": 4096,'
if anchor not in agent:
    raise RuntimeError("Could not find the fixed 4096-token completion cap")
agent = agent.replace(anchor, '"max_tokens": completion_budget(tasks),', 1)
parse(agent, agent_path)
agent_path.write_text(agent, encoding="utf-8")

arithmetic = arithmetic_path.read_text(encoding="utf-8")
old_percentage = 'rf"(?:what is |calculate |compute )?"'
new_percentage = (
    'rf"(?:(?:what is|how much is|calculate|compute|find|determine)'
    '(?:\\s+the\\s+value\\s+of)?\\s+)?"'
)
if old_percentage not in arithmetic:
    raise RuntimeError("Could not find the percentage-prefix anchor")
arithmetic = arithmetic.replace(old_percentage, new_percentage, 1)
old_direct = '''        r"(?:please )?"\n        r"(?:what is|calculate|compute|evaluate|solve)"\n        r"\\s+([-0-9.\\s()+*/%]+)\\??",'''
new_direct = '''        r"(?:please\\s+)?"\n        r"(?:(?:what|how much)\\s+is|"\n        r"(?:calculate|compute|evaluate|solve|find|determine|work\\s+out)"\n        r"(?:\\s+the\\s+value\\s+of)?)"\n        r"\\s+([-0-9.\\s()+*/%]+)\\??",'''
if old_direct not in arithmetic:
    raise RuntimeError("Could not find the direct-expression command anchor")
arithmetic = arithmetic.replace(old_direct, new_direct, 1)
parse(arithmetic, arithmetic_path)
arithmetic_path.write_text(arithmetic, encoding="utf-8")

sentiment = sentiment_path.read_text(encoding="utf-8")
sentiment = replace_function(
    sentiment,
    sentiment_path,
    "_extract_statement",
    r'''
def _extract_statement(prompt: str) -> str:
    patterns = (
        r"^\s*classify\s+as\s+positive\s*,\s*negative\s*,\s*or\s*neutral\s*:\s*(.+)$",
        r"^\s*classify\s+the\s+sentiment\s*:\s*(.+)$",
        r"^\s*determine\s+whether\s+the\s+following\s+(?:text|statement)\s+is\s+positive\s*,\s*negative\s*,\s*or\s*neutral\s*:\s*(.+)$",
        r"^\s*label\s+the\s+sentiment\s+as\s+positive\s*,\s*negative\s*,\s*or\s*neutral\s*:\s*(.+)$",
        r"^\s*what\s+is\s+the\s+sentiment\s+of\s+the\s+following\s+(?:text|statement)\s*:\s*(.+)$",
    )
    for pattern in patterns:
        match = re.match(pattern, prompt, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    return ""
''',
)
parse(sentiment, sentiment_path)
sentiment_path.write_text(sentiment, encoding="utf-8")

print("Applied:")
print("  1. Dynamic per-task completion budget")
print("  2. Conservative answer-wrapper normalization")
print("  3. Strict-expression arithmetic phrasing expansion")
print("  4. Sentiment prompt-format expansion without vocabulary changes")
PY

cat > "$CANDIDATE_DIR/tests/test_v172_optimizations.py" <<'PYTEST'
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("routeiq_v172", ROOT / "agent.py")
AGENT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(AGENT)

from local.arithmetic import solve_arithmetic
from local.sentiment import solve_sentiment


class V172OptimizationTests(unittest.TestCase):
    def test_dynamic_completion_budget_is_used(self):
        tasks = [
            {"task_id": "f", "task_type": "factual knowledge", "prompt": "Capital of Japan?"},
            {"task_id": "m", "task_type": "mathematical reasoning", "prompt": "What is 2 + 2?"},
        ]
        captured = {}

        def fake_request(payload, api_key, url, deadline=None):
            captured.update(payload)
            content = json.dumps({"r": [{"i": 0, "a": "Tokyo"}, {"i": 1, "a": "4"}]})
            return {"choices": [{"message": {"content": content}}]}

        original = AGENT._perform_request
        AGENT._perform_request = fake_request
        AGENT.ACTIVE_DEADLINE = AGENT.time.monotonic() + 20
        try:
            answers = AGENT.request_batch(tasks, "minimax-m3", "mock", "https://example.invalid")
        finally:
            AGENT._perform_request = original
            AGENT.ACTIVE_DEADLINE = None

        self.assertEqual(answers, {"f": "Tokyo", "m": "4"})
        self.assertEqual(captured["max_tokens"], AGENT.completion_budget(tasks))
        self.assertLess(captured["max_tokens"], 4096)

    def test_safe_answer_normalization(self):
        self.assertEqual(AGENT.normalize_answer("The answer is: 42"), "42")
        self.assertEqual(AGENT.normalize_answer("Final answer - Tokyo"), "Tokyo")
        self.assertEqual(AGENT.normalize_answer("Sentiment: Positive."), "positive")
        self.assertEqual(AGENT.normalize_answer("42."), "42")
        self.assertEqual(AGENT.normalize_answer("result = 4"), "result = 4")

    def test_additional_strict_arithmetic_phrasings(self):
        cases = {
            "Find the value of 21 * 4": "84",
            "How much is (18 + 6) / 3?": "8",
            "Work out 29 % 6": "5",
            "Determine the value of 12.5% of 800": "100",
        }
        for prompt, expected in cases.items():
            with self.subTest(prompt=prompt):
                decision = solve_arithmetic(prompt)
                self.assertTrue(decision.accepted, decision.reason)
                self.assertEqual(decision.answer, expected)

    def test_additional_sentiment_prompt_formats(self):
        tasks = [
            {
                "task_type": "sentiment classification",
                "prompt": "Determine whether the following text is positive, negative, or neutral: The rollout was excellent.",
                "expected": "positive",
            },
            {
                "task_type": "sentiment classification",
                "prompt": "Label the sentiment as positive, negative, or neutral: The application crashed.",
                "expected": "negative",
            },
            {
                "task_type": "sentiment classification",
                "prompt": "What is the sentiment of the following statement: The opinion is neutral.",
                "expected": "neutral",
            },
        ]
        for task in tasks:
            expected = task.pop("expected")
            decision = solve_sentiment(task)
            self.assertTrue(decision.accepted, decision.reason)
            self.assertEqual(decision.answer, expected)


if __name__ == "__main__":
    unittest.main()
PYTEST

say "Running all inherited and new unit tests"
(
  cd "$CANDIDATE_DIR"
  python3 -m compileall -q agent.py local tests
  python3 -m unittest discover -s tests -v
)
find "$CANDIDATE_DIR" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$CANDIDATE_DIR" -type f -name '*.pyc' -delete

say "Auditing the exact candidate changes"
git diff --no-index --stat "$SOURCE_DIR" "$CANDIDATE_DIR" || true
grep -n '"max_tokens"' "$CANDIDATE_DIR/agent.py"

if [[ "$SKIP_DOCKER" == "1" ]]; then
  say "Docker build skipped by ROUTEIQ_SKIP_DOCKER=1"
else
  command -v docker >/dev/null 2>&1 || die "docker is required unless ROUTEIQ_SKIP_DOCKER=1"
  docker info >/dev/null 2>&1 || die "Docker daemon is unavailable"

  say "Building the evaluator-safe linux/amd64 candidate locally"
  docker build --progress=plain --tag "$LOCAL_IMAGE" "$CANDIDATE_DIR"
  ARCH="$(docker image inspect --format '{{.Architecture}}' "$LOCAL_IMAGE")"
  SIZE="$(docker image inspect --format '{{.Size}}' "$LOCAL_IMAGE")"
  [[ "$ARCH" == "amd64" ]] || die "candidate architecture is $ARCH, not amd64"
  [[ "$SIZE" -lt 500000000 ]] || die "candidate image is unexpectedly large: $SIZE bytes"
  printf 'Local image size: %.1f MB\n' "$(python3 -c "print($SIZE/1000000)")"

  say "Running an all-local container smoke test"
  TMP_ROOT="$(mktemp -d)"
  mkdir -p "$TMP_ROOT/local-input" "$TMP_ROOT/local-output"
  chmod 777 "$TMP_ROOT/local-output"
  cat > "$TMP_ROOT/local-input/tasks.json" <<'JSON'
[
  {"task_id":"a1","task_type":"mathematical reasoning","prompt":"Find the value of 21 * 4"},
  {"task_id":"a2","task_type":"mathematical reasoning","prompt":"How much is (18 + 6) / 3?"},
  {"task_id":"a3","task_type":"mathematical reasoning","prompt":"Determine the value of 12.5% of 800"},
  {"task_id":"s1","task_type":"sentiment classification","prompt":"Label the sentiment as positive, negative, or neutral: The application crashed."},
  {"task_id":"s2","task_type":"sentiment classification","prompt":"What is the sentiment of the following statement: The opinion is neutral."}
]
JSON
  docker run --rm --network none \
    -v "$TMP_ROOT/local-input:/input:ro" \
    -v "$TMP_ROOT/local-output:/output" \
    "$LOCAL_IMAGE"
  python3 - "$TMP_ROOT/local-output/results.json" <<'PY'
import json, sys
results = json.load(open(sys.argv[1], encoding="utf-8"))
expected = {"a1":"84", "a2":"8", "a3":"100", "s1":"negative", "s2":"neutral"}
actual = {str(item["task_id"]): item["answer"] for item in results}
if actual != expected:
    raise SystemExit(f"Local container smoke test failed: {actual}")
print("PASS: local container smoke test", actual)
PY

  say "Running a container-level compact remote-batch smoke test"
  NETWORK_NAME="routeiq-v172-net-${STAMP}"
  MOCK_NAME="routeiq-v172-mock-${STAMP}"
  docker network create "$NETWORK_NAME" >/dev/null
  cat > "$TMP_ROOT/mock_fireworks.py" <<'PYMOCK'
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return
    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        request = json.loads(self.rfile.read(length).decode("utf-8"))
        user = json.loads(request["messages"][1]["content"])
        count = len(user.get("q", []))
        answers = ["Tokyo", "B", "Concise summary."]
        content = json.dumps({"r": [{"i": i, "a": answers[i] if i < len(answers) else "ok"} for i in range(count)]})
        body = json.dumps({"choices": [{"message": {"content": content}}]}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
PYMOCK
  docker run -d --rm --name "$MOCK_NAME" --network "$NETWORK_NAME" \
    -v "$TMP_ROOT/mock_fireworks.py:/mock_fireworks.py:ro" \
    python:3.12-slim python3 /mock_fireworks.py >/dev/null
  sleep 2
  mkdir -p "$TMP_ROOT/remote-input" "$TMP_ROOT/remote-output"
  chmod 777 "$TMP_ROOT/remote-output"
  cat > "$TMP_ROOT/remote-input/tasks.json" <<'JSON'
[
  {"task_id":"local","task_type":"mathematical reasoning","prompt":"Calculate 7 * 8."},
  {"task_id":"fact","task_type":"factual knowledge","prompt":"What is the capital of Japan?"},
  {"task_id":"logic","task_type":"logic","prompt":"Choose the correct option: A or B. Return only the letter."},
  {"task_id":"summary","task_type":"summarization","prompt":"Summarize the supplied note briefly."}
]
JSON
  docker run --rm --network "$NETWORK_NAME" \
    -e FIREWORKS_API_KEY=mock \
    -e FIREWORKS_BASE_URL=http://"$MOCK_NAME":8080/v1 \
    -e 'ALLOWED_MODELS=["minimax-m3"]' \
    -v "$TMP_ROOT/remote-input:/input:ro" \
    -v "$TMP_ROOT/remote-output:/output" \
    "$LOCAL_IMAGE"
  python3 - "$TMP_ROOT/remote-output/results.json" <<'PY'
import json, sys
results = json.load(open(sys.argv[1], encoding="utf-8"))
actual = {str(item["task_id"]): item["answer"] for item in results}
expected = {"local":"56", "fact":"Tokyo", "logic":"B", "summary":"Concise summary."}
if actual != expected:
    raise SystemExit(f"Hybrid container smoke test failed: {actual}")
print("PASS: hybrid container smoke test", actual)
PY
  docker rm -f "$MOCK_NAME" >/dev/null 2>&1 || true
  MOCK_NAME=""
  docker network rm "$NETWORK_NAME" >/dev/null 2>&1 || true
  NETWORK_NAME=""
  rm -rf "$TMP_ROOT"
  TMP_ROOT=""
fi

say "Creating the isolated GitHub Actions publication workflow"
mkdir -p .github/workflows
cat > "$WORKFLOW_FILE" <<YAML
name: $WORKFLOW_NAME

on:
  workflow_dispatch:
  push:
    branches:
      - "$BRANCH"
    paths:
      - "$CANDIDATE_DIR/**"
      - "$WORKFLOW_FILE"

permissions:
  contents: read
  packages: write

concurrency:
  group: publish-routeiq-v172-compact-hybrid
  cancel-in-progress: false

jobs:
  publish:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - name: Checkout candidate branch
        uses: actions/checkout@v4
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: \${{ github.actor }}
          password: \${{ secrets.GITHUB_TOKEN }}
      - name: Build and publish linux/amd64 candidate
        uses: docker/build-push-action@v6
        with:
          context: ./$CANDIDATE_DIR
          file: ./$CANDIDATE_DIR/Dockerfile
          platforms: linux/amd64
          push: true
          provenance: false
          sbom: false
          tags: ghcr.io/\${{ github.repository_owner }}/omniedge-routeiq-track1:c-v172-\${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
YAML

say "Candidate gate passed"
printf '%s\n' "Tests: PASS"
printf '%s\n' "Container smoke tests: $([[ "$SKIP_DOCKER" == "1" ]] && echo SKIPPED || echo PASS)"
printf '%s\n' "Portal submission: UNCHANGED"

if [[ "$PUBLISH" != "1" ]]; then
  printf '\nPublication was skipped. To test, publish, and verify in one run:\n'
  printf '  ROUTEIQ_PUBLISH=1 ./%s\n' "$(basename "$0")"
  exit 0
fi

for command in gh docker timeout; do
  command -v "$command" >/dev/null 2>&1 || die "$command is required for publication"
done
gh auth status >/dev/null 2>&1 || die "GitHub CLI is not authenticated"

say "Committing only the v1.7.2 candidate and its workflow"
git add "$CANDIDATE_DIR" "$WORKFLOW_FILE"
if git diff --cached --quiet; then
  say "No new candidate changes to commit"
else
  git commit -m "feat(track1): add v1.7.2 compact hybrid candidate"
fi
COMMIT="$(git rev-parse HEAD)"
OWNER="$(gh repo view --json owner --jq '.owner.login' | tr '[:upper:]' '[:lower:]')"
REMOTE_IMAGE="ghcr.io/${OWNER}/omniedge-routeiq-track1:c-v172-${COMMIT}"

git push -u origin "$BRANCH"

say "Waiting for GitHub Actions publication"
RUN_ID=""
for _ in $(seq 1 48); do
  RUN_ID="$(gh run list --workflow "$WORKFLOW_NAME" --branch "$BRANCH" --limit 10 \
    --json databaseId,headSha --jq ".[] | select(.headSha == \"$COMMIT\") | .databaseId" 2>/dev/null | head -n1 || true)"
  [[ -n "$RUN_ID" ]] && break
  sleep 5
done
[[ -n "$RUN_ID" ]] || die "GitHub Actions run did not appear"
gh run watch "$RUN_ID" --exit-status

say "Verifying anonymous pull and architecture"
docker image rm "$REMOTE_IMAGE" >/dev/null 2>&1 || true
docker logout ghcr.io >/dev/null 2>&1 || true
timeout 240 docker pull "$REMOTE_IMAGE" >/dev/null
REMOTE_ARCH="$(docker image inspect --format '{{.Architecture}}' "$REMOTE_IMAGE")"
REMOTE_SIZE="$(docker image inspect --format '{{.Size}}' "$REMOTE_IMAGE")"
[[ "$REMOTE_ARCH" == "amd64" ]] || die "published image architecture is $REMOTE_ARCH"
[[ "$REMOTE_SIZE" -lt 500000000 ]] || die "published image is unexpectedly large: $REMOTE_SIZE"

DETAILS_FILE="routeiq-v172-candidate-${STAMP}.txt"
cat > "$DETAILS_FILE" <<EOF
OmniEdge RouteIQ v1.7.2 compact hybrid candidate
image=$REMOTE_IMAGE
commit=$COMMIT
branch=$BRANCH
workflow_run=$RUN_ID
architecture=$REMOTE_ARCH
size_bytes=$REMOTE_SIZE
protected_portal_baseline=94.7% accuracy / 3100 tokens / rank 16
portal_changed=no
EOF

printf '\n============================================================\n'
printf ' V1.7.2 CANDIDATE PUBLISHED AND VERIFIED\n'
printf '============================================================\n'
printf 'Image: %s\n' "$REMOTE_IMAGE"
printf 'Commit: %s\n' "$COMMIT"
printf 'Workflow run: %s\n' "$RUN_ID"
printf 'Details: %s\n' "$DETAILS_FILE"
printf 'ACT II portal: NOT CHANGED\n'
printf 'Do not replace the protected 3,100-token submission until this candidate is reviewed.\n'
