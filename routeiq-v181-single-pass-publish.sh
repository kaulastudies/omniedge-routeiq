#!/usr/bin/env bash
set -Eeuo pipefail

WORKTREE="${ROUTEIQ_WORKTREE:-/tmp/routeiq-v18}"
BRANCH="${ROUTEIQ_BRANCH:-track1-v18-zero-token-audit}"
SOURCE_DIR="${ROUTEIQ_SOURCE_DIR:-track1-v18-agent}"
CANDIDATE_DIR="${ROUTEIQ_CANDIDATE_DIR:-track1-v181-agent}"
BASE_IMAGE="${ROUTEIQ_BASE_IMAGE:-routeiq-v14-ultra-local:base}"
LOCAL_IMAGE="${ROUTEIQ_LOCAL_IMAGE:-routeiq-v181-single-pass:test}"
MIN_PASS="${ROUTEIQ_MIN_PASS:-18}"

say() { printf '\n==> %s\n' "$*"; }
die() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }
trap 'printf "\nFAILED at line %s. The portal and current scored submission were not changed.\n" "$LINENO" >&2' ERR

for command in git python3 docker timeout gh; do
  command -v "$command" >/dev/null || die "$command is required"
done

[[ -d "$WORKTREE/.git" || -f "$WORKTREE/.git" ]] || die "missing v1.8 worktree: $WORKTREE"
cd "$WORKTREE"
[[ "$(git branch --show-current)" == "$BRANCH" ]] || die "expected branch $BRANCH"
[[ -d "$SOURCE_DIR" ]] || die "missing source folder: $SOURCE_DIR"
[[ -f "$SOURCE_DIR/Dockerfile" ]] || die "missing source Dockerfile"
docker image inspect "$BASE_IMAGE" >/dev/null 2>&1 || die "missing local 4B base image: $BASE_IMAGE"

say "Creating v1.8.1 single-pass local-only candidate"
rm -rf "$CANDIDATE_DIR"
cp -a "$SOURCE_DIR" "$CANDIDATE_DIR"
chmod -R u+rwX "$CANDIDATE_DIR"

cat > "$CANDIDATE_DIR/Dockerfile.local" <<'DOCKER'
FROM routeiq-v14-ultra-local:base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ROUTEIQ_LOCAL_ONLY=1 \
    ROUTEIQ_TOTAL_BUDGET_SECONDS=575 \
    QWEN_ENABLED=1 \
    QWEN_BINARY=/app/llama-completion \
    QWEN_MODEL_PATH=/app/models/Qwen3-4B-Q4_K_M.gguf \
    QWEN_THREADS=2 \
    QWEN_CONTEXT_SIZE=4096 \
    QWEN_PROPOSAL_MODE=thinking \
    QWEN_PROPOSAL_MAX_TOKENS=1800 \
    QWEN_PROPOSAL_TIMEOUT_SECONDS=430 \
    QWEN_AUDIT_ENABLED=0 \
    QWEN_REASONING_BUDGET=768 \
    QWEN_PRESENCE_PENALTY=0.0

COPY agent.py /app/agent.py
COPY local /app/local

ENTRYPOINT ["python3", "/app/agent.py"]
DOCKER

cp "$CANDIDATE_DIR/Dockerfile" "$CANDIDATE_DIR/Dockerfile.v181"
cat >> "$CANDIDATE_DIR/Dockerfile.v181" <<'DOCKER'

ENV ROUTEIQ_LOCAL_ONLY=1 \
    ROUTEIQ_TOTAL_BUDGET_SECONDS=575 \
    QWEN_PROPOSAL_MODE=thinking \
    QWEN_PROPOSAL_MAX_TOKENS=1800 \
    QWEN_PROPOSAL_TIMEOUT_SECONDS=430 \
    QWEN_AUDIT_ENABLED=0 \
    QWEN_REASONING_BUDGET=768 \
    QWEN_PRESENCE_PENALTY=0.0
DOCKER

say "Running syntax and unit tests"
(
  cd "$CANDIDATE_DIR"
  python3 -m py_compile agent.py local/*.py
  python3 -m unittest discover -s tests -v
)

say "Building thin local benchmark image"
docker build --progress=plain \
  -f "$CANDIDATE_DIR/Dockerfile.local" \
  -t "$LOCAL_IMAGE" \
  "$CANDIDATE_DIR"

BENCH_ROOT="$(mktemp -d)"
mkdir -p "$BENCH_ROOT/input" "$BENCH_ROOT/output"
chmod 777 "$BENCH_ROOT/output"
cp "$CANDIDATE_DIR/bench/tasks.json" "$BENCH_ROOT/input/tasks.json"

say "Running 19-task single-pass zero-Fireworks benchmark under 2 CPU / 4 GB"
START="$(date +%s)"
set +e
timeout 590 docker run --rm \
  --network none \
  --cpus=2 \
  --memory=4g \
  -v "$BENCH_ROOT/input:/input:ro" \
  -v "$BENCH_ROOT/output:/output" \
  "$LOCAL_IMAGE" 2>&1 | tee "$BENCH_ROOT/container.log"
RUN_STATUS="${PIPESTATUS[0]}"
set -e
END="$(date +%s)"
printf '%s\n' "$((END - START))" > "$BENCH_ROOT/runtime.txt"

[[ "$RUN_STATUS" -eq 0 ]] || die "candidate failed or exceeded runtime"
[[ -s "$BENCH_ROOT/output/results.json" ]] || die "candidate produced no results.json"

set +e
python3 "$CANDIDATE_DIR/bench/score_benchmark.py" \
  "$BENCH_ROOT/input/tasks.json" \
  "$BENCH_ROOT/output/results.json" \
  "$BENCH_ROOT/runtime.txt" | tee "$BENCH_ROOT/score.log"
set -e

GATE="$(python3 - "$BENCH_ROOT/output/benchmark-report.json" "$MIN_PASS" <<'PY'
import json, sys
report = json.load(open(sys.argv[1], encoding="utf-8"))
minimum = int(sys.argv[2])
passed = int(report.get("passed", 0))
missing = report.get("missing", [])
runtime = float(report.get("runtime_seconds", 9999))
if missing:
    raise SystemExit(f"GATE FAILED: missing answers remain: {missing}")
if passed < minimum:
    raise SystemExit(f"GATE FAILED: only {passed}/19 passed; minimum is {minimum}")
if runtime > 560:
    raise SystemExit(f"GATE FAILED: runtime {runtime:.1f}s exceeds 560s")
print("PERFECT_LOCAL" if passed == 19 else f"ZERO_TOKEN_EXPERIMENT_{passed}_OF_19")
PY
)"
printf 'V181_GATE=%s\n' "$GATE"

say "Creating GitHub Actions publication workflow"
mkdir -p .github/workflows
cat > .github/workflows/publish-track1-v181.yml <<'YAML'
name: Publish RouteIQ v1.8.1 Single Pass

on:
  push:
    branches:
      - track1-v18-zero-token-audit
    paths:
      - "track1-v181-agent/**"
      - ".github/workflows/publish-track1-v181.yml"

permissions:
  contents: read
  packages: write

concurrency:
  group: publish-routeiq-v181-single-pass
  cancel-in-progress: false

jobs:
  publish:
    runs-on: ubuntu-latest
    timeout-minutes: 40

    steps:
      - name: Checkout candidate branch
        uses: actions/checkout@v4

      - name: Free runner disk space
        run: |
          sudo rm -rf /usr/local/lib/android /usr/share/dotnet /opt/ghc || true
          df -h

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and publish linux/amd64 candidate
        uses: docker/build-push-action@v6
        with:
          context: ./track1-v181-agent
          file: ./track1-v181-agent/Dockerfile.v181
          platforms: linux/amd64
          push: true
          provenance: false
          sbom: false
          tags: ghcr.io/${{ github.repository_owner }}/omniedge-routeiq-track1:c-v181-${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
YAML

find "$CANDIDATE_DIR" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$CANDIDATE_DIR" -type f -name '*.pyc' -delete
git add "$CANDIDATE_DIR" .github/workflows/publish-track1-v181.yml
git commit -m "feat(track1): add v1.8.1 single-pass zero-token candidate"
COMMIT="$(git rev-parse HEAD)"

say "Pushing the experimental branch"
git push -u origin "$BRANCH"

say "Waiting for GitHub Actions publication"
RUN_ID=""
for _ in $(seq 1 40); do
  RUN_ID="$(gh api "repos/kaulastudies/omniedge-routeiq/actions/runs?branch=$BRANCH&per_page=10" \
    --jq ".workflow_runs[] | select(.head_sha == \"$COMMIT\") | .id" 2>/dev/null | head -n1 || true)"
  [[ -n "$RUN_ID" ]] && break
  sleep 5
done
[[ -n "$RUN_ID" ]] || die "workflow did not appear"

RUN_URL="$(gh run view "$RUN_ID" --json url --jq '.url')"
printf 'Workflow: %s\n' "$RUN_URL"
gh run watch "$RUN_ID" --exit-status

OWNER="$(gh repo view --json owner --jq '.owner.login')"
IMAGE="ghcr.io/${OWNER,,}/omniedge-routeiq-track1:c-v181-${COMMIT}"

say "Verifying anonymous public pull"
docker logout ghcr.io >/dev/null 2>&1 || true
docker image rm "$IMAGE" >/dev/null 2>&1 || true
docker pull "$IMAGE" >/dev/null

PRIVATE_DIR="/workspaces/.routeiq-private"
PRIVATE_FILE="$PRIVATE_DIR/v181-candidate.txt"
mkdir -p "$PRIVATE_DIR"
chmod 700 "$PRIVATE_DIR"
{
  printf 'PRIVATE — DO NOT POST IN DISCORD, README, OR SCREENSHOTS\n'
  printf 'image=%s\n' "$IMAGE"
  printf 'commit=%s\n' "$COMMIT"
  printf 'gate=%s\n' "$GATE"
  printf 'benchmark_report=%s\n' "$BENCH_ROOT/output/benchmark-report.json"
  printf 'benchmark_results=%s\n' "$BENCH_ROOT/output/results.json"
  printf 'container_log=%s\n' "$BENCH_ROOT/container.log"
  printf 'workflow=%s\n' "$RUN_URL"
} > "$PRIVATE_FILE"
chmod 600 "$PRIVATE_FILE"

say "v1.8.1 single-pass zero-token candidate published successfully"
printf 'Gate: %s\nPrivate candidate record: %s\n' "$GATE" "$PRIVATE_FILE"
printf 'The portal and current scored submission were not changed.\n'
printf 'Do not submit until this benchmark result is reviewed.\n'
