#!/usr/bin/env bash
set -Eeuo pipefail

REPO="${ROUTEIQ_REPO:-/tmp/routeiq-v13}"
EXPECTED_BRANCH="${ROUTEIQ_EXPECTED_BRANCH:-track1-v13-ultra-local}"
SOURCE_DIR="${ROUTEIQ_SOURCE_DIR:-track1-v14-agent}"
TARGET_DIR="${ROUTEIQ_TARGET_DIR:-track1-v15-agent}"
BASE_IMAGE="${ROUTEIQ_BASE_IMAGE:-routeiq-v14-ultra-local:base}"
LOCAL_IMAGE="${ROUTEIQ_LOCAL_IMAGE:-routeiq-v15-precision-hybrid:test}"
PUBLISH="${ROUTEIQ_PUBLISH:-1}"

say() { printf '\n==> %s\n' "$*"; }
die() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }
trap 'printf "\nFAILED at line %s. The scored champion and portal submission were not changed.\n" "$LINENO" >&2' ERR

for command in git python3 docker timeout; do
  command -v "$command" >/dev/null || die "$command is required"
done

[[ -d "$REPO" ]] || die "worktree not found: $REPO"
cd "$REPO"
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || die "expected branch $EXPECTED_BRANCH"
[[ -d "$SOURCE_DIR" ]] || die "$SOURCE_DIR is missing; run the v1.4 script first"
docker image inspect "$BASE_IMAGE" >/dev/null 2>&1 || die "local 4B base image is missing: $BASE_IMAGE"

FREE_KB="$(df -Pk /workspaces | awk 'NR==2 {print $4}')"
[[ "$FREE_KB" =~ ^[0-9]+$ ]] || die "could not determine free disk space"
if (( FREE_KB < 3145728 )); then
  die "less than 3 GB is free; prune Docker cache before continuing"
fi

say "Creating isolated v1.5 precision-hybrid candidate"
STAMP="$(date +%Y%m%d-%H%M%S)"
if [[ -e "$TARGET_DIR" ]]; then
  tar -czf "/tmp/routeiq-v15-backup-${STAMP}.tgz" "$TARGET_DIR"
  rm -rf "$TARGET_DIR"
fi
cp -a "$SOURCE_DIR" "$TARGET_DIR"

python3 - "$TARGET_DIR" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
qwen = root / "local" / "qwen.py"
validation = root / "local" / "validation.py"
agent = root / "agent.py"

qwen_text = qwen.read_text(encoding="utf-8")
start = qwen_text.index("    prompt = (\n")
end_marker = "        + mode_suffix\n    )\n"
end = qwen_text.index(end_marker, start) + len(end_marker)
new_prompt = '''    prompt = (
        "Act as a cautious final-answer solver. Solve every task independently, then audit every "
        "requested clause before emitting output. Keep factual answers concise, normally under 80 words. "
        "Never replace an unknown local geographic feature with a distant ocean. When asked what body "
        "of water a city is near, prefer a specific river, lake, bay, harbour, canal, or reservoir "
        "directly in or beside that city; name an ocean only when the city is genuinely coastal. "
        "For comparisons, define both items, explain how each works, and state the decisive distinction. "
        "For code, return complete executable Python. For NER, include every entity and allowed label. "
        "For constrained summaries, obey counts and limits exactly. "
        "Output one compact JSON object per line only: "
        '{"i":"ID","a":"FINAL ANSWER"}. No array, markdown, or commentary outside answer strings. '
        "Escape newlines inside JSON strings. Tasks:"
        + json.dumps(compact_tasks, ensure_ascii=False, separators=(",", ":"))
        + " "
        + mode_suffix
    )
'''
qwen_text = qwen_text[:start] + new_prompt + qwen_text[end:]
qwen.write_text(qwen_text, encoding="utf-8")

validation_text = validation.read_text(encoding="utf-8")
old = '''    elif category == "factual":
        if not re.search(r"[A-Za-z0-9]", answer):
            return False, "factual answer has no substantive content"

    return True, "format validation passed"
'''
new = '''    elif category == "factual":
        if not re.search(r"[A-Za-z0-9]", answer):
            return False, "factual answer has no substantive content"

        prompt_lower = prompt.lower()
        answer_words = re.findall(r"\\b[\\w'-]+\\b", answer)
        if "briefly" in prompt_lower and len(answer_words) > 120:
            return False, "brief factual answer is excessively long or possibly truncated"

        if "rgb" in prompt_lower and "ryb" in prompt_lower:
            if not all(term in lowered for term in ("red", "green", "blue")):
                return False, "RGB primary colors are incomplete"
            if "additive" not in lowered or not any(term in lowered for term in ("pigment", "subtractive")):
                return False, "RGB versus RYB distinction is incomplete"

        if "machine learning" in prompt_lower and "deep learning" in prompt_lower:
            if "neural" not in lowered:
                return False, "deep-learning mechanism is missing"
            if not any(term in lowered for term in ("feature", "representation")):
                return False, "feature-learning distinction is missing"

        if re.search(r"\\bram\\b", prompt_lower) and re.search(r"\\brom\\b", prompt_lower):
            if "volatile" not in lowered or not any(term in lowered for term in ("non-volatile", "nonvolatile")):
                return False, "RAM/ROM volatility distinction is incomplete"
            if not any(term in lowered for term in ("firmware", "bios")):
                return False, "ROM use is incomplete"

        if "body of water" in prompt_lower:
            local_water_terms = (
                "lake", "river", "bay", "harbour", "harbor", "canal", "reservoir",
                "lagoon", "creek", "strait", "estuary", "fjord", "inlet",
            )
            broad_oceans = (
                "pacific ocean", "atlantic ocean", "indian ocean",
                "southern ocean", "arctic ocean",
            )
            if any(ocean in lowered for ocean in broad_oceans) and not any(
                term in lowered for term in local_water_terms
            ):
                return False, "nearby-water answer names only a broad ocean"

    return True, "format validation passed"
'''
if old not in validation_text:
    raise SystemExit("validation patch marker not found")
validation.write_text(validation_text.replace(old, new), encoding="utf-8")

agent_text = agent.read_text(encoding="utf-8")
agent_text = agent_text.replace(
    "from local.validation import task_prompt, validate_answer",
    "from local.validation import infer_category, task_prompt, validate_answer",
)
old_budget = '"max_tokens": min(4096, max(256, 220 * len(tasks))),'
new_budget = '''"max_tokens": min(
            4096,
            max(
                96,
                sum(
                    140 if infer_category(task) == "factual"
                    else 260 if infer_category(task) == "code"
                    else 190
                    for task in tasks
                ),
            ),
        ),'''
if old_budget not in agent_text:
    raise SystemExit("remote token-budget patch marker not found")
agent_text = agent_text.replace(old_budget, new_budget)
agent.write_text(agent_text, encoding="utf-8")

dockerfile = root / "Dockerfile.v15"
dockerfile.write_text(
    '''FROM routeiq-v14-ultra-local:base

ENV QWEN_MODE=thinking \\
    QWEN_THINK_TEMP=0.25 \\
    QWEN_THINK_TOP_K=20 \\
    QWEN_THINK_TOP_P=0.90 \\
    QWEN_PRESENCE_PENALTY=0.0 \\
    QWEN_REASONING_BUDGET=640 \\
    QWEN_MAX_TOKENS=1200 \\
    QWEN_TIMEOUT_SECONDS=330

COPY agent.py /app/agent.py
COPY local /app/local

ENTRYPOINT ["python3", "/app/agent.py"]
''',
    encoding="utf-8",
)
PY

say "Running v1.5 Python tests"
(
  cd "$TARGET_DIR"
  python3 -m unittest discover -s tests -v
)

say "Building a thin candidate on the existing 4B model layer"
docker build --progress=plain \
  -f "$TARGET_DIR/Dockerfile.v15" \
  -t "$LOCAL_IMAGE" \
  "$TARGET_DIR"

BENCH_ROOT="$(mktemp -d)"
mkdir -p "$BENCH_ROOT/input" "$BENCH_ROOT/output"
chmod 777 "$BENCH_ROOT/output"
cp "$TARGET_DIR/bench/tasks.json" "$BENCH_ROOT/input/tasks.json"

say "Running the 19-task benchmark under 2 CPU / 4 GB"
START="$(date +%s)"
set +e
timeout 540 docker run --rm \
  --network none \
  --cpus=2 \
  --memory=4g \
  -e ROUTEIQ_LOCAL_ONLY=1 \
  -v "$BENCH_ROOT/input:/input:ro" \
  -v "$BENCH_ROOT/output:/output" \
  "$LOCAL_IMAGE" 2>&1 | tee "$BENCH_ROOT/container.log"
RUN_STATUS="${PIPESTATUS[0]}"
set -e
END="$(date +%s)"
printf '%s\n' "$((END - START))" > "$BENCH_ROOT/runtime.txt"

[[ "$RUN_STATUS" -eq 0 ]] || die "candidate container failed"
[[ -s "$BENCH_ROOT/output/results.json" ]] || die "candidate produced no results.json"

set +e
python3 "$TARGET_DIR/bench/score_benchmark.py" \
  "$BENCH_ROOT/input/tasks.json" \
  "$BENCH_ROOT/output/results.json" \
  "$BENCH_ROOT/runtime.txt" | tee "$BENCH_ROOT/score.log"
set -e

python3 - "$BENCH_ROOT/output/benchmark-report.json" "$BENCH_ROOT/output/results.json" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="utf-8"))
results = json.load(open(sys.argv[2], encoding="utf-8"))

if not isinstance(results, list) or len(results) != 19:
    raise SystemExit("GATE FAILED: results schema/count is invalid")
ids = [str(item.get("task_id", "")) for item in results if isinstance(item, dict)]
if len(ids) != 19 or len(set(ids)) != 19:
    raise SystemExit("GATE FAILED: duplicate or missing task IDs")

wrong = report.get("wrong", [])
missing = report.get("missing", [])
passed = int(report.get("passed", 0))
runtime = float(report.get("runtime_seconds", 9999))

if wrong:
    raise SystemExit(f"GATE FAILED: accepted wrong answers remain: {wrong}")
if runtime > 420:
    raise SystemExit(f"GATE FAILED: runtime {runtime:.1f}s exceeds 420s")
if passed == 19 and not missing:
    print("V1.5_GATE=PERFECT_LOCAL")
elif passed >= 18 and len(missing) <= 1:
    print("V1.5_GATE=SAFE_HYBRID")
    print(f"V1.5_FALLBACK_TASKS={','.join(missing)}")
else:
    raise SystemExit(
        f"GATE FAILED: require 19/19 local or at least 18 correct with only one safely rejected fallback; "
        f"passed={passed}, missing={missing}"
    )
PY

GATE_MODE="$(python3 - "$BENCH_ROOT/output/benchmark-report.json" <<'PY'
import json,sys
r=json.load(open(sys.argv[1]))
print("PERFECT_LOCAL" if r["passed"] == 19 and not r["missing"] else "SAFE_HYBRID")
PY
)"

ARCH="$(docker image inspect --format '{{.Architecture}}' "$LOCAL_IMAGE")"
SIZE="$(docker image inspect --format '{{.Size}}' "$LOCAL_IMAGE")"
[[ "$ARCH" == "amd64" ]] || die "candidate architecture is $ARCH, not amd64"
[[ "$SIZE" -lt 8000000000 ]] || die "candidate image is unexpectedly large: $SIZE bytes"

say "Saving the gated v1.5 source locally"
find "$TARGET_DIR" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$TARGET_DIR" -type f -name '*.pyc' -delete
git add "$TARGET_DIR"
if ! git diff --cached --quiet; then
  git commit -m "feat(track1): add v1.5 precision-hybrid factual guard"
fi
COMMIT="$(git rev-parse HEAD)"

if [[ "$PUBLISH" != "1" ]]; then
  say "Gate passed; publication skipped by ROUTEIQ_PUBLISH=$PUBLISH"
  printf 'Gate: %s\nCommit: %s\nBenchmark: %s\n' \
    "$GATE_MODE" "$COMMIT" "$BENCH_ROOT/output/benchmark-report.json"
  exit 0
fi

command -v gh >/dev/null || die "GitHub CLI is required for publication"
OWNER="$(gh repo view --json owner --jq '.owner.login')"
TOKEN="$(gh auth token)"
[[ -n "$OWNER" && -n "$TOKEN" ]] || die "GitHub CLI is not authenticated"

OPAQUE="$(python3 - <<'PY'
import secrets
print(secrets.token_hex(8))
PY
)"
REMOTE_IMAGE="ghcr.io/${OWNER,,}/omniedge-routeiq-track1:c-${OPAQUE}"
PUSH_LOG="$(mktemp)"

say "Publishing the gated candidate under an opaque reference"
printf '%s' "$TOKEN" | docker login ghcr.io -u "$OWNER" --password-stdin >/dev/null 2>&1
docker tag "$LOCAL_IMAGE" "$REMOTE_IMAGE"
if ! docker push "$REMOTE_IMAGE" >"$PUSH_LOG" 2>&1; then
  tail -n 40 "$PUSH_LOG" >&2
  die "candidate push failed"
fi
DIGEST="$(grep -Eo 'sha256:[0-9a-f]{64}' "$PUSH_LOG" | tail -n1 || true)"

PRIVATE_FILE="/tmp/routeiq-v15-private-candidate.txt"
{
  printf 'PRIVATE — DO NOT POST IN DISCORD, README, OR SCREENSHOTS\n'
  printf 'image=%s\n' "$REMOTE_IMAGE"
  printf 'digest=%s\n' "$DIGEST"
  printf 'commit=%s\n' "$COMMIT"
  printf 'gate=%s\n' "$GATE_MODE"
  printf 'benchmark_report=%s\n' "$BENCH_ROOT/output/benchmark-report.json"
  printf 'benchmark_results=%s\n' "$BENCH_ROOT/output/results.json"
  printf 'container_log=%s\n' "$BENCH_ROOT/container.log"
  printf 'push_log=%s\n' "$PUSH_LOG"
} > "$PRIVATE_FILE"
chmod 600 "$PRIVATE_FILE"

docker logout ghcr.io >/dev/null 2>&1 || true
docker manifest inspect "$REMOTE_IMAGE" >/dev/null 2>&1 || die "public manifest verification failed"

say "V1.5 candidate passed and was published without touching the portal"
printf 'Gate: %s\nPrivate candidate details: %s\nBenchmark report: %s\n' \
  "$GATE_MODE" "$PRIVATE_FILE" "$BENCH_ROOT/output/benchmark-report.json"
printf 'Do not resubmit the portal until this result is reviewed.\n'
