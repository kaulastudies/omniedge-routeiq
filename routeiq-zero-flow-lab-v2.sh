#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# OmniEdge RouteIQ — Zero-token flow laboratory
#
# Purpose:
#   - Does NOT edit the repository.
#   - Does NOT push an image.
#   - Does NOT change the ACT II submission.
#   - Uses the published v1.8.1 image only as the local runtime/model base.
#   - Tests deterministic-only coverage and an experimental category-
#     microbatch Qwen flow against:
#       1) the repository benchmark; and
#       2) a fresh 19-task shadow benchmark.
#
# Usage from the repository root:
#   chmod +x routeiq-zero-flow-lab.sh
#   ./routeiq-zero-flow-lab.sh
df -h /workspaces
docker system df 2>/dev/null || true# Optional comparison with the untouched original Qwen flow:
#   RUN_ORIGINAL=1 ./routeiq-zero-flow-lab.sh
#
# Override paths/image when necessary:
#   AGENT_DIR=track1-v181-agent \
#   BASE_IMAGE=ghcr.io/kaulastudies/omniedge-routeiq-track1:c-v181-9ce53f5e4565f102d057a4b00192572f2fd7fb7b \
#   ./routeiq-zero-flow-lab.sh
# ============================================================

BASE_IMAGE="${BASE_IMAGE:-ghcr.io/kaulastudies/omniedge-routeiq-track1:c-v181-9ce53f5e4565f102d057a4b00192572f2fd7fb7b}"
AGENT_DIR="${AGENT_DIR:-}"
SOURCE_REF="${SOURCE_REF:-origin/track1-v18-zero-token-audit}"
SOURCE_SUBDIR="${SOURCE_SUBDIR:-track1-v181-agent}"
RUN_ORIGINAL="${RUN_ORIGINAL:-0}"
TOTAL_BUDGET="${TOTAL_BUDGET:-575}"
STAMP="$(date +%Y%m%d-%H%M%S)"
LAB_ROOT="${LAB_ROOT:-.routeiq-zero-flow-lab-${STAMP}}"
REPORT_FILE="${LAB_ROOT}/routeiq-zero-flow-summary.txt"

fail() {
  echo >&2
  echo "ERROR: $*" >&2
  echo "Nothing was pushed and the portal submission was not changed." >&2
  exit 1
}

command -v git >/dev/null 2>&1 || fail "git is required."
command -v docker >/dev/null 2>&1 || fail "Docker is required in this Codespace."
command -v python3 >/dev/null 2>&1 || fail "python3 is required."
command -v timeout >/dev/null 2>&1 || fail "the timeout command is required."

git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
  || fail "Run this from inside the OmniEdge RouteIQ Git repository."

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

if [[ "$LAB_ROOT" != /* ]]; then
  LAB_ROOT="$REPO_ROOT/$LAB_ROOT"
fi
REPORT_FILE="$LAB_ROOT/routeiq-zero-flow-summary.txt"

mkdir -p "$LAB_ROOT"

is_valid_agent_dir() {
  local candidate="$1"
  [[ -f "$candidate/agent.py" ]] \
    && [[ -d "$candidate/local" ]] \
    && [[ -f "$candidate/bench/tasks.json" ]] \
    && [[ -f "$candidate/bench/score_benchmark.py" ]]
}

SOURCE_MODE=""

resolve_agent_dir() {
  local candidate agent_file ref

  # 1) Respect an explicitly supplied directory.
  if [[ -n "$AGENT_DIR" ]]; then
    if is_valid_agent_dir "$AGENT_DIR"; then
      AGENT_DIR="$(cd "$AGENT_DIR" && pwd)"
      SOURCE_MODE="explicit directory"
      return 0
    fi
    fail "AGENT_DIR='$AGENT_DIR' does not contain agent.py, local/, bench/tasks.json, and bench/score_benchmark.py."
  fi

  # 2) Check common locations in the current checkout.
  for candidate in "." "$SOURCE_SUBDIR"; do
    if is_valid_agent_dir "$candidate"; then
      AGENT_DIR="$(cd "$candidate" && pwd)"
      SOURCE_MODE="current checkout"
      return 0
    fi
  done

  # 3) Search nested folders, excluding Git metadata and previous labs.
  while IFS= read -r -d '' agent_file; do
    candidate="$(dirname "$agent_file")"
    if is_valid_agent_dir "$candidate"; then
      AGENT_DIR="$(cd "$candidate" && pwd)"
      SOURCE_MODE="auto-detected checkout folder"
      return 0
    fi
  done < <(
    find "$REPO_ROOT" -maxdepth 6 \
      -path "$REPO_ROOT/.git" -prune -o \
      -path "$REPO_ROOT/.routeiq-zero-flow-lab-*" -prune -o \
      -type f -name agent.py -print0
  )

  # 4) Extract the required source from an existing local Git ref without
  #    switching branches or modifying the working tree.
  for ref in \
    "$SOURCE_REF" \
    "refs/remotes/origin/track1-v18-zero-token-audit" \
    "refs/heads/track1-v18-zero-token-audit"; do
    if git cat-file -e "$ref:$SOURCE_SUBDIR/agent.py" 2>/dev/null \
      && git cat-file -e "$ref:$SOURCE_SUBDIR/bench/tasks.json" 2>/dev/null; then
      mkdir -p "$LAB_ROOT/source-snapshot"
      git archive "$ref" "$SOURCE_SUBDIR" \
        | tar -x -C "$LAB_ROOT/source-snapshot"
      AGENT_DIR="$LAB_ROOT/source-snapshot/$SOURCE_SUBDIR"
      SOURCE_MODE="Git snapshot from $ref"
      return 0
    fi
  done

  # 5) Fetch only the source branch ref, then extract it. This does not check
  #    out the branch and does not alter repository files.
  if git remote get-url origin >/dev/null 2>&1; then
    echo "Required v1.8.1 source is not in this checkout; fetching its Git ref only..."
    if git fetch --quiet origin \
      track1-v18-zero-token-audit:refs/remotes/origin/track1-v18-zero-token-audit; then
      ref="refs/remotes/origin/track1-v18-zero-token-audit"
      if git cat-file -e "$ref:$SOURCE_SUBDIR/agent.py" 2>/dev/null \
        && git cat-file -e "$ref:$SOURCE_SUBDIR/bench/tasks.json" 2>/dev/null; then
        mkdir -p "$LAB_ROOT/source-snapshot"
        git archive "$ref" "$SOURCE_SUBDIR" \
          | tar -x -C "$LAB_ROOT/source-snapshot"
        AGENT_DIR="$LAB_ROOT/source-snapshot/$SOURCE_SUBDIR"
        SOURCE_MODE="Git snapshot fetched from origin"
        return 0
      fi
    fi
  fi

  fail "Could not locate the v1.8.1 agent source. The script checked the current branch and origin/track1-v18-zero-token-audit without changing your working tree."
}

resolve_agent_dir

[[ -f "$AGENT_DIR/agent.py" ]] || fail "$AGENT_DIR/agent.py is missing."
[[ -d "$AGENT_DIR/local" ]] || fail "$AGENT_DIR/local is missing."
[[ -f "$AGENT_DIR/bench/tasks.json" ]] || fail "$AGENT_DIR/bench/tasks.json is missing."
[[ -f "$AGENT_DIR/bench/score_benchmark.py" ]] || fail "$AGENT_DIR/bench/score_benchmark.py is missing."

docker info >/dev/null 2>&1 || fail "Docker daemon is unavailable. Start/rebuild the Codespace with Docker support."

mkdir -p "$LAB_ROOT"/{original,micro,shadow,runs}
cp -a "$AGENT_DIR/agent.py" "$LAB_ROOT/original/agent.py"
cp -a "$AGENT_DIR/local" "$LAB_ROOT/original/local"
cp -a "$AGENT_DIR/agent.py" "$LAB_ROOT/micro/agent.py"
cp -a "$AGENT_DIR/local" "$LAB_ROOT/micro/local"
cp -a "$AGENT_DIR/bench/tasks.json" "$LAB_ROOT/canonical-tasks.json"
cp -a "$AGENT_DIR/bench/score_benchmark.py" "$LAB_ROOT/canonical-scorer.py"

exec > >(tee -a "$REPORT_FILE") 2>&1

echo "============================================================"
echo " OmniEdge RouteIQ zero-token flow laboratory"
echo "============================================================"
echo "Started:       $(date)"
echo "Repository:    $REPO_ROOT"
echo "Source folder: $AGENT_DIR"
echo "Source mode:   $SOURCE_MODE"
echo "Base image:    $BASE_IMAGE"
echo "Lab folder:    $LAB_ROOT"
echo "Git branch:    $(git branch --show-current || true)"
echo "Git commit:    $(git rev-parse --short HEAD)"
echo "Portal/source changes: NONE"
echo

echo "[1/8] Verifying the base image..."
if ! docker image inspect "$BASE_IMAGE" >/dev/null 2>&1; then
  echo "Base image is not local. Pulling it now..."
  docker pull "$BASE_IMAGE"
fi

docker image inspect "$BASE_IMAGE" \
  --format 'Image={{.RepoTags}} Architecture={{.Architecture}} OS={{.Os}} SizeBytes={{.Size}}'

ARCH="$(docker image inspect "$BASE_IMAGE" --format '{{.Architecture}}')"
OS_NAME="$(docker image inspect "$BASE_IMAGE" --format '{{.Os}}')"
[[ "$ARCH" == "amd64" ]] || fail "Base image architecture is '$ARCH', expected amd64."
[[ "$OS_NAME" == "linux" ]] || fail "Base image OS is '$OS_NAME', expected linux."

echo
echo_patch="[2/8] Creating the experimental category-microbatch router..."
echo "$echo_patch"

python3 - "$LAB_ROOT/micro/agent.py" <<'PY_PATCH'
from __future__ import annotations

import ast
import sys
from pathlib import Path

path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
tree = ast.parse(source, filename=str(path))

if any(isinstance(node, ast.FunctionDef) and node.name == "call_qwen_microbatches" for node in tree.body):
    raise SystemExit("call_qwen_microbatches already exists; refusing to double-patch the lab copy")

helper_source = r'''
def call_qwen_microbatches(tasks: list[dict[str, Any]]) -> dict[str, str]:
    """Run no more than three task-family batches through local Qwen.

    This isolates knowledge/extraction, reasoning/code, and language tasks
    while avoiding one giant mixed prompt. It remains fully local.
    """
    if not tasks:
        return {}

    families: dict[str, list[dict[str, Any]]] = {
        "knowledge": [],
        "reasoning": [],
        "language": [],
    }

    for task in tasks:
        category = infer_category(task)
        if category in {"factual", "ner"}:
            families["knowledge"].append(task)
        elif category in {"logic", "math", "code"}:
            families["reasoning"].append(task)
        else:
            families["language"].append(task)

    answers: dict[str, str] = {}
    minimum_remaining = int(os.getenv("QWEN_MICROBATCH_MIN_REMAINING", "65"))

    for family in ("knowledge", "reasoning", "language"):
        batch = families[family]
        if not batch:
            continue
        if seconds_left() < minimum_remaining:
            log(
                f"Skipping Qwen {family} microbatch: "
                f"only {seconds_left():.1f}s remain"
            )
            continue
        try:
            log(f"Running Qwen {family} microbatch with {len(batch)} tasks")
            proposed = call_qwen_batch(batch)
            for task_id, answer in proposed.items():
                if task_id not in answers and answer:
                    answers[task_id] = answer
        except Exception as error:
            log(
                f"Qwen {family} microbatch failed: "
                f"{type(error).__name__}: {error}"
            )

    return answers
'''
helper = ast.parse(helper_source).body[0]

class MainCallTransformer(ast.NodeTransformer):
    def __init__(self) -> None:
        self.in_main = False
        self.replacements = 0

    def visit_FunctionDef(self, node: ast.FunctionDef):
        previous = self.in_main
        if node.name == "main":
            self.in_main = True
        node = self.generic_visit(node)
        self.in_main = previous
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        previous = self.in_main
        if node.name == "main":
            self.in_main = True
        node = self.generic_visit(node)
        self.in_main = previous
        return node

    def visit_Call(self, node: ast.Call):
        node = self.generic_visit(node)
        if (
            self.in_main
            and isinstance(node.func, ast.Name)
            and node.func.id == "call_qwen_batch"
        ):
            node.func.id = "call_qwen_microbatches"
            self.replacements += 1
        return node

transformer = MainCallTransformer()
tree = transformer.visit(tree)
ast.fix_missing_locations(tree)

if transformer.replacements != 1:
    raise SystemExit(
        f"Expected to replace one call_qwen_batch call inside main; "
        f"replaced {transformer.replacements}"
    )

main_index = next(
    (index for index, node in enumerate(tree.body)
     if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "main"),
    None,
)
if main_index is None:
    raise SystemExit("main() was not found")

tree.body.insert(main_index, helper)
ast.fix_missing_locations(tree)

patched = "#!/usr/bin/env python3\n" + ast.unparse(tree) + "\n"
compile(patched, str(path), "exec")
path.write_text(patched, encoding="utf-8")
print("Experimental patch created successfully.")
PY_PATCH

python3 -m py_compile "$LAB_ROOT/micro/agent.py"
python3 -m compileall -q "$LAB_ROOT/micro/local"

grep -n "def call_qwen_microbatches" "$LAB_ROOT/micro/agent.py"

echo

echo "[3/8] Creating a fresh 19-task shadow benchmark..."

cat > "$LAB_ROOT/shadow/tasks.json" <<'SHADOW_TASKS'
[
  {
    "task_id": "X01",
    "task_type": "factual_knowledge",
    "prompt": "Briefly explain the difference between TCP and UDP. Mention connection setup, reliability, and a typical use case for each."
  },
  {
    "task_id": "X01b",
    "task_type": "factual_knowledge",
    "prompt": "What are the main inputs and outputs of photosynthesis? Answer briefly."
  },
  {
    "task_id": "X01c",
    "task_type": "factual_knowledge",
    "prompt": "Explain the difference between an SSD and an HDD, including how each stores data and one practical advantage of SSDs."
  },
  {
    "task_id": "X02",
    "task_type": "mathematical_reasoning",
    "prompt": "A warehouse starts with 3,200 units. It sells 25% of them, restocks 450 units, and then sells 600 units. How many units remain?"
  },
  {
    "task_id": "X02b",
    "task_type": "mathematical_reasoning",
    "prompt": "A recipe uses 2/3 cup of flour for 8 muffins. How much flour is needed for 20 muffins? If flour costs $3.00 per cup, what is the cost?"
  },
  {
    "task_id": "X03",
    "task_type": "mathematical_reasoning",
    "prompt": "A shop has 500 items. It sells 18% on Monday and 75 more on Tuesday. How many items remain?"
  },
  {
    "task_id": "X04",
    "task_type": "mathematical_reasoning",
    "prompt": "A $1,800 laptop is discounted by 20%, then 12% tax is applied to the discounted price. What is the final price?"
  },
  {
    "task_id": "X05",
    "task_type": "sentiment_classification",
    "prompt": "Classify as Positive, Negative, Neutral, or Mixed and give exactly one sentence of reasoning: 'Delivery was late and the carton was torn, but the product performs excellently and support replaced the missing cable immediately.'"
  },
  {
    "task_id": "X05b",
    "task_type": "sentiment_classification",
    "prompt": "Classify as Positive, Negative, Neutral, or Mixed and give exactly one sentence of reasoning: 'The phone is fast and the camera is sharp, although the battery drains sooner than expected.'"
  },
  {
    "task_id": "X05c",
    "task_type": "sentiment_classification",
    "prompt": "Classify the sentiment as Positive, Negative, Neutral, or Mixed: 'The application loads quickly, but customization options are limited.'"
  },
  {
    "task_id": "X06",
    "task_type": "text_summarization",
    "prompt": "Summarize the following in exactly two sentences: 'Artificial intelligence is helping farmers detect crop disease, forecast yields, and use water more efficiently. These tools can improve productivity and reduce waste. However, small farms may struggle with device costs, unreliable connectivity, limited local-language support, and uncertainty about ownership of agricultural data.'"
  },
  {
    "task_id": "X06b",
    "task_type": "text_summarization",
    "prompt": "Summarize the following in exactly three bullet points, each no longer than 15 words: 'Online education expands access and gives learners more control over scheduling. It can reduce travel and accommodation costs. Challenges include weak engagement, unequal internet access, and limited hands-on practice. Institutions are investing in interactive platforms, mentoring, and hybrid learning spaces.'"
  },
  {
    "task_id": "X07",
    "task_type": "named_entity_recognition",
    "prompt": "Extract and label all named entities as PERSON, ORGANIZATION, LOCATION, or DATE: 'On April 8 2024, Satya Nadella said Microsoft would open a research centre in London with University College London.'"
  },
  {
    "task_id": "X07b",
    "task_type": "named_entity_recognition",
    "prompt": "Extract all named entities and their types from: Aisha Khan joined Anthropic in Singapore last Tuesday."
  },
  {
    "task_id": "X08",
    "task_type": "code_debugging",
    "prompt": "This function should return the sum of a list but is incorrect: def total(nums): return nums[0]. Fix it."
  },
  {
    "task_id": "X09",
    "task_type": "logical_deductive_reasoning",
    "prompt": "Noah, Mira, and Leo each own a different pet: rabbit, fish, or dog. Mira owns the fish. Leo does not own the dog. Who owns the dog?"
  },
  {
    "task_id": "X10",
    "task_type": "code_generation",
    "prompt": "Write a Python function that returns the second-smallest distinct number in a list and handles duplicates correctly."
  },
  {
    "task_id": "X11",
    "task_type": "factual_knowledge",
    "prompt": "What is the capital of Canada, and what river runs through or beside it?"
  },
  {
    "task_id": "X12",
    "task_type": "logical_deductive_reasoning",
    "prompt": "Ira, Dev, and Nia each chose a different snack: fruit, sandwich, or soup. Dev chose soup. Nia did not choose fruit. Who chose fruit?"
  }
]
SHADOW_TASKS

cat > "$LAB_ROOT/shadow/score_shadow.py" <<'PY_SHADOW_SCORE'
#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Callable


def lowered(text: str) -> str:
    return text.lower().replace("organisation", "organization")


def has_all(text: str, terms: tuple[str, ...]) -> bool:
    value = lowered(text)
    return all(term.lower() in value for term in terms)


def has_any(text: str, terms: tuple[str, ...]) -> bool:
    value = lowered(text)
    return any(term.lower() in value for term in terms)


def numeric(text: str, target: float, tolerance: float = 0.02) -> bool:
    values = [
        float(value.replace(",", ""))
        for value in re.findall(r"-?\d[\d,]*(?:\.\d+)?", text)
    ]
    return any(abs(value - target) <= tolerance for value in values)


def sentence_count(text: str) -> int:
    return len(re.findall(r"[^.!?\n]+[.!?](?:\s|$)", text.strip()))


def bullet_lines(text: str) -> list[str]:
    output: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^\s*(?:[-*•]|\d+[.)])\s+(.+)$", line)
        if match:
            output.append(match.group(1).strip())
    return output


def extract_code(answer: str) -> str:
    fenced = re.search(r"```(?:python)?\s*(.*?)```", answer, flags=re.I | re.S)
    if fenced:
        return fenced.group(1).strip()
    index = answer.find("def ")
    return answer[index:].strip() if index >= 0 else answer.strip()


def run_function(answer: str, names: tuple[str, ...], tests: Callable[[Callable], bool]) -> bool:
    code = extract_code(answer)
    namespace: dict[str, object] = {
        "__builtins__": {
            "sum": sum,
            "sorted": sorted,
            "set": set,
            "list": list,
            "len": len,
            "ValueError": ValueError,
            "min": min,
            "max": max,
        }
    }
    try:
        ast.parse(code)
        exec(code, namespace, namespace)
    except Exception:
        return False
    function = next((namespace.get(name) for name in names if callable(namespace.get(name))), None)
    if not callable(function):
        function = next((value for value in namespace.values() if callable(value)), None)
    if not callable(function):
        return False
    try:
        return bool(tests(function))
    except Exception:
        return False


def check(task_id: str, answer: str) -> bool:
    value = lowered(answer)

    if task_id == "X01":
        return (
            has_all(answer, ("tcp", "udp"))
            and has_any(answer, ("connection-oriented", "connection oriented", "handshake"))
            and has_any(answer, ("connectionless", "no connection", "without a connection"))
            and has_any(answer, ("reliable", "reliability", "ordered"))
            and has_any(answer, ("stream", "web", "file", "video", "gaming", "dns", "voice"))
        )
    if task_id == "X01b":
        return has_all(answer, ("carbon dioxide", "water", "oxygen")) and has_any(answer, ("glucose", "sugar"))
    if task_id == "X01c":
        return (
            has_all(answer, ("ssd", "hdd"))
            and has_any(answer, ("flash", "solid-state", "solid state"))
            and has_any(answer, ("magnetic", "spinning", "disk", "platter"))
            and has_any(answer, ("faster", "speed", "durable", "no moving parts"))
        )
    if task_id == "X02":
        return numeric(answer, 2250)
    if task_id == "X02b":
        quantity_ok = numeric(answer, 1.666666, 0.03) or "5/3" in answer or "1 2/3" in answer
        return quantity_ok and numeric(answer, 5.0, 0.02)
    if task_id == "X03":
        return numeric(answer, 335)
    if task_id == "X04":
        return numeric(answer, 1612.8, 0.03)
    if task_id in {"X05", "X05b"}:
        label_ok = re.match(r"^(mixed|positive|neutral)\b", value) is not None
        positive_ok = has_any(answer, ("excellent", "performs", "support", "replaced", "fast", "sharp", "camera"))
        negative_ok = has_any(answer, ("late", "torn", "missing", "battery", "drains", "although", "but"))
        return label_ok and positive_ok and negative_ok and sentence_count(answer) == 1
    if task_id == "X05c":
        return re.match(r"^(mixed|neutral|positive)\b", value) is not None
    if task_id == "X06":
        opportunity = has_any(answer, ("disease", "yield", "water", "productivity", "waste"))
        challenge = has_any(answer, ("cost", "connectivity", "language", "data", "ownership"))
        return sentence_count(answer) == 2 and opportunity and challenge
    if task_id == "X06b":
        bullets = bullet_lines(answer)
        if len(bullets) != 3:
            return False
        if any(len(re.findall(r"\b[\w'-]+\b", bullet)) > 15 for bullet in bullets):
            return False
        joined = " ".join(bullets)
        return (
            has_any(joined, ("access", "schedule", "cost", "travel"))
            and has_any(joined, ("engagement", "internet", "practice"))
            and has_any(joined, ("platform", "mentoring", "hybrid"))
        )
    if task_id == "X07":
        pairs = (
            ("satya nadella", "person"),
            ("microsoft", "organization"),
            ("london", "location"),
            ("university college london", "organization"),
            ("april 8 2024", "date"),
        )
        entities_ok = all(entity in value and label in value[value.find(entity):value.find(entity) + 140] for entity, label in pairs[:-1])
        date_ok = re.search(r"april\s+8[,]?\s+2024", value) is not None and "date" in value
        return entities_ok and date_ok
    if task_id == "X07b":
        return has_all(answer, ("Aisha Khan", "PERSON", "Anthropic", "ORGANIZATION", "Singapore", "LOCATION", "last Tuesday", "DATE"))
    if task_id == "X08":
        return run_function(answer, ("total", "sum_list", "list_sum"), lambda fn: fn([1, 2, 3, 4]) == 10 and fn([-2, 5]) == 3 and fn([]) == 0)
    if task_id == "X09":
        return "noah" in value and "dog" in value
    if task_id == "X10":
        def tests(fn: Callable) -> bool:
            return fn([4, 1, 1, 3, 2]) == 2 and fn([9, 9, 5, 7, 5]) == 7
        return run_function(answer, ("second_smallest", "find_second_smallest", "second_smallest_number"), tests)
    if task_id == "X11":
        return "ottawa" in value and "ottawa river" in value
    if task_id == "X12":
        return "ira" in value and "fruit" in value
    return False


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: score_shadow.py TASKS RESULTS RUNTIME_SECONDS", file=sys.stderr)
        return 2

    tasks_path, results_path, runtime_path = map(Path, sys.argv[1:])
    tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
    results = json.loads(results_path.read_text(encoding="utf-8"))
    runtime = float(runtime_path.read_text(encoding="utf-8").strip())

    if isinstance(results, dict) and isinstance(results.get("results"), list):
        results = results["results"]

    result_map = {
        str(item.get("task_id", item.get("id", ""))): str(item.get("answer", ""))
        for item in results
        if isinstance(item, dict)
    }

    passed: list[str] = []
    wrong: list[str] = []
    missing: list[str] = []

    for task in tasks:
        task_id = str(task["task_id"])
        answer = result_map.get(task_id, "").strip()
        if not answer:
            missing.append(task_id)
        elif check(task_id, answer):
            passed.append(task_id)
        else:
            wrong.append(task_id)

    accuracy = 100.0 * len(passed) / len(tasks)
    print(
        f"SHADOW passed={len(passed)}/{len(tasks)} accuracy={accuracy:.1f}% "
        f"wrong={wrong} missing={missing} runtime={runtime:.2f}s"
    )
    for task_id in wrong:
        preview = result_map.get(task_id, "").replace("\n", " ")[:500]
        print(f"WRONG {task_id}: {preview}")

    report = {
        "passed": len(passed),
        "total": len(tasks),
        "accuracy": accuracy,
        "wrong": wrong,
        "missing": missing,
        "runtime_seconds": runtime,
    }
    (results_path.parent / "benchmark-report.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    return 0 if not wrong and not missing and runtime <= 420 else 1


if __name__ == "__main__":
    raise SystemExit(main())
PY_SHADOW_SCORE

chmod +x "$LAB_ROOT/shadow/score_shadow.py"
python3 -m py_compile "$LAB_ROOT/shadow/score_shadow.py"

run_case() {
  local label="$1"
  local code_dir="$2"
  local tasks_file="$3"
  local scorer="$4"
  local qwen_enabled="$5"

  local case_dir="$LAB_ROOT/runs/$label"
  local input_dir="$case_dir/input"
  local output_dir="$case_dir/output"
  local logs_file="$case_dir/container.log"
  local runtime_file="$case_dir/runtime.txt"

  mkdir -p "$input_dir" "$output_dir"
  cp "$tasks_file" "$input_dir/tasks.json"
  rm -f "$output_dir/results.json" "$output_dir/benchmark-report.json"

  echo
  echo "------------------------------------------------------------"
  echo "Running case: $label"
  echo "Qwen enabled: $qwen_enabled"
  echo "Tasks: $tasks_file"
  echo "------------------------------------------------------------"

  local start_ns end_ns runtime status
  start_ns="$(date +%s%N)"

  set +e
  timeout "$((TOTAL_BUDGET + 45))" docker run --rm \
    --network none \
    --cpus 2 \
    --memory 4g \
    --pids-limit 512 \
    -v "$input_dir:/input:ro" \
    -v "$output_dir:/output" \
    -v "$code_dir/agent.py:/app/agent.py:ro" \
    -v "$code_dir/local:/app/local:ro" \
    -e INPUT_PATH=/input/tasks.json \
    -e OUTPUT_PATH=/output/results.json \
    -e ROUTEIQ_LOCAL_ONLY=1 \
    -e ROUTEIQ_TOTAL_BUDGET_SECONDS="$TOTAL_BUDGET" \
    -e QWEN_ENABLED="$qwen_enabled" \
    -e QWEN_PROPOSAL_MODE=nonthinking \
    -e QWEN_PROPOSAL_MAX_TOKENS=1050 \
    -e QWEN_PROPOSAL_TIMEOUT_SECONDS=180 \
    -e QWEN_AUDIT_ENABLED=0 \
    -e QWEN_REASONING_BUDGET=0 \
    -e QWEN_CHAT_TEMP=0.05 \
    -e QWEN_CHAT_TOP_K=10 \
    -e QWEN_CHAT_TOP_P=0.80 \
    -e QWEN_MICROBATCH_MIN_REMAINING=65 \
    -e FIREWORKS_API_KEY= \
    -e FIREWORKS_BASE_URL= \
    "$BASE_IMAGE" \
    > >(tee "$logs_file") 2>&1
  status=$?
  set -e

  end_ns="$(date +%s%N)"
  runtime="$(python3 - "$start_ns" "$end_ns" <<'PY_RUNTIME'
import sys
start = int(sys.argv[1])
end = int(sys.argv[2])
print(f"{(end-start)/1_000_000_000:.6f}")
PY_RUNTIME
)"
  printf '%s\n' "$runtime" > "$runtime_file"

  echo "Container exit status: $status"
  echo "Runtime seconds: $runtime"

  if [[ ! -f "$output_dir/results.json" ]]; then
    echo '{"passed":0,"total":19,"wrong":[],"missing":["NO_RESULTS"],"runtime_seconds":0}' \
      > "$output_dir/benchmark-report.json"
    echo "No results.json was produced."
    return 0
  fi

  echo "Results coverage:"
  python3 - "$input_dir/tasks.json" "$output_dir/results.json" <<'PY_COVERAGE'
import json
import sys
from pathlib import Path

tasks = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
results = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
if isinstance(tasks, dict):
    tasks = tasks.get("tasks", [])
if isinstance(results, dict):
    results = results.get("results", [])
expected = [str(item.get("task_id", item.get("id", ""))) for item in tasks]
answers = {
    str(item.get("task_id", item.get("id", ""))): str(item.get("answer", "")).strip()
    for item in results if isinstance(item, dict)
}
completed = [task_id for task_id in expected if answers.get(task_id)]
missing = [task_id for task_id in expected if not answers.get(task_id)]
print(f"completed={len(completed)}/{len(expected)} missing={missing}")
PY_COVERAGE

  echo "Scoring:"
  set +e
  python3 "$scorer" "$input_dir/tasks.json" "$output_dir/results.json" "$runtime_file"
  local score_status=$?
  set -e
  echo "Scorer exit status: $score_status"
}

echo

echo "[4/8] Measuring deterministic-only coverage..."
run_case \
  "canonical-deterministic" \
  "$LAB_ROOT/micro" \
  "$LAB_ROOT/canonical-tasks.json" \
  "$LAB_ROOT/canonical-scorer.py" \
  "0"

run_case \
  "shadow-deterministic" \
  "$LAB_ROOT/micro" \
  "$LAB_ROOT/shadow/tasks.json" \
  "$LAB_ROOT/shadow/score_shadow.py" \
  "0"

echo

echo "[5/8] Testing experimental zero-token microbatch flow..."
run_case \
  "canonical-microbatch" \
  "$LAB_ROOT/micro" \
  "$LAB_ROOT/canonical-tasks.json" \
  "$LAB_ROOT/canonical-scorer.py" \
  "1"

run_case \
  "shadow-microbatch" \
  "$LAB_ROOT/micro" \
  "$LAB_ROOT/shadow/tasks.json" \
  "$LAB_ROOT/shadow/score_shadow.py" \
  "1"

if [[ "$RUN_ORIGINAL" == "1" ]]; then
  echo
  echo "[6/8] Comparing the untouched original Qwen flow on the shadow set..."
  run_case \
    "shadow-original" \
    "$LAB_ROOT/original" \
    "$LAB_ROOT/shadow/tasks.json" \
    "$LAB_ROOT/shadow/score_shadow.py" \
    "1"
else
  echo
  echo "[6/8] Original-flow comparison skipped (RUN_ORIGINAL=0)."
fi

echo

echo "[7/8] Producing consolidated decision report..."

python3 - "$LAB_ROOT" "$RUN_ORIGINAL" <<'PY_SUMMARY'
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
run_original = sys.argv[2] == "1"

labels = [
    "canonical-deterministic",
    "shadow-deterministic",
    "canonical-microbatch",
    "shadow-microbatch",
]
if run_original:
    labels.append("shadow-original")

reports: dict[str, dict] = {}
for label in labels:
    path = root / "runs" / label / "output" / "benchmark-report.json"
    if path.is_file():
        try:
            reports[label] = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            reports[label] = {"passed": 0, "total": 19, "missing": ["INVALID_REPORT"]}
    else:
        reports[label] = {"passed": 0, "total": 19, "missing": ["NO_REPORT"]}

print("\n================ CONSOLIDATED RESULTS ================")
for label in labels:
    report = reports[label]
    passed = int(report.get("passed", 0))
    total = int(report.get("total", 19) or 19)
    accuracy = 100.0 * passed / total
    runtime = float(report.get("runtime_seconds", 0.0) or 0.0)
    wrong = report.get("wrong", [])
    missing = report.get("missing", [])
    print(
        f"{label:28s} {passed:2d}/{total:<2d} "
        f"({accuracy:5.1f}%) runtime={runtime:7.2f}s "
        f"wrong={wrong} missing={missing}"
    )

canonical = reports["canonical-microbatch"]
shadow = reports["shadow-microbatch"]
cp = int(canonical.get("passed", 0))
ct = int(canonical.get("total", 19) or 19)
sp = int(shadow.get("passed", 0))
st = int(shadow.get("total", 19) or 19)
cr = float(canonical.get("runtime_seconds", 9999) or 9999)
sr = float(shadow.get("runtime_seconds", 9999) or 9999)
cm = canonical.get("missing", [])
sm = shadow.get("missing", [])

if cp == ct and sp == st and cr <= 420 and sr <= 420 and not cm and not sm:
    verdict = "STRONG LOCAL RESULT"
    next_step = (
        "The experimental flow passed both 19-task suites at zero external tokens. "
        "It is worth packaging as a separate immutable candidate, but official hidden "
        "accuracy is still not guaranteed."
    )
elif cp >= 18 and sp >= 17 and cr <= 540 and sr <= 540 and not cm and not sm:
    verdict = "PROMISING, NOT YET 100%"
    next_step = (
        "The architecture generalises better, but inspect the listed wrong tasks before "
        "building or submitting. Patch only those categories and rerun this lab."
    )
elif cp >= 18 and sp < 17:
    verdict = "OVERFITTING DETECTED"
    next_step = (
        "The repository benchmark is misleading. Do not submit this zero-token build. "
        "Use the wrong shadow-task categories to improve deterministic rules or retain a "
        "small Fireworks fallback."
    )
else:
    verdict = "DO NOT PACKAGE OR SUBMIT"
    next_step = (
        "The current local flow is not reliable enough. Preserve the safe hybrid image "
        "and use these logs to repair correctness before another candidate build."
    )

print("\nVERDICT:", verdict)
print("NEXT STEP:", next_step)
print("======================================================")

summary = {
    "reports": reports,
    "verdict": verdict,
    "next_step": next_step,
}
(root / "consolidated-report.json").write_text(
    json.dumps(summary, indent=2),
    encoding="utf-8",
)
PY_SUMMARY

echo

echo "[8/8] Finished."
echo "Full text report:       $REPORT_FILE"
echo "Machine-readable report: $LAB_ROOT/consolidated-report.json"
echo "Per-run outputs/logs:    $LAB_ROOT/runs/"
echo
echo "IMPORTANT: This lab did not commit, push, build a new registry image,"
echo "or touch the active ACT II submission."
echo "Completed: $(date)"
