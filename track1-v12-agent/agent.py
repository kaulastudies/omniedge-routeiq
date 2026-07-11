#!/usr/bin/env python3

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from local.arithmetic import solve_arithmetic
from local.sentiment import solve_sentiment
from local.qwen import call_qwen_batch


INPUT_PATH = Path(
    os.getenv("INPUT_PATH", "/input/tasks.json")
)

OUTPUT_PATH = Path(
    os.getenv("OUTPUT_PATH", "/output/results.json")
)


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def load_tasks() -> list[dict[str, Any]]:
    with INPUT_PATH.open(
        "r",
        encoding="utf-8",
    ) as handle:
        data = json.load(handle)

    if isinstance(data, list):
        tasks = data
    elif (
        isinstance(data, dict)
        and isinstance(data.get("tasks"), list)
    ):
        tasks = data["tasks"]
    else:
        raise ValueError(
            "tasks.json must be a list or contain a tasks list"
        )

    normalized = []

    for index, raw_task in enumerate(tasks):
        if not isinstance(raw_task, dict):
            raise ValueError(
                f"Task {index} is not an object"
            )

        task = dict(raw_task)

        if "task_id" not in task:
            if "id" in task:
                task["task_id"] = task["id"]
            else:
                raise ValueError(
                    f"Task {index} has no task_id"
                )

        normalized.append(task)

    return normalized


def write_results(
    results: list[dict[str, str]],
) -> None:
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = OUTPUT_PATH.with_suffix(".tmp")

    with temporary.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            results,
            handle,
            ensure_ascii=False,
            indent=2,
        )

    temporary.replace(OUTPUT_PATH)


def parse_allowed_models() -> list[str]:
    raw = os.getenv(
        "ALLOWED_MODELS",
        "",
    ).strip()

    if not raw:
        raise ValueError("ALLOWED_MODELS is missing")

    try:
        decoded = json.loads(raw)

        if isinstance(decoded, list):
            models = [
                str(item).strip()
                for item in decoded
                if str(item).strip()
            ]

            if models:
                return models

    except json.JSONDecodeError:
        pass

    raw = (
        raw
        .replace(";", ",")
        .replace("\n", ",")
    )

    pieces = (
        raw.split(",")
        if "," in raw
        else raw.split()
    )

    models = [
        item.strip()
        for item in pieces
        if item.strip()
    ]

    if not models:
        raise ValueError(
            "ALLOWED_MODELS has no usable models"
        )

    return models


def ordered_models(
    models: list[str],
) -> list[str]:
    ordered = []

    for keyword in (
        "minimax",
        "gemma",
        "kimi",
    ):
        for model in models:
            if (
                keyword in model.lower()
                and model not in ordered
            ):
                ordered.append(model)

    for model in models:
        if model not in ordered:
            ordered.append(model)

    return ordered


def completion_url() -> str:
    base = os.getenv(
        "FIREWORKS_BASE_URL",
        "",
    ).strip().rstrip("/")

    if not base:
        raise ValueError(
            "FIREWORKS_BASE_URL is missing"
        )

    if base.endswith("/chat/completions"):
        return base

    return f"{base}/chat/completions"


def model_candidates(
    model: str,
    url: str,
) -> list[str]:
    value = model.strip()
    candidates = [value]

    if (
        "api.fireworks.ai" in url.lower()
        and not value.startswith("accounts/")
        and "/" not in value
    ):
        candidates.append(
            f"accounts/fireworks/models/{value}"
        )

    return candidates


def compact_tasks(
    tasks: list[dict[str, Any]],
) -> str:
    payload = []

    for task in tasks:
        content = {
            key: value
            for key, value in task.items()
            if key not in ("task_id", "id")
        }

        payload.append({
            "task_id": task["task_id"],
            "task": content,
        })

    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def extract_json(content: str) -> Any:
    cleaned = content.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

    try:
        return json.loads(cleaned)

    except json.JSONDecodeError:
        pass

    object_start = cleaned.find("{")
    object_end = cleaned.rfind("}")

    if (
        object_start != -1
        and object_end > object_start
    ):
        try:
            return json.loads(
                cleaned[object_start:object_end + 1]
            )
        except json.JSONDecodeError:
            pass

    array_start = cleaned.find("[")
    array_end = cleaned.rfind("]")

    if (
        array_start != -1
        and array_end > array_start
    ):
        return json.loads(
            cleaned[array_start:array_end + 1]
        )

    raise ValueError(
        "Model response did not contain valid JSON"
    )


def normalize_answer(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def parse_batch_results(
    content: str,
    tasks: list[dict[str, Any]],
) -> dict[str, str]:
    decoded = extract_json(content)

    if isinstance(decoded, dict):
        for key in (
            "results",
            "answers",
            "data",
        ):
            if isinstance(decoded.get(key), list):
                decoded = decoded[key]
                break

    if not isinstance(decoded, list):
        raise ValueError(
            "Batch response is not a result list"
        )

    expected_ids = [
        str(task["task_id"])
        for task in tasks
    ]

    results: dict[str, str] = {}

    for index, item in enumerate(decoded):
        if not isinstance(item, dict):
            continue

        task_id = (
            item.get("task_id")
            or item.get("id")
        )

        if (
            task_id is None
            and index < len(expected_ids)
        ):
            task_id = expected_ids[index]

        if task_id is None:
            continue

        answer = item.get("answer")

        if answer is None:
            for alternate in (
                "output",
                "response",
                "result",
            ):
                if alternate in item:
                    answer = item[alternate]
                    break

        normalized = normalize_answer(answer)

        if normalized:
            results[str(task_id)] = normalized

    return results


def batch_response_format() -> dict[str, Any]:
    """
    Enforce a compact results wrapper through Fireworks structured output.

    The schema deliberately avoids unsupported size constraints and accepts
    either string or numeric task IDs.
    """
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "RouteIQBatchResults",
            "schema": {
                "type": "object",
                "properties": {
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "task_id": {
                                    "anyOf": [
                                        {"type": "string"},
                                        {"type": "integer"},
                                    ]
                                },
                                "answer": {
                                    "type": "string"
                                },
                            },
                            "required": [
                                "task_id",
                                "answer",
                            ],
                            "additionalProperties": False,
                        },
                    }
                },
                "required": ["results"],
                "additionalProperties": False,
            },
        },
    }


def _perform_request(
    payload: dict[str, Any],
    api_key: str,
    url: str,
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=120,
    ) as response:
        return json.loads(
            response.read().decode("utf-8")
        )


def request_batch(
    tasks: list[dict[str, Any]],
    model: str,
    api_key: str,
    url: str,
) -> dict[str, str]:
    system_prompt = (
        "Solve every independent task accurately. "
        "Return only JSON matching the enforced schema. "
        "Include every task exactly once and preserve task_id. "
        "Follow each task's requested format, length, and language. "
        "Put only the final answer in answer. "
        "Do not include reasoning, explanations, labels, or markdown "
        "unless the task explicitly requires them. "
        "For code tasks, place complete code in the answer string."
    )

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": compact_tasks(tasks),
            },
        ],
        "temperature": 0,
        "max_tokens": 4096,
        "stream": False,
        "response_format": batch_response_format(),
    }

    try:
        body = _perform_request(
            payload,
            api_key,
            url,
        )

    except urllib.error.HTTPError as error:
        details = error.read().decode(
            "utf-8",
            errors="replace",
        )

        if error.code not in (400, 422):
            raise RuntimeError(
                f"Fireworks HTTP {error.code}: {details[:500]}"
            ) from error

        log(
            "Structured output was rejected; "
            "retrying the same model in plain JSON mode"
        )

        fallback_payload = dict(payload)
        fallback_payload.pop(
            "response_format",
            None,
        )

        body = _perform_request(
            fallback_payload,
            api_key,
            url,
        )

    choices = body.get("choices", [])

    if not choices:
        raise RuntimeError(
            "Fireworks response contains no choices"
        )

    message = choices[0].get("message", {})
    content = message.get("content")

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError(
            "Fireworks response contains no answer text"
        )

    answers = parse_batch_results(
        content,
        tasks,
    )

    if not answers:
        raise RuntimeError(
            "Structured response contained no usable answers"
        )

    return answers


def call_batch(
    tasks: list[dict[str, Any]],
    models: list[str],
    api_key: str,
    url: str,
) -> dict[str, str]:
    last_error: Exception | None = None

    for model in ordered_models(models):
        for candidate in model_candidates(
            model,
            url,
        ):
            try:
                log(
                    f"Attempting one batch call with: {candidate}"
                )

                answers = request_batch(
                    tasks,
                    candidate,
                    api_key,
                    url,
                )

                if answers:
                    return answers

            except Exception as error:
                last_error = error

                log(
                    f"Batch model {candidate} failed: "
                    f"{type(error).__name__}: {error}"
                )

    raise last_error or RuntimeError(
        "All batch models failed"
    )


def call_missing_individually(
    missing: list[dict[str, Any]],
    models: list[str],
    api_key: str,
    url: str,
) -> dict[str, str]:
    recovered: dict[str, str] = {}

    for task in missing:
        task_id = str(task["task_id"])

        try:
            answer_map = call_batch(
                [task],
                models,
                api_key,
                url,
            )

            answer = answer_map.get(task_id, "")

            if answer:
                recovered[task_id] = answer

        except Exception as error:
            log(
                f"Fallback task {task_id} failed: "
                f"{type(error).__name__}: {error}"
            )

    return recovered


def self_test() -> int:
    tasks = [
        {
            "task_id": "t1",
            "prompt": "What is 2 + 2?",
        },
        {
            "task_id": "t2",
            "prompt": "Classify the sentiment.",
        },
    ]

    fenced = """```json
{
  "results": [
    {"task_id": "t1", "answer": "4"},
    {"task_id": "t2", "answer": "positive"}
  ]
}
```"""

    parsed = parse_batch_results(
        fenced,
        tasks,
    )

    assert parsed == {
        "t1": "4",
        "t2": "positive",
    }

    ordered = parse_batch_results(
        '[{"answer":"4"},{"answer":"positive"}]',
        tasks,
    )

    assert ordered == {
        "t1": "4",
        "t2": "positive",
    }

    print("PASS: fenced JSON parsing")
    print("PASS: task-id mapping")
    print("PASS: ordered fallback mapping")
    print("PASS: compact batch payload")
    return 0



LOCAL_TEXT_KEYS = (
    "prompt",
    "question",
    "instruction",
    "text",
    "input",
    "query",
)

LOCAL_NESTED_KEYS = (
    "task",
    "payload",
    "data",
)


def task_text_for_local(
    task: dict[str, Any],
) -> str:
    """
    Extract one clear task instruction for deterministic specialists.

    Reject ambiguous multi-string objects rather than combining fields and
    accidentally changing task meaning.
    """
    for key in LOCAL_TEXT_KEYS:
        value = task.get(key)

        if isinstance(value, str) and value.strip():
            return value.strip()

    for key in LOCAL_NESTED_KEYS:
        value = task.get(key)

        if isinstance(value, dict):
            nested = task_text_for_local(value)

            if nested:
                return nested

    string_values = [
        value.strip()
        for key, value in task.items()
        if (
            key not in ("task_id", "id")
            and isinstance(value, str)
            and value.strip()
        )
    ]

    if len(string_values) == 1:
        return string_values[0]

    return ""


def resolve_local_tasks(
    tasks: list[dict[str, Any]],
) -> tuple[
    dict[str, str],
    list[dict[str, Any]],
]:
    answers: dict[str, str] = {}
    unresolved: list[dict[str, Any]] = []

    for task in tasks:
        task_id = str(task["task_id"])
        task_text = task_text_for_local(task)

        if not task_text:
            unresolved.append(task)
            log(
                f"Local reject {task_id}: "
                "no unambiguous task text"
            )
            continue

        arithmetic_decision = solve_arithmetic(
            task_text
        )

        if (
            arithmetic_decision.accepted
            and arithmetic_decision.answer
        ):
            answers[task_id] = (
                arithmetic_decision.answer
            )

            log(
                f"Local arithmetic accept {task_id}: "
                f"{arithmetic_decision.reason}"
            )

            continue

        sentiment_decision = solve_sentiment(task)

        if (
            sentiment_decision.accepted
            and sentiment_decision.answer
        ):
            answers[task_id] = (
                sentiment_decision.answer
            )

            log(
                f"Local sentiment accept {task_id}: "
                f"{sentiment_decision.reason}"
            )

            continue

        unresolved.append(task)

        log(
            f"Local reject {task_id}: "
            f"arithmetic={arithmetic_decision.reason}; "
            f"sentiment={sentiment_decision.reason}"
        )

    return answers, unresolved


def main() -> int:
    try:
        tasks = load_tasks()

    except Exception as error:
        log(f"Input error: {error}")
        write_results([])
        return 1

    local_answers, unresolved = resolve_local_tasks(
        tasks
    )

    answers = dict(local_answers)
    qwen_answers: dict[str, str] = {}

    if unresolved:
        try:
            qwen_batch_size = int(
                os.getenv(
                    "QWEN_BATCH_SIZE",
                    "4",
                )
            )
        except ValueError:
            qwen_batch_size = 4

        qwen_batch_size = max(
            1,
            min(qwen_batch_size, 8),
        )

        total_batches = (
            len(unresolved)
            + qwen_batch_size
            - 1
        ) // qwen_batch_size

        log(
            f"Attempting {total_batches} guarded "
            f"Qwen batches for {len(unresolved)} tasks; "
            f"batch_size={qwen_batch_size}"
        )

        for offset in range(
            0,
            len(unresolved),
            qwen_batch_size,
        ):
            batch = unresolved[
                offset : offset + qwen_batch_size
            ]

            batch_number = (
                offset // qwen_batch_size
            ) + 1

            try:
                batch_answers = call_qwen_batch(
                    batch
                )

                qwen_answers.update(
                    batch_answers
                )

                answers.update(
                    batch_answers
                )

                log(
                    f"Qwen batch {batch_number}/"
                    f"{total_batches} accepted "
                    f"{len(batch_answers)}/"
                    f"{len(batch)} answers"
                )

            except Exception as error:
                log(
                    f"Qwen batch {batch_number}/"
                    f"{total_batches} failed: "
                    f"{type(error).__name__}: {error}"
                )

        log(
            f"Qwen accepted "
            f"{len(qwen_answers)}/"
            f"{len(unresolved)} unresolved tasks"
        )

    remote_candidates = [
        task
        for task in unresolved
        if not answers.get(
            str(task["task_id"]),
            "",
        ).strip()
    ]

    log(
        f"Routing summary: "
        f"deterministic={len(local_answers)}; "
        f"qwen={len(qwen_answers)}; "
        f"remote={len(remote_candidates)}"
    )

    if remote_candidates:
        try:
            models = parse_allowed_models()
            url = completion_url()

            api_key = os.getenv(
                "FIREWORKS_API_KEY",
                "",
            ).strip()

            if not api_key:
                raise ValueError(
                    "FIREWORKS_API_KEY is missing"
                )

        except Exception as error:
            log(
                f"Remote configuration error: {error}"
            )

            results = [
                {
                    "task_id": task["task_id"],
                    "answer": answers.get(
                        str(task["task_id"]),
                        "",
                    ),
                }
                for task in tasks
            ]

            write_results(results)
            return 1

        try:
            remote_answers = call_batch(
                remote_candidates,
                models,
                api_key,
                url,
            )

            answers.update(remote_answers)

        except Exception as error:
            log(
                f"Primary remote batch failed: "
                f"{type(error).__name__}: {error}"
            )

        missing = [
            task
            for task in remote_candidates
            if not answers.get(
                str(task["task_id"]),
                "",
            ).strip()
        ]

        if missing:
            log(
                f"Recovering {len(missing)} "
                "missing remote answers individually"
            )

            answers.update(
                call_missing_individually(
                    missing,
                    models,
                    api_key,
                    url,
                )
            )

    results = [
        {
            "task_id": task["task_id"],
            "answer": answers.get(
                str(task["task_id"]),
                "",
            ),
        }
        for task in tasks
    ]

    write_results(results)

    completed = sum(
        1
        for result in results
        if result["answer"]
    )

    log(
        f"Wrote {len(results)} results; "
        f"completed={completed}; "
        f"missing={len(results) - completed}; "
        f"deterministic={len(local_answers)}; "
        f"qwen={len(qwen_answers)}; "
        f"remote={len(remote_candidates)}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
