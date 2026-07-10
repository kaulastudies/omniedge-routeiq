#!/usr/bin/env python3

import ast
import json
import math
import operator
import re
import subprocess
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


INPUT_PATH = Path(os.getenv("INPUT_PATH", "/input/tasks.json"))
OUTPUT_PATH = Path(os.getenv("OUTPUT_PATH", "/output/results.json"))


def log(message):
    print(message, file=sys.stderr, flush=True)


def load_tasks():
    with INPUT_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if isinstance(data, list):
        tasks = data
    elif isinstance(data, dict) and isinstance(data.get("tasks"), list):
        tasks = data["tasks"]
    else:
        raise ValueError(
            "tasks.json must be a list or an object containing a tasks list"
        )

    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise ValueError(f"Task {index} is not an object")

        if "task_id" not in task:
            if "id" in task:
                task["task_id"] = task["id"]
            else:
                raise ValueError(f"Task {index} has no task_id")

    return tasks


def parse_allowed_models():
    raw = os.getenv("ALLOWED_MODELS", "").strip()

    if not raw:
        raise ValueError("ALLOWED_MODELS is missing")

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            models = [str(model).strip() for model in parsed]
            return [model for model in models if model]
    except json.JSONDecodeError:
        pass

    raw = raw.replace(";", ",").replace("\n", ",")

    if "," in raw:
        models = raw.split(",")
    else:
        models = raw.split()

    return [model.strip() for model in models if model.strip()]


def choose_model(models):
    if not models:
        raise ValueError("ALLOWED_MODELS contains no usable models")

    # MiniMax is currently our verified evaluator-safe primary model.
    for keyword in ("minimax", "gemma", "kimi"):
        for model in models:
            if keyword in model.lower():
                return model

    return models[0]


def completion_url():
    base_url = os.getenv("FIREWORKS_BASE_URL", "").strip().rstrip("/")

    if not base_url:
        raise ValueError("FIREWORKS_BASE_URL is missing")

    if base_url.endswith("/chat/completions"):
        return base_url

    return f"{base_url}/chat/completions"


def task_text(task):
    for field in (
        "prompt",
        "question",
        "instruction",
        "input",
        "query",
        "text",
        "content",
    ):
        value = task.get(field)

        if value not in (None, ""):
            if isinstance(value, (dict, list)):
                return json.dumps(value, ensure_ascii=False)

            return str(value)

    safe_task = {
        key: value
        for key, value in task.items()
        if key not in ("task_id", "id")
    }

    return json.dumps(safe_task, ensure_ascii=False)



LOCAL_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

LOCAL_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def evaluate_local_number(node):
    if isinstance(node, ast.Expression):
        return evaluate_local_number(node.body)

    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
    ):
        return node.value

    if isinstance(node, ast.UnaryOp):
        operation = LOCAL_UNARY_OPERATORS.get(type(node.op))

        if operation is None:
            raise ValueError("Unsupported unary operator")

        return operation(evaluate_local_number(node.operand))

    if isinstance(node, ast.BinOp):
        operation = LOCAL_BINARY_OPERATORS.get(type(node.op))

        if operation is None:
            raise ValueError("Unsupported binary operator")

        left = evaluate_local_number(node.left)
        right = evaluate_local_number(node.right)

        if isinstance(node.op, ast.Pow) and abs(right) > 10:
            raise ValueError("Exponent is outside the safe range")

        value = operation(left, right)

        if not math.isfinite(float(value)):
            raise ValueError("Result is not finite")

        if abs(float(value)) > 1_000_000_000_000_000:
            raise ValueError("Result is outside the safe range")

        return value

    raise ValueError("Unsupported arithmetic expression")


def format_local_number(value):
    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    if isinstance(value, int):
        return str(value)

    return (
        f"{float(value):.10f}"
        .rstrip("0")
        .rstrip(".")
    )


def local_math_answer(task):
    prompt = task_text(task)
    lowered = (
        prompt.lower()
        .replace(",", "")
        .replace("×", "*")
        .replace("÷", "/")
    )

    markers = (
        "calculate",
        "compute",
        "evaluate",
        "what is",
        "multiplied by",
        "divided by",
        " plus ",
        " minus ",
        " times ",
    )

    if not any(marker in lowered for marker in markers):
        return None

    match = re.search(
        r"(?:calculate|compute|evaluate|what\s+is)\s+(.+)",
        lowered,
    )

    candidate = match.group(1) if match else lowered

    candidate = re.split(
        r"(?:\breturn\b|\bgive\b|\banswer\b|[?.])",
        candidate,
        maxsplit=1,
    )[0]

    replacements = (
        ("to the power of", "**"),
        ("raised to the power of", "**"),
        ("multiplied by", "*"),
        ("divided by", "/"),
        ("times", "*"),
        ("plus", "+"),
        ("minus", "-"),
        ("^", "**"),
    )

    for source, replacement in replacements:
        candidate = candidate.replace(source, replacement)

    candidate = candidate.strip()

    if not candidate or len(candidate) > 120:
        return None

    if not re.fullmatch(
        r"[\d\s+\-*/%.()]+",
        candidate,
    ):
        return None

    try:
        tree = ast.parse(candidate, mode="eval")
        value = evaluate_local_number(tree)
        return format_local_number(value)
    except Exception:
        return None


def local_sentiment_answer(task):
    prompt = task_text(task)
    lowered = prompt.lower()

    if "sentiment" not in lowered:
        return None

    body = prompt.split(":", 1)[-1].lower()
    body = re.split(
        r"\breturn\s+only\b",
        body,
        maxsplit=1,
    )[0]

    positive_weights = {
        "love": 2,
        "loved": 2,
        "excellent": 2,
        "amazing": 2,
        "fantastic": 2,
        "wonderful": 2,
        "great": 1,
        "happy": 1,
        "satisfied": 1,
        "enjoyed": 1,
        "good": 1,
    }

    negative_weights = {
        "hate": 2,
        "hated": 2,
        "awful": 2,
        "terrible": 2,
        "horrible": 2,
        "worst": 2,
        "bad": 1,
        "angry": 1,
        "disappointed": 1,
        "poor": 1,
        "broken": 1,
    }

    words = re.findall(r"[a-z']+", body)

    positive_score = sum(
        positive_weights.get(word, 0)
        for word in words
    )

    negative_score = sum(
        negative_weights.get(word, 0)
        for word in words
    )

    if re.search(
        r"\bnot\s+(?:good|great|happy|satisfied)\b",
        body,
    ):
        negative_score += 2
        positive_score = max(0, positive_score - 1)

    if positive_score >= 2 and negative_score == 0:
        return "positive"

    if negative_score >= 2 and positive_score == 0:
        return "negative"

    return None


def local_logic_answer(task):
    prompt = " ".join(
        task_text(task).lower().split()
    )

    if "can we conclude" not in prompt:
        return None

    patterns = (
        (
            re.compile(
                r"all ([a-z]+) are ([a-z]+).*?"
                r"all \2 are ([a-z]+).*?"
                r"conclude(?: that)? all \1 are \3"
            ),
            "Yes",
        ),
        (
            re.compile(
                r"all ([a-z]+) are ([a-z]+).*?"
                r"no \2 are ([a-z]+).*?"
                r"conclude(?: that)? no \1 are \3"
            ),
            "Yes",
        ),
        (
            re.compile(
                r"some ([a-z]+) are ([a-z]+).*?"
                r"all \2 are ([a-z]+).*?"
                r"conclude(?: that)? some \1 are \3"
            ),
            "Yes",
        ),
        (
            re.compile(
                r"all ([a-z]+) are ([a-z]+).*?"
                r"some \2 are ([a-z]+).*?"
                r"conclude(?: that)? some \1 are \3"
            ),
            "No",
        ),
    )

    for pattern, answer in patterns:
        if pattern.search(prompt):
            return answer

    return None


def try_local_answer(task):
    handlers = (
        local_math_answer,
        local_sentiment_answer,
        local_logic_answer,
    )

    for handler in handlers:
        answer = handler(task)

        if answer is not None:
            return answer

    return None



LLAMA_ANSI_PATTERN = re.compile(
    r"\x1b\[[0-9;?]*[A-Za-z]"
)


def local_task_category(task):
    raw = str(
        task.get("task_type")
        or task.get("category")
        or task.get("type")
        or ""
    ).strip().lower()

    normalized = (
        raw.replace("-", "_")
        .replace(" ", "_")
        .replace("/", "_")
    )

    aliases = (
        (
            "code_debugging",
            (
                "code_debug",
                "debugging",
                "bug_fix",
                "fix_code",
            ),
        ),
        (
            "code_generation",
            (
                "code_generation",
                "generate_code",
                "programming",
            ),
        ),
        ("sentiment", ("sentiment",)),
        ("summarization", ("summar",)),
        (
            "ner",
            (
                "named_entity",
                "entity_extraction",
                "ner",
            ),
        ),
        (
            "math",
            (
                "math",
                "arithmetic",
                "calculation",
            ),
        ),
        (
            "logic",
            (
                "logic",
                "deductive",
                "deduction",
            ),
        ),
        (
            "factual",
            (
                "factual",
                "knowledge",
                "question_answering",
            ),
        ),
    )

    for category, category_aliases in aliases:
        if any(
            alias in normalized
            for alias in category_aliases
        ):
            return category

    prompt = task_text(task).lower()

    if any(
        phrase in prompt
        for phrase in (
            "debug this",
            "fix this code",
            "fix the code",
            "find the bug",
            "correct the code",
        )
    ):
        return "code_debugging"

    if any(
        phrase in prompt
        for phrase in (
            "write a function",
            "write a program",
            "generate code",
            "implement a function",
            "create a function",
        )
    ):
        return "code_generation"

    if "sentiment" in prompt:
        return "sentiment"

    if "summarize" in prompt or "summary" in prompt:
        return "summarization"

    if any(
        phrase in prompt
        for phrase in (
            "named entities",
            "extract entities",
            "extract the person",
            "extract the organization",
            "ner",
        )
    ):
        return "ner"

    if any(
        phrase in prompt
        for phrase in (
            "calculate",
            "compute",
            "multiply",
            "divided by",
            "solve the equation",
        )
    ):
        return "math"

    if any(
        phrase in prompt
        for phrase in (
            "deduce",
            "logically",
            "syllogism",
            "can we conclude",
            "which conclusion",
        )
    ):
        return "logic"

    return "factual"


def local_gemma_budget(category):
    budgets = {
        "factual": 64,
        "sentiment": 24,
        "summarization": 160,
        "ner": 128,
        "code_generation": 256,
    }

    return budgets.get(category, 96)


def local_gemma_instruction(category):
    instructions = {
        "factual": (
            "Answer accurately and directly. "
            "Return only the requested answer."
        ),
        "sentiment": (
            "Return only one label: "
            "positive, negative, or neutral."
        ),
        "summarization": (
            "Write a faithful concise summary and obey "
            "the requested length and format."
        ),
        "ner": (
            "Extract every requested named entity. "
            "Do not omit organizations or people."
        ),
        "code_generation": (
            "Generate correct executable code matching every "
            "constraint. Return only the code."
        ),
    }

    return instructions.get(
        category,
        "Return only the requested answer.",
    )


def extract_local_gemma_answer(output):
    cleaned = LLAMA_ANSI_PATTERN.sub("", output)
    lines = cleaned.splitlines()

    start = None

    for index, line in enumerate(lines):
        if line.startswith("> "):
            start = index + 1

    if start is None:
        return ""

    answer_lines = []

    for line in lines[start:]:
        stripped = line.strip()

        if stripped.startswith("[ Prompt:"):
            break

        if stripped == "Exiting...":
            break

        answer_lines.append(line)

    return "\n".join(answer_lines).strip()


def strip_code_fence(answer):
    value = answer.strip()

    if not value.startswith("```"):
        return value

    lines = value.splitlines()

    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]

    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    return "\n".join(lines).strip()


def normalize_local_gemma_answer(category, answer):
    value = answer.strip()

    if category == "sentiment":
        match = re.search(
            r"\b(positive|negative|neutral)\b",
            value,
            flags=re.IGNORECASE,
        )

        return match.group(1).lower() if match else ""

    if category == "code_generation":
        return strip_code_fence(value)

    if category == "ner":
        value = value.replace("**", "")
        value = re.sub(
            r"(?m)^\s*[-*]\s*",
            "",
            value,
        )

    return value.strip()


def validate_local_gemma_answer(
    task,
    category,
    answer,
):
    if not answer:
        return False

    lowered = answer.lower()

    if any(
        phrase in lowered
        for phrase in (
            "i don't know",
            "i do not know",
            "cannot answer",
            "unable to answer",
        )
    ):
        return False

    if category == "sentiment":
        return answer in (
            "positive",
            "negative",
            "neutral",
        )

    if category == "factual":
        return len(answer) <= 300

    if category == "summarization":
        return 5 <= len(answer) <= 1500

    if category == "ner":
        return len(answer) <= 1000

    if category == "code_generation":
        prompt = task_text(task).lower()

        if "python" in prompt:
            try:
                compile(
                    answer,
                    "<local-gemma>",
                    "exec",
                )
            except SyntaxError:
                return False

        return any(
            token in answer
            for token in (
                "def ",
                "class ",
                "function ",
                "const ",
                "let ",
                "public ",
            )
        )

    return False


def try_local_gemma(task):
    category = local_task_category(task)

    allowed_categories = {
        "sentiment",
        "summarization",
        "ner",
        "code_generation",
    }

    if category not in allowed_categories:
        return None

    model = os.getenv(
        "ROUTEIQ_LOCAL_GEMMA_MODEL",
        "/models/gemma-3-1b-it-Q4_K_M.gguf",
    ).strip()

    if not model or not Path(model).is_file():
        log(
            f"Local Gemma unavailable for "
            f"task {task['task_id']}"
        )
        return None

    original_prompt = task_text(task)
    flattened_prompt = original_prompt.replace(
        "\n",
        "\\n",
    )

    prompt = (
        f"{local_gemma_instruction(category)} "
        f"Task: {flattened_prompt}"
    )

    command = [
        "/usr/local/bin/llama-cli",
        "-m",
        model,
        "-p",
        prompt,
        "-n",
        str(local_gemma_budget(category)),
        "-t",
        os.getenv(
            "ROUTEIQ_LOCAL_GEMMA_THREADS",
            "2",
        ),
        "-c",
        os.getenv(
            "ROUTEIQ_LOCAL_GEMMA_CONTEXT",
            "1024",
        ),
        "--temp",
        "0",
        "--single-turn",
        "--no-display-prompt",
    ]

    started = time.monotonic()

    try:
        process = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
    except Exception as error:
        log(
            f"Local Gemma failed for "
            f"task {task['task_id']}: {error}"
        )
        return None

    elapsed = time.monotonic() - started
    combined = process.stdout + "\n" + process.stderr

    answer = extract_local_gemma_answer(
        combined
    )

    answer = normalize_local_gemma_answer(
        category,
        answer,
    )

    if process.returncode != 0:
        log(
            f"Local Gemma exited with "
            f"{process.returncode} for "
            f"task {task['task_id']}"
        )
        return None

    if not validate_local_gemma_answer(
        task,
        category,
        answer,
    ):
        log(
            f"Local Gemma validation rejected "
            f"task {task['task_id']}"
        )
        return None

    log(
        f"Task {task['task_id']} solved by "
        f"local Gemma category={category} "
        f"in {elapsed:.2f}s"
    )

    return answer


def fireworks_token_budget(task):
    category = local_task_category(task)

    budgets = {
        "factual": 64,
        "code_debugging": 256,
        "sentiment": 32,
        "math": 128,
        "logic": 128,
        "ner": 128,
        "summarization": 192,
        "code_generation": 256,
    }

    return budgets.get(category, 128)


def model_id_candidates(model, url):
    """
    Use the evaluator-provided model ID exactly as supplied.

    The public Fireworks endpoint requires canonical IDs, so canonical
    fallback is attempted only during direct api.fireworks.ai testing.
    """
    value = str(model).strip()

    if not value:
        raise ValueError("Selected model is empty")

    candidates = [value]

    if (
        "api.fireworks.ai" in url.lower()
        and not value.startswith("accounts/")
        and "/" not in value
    ):
        candidates.append(f"accounts/fireworks/models/{value}")

    return candidates


def request_fireworks(task, request_model, api_key, url):
    category = str(
        task.get("task_type")
        or task.get("category")
        or task.get("type")
        or "general"
    )

    payload = {
        "model": request_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Complete the task accurately and concisely. "
                    "Follow every requested format or length constraint. "
                    "Return only the requested answer. "
                    f"Task category: {category}."
                ),
            },
            {
                "role": "user",
                "content": task_text(task),
            },
        ],
        "temperature": 0,
        "max_tokens": fireworks_token_budget(task),
        "stream": False,
    }

    last_error = None

    for attempt in range(2):
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                body = json.loads(response.read().decode("utf-8"))

            choices = body.get("choices", [])

            if not choices:
                raise RuntimeError("Response contains no choices")

            message = choices[0].get("message", {})
            content = message.get("content")

            if not isinstance(content, str) or not content.strip():
                raise RuntimeError("Response contains no answer text")

            usage = body.get("usage") or {}

            prompt_tokens = usage.get(
                "prompt_tokens",
                0,
            )

            completion_tokens = usage.get(
                "completion_tokens",
                0,
            )

            total_tokens = usage.get(
                "total_tokens",
                0,
            )

            log(
                f"Fireworks usage task={task['task_id']} "
                f"prompt={prompt_tokens} "
                f"completion={completion_tokens} "
                f"total={total_tokens}"
            )

            return content.strip()

        except urllib.error.HTTPError as error:
            details = error.read().decode(
                "utf-8",
                errors="replace",
            )

            last_error = RuntimeError(
                f"Fireworks HTTP {error.code}: {details[:500]}"
            )

            if error.code not in (429, 500, 502, 503, 504):
                break

        except Exception as error:
            last_error = error

        if attempt == 0:
            time.sleep(2)

    raise last_error or RuntimeError("Fireworks request failed")


def call_fireworks(task, model, api_key, url):
    last_error = None

    for request_model in model_id_candidates(model, url):
        try:
            log(f"Trying Fireworks model ID: {request_model}")
            return request_fireworks(
                task,
                request_model,
                api_key,
                url,
            )
        except Exception as error:
            last_error = error
            log(
                f"Model ID {request_model} failed: "
                f"{type(error).__name__}: {error}"
            )

    raise last_error or RuntimeError("All model-ID forms failed")


def ordered_models(models):
    ordered = []

    for keyword in ("minimax", "gemma", "kimi"):
        for model in models:
            if keyword in model.lower() and model not in ordered:
                ordered.append(model)

    for model in models:
        if model not in ordered:
            ordered.append(model)

    return ordered


def call_fireworks_with_fallback(
    task,
    models,
    api_key,
    url,
):
    last_error = None

    for model in ordered_models(models):
        try:
            log(f"Attempting allowed model: {model}")
            return call_fireworks(
                task,
                model,
                api_key,
                url,
            )
        except Exception as error:
            last_error = error
            log(
                f"Allowed model {model} failed: "
                f"{type(error).__name__}: {error}"
            )

    raise last_error or RuntimeError(
        "All allowed Fireworks models failed"
    )



def write_results(results):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = OUTPUT_PATH.with_suffix(".tmp")

    with temporary_path.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, ensure_ascii=False, indent=2)

    temporary_path.replace(OUTPUT_PATH)


def main():
    try:
        tasks = load_tasks()
    except Exception as error:
        log(f"Input error: {error}")
        write_results([])
        return 1

    if os.getenv("ROUTEIQ_MOCK", "0") == "1":
        results = [
            {
                "task_id": task["task_id"],
                "answer": f"mock-answer-for-{task['task_id']}",
            }
            for task in tasks
        ]

        write_results(results)
        log(f"Wrote {len(results)} mock results")
        return 0

    api_key = os.getenv("FIREWORKS_API_KEY", "").strip()

    if not api_key:
        log("FIREWORKS_API_KEY is missing")
        write_results(
            [
                {"task_id": task["task_id"], "answer": ""}
                for task in tasks
            ]
        )
        return 1

    try:
        models = parse_allowed_models()
        model = choose_model(models)
        url = completion_url()
    except Exception as error:
        log(f"Configuration error: {error}")
        write_results(
            [
                {"task_id": task["task_id"], "answer": ""}
                for task in tasks
            ]
        )
        return 1

    log(f"Selected allowed model: {model}")

    results = []
    local_count = 0

    for task in tasks:
        try:
            answer = try_local_answer(task)

            if answer is not None:
                local_count += 1
                log(
                    f"Task {task['task_id']} solved by "
                    f"deterministic local handler"
                )
            else:
                answer = try_local_gemma(task)

                if answer is not None:
                    local_count += 1
                else:
                    answer = call_fireworks_with_fallback(
                        task,
                        models,
                        api_key,
                        url,
                    )
        except Exception as error:
            log(f"Task {task['task_id']} failed: {error}")
            answer = ""

        results.append(
            {
                "task_id": task["task_id"],
                "answer": answer,
            }
        )

        write_results(results)

    log(
        f"Wrote {len(results)} results "
        f"({local_count} local, "
        f"{len(results) - local_count} Fireworks)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
