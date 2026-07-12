#!/usr/bin/env bash
set -Eeuo pipefail

REPO="${ROUTEIQ_REPO:-/tmp/routeiq-v13}"
BRANCH="${ROUTEIQ_EXPECTED_BRANCH:-track1-v13-ultra-local}"
SOURCE="${ROUTEIQ_SOURCE_DIR:-track1-v14-agent}"
TARGET="${ROUTEIQ_TARGET_DIR:-track1-v16-agent}"
BASE_IMAGE="${ROUTEIQ_BASE_IMAGE:-routeiq-v14-ultra-local:base}"
LOCAL_IMAGE="${ROUTEIQ_LOCAL_IMAGE:-routeiq-v16-safe-hybrid:test}"
PUBLISH="${ROUTEIQ_PUBLISH:-1}"

say(){ printf '\n==> %s\n' "$*"; }
die(){ printf '\nERROR: %s\n' "$*" >&2; exit 1; }
trap 'printf "\nFAILED at line %s. Champion and portal were not changed.\n" "$LINENO" >&2' ERR

cd "$REPO"
[[ "$(git branch --show-current)" == "$BRANCH" ]] || die "expected branch $BRANCH"
[[ -d "$SOURCE" ]] || die "$SOURCE is missing"
docker image inspect "$BASE_IMAGE" >/dev/null 2>&1 || die "missing base image $BASE_IMAGE"
FREE_KB="$(df -Pk /workspaces | awk 'NR==2{print $4}')"
(( FREE_KB >= 3145728 )) || die "less than 3 GB free"

say "Creating v1.6 safe-hybrid candidate"
rm -rf "$TARGET"
cp -a "$SOURCE" "$TARGET"
PATCHER="$(mktemp)"
base64 -d > "$PATCHER" <<'PATCH64'
ZnJvbSBwYXRobGliIGltcG9ydCBQYXRoCmltcG9ydCBzeXMKCnJvb3QgPSBQYXRoKHN5cy5hcmd2WzFdKQphZ2VudCA9IHJvb3QgLyAnYWdlbnQucHknCnRleHQgPSBhZ2VudC5yZWFkX3RleHQoZW5jb2Rpbmc9J3V0Zi04JykKCm9sZCA9ICdmcm9tIGxvY2FsLnZhbGlkYXRpb24gaW1wb3J0IHRhc2tfcHJvbXB0LCB2YWxpZGF0ZV9hbnN3ZXInCm5ldyA9ICdmcm9tIGxvY2FsLnZhbGlkYXRpb24gaW1wb3J0IGluZmVyX2NhdGVnb3J5LCB0YXNrX3Byb21wdCwgdmFsaWRhdGVfYW5zd2VyJwppZiBvbGQgbm90IGluIHRleHQ6CiAgICByYWlzZSBTeXN0ZW1FeGl0KCdhZ2VudCBpbXBvcnQgbWFya2VyIG5vdCBmb3VuZCcpCnRleHQgPSB0ZXh0LnJlcGxhY2Uob2xkLCBuZXcsIDEpCgpyZXF1ZXN0X21hcmtlciA9ICdcbmRlZiByZXF1ZXN0X2JhdGNoKHRhc2tzOiBsaXN0W2RpY3Rbc3RyLCBBbnldXSwgbW9kZWw6IHN0ciwgYXBpX2tleTogc3RyLCB1cmw6IHN0cikgLT4gZGljdFtzdHIsIHN0cl06XG4nCmlmIHJlcXVlc3RfbWFya2VyIG5vdCBpbiB0ZXh0OgogICAgcmFpc2UgU3lzdGVtRXhpdCgncmVxdWVzdF9iYXRjaCBtYXJrZXIgbm90IGZvdW5kJykKaGVscGVyID0gJycnCgpkZWYgcmVtb3RlX3Rva2VuX2J1ZGdldCh0YXNrczogbGlzdFtkaWN0W3N0ciwgQW55XV0pIC0+IGludDoKICAgIHBlcl90YXNrID0gewogICAgICAgICJmYWN0dWFsIjogMTkyLAogICAgICAgICJtYXRoIjogMTYwLAogICAgICAgICJzZW50aW1lbnQiOiAxNjAsCiAgICAgICAgInN1bW1hcnkiOiAyMjAsCiAgICAgICAgIm5lciI6IDIyMCwKICAgICAgICAibG9naWMiOiAxOTIsCiAgICAgICAgImNvZGUiOiAzMjAsCiAgICB9CiAgICB0b3RhbCA9IHN1bShwZXJfdGFzay5nZXQoaW5mZXJfY2F0ZWdvcnkodGFzayksIDIyMCkgZm9yIHRhc2sgaW4gdGFza3MpCiAgICByZXR1cm4gbWluKDQwOTYsIG1heCg5NiwgdG90YWwpKQonJycKdGV4dCA9IHRleHQucmVwbGFjZShyZXF1ZXN0X21hcmtlciwgaGVscGVyICsgcmVxdWVzdF9tYXJrZXIsIDEpCgpvbGQgPSAnIm1heF90b2tlbnMiOiBtaW4oNDA5NiwgbWF4KDI1NiwgMjIwICogbGVuKHRhc2tzKSkpLCcKaWYgb2xkIG5vdCBpbiB0ZXh0OgogICAgcmFpc2UgU3lzdGVtRXhpdCgncmVtb3RlIG1heF90b2tlbnMgbWFya2VyIG5vdCBmb3VuZCcpCnRleHQgPSB0ZXh0LnJlcGxhY2Uob2xkLCAnIm1heF90b2tlbnMiOiByZW1vdGVfdG9rZW5fYnVkZ2V0KHRhc2tzKSwnLCAxKQoKdmFsaWRhdGVkX21hcmtlciA9ICdcbmRlZiBfdmFsaWRhdGVkX3N1YnNldCh0YXNrczogbGlzdFtkaWN0W3N0ciwgQW55XV0sIHByb3Bvc2VkOiBkaWN0W3N0ciwgc3RyXSwgc291cmNlOiBzdHIpIC0+IGRpY3Rbc3RyLCBzdHJdOlxuJwppZiB2YWxpZGF0ZWRfbWFya2VyIG5vdCBpbiB0ZXh0OgogICAgcmFpc2UgU3lzdGVtRXhpdCgnX3ZhbGlkYXRlZF9zdWJzZXQgbWFya2VyIG5vdCBmb3VuZCcpCmhlbHBlciA9ICcnJwoKZGVmIHJlcXVpcmVzX3ZlcmlmaWVkX2dlb2dyYXBoeSh0YXNrOiBkaWN0W3N0ciwgQW55XSkgLT4gYm9vbDoKICAgIGlmIGluZmVyX2NhdGVnb3J5KHRhc2spICE9ICJmYWN0dWFsIjoKICAgICAgICByZXR1cm4gRmFsc2UKICAgIHByb21wdCA9IHRhc2tfcHJvbXB0KHRhc2spLmxvd2VyKCkKICAgIGV4cGxpY2l0ID0gYW55KHRlcm0gaW4gcHJvbXB0IGZvciB0ZXJtIGluICgKICAgICAgICAiYm9keSBvZiB3YXRlciIsICJ3aGF0IHdhdGVyIiwgIndoaWNoIHdhdGVyIiwgIm5lYXJieSB3YXRlciIsCiAgICAgICAgInJpdmVyIGlzIGl0IG5lYXIiLCAibGFrZSBpcyBpdCBuZWFyIiwgInNlYSBpcyBpdCBuZWFyIiwKICAgICAgICAib2NlYW4gaXMgaXQgbmVhciIsICJsb2NhdGVkIG5lYXIgd2hpY2ggcml2ZXIiLCAibG9jYXRlZCBuZWFyIHdoaWNoIGxha2UiLAogICAgKSkKICAgIGluZmVycmVkID0gKAogICAgICAgIGFueSh0ZXJtIGluIHByb21wdCBmb3IgdGVybSBpbiAoIiBuZWFyIiwgIm5lYXIgIiwgImJlc2lkZSIsICJhZGphY2VudCIsICJjbG9zZXN0IiwgIm5lYXJieSIpKQogICAgICAgIGFuZCBhbnkodGVybSBpbiBwcm9tcHQgZm9yIHRlcm0gaW4gKCJjYXBpdGFsIiwgImNpdHkiLCAidG93biIsICJjb3VudHJ5IiwgImxvY2F0aW9uIiwgImxvY2F0ZWQiKSkKICAgICAgICBhbmQgYW55KHRlcm0gaW4gcHJvbXB0IGZvciB0ZXJtIGluICgid2F0ZXIiLCAicml2ZXIiLCAibGFrZSIsICJzZWEiLCAib2NlYW4iLCAiYmF5IiwgImhhcmJvdXIiLCAiaGFyYm9yIikpCiAgICApCiAgICByZXR1cm4gZXhwbGljaXQgb3IgaW5mZXJyZWQKJycnCnRleHQgPSB0ZXh0LnJlcGxhY2UodmFsaWRhdGVkX21hcmtlciwgaGVscGVyICsgdmFsaWRhdGVkX21hcmtlciwgMSkKCm9sZCA9ICcgICAgICAgIGlmIG5vdCB0YXNrOlxuICAgICAgICAgICAgY29udGludWVcbiAgICAgICAgcmVwYWlyZWQgPSByZXBhaXJfYW5zd2VyKHRhc2ssIGFuc3dlcilcbicKbmV3ID0gJyAgICAgICAgaWYgbm90IHRhc2s6XG4gICAgICAgICAgICBjb250aW51ZVxuICAgICAgICBpZiBzb3VyY2UgPT0gIlF3ZW4iIGFuZCByZXF1aXJlc192ZXJpZmllZF9nZW9ncmFwaHkodGFzayk6XG4gICAgICAgICAgICBsb2coZiJRd2VuIHZhbGlkYXRpb24gcmVqZWN0ZWQge3Rhc2tfaWR9OiBnZW9ncmFwaGljIHByb3hpbWl0eSByZXF1aXJlcyB2ZXJpZmllZCBmYWxsYmFjayIpXG4gICAgICAgICAgICBjb250aW51ZVxuICAgICAgICByZXBhaXJlZCA9IHJlcGFpcl9hbnN3ZXIodGFzaywgYW5zd2VyKVxuJwppZiBvbGQgbm90IGluIHRleHQ6CiAgICByYWlzZSBTeXN0ZW1FeGl0KCd2YWxpZGF0ZWQtc3Vic2V0IGJvZHkgbWFya2VyIG5vdCBmb3VuZCcpCnRleHQgPSB0ZXh0LnJlcGxhY2Uob2xkLCBuZXcsIDEpCgphZ2VudC53cml0ZV90ZXh0KHRleHQsIGVuY29kaW5nPSd1dGYtOCcpCgoocm9vdCAvICd0ZXN0cycgLyAndGVzdF9zYWZlX2h5YnJpZC5weScpLndyaXRlX3RleHQoJycnaW1wb3J0IHVuaXR0ZXN0CmZyb20gYWdlbnQgaW1wb3J0IHJlbW90ZV90b2tlbl9idWRnZXQsIHJlcXVpcmVzX3ZlcmlmaWVkX2dlb2dyYXBoeQoKY2xhc3MgU2FmZUh5YnJpZFRlc3RzKHVuaXR0ZXN0LlRlc3RDYXNlKToKICAgIGRlZiB0ZXN0X2dlb2dyYXBoeV9pc19mYWlsX2Nsb3NlZChzZWxmKToKICAgICAgICB0YXNrID0geyJ0YXNrX2lkIjoiZzEiLCJ0YXNrX3R5cGUiOiJmYWN0dWFsX2tub3dsZWRnZSIsInByb21wdCI6IldoYXQgaXMgdGhlIGNhcGl0YWwsIGFuZCB3aGF0IGJvZHkgb2Ygd2F0ZXIgaXMgaXQgbmVhcj8ifQogICAgICAgIHNlbGYuYXNzZXJ0VHJ1ZShyZXF1aXJlc192ZXJpZmllZF9nZW9ncmFwaHkodGFzaykpCgogICAgZGVmIHRlc3RfY29uY2VwdF9jb21wYXJpc29uX3N0YXlzX2xvY2FsKHNlbGYpOgogICAgICAgIHRhc2sgPSB7InRhc2tfaWQiOiJmMSIsInRhc2tfdHlwZSI6ImZhY3R1YWxfa25vd2xlZGdlIiwicHJvbXB0IjoiQnJpZWZseSBjb21wYXJlIG1hY2hpbmUgbGVhcm5pbmcgYW5kIGRlZXAgbGVhcm5pbmcuIn0KICAgICAgICBzZWxmLmFzc2VydEZhbHNlKHJlcXVpcmVzX3ZlcmlmaWVkX2dlb2dyYXBoeSh0YXNrKSkKCiAgICBkZWYgdGVzdF9mYWN0dWFsX2ZhbGxiYWNrX2J1ZGdldChzZWxmKToKICAgICAgICB0YXNrID0geyJ0YXNrX2lkIjoiZjIiLCJ0YXNrX3R5cGUiOiJmYWN0dWFsX2tub3dsZWRnZSIsInByb21wdCI6Ik5hbWUgYSBjYXBpdGFsIGNpdHkuIn0KICAgICAgICBzZWxmLmFzc2VydEVxdWFsKHJlbW90ZV90b2tlbl9idWRnZXQoW3Rhc2tdKSwgMTkyKQonJycsIGVuY29kaW5nPSd1dGYtOCcpCgoocm9vdCAvICdEb2NrZXJmaWxlLnYxNicpLndyaXRlX3RleHQoJycnRlJPTSByb3V0ZWlxLXYxNC11bHRyYS1sb2NhbDpiYXNlCkVOViBRV0VOX01PREU9dGhpbmtpbmcgXFwKICAgIFFXRU5fU0VFRD00MiBcXAogICAgUVdFTl9USU1FT1VUX1NFQ09ORFM9MzYwCkNPUFkgYWdlbnQucHkgL2FwcC9hZ2VudC5weQpDT1BZIGxvY2FsIC9hcHAvbG9jYWwKRU5UUllQT0lOVCBbInB5dGhvbjMiLCAiL2FwcC9hZ2VudC5weSJdCicnJywgZW5jb2Rpbmc9J3V0Zi04JykK
PATCH64
python3 "$PATCHER" "$TARGET"
rm -f "$PATCHER"

say "Running unit tests"
(cd "$TARGET" && python3 -m unittest discover -s tests -v)

say "Building thin image on existing 4B layer"
docker build --progress=plain -f "$TARGET/Dockerfile.v16" -t "$LOCAL_IMAGE" "$TARGET"

ROOT="$(mktemp -d)"
mkdir -p "$ROOT/input" "$ROOT/output"
chmod 777 "$ROOT/output"
cp "$TARGET/bench/tasks.json" "$ROOT/input/tasks.json"

say "Running 19-task benchmark under 2 CPU / 4 GB"
START="$(date +%s)"
set +e
timeout 540 docker run --rm --network none --cpus=2 --memory=4g \
  -e ROUTEIQ_LOCAL_ONLY=1 \
  -v "$ROOT/input:/input:ro" -v "$ROOT/output:/output" \
  "$LOCAL_IMAGE" 2>&1 | tee "$ROOT/container.log"
RUN_STATUS="${PIPESTATUS[0]}"
set -e
END="$(date +%s)"
printf '%s\n' "$((END-START))" > "$ROOT/runtime.txt"
[[ "$RUN_STATUS" -eq 0 ]] || die "container failed"
[[ -s "$ROOT/output/results.json" ]] || die "results.json missing"

set +e
python3 "$TARGET/bench/score_benchmark.py" \
  "$ROOT/input/tasks.json" "$ROOT/output/results.json" "$ROOT/runtime.txt" | tee "$ROOT/score.log"
set -e

python3 - "$TARGET" "$ROOT/input/tasks.json" "$ROOT/output/results.json" "$ROOT/output/benchmark-report.json" <<'PY'
import importlib.util,json,sys
from pathlib import Path

target=Path(sys.argv[1])
tasks=json.load(open(sys.argv[2],encoding='utf-8'))
results=json.load(open(sys.argv[3],encoding='utf-8'))
report=json.load(open(sys.argv[4],encoding='utf-8'))
spec=importlib.util.spec_from_file_location('candidate_agent',target/'agent.py')
module=importlib.util.module_from_spec(spec)
sys.path.insert(0,str(target)); spec.loader.exec_module(module)
wrong=report.get('wrong',[]); missing=report.get('missing',[])
passed=int(report.get('passed',0)); runtime=float(report.get('runtime_seconds',9999))
if wrong: raise SystemExit(f'GATE FAILED: wrong={wrong}')
if runtime>420: raise SystemExit(f'GATE FAILED: runtime={runtime}')
if not isinstance(results,list) or len(results)!=len(tasks): raise SystemExit('GATE FAILED: output count/schema')
by_id={str(t['task_id']):t for t in tasks}
if passed==len(tasks) and not missing:
    print('V1.6_GATE=PERFECT_LOCAL')
elif passed>=len(tasks)-1 and len(missing)==1:
    mid=str(missing[0]); task=by_id.get(mid)
    if not task or not module.requires_verified_geography(task):
        raise SystemExit(f'GATE FAILED: unexpected missing={missing}')
    print('V1.6_GATE=SAFE_HYBRID')
    print(f'V1.6_FALLBACK_TASK={mid}')
    print(f'V1.6_REMOTE_COMPLETION_CAP={module.remote_token_budget([task])}')
else:
    raise SystemExit(f'GATE FAILED: passed={passed} missing={missing}')
PY

GATE="$(python3 - "$ROOT/output/benchmark-report.json" <<'PY'
import json,sys
r=json.load(open(sys.argv[1])); print('PERFECT_LOCAL' if not r.get('missing') else 'SAFE_HYBRID')
PY
)"

ARCH="$(docker image inspect --format '{{.Architecture}}' "$LOCAL_IMAGE")"
SIZE="$(docker image inspect --format '{{.Size}}' "$LOCAL_IMAGE")"
[[ "$ARCH" == amd64 ]] || die "wrong architecture: $ARCH"
[[ "$SIZE" -lt 8000000000 ]] || die "image too large: $SIZE"

say "Saving gated source"
find "$TARGET" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$TARGET" -type f -name '*.pyc' -delete
git add "$TARGET"
if ! git diff --cached --quiet; then git commit -m "feat(track1): add v1.6 safe hybrid routing"; fi
COMMIT="$(git rev-parse HEAD)"

if [[ "$PUBLISH" != 1 ]]; then
  printf 'Gate: %s\nCommit: %s\nReport: %s\n' "$GATE" "$COMMIT" "$ROOT/output/benchmark-report.json"
  exit 0
fi

command -v gh >/dev/null || die "gh CLI missing"
OWNER="$(gh repo view --json owner --jq '.owner.login')"
TOKEN="$(gh auth token)"
OPAQUE="$(python3 - <<'PY'
import secrets; print(secrets.token_hex(8))
PY
)"
REMOTE="ghcr.io/${OWNER,,}/omniedge-routeiq-track1:c-${OPAQUE}"
PUSH_LOG="$(mktemp)"
printf '%s' "$TOKEN" | docker login ghcr.io -u "$OWNER" --password-stdin >/dev/null 2>&1
docker tag "$LOCAL_IMAGE" "$REMOTE"
docker push "$REMOTE" > "$PUSH_LOG" 2>&1 || { tail -40 "$PUSH_LOG" >&2; die "push failed"; }
DIGEST="$(grep -Eo 'sha256:[0-9a-f]{64}' "$PUSH_LOG" | tail -1 || true)"
docker logout ghcr.io >/dev/null 2>&1 || true
docker manifest inspect "$REMOTE" >/dev/null 2>&1 || die "manifest check failed"

PRIVATE="/tmp/routeiq-v16-private-candidate.txt"
{
  echo 'PRIVATE — DO NOT POST OR SCREENSHOT'
  printf 'image=%s\ndigest=%s\ncommit=%s\ngate=%s\n' "$REMOTE" "$DIGEST" "$COMMIT" "$GATE"
  printf 'benchmark_report=%s\nbenchmark_results=%s\ncontainer_log=%s\n' \
    "$ROOT/output/benchmark-report.json" "$ROOT/output/results.json" "$ROOT/container.log"
} > "$PRIVATE"
chmod 600 "$PRIVATE"

say "V1.6 passed and was published; portal untouched"
printf 'Gate: %s\nPrivate details: %s\nReport: %s\n' "$GATE" "$PRIVATE" "$ROOT/output/benchmark-report.json"
printf 'Do not resubmit the portal yet.\n'
