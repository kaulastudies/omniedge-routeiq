#!/usr/bin/env python3

import json
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


def task_category(task):
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

    metadata_aliases = (
        ("code_debugging", ("code_debug", "debugging", "bug_fix", "fix_code")),
        ("code_generation", ("code_generation", "generate_code", "programming")),
        ("sentiment", ("sentiment",)),
        ("summarization", ("summar",)),
        ("ner", ("named_entity", "entity_extraction", "ner")),
        ("math", ("math", "arithmetic", "calculation")),
        ("logic", ("logic", "deductive", "deduction")),
        ("factual", ("factual", "knowledge", "question_answering")),
    )

    for category, aliases in metadata_aliases:
        if any(alias in normalized for alias in aliases):
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

    if any(
        phrase in prompt
        for phrase in (
            "sentiment",
            "positive, negative",
            "positive or negative",
        )
    ):
        return "sentiment"

    if "summarize" in prompt or "summary" in prompt:
        return "summarization"

    if any(
        phrase in prompt
        for phrase in (
            "named entities",
            "extract entities",
            "person and organization",
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
            "arithmetic",
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


def token_budget(task):
    category = task_category(task)

    budgets = {
        "sentiment": 48,
        "ner": 160,
        "factual": 160,
        "math": 256,
        "logic": 256,
        "summarization": 320,
        "code_debugging": 512,
        "code_generation": 640,
    }

    return budgets.get(category, 256)


def system_prompt(task):
    category = task_category(task)

    prompts = {
        "factual": (
            "Answer accurately and directly. "
            "Return only the requested answer."
        ),
        "math": (
            "Solve carefully and verify the arithmetic. "
            "Return only the final requested answer."
        ),
        "sentiment": (
            "Classify the sentiment accurately. "
            "Return only the requested label."
        ),
        "summarization": (
            "Summarize faithfully and obey all requested "
            "length and formatting constraints."
        ),
        "ner": (
            "Extract only the requested named entities. "
            "Preserve spelling and follow the requested format."
        ),
        "code_debugging": (
            "Correct the bug accurately. Return only the "
            "requested corrected code or final answer."
        ),
        "logic": (
            "Evaluate the logic carefully. Return only the "
            "final conclusion or requested option."
        ),
        "code_generation": (
            "Generate correct executable code matching every "
            "constraint. Return only code unless asked otherwise."
        ),
    }

    return prompts.get(
        category,
        "Complete the task accurately and return only the requested result.",
    )


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


def request_fireworks(
    task,
    request_model,
    api_key,
    url,
):
    payload = {
        "model": request_model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt(task),
            },
            {
                "role": "user",
                "content": task_text(task),
            },
        ],
        "temperature": 0,
        "max_tokens": token_budget(task),
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
            with urllib.request.urlopen(
                request,
                timeout=90,
            ) as response:
                body = json.loads(
                    response.read().decode("utf-8")
                )

            choices = body.get("choices", [])

            if not choices:
                raise RuntimeError(
                    "Response contains no choices"
                )

            message = choices[0].get("message", {})
            content = message.get("content")

            if not isinstance(content, str):
                raise RuntimeError(
                    "Response contains no answer text"
                )

            answer = content.strip()

            if not answer:
                raise RuntimeError(
                    "Response answer is empty"
                )

            return answer

        except urllib.error.HTTPError as error:
            details = error.read().decode(
                "utf-8",
                errors="replace",
            )

            last_error = RuntimeError(
                f"Fireworks HTTP {error.code}: "
                f"{details[:500]}"
            )

            if error.code not in (
                429,
                500,
                502,
                503,
                504,
            ):
                break

        except Exception as error:
            last_error = error

        if attempt == 0:
            time.sleep(2)

    raise last_error or RuntimeError(
        "Fireworks request failed"
    )


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


def ordered_models(models, task):
    category = task_category(task)

    if category in (
        "code_debugging",
        "code_generation",
    ):
        preferences = (
            "kimi-k2p7-code",
            "kimi",
            "minimax-m3",
            "minimax",
            "gemma-4-31b-it",
            "gemma",
        )

    elif category in ("math", "logic"):
        preferences = (
            "minimax-m3",
            "minimax",
            "gemma-4-31b-it",
            "gemma-4-31b-it-nvfp4",
            "gemma",
            "kimi",
        )

    else:
        preferences = (
            "gemma-4-31b-it",
            "gemma-4-31b-it-nvfp4",
            "gemma-4-26b-a4b-it",
            "gemma",
            "minimax-m3",
            "minimax",
            "kimi",
        )

    ordered = []

    for preference in preferences:
        for model in models:
            basename = (
                str(model)
                .strip()
                .rsplit("/", 1)[-1]
                .lower()
            )

            if preference in (
                "gemma",
                "minimax",
                "kimi",
            ):
                matched = preference in basename
            else:
                matched = basename == preference

            if matched and model not in ordered:
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
    category = task_category(task)
    budget = token_budget(task)

    log(
        f"Task {task['task_id']}: "
        f"category={category}, "
        f"max_tokens={budget}"
    )

    for model in ordered_models(models, task):
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

    log(f"Loaded {len(models)} allowed models; default={model}")

    results = []

    for task in tasks:
        try:
            answer = call_fireworks_with_fallback(task, models, api_key, url)
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

    log(f"Wrote {len(results)} results")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
