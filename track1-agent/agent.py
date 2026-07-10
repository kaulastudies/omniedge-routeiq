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

    for keyword in ("gemma", "kimi", "minimax"):
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


def call_fireworks(task, model, api_key, url):
    category = str(
        task.get("task_type")
        or task.get("category")
        or task.get("type")
        or "general"
    )

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Complete the task accurately and concisely. "
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
        "max_tokens": 512,
        "stream": False,
    }

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

    last_error = None

    for attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                body = json.loads(response.read().decode("utf-8"))

            choices = body.get("choices", [])

            if not choices:
                raise RuntimeError("Response contains no choices")

            message = choices[0].get("message", {})
            content = message.get("content")

            if not isinstance(content, str):
                raise RuntimeError("Response contains no answer text")

            return content.strip()

        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            last_error = RuntimeError(
                f"Fireworks HTTP {error.code}: {details[:400]}"
            )

        except Exception as error:
            last_error = error

        if attempt == 0:
            time.sleep(2)

    raise RuntimeError(str(last_error))


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
        model = choose_model(parse_allowed_models())
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

    for task in tasks:
        try:
            answer = call_fireworks(task, model, api_key, url)
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
