#!/usr/bin/env bash
set -Eeuo pipefail

REPO="${ROUTEIQ_REPO:-/tmp/routeiq-v13}"
BRANCH="${ROUTEIQ_BRANCH:-track1-v13-ultra-local}"
WORKFLOW_FILE=".github/workflows/publish-track1-v16-candidate.yml"
WORKFLOW_NAME="Publish RouteIQ v1.6 Candidate"
PACKAGE="omniedge-routeiq-track1"

say() { printf '\n==> %s\n' "$*"; }
die() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }
trap 'printf "\nFAILED at line %s. The scored champion and portal were not changed.\n" "$LINENO" >&2' ERR

for command in git gh docker sudo; do
  command -v "$command" >/dev/null || die "$command is required"
done

[[ -d "$REPO" ]] || die "missing worktree: $REPO"
cd "$REPO"
[[ "$(git branch --show-current)" == "$BRANCH" ]] || die "expected branch $BRANCH"
[[ -f track1-v16-agent/Dockerfile ]] || die "track1-v16-agent/Dockerfile is missing"
[[ -f track1-v16-agent/agent.py ]] || die "track1-v16-agent/agent.py is missing"

say "Making only the candidate and workflow paths writable"
mkdir -p .github/workflows
sudo chown -R "$(id -u):$(id -g)" track1-v16-agent .github
chmod -R u+rwX track1-v16-agent .github

# Remove the failed local GHCR session. Publishing below uses GitHub Actions,
# whose repository token has packages:write permission.
docker logout ghcr.io >/dev/null 2>&1 || true

cat > "$WORKFLOW_FILE" <<'YAML'
name: Publish RouteIQ v1.6 Candidate

on:
  push:
    branches:
      - track1-v13-ultra-local
    paths:
      - "track1-v16-agent/**"
      - ".github/workflows/publish-track1-v16-candidate.yml"

permissions:
  contents: read
  packages: write

concurrency:
  group: publish-routeiq-v16-candidate
  cancel-in-progress: false

jobs:
  publish:
    runs-on: ubuntu-latest
    timeout-minutes: 35

    steps:
      - name: Checkout candidate branch
        uses: actions/checkout@v4

      - name: Free runner disk space
        run: |
          sudo rm -rf /usr/local/lib/android /usr/share/dotnet /opt/ghc || true
          docker system df || true
          df -h

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR with repository token
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and publish linux/amd64 candidate
        uses: docker/build-push-action@v6
        with:
          context: ./track1-v16-agent
          file: ./track1-v16-agent/Dockerfile
          platforms: linux/amd64
          push: true
          provenance: false
          sbom: false
          tags: ghcr.io/${{ github.repository_owner }}/omniedge-routeiq-track1:c-${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
YAML

say "Committing the workflow"
git add "$WORKFLOW_FILE"
if ! git diff --cached --quiet; then
  git commit -m "ci(track1): publish v1.6 candidate through GitHub Actions"
fi

COMMIT="$(git rev-parse HEAD)"
OWNER="$(gh repo view --json owner --jq '.owner.login')"
[[ -n "$OWNER" ]] || die "could not determine repository owner"
IMAGE="ghcr.io/${OWNER,,}/${PACKAGE}:c-${COMMIT}"

say "Pushing the candidate branch"
git push -u origin "$BRANCH"

say "Waiting for the GitHub Actions run to appear"
RUN_ID=""
for _ in $(seq 1 30); do
  RUN_ID="$(gh run list \
    --workflow "$WORKFLOW_NAME" \
    --branch "$BRANCH" \
    --limit 1 \
    --json databaseId,headSha \
    --jq ".[] | select(.headSha == \"$COMMIT\") | .databaseId" 2>/dev/null | head -n1 || true)"
  [[ -n "$RUN_ID" ]] && break
  sleep 5
done
[[ -n "$RUN_ID" ]] || die "workflow was pushed but no run appeared; inspect the Actions tab"

RUN_URL="$(gh run view "$RUN_ID" --json url --jq '.url')"
printf 'Workflow: %s\n' "$RUN_URL"

say "Watching the package publication"
gh run watch "$RUN_ID" --exit-status

say "Verifying the published public manifest"
for _ in $(seq 1 12); do
  if docker manifest inspect "$IMAGE" >/dev/null 2>&1; then
    VERIFIED=1
    break
  fi
  sleep 5
done
[[ "${VERIFIED:-0}" == "1" ]] || die "workflow succeeded but public manifest verification is still unavailable"

PRIVATE_FILE="/tmp/routeiq-v16-private-candidate.txt"
{
  printf 'PRIVATE — DO NOT POST IN DISCORD, README, OR SCREENSHOTS\n'
  printf 'image=%s\n' "$IMAGE"
  printf 'commit=%s\n' "$COMMIT"
  printf 'gate=SAFE_HYBRID\n'
  printf 'local_benchmark=18/19 correct; 0 accepted wrong; 1 verified fallback\n'
  printf 'remote_completion_cap=192\n'
  printf 'workflow=%s\n' "$RUN_URL"
} > "$PRIVATE_FILE"
chmod 600 "$PRIVATE_FILE"

say "Publication completed without local package-write permissions"
printf 'Private candidate details: %s\n' "$PRIVATE_FILE"
printf 'The scored champion and portal submission were not changed.\n'
printf 'Do not resubmit tonight. The candidate is safely published for review.\n'
