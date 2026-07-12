#!/usr/bin/env python3

from __future__ import annotations

import ast
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from local.arithmetic import solve_arithmetic
from local.sentiment import solve_sentiment

INPUT_PATH = Path(os.getenv("INPUT_PATH", "/input/tasks.json"))
OUTPUT_PATH = Path(os.getenv("OUTPUT_PATH", "/output/results.json"))

TEXT_KEYS = (
    "prompt", "question", "instruction", "query", "text", "input",
)


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def load_tasks() -> list[dict[str, Any]]:
    with INPUT_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, list):
        raw_tasks = payload
    elif isinstance(payload, dict) and isinstance(payload.get("tasks"), list):
        raw_tasks = payload["tasks"]
    else:
        raise ValueError("tasks.json must be a list or contain a tasks list")

    tasks: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_tasks):
        if not isinstance(raw, dict):
            raise ValueError(f"Task {index} is not an object")
        task = dict(raw)
        if "task_id" not in task:
            if "id" in task:
                task["task_id"] = task["id"]
            else:
                raise ValueError(f"Task {index} has no task_id")
        tasks.append(task)
    return tasks


def write_results(results: list[dict[str, str]]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT_PATH.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, ensure_ascii=False, separators=(",", ":"))
    temporary.replace(OUTPUT_PATH)


def task_text(task: dict[str, Any]) -> str:
    for key in TEXT_KEYS:
        value = task.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    for nested_key in ("task", "payload", "data"):
        value = task.get(nested_key)
        if isinstance(value, dict):
            nested = task_text(value)
            if nested:
                return nested
    return ""


def task_text_for_local(task: dict[str, Any]) -> str:
    return task_text(task)


def parse_allowed_models() -> list[str]:
    raw = os.getenv("ALLOWED_MODELS", "").strip()
    if not raw:
        raise ValueError("ALLOWED_MODELS is missing")

    try:
        decoded = json.loads(raw)
        if isinstance(decoded, list):
            models = [str(item).strip() for item in decoded if str(item).strip()]
            if models:
                return models
    except json.JSONDecodeError:
        pass

    normalized = raw.replace(";", ",").replace("\n", ",")
    pieces = normalized.split(",") if "," in normalized else normalized.split()
    models = [piece.strip() for piece in pieces if piece.strip()]
    if not models:
        raise ValueError("ALLOWED_MODELS has no usable models")
    return models


def ordered_models(models: list[str]) -> list[str]:
    ordered: list[str] = []
    for keyword in ("minimax", "gemma-4-31b", "kimi", "gemma"):
        for model in models:
            if keyword in model.lower() and model not in ordered:
                ordered.append(model)
    for model in models:
        if model not in ordered:
            ordered.append(model)
    return ordered


def completion_url() -> str:
    base = os.getenv("FIREWORKS_BASE_URL", "").strip().rstrip("/")
    if not base:
        raise ValueError("FIREWORKS_BASE_URL is missing")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def model_candidates(model: str, url: str) -> list[str]:
    value = model.strip()
    candidates = [value]
    if (
        "api.fireworks.ai" in url.lower()
        and not value.startswith("accounts/")
        and "/" not in value
    ):
        candidates.append(f"accounts/fireworks/models/{value}")
    return candidates


def compact_task_content(task: dict[str, Any]) -> dict[str, Any]:
    """Preserve task meaning while shortening common field names."""
    content: dict[str, Any] = {}
    prompt_written = False

    for key, value in task.items():
        if key in ("task_id", "id"):
            continue
        if key == "task_type":
            content["t"] = value
        elif key in TEXT_KEYS and isinstance(value, str) and value.strip():
            if not prompt_written:
                content["p"] = value.strip()
                prompt_written = True
            elif value.strip() != content.get("p"):
                content[key] = value
        else:
            content[key] = value
    return content


def compact_tasks(tasks: list[dict[str, Any]]) -> str:
    payload = [
        [index, compact_task_content(task)]
        for index, task in enumerate(tasks)
    ]
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def strip_fences(content: str) -> str:
    cleaned = content.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def extract_json(content: str) -> Any:
    cleaned = strip_fences(content)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    object_start, object_end = cleaned.find("{"), cleaned.rfind("}")
    if object_start != -1 and object_end > object_start:
        try:
            return json.loads(cleaned[object_start:object_end + 1])
        except json.JSONDecodeError:
            pass

    array_start, array_end = cleaned.find("["), cleaned.rfind("]")
    if array_start != -1 and array_end > array_start:
        return json.loads(cleaned[array_start:array_end + 1])
    raise ValueError("Model response did not contain valid JSON")


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


def parse_batch_results(content: str, tasks: list[dict[str, Any]]) -> dict[str, str]:
    decoded = extract_json(content)
    if isinstance(decoded, dict):
        for key in ("r", "results", "answers", "data"):
            if isinstance(decoded.get(key), list):
                decoded = decoded[key]
                break

    if not isinstance(decoded, list):
        raise ValueError("Batch response is not a result list")

    expected = [str(task["task_id"]) for task in tasks]
    answers: dict[str, str] = {}

    for position, item in enumerate(decoded):
        index: int | None = None
        answer: Any = None

        if isinstance(item, list) and len(item) >= 2:
            raw_index, answer = item[0], item[1]
            if isinstance(raw_index, int):
                index = raw_index
            elif isinstance(raw_index, str) and raw_index.isdigit():
                index = int(raw_index)
        elif isinstance(item, dict):
            raw_index = item.get("i", item.get("index"))
            raw_id = item.get("task_id", item.get("id"))
            answer = item.get("a", item.get("answer"))
            if answer is None:
                for alternate in ("output", "response", "result"):
                    if alternate in item:
                        answer = item[alternate]
                        break
            if isinstance(raw_index, int):
                index = raw_index
            elif isinstance(raw_index, str) and raw_index.isdigit():
                index = int(raw_index)
            elif raw_id is not None and str(raw_id) in expected:
                task_id = str(raw_id)
                normalized = normalize_answer(answer)
                if normalized and task_id not in answers:
                    answers[task_id] = normalized
                continue
        else:
            continue

        if index is None and position < len(expected):
            index = position
        if index is None or not 0 <= index < len(expected):
            continue

        task_id = expected[index]
        normalized = normalize_answer(answer)
        if normalized and task_id not in answers:
            answers[task_id] = normalized

    return answers


def infer_kind(task: dict[str, Any]) -> str:
    task_type = str(task.get("task_type", "")).lower()
    prompt = task_text(task).lower()
    joined = f"{task_type} {prompt}"
    if any(term in joined for term in ("python", "code", "function", "debug")):
        return "code"
    if "named entit" in joined or " ner " in f" {joined} ":
        return "ner"
    if "summar" in joined or "bullet" in joined or "sentence" in joined:
        return "summary"
    if "sentiment" in joined:
        return "sentiment"
    if any(term in task_type for term in ("math", "arithmetic", "reasoning")):
        return "math"
    if "logic" in task_type:
        return "logic"
    return "factual"


def completion_budget(tasks: list[dict[str, Any]]) -> int:
    per_kind = {
        "factual": 110,
        "math": 100,
        "sentiment": 100,
        "summary": 180,
        "ner": 200,
        "logic": 130,
        "code": 420,
    }
    total = sum(per_kind[infer_kind(task)] for task in tasks)
    return min(3072, max(160, total))


def validate_answer(task: dict[str, Any], answer: str) -> tuple[bool, str]:
    if not isinstance(answer, str) or not answer.strip():
        return False, "empty answer"

    prompt = task_text(task)
    lowered = prompt.lower()
    stripped = answer.strip()

    if "python" in lowered or "python" in str(task.get("task_type", "")).lower():
        candidate = stripped
        fenced = re.search(r"```(?:python)?\s*(.*?)```", candidate, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            candidate = fenced.group(1).strip()
        try:
            ast.parse(candidate)
        except SyntaxError:
            return False, "invalid Python syntax"

    bullet_match = re.search(r"exactly\s+(\d+)\s+bullets?", lowered)
    if bullet_match:
        required = int(bullet_match.group(1))
        bullets = [line for line in stripped.splitlines() if re.match(r"^\s*[-*•]\s+", line)]
        if len(bullets) != required:
            return False, f"expected exactly {required} bullets"
        word_limit = re.search(r"(?:at most|no more than|maximum|max)\s+(\d+)\s+words?", lowered)
        if word_limit:
            maximum = int(word_limit.group(1))
            for bullet in bullets:
                words = re.findall(r"\b[\w'-]+\b", re.sub(r"^\s*[-*•]\s+", "", bullet))
                if len(words) > maximum:
                    return False, f"bullet exceeds {maximum} words"

    sentence_match = re.search(r"exactly\s+(\d+)\s+sentences?", lowered)
    if sentence_match:
        required = int(sentence_match.group(1))
        sentences = [part for part in re.split(r"(?<=[.!?])\s+", stripped) if part.strip()]
        if len(sentences) != required:
            return False, f"expected exactly {required} sentences"

    return True, "valid"



REQUEST_TIMEOUT_SECONDS = max(
    2.0,
    float(os.getenv("ROUTEIQ_REQUEST_TIMEOUT", "90")),
)
GLOBAL_DEADLINE_SECONDS = max(
    60.0,
    float(os.getenv("ROUTEIQ_GLOBAL_DEADLINE", "520")),
)
ACTIVE_DEADLINE: float | None = None


def batch_response_format() -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "RouteIQCompactResults",
            "schema": {
                "type": "object",
                "properties": {
                    "r": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "i": {"type": "integer"},
                                "a": {"type": "string"},
                            },
                            "required": ["i", "a"],
                            "additionalProperties": False,
                        },
                    }
                },
                "required": ["r"],
                "additionalProperties": False,
            },
        },
    }


def active_deadline() -> float:
    return ACTIVE_DEADLINE if ACTIVE_DEADLINE is not None else time.monotonic() + GLOBAL_DEADLINE_SECONDS


def remaining_timeout(deadline: float, preferred: float | None = None) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 1:
        raise TimeoutError("RouteIQ global deadline reached")
    requested = preferred if preferred is not None else REQUEST_TIMEOUT_SECONDS
    return max(1.0, min(requested, remaining - 0.5))


def _perform_request(
    payload: dict[str, Any],
    api_key: str,
    url: str,
    deadline: float | None = None,
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    timeout = remaining_timeout(deadline if deadline is not None else active_deadline())
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace")
    decoded = json.loads(raw)
    if not isinstance(decoded, dict):
        raise RuntimeError("Fireworks response is not a JSON object")
    return decoded


def extract_message_content(body: dict[str, Any]) -> str:
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("Fireworks response contains no choices")
    first = choices[0]
    if not isinstance(first, dict):
        raise RuntimeError("Fireworks choice is malformed")
    message = first.get("message", {})
    if not isinstance(message, dict):
        raise RuntimeError("Fireworks message is malformed")
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    if isinstance(content, list):
        pieces: list[str] = []
        for part in content:
            if isinstance(part, str):
                pieces.append(part)
            elif isinstance(part, dict):
                value = part.get("text", part.get("content"))
                if isinstance(value, str):
                    pieces.append(value)
        joined = "".join(pieces).strip()
        if joined:
            return joined
    for alternate in ("output_text", "text"):
        value = message.get(alternate)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise RuntimeError("Fireworks response contains no answer text")


def request_batch(
    tasks: list[dict[str, Any]],
    model: str,
    api_key: str,
    url: str,
    repair_reasons: dict[str, str] | None = None,
) -> dict[str, str]:
    system_prompt = (
        'Solve every independent task accurately. Return JSON only as '
        '{"r":[{"i":index,"a":"answer"},...]}. Include every index exactly once. '
        'Obey each requested format, length, and language. Put only the final answer in a. '
        'Include explanation or complete code only when the task requests it.'
    )
    user_content: dict[str, Any] = {"q": json.loads(compact_tasks(tasks))}
    if repair_reasons:
        system_prompt += " Repair every supplied task and correct the listed validation issue."
        user_content["x"] = [
            [index, repair_reasons.get(str(task["task_id"]), "missing or invalid")]
            for index, task in enumerate(tasks)
        ]

    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(user_content, ensure_ascii=False, separators=(",", ":")),
            },
        ],
        "temperature": 0,
        "max_tokens": completion_budget(tasks),
        "stream": False,
        "response_format": batch_response_format(),
    }

    try:
        body = _perform_request(payload, api_key, url, active_deadline())
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        if error.code not in (400, 404, 422):
            raise RuntimeError(f"Fireworks HTTP {error.code}: {details[:500]}") from error
        log("Structured output rejected; retrying the same model in plain compact JSON mode")
        payload.pop("response_format", None)
        body = _perform_request(payload, api_key, url, active_deadline())

    content = extract_message_content(body)
    answers = parse_batch_results(content, tasks)
    if not answers:
        raise RuntimeError("Remote response contained no usable answers")
    return answers


def call_batch(
    tasks: list[dict[str, Any]],
    models: list[str],
    api_key: str,
    url: str,
    repair_reasons: dict[str, str] | None = None,
) -> dict[str, str]:
    deadline = active_deadline()
    last_error: Exception | None = None
    for model in ordered_models(models):
        for candidate in model_candidates(model, url):
            if deadline - time.monotonic() <= 2:
                break
            try:
                log(f"Attempting robust compact batch with: {candidate}")
                return request_batch(
                    tasks,
                    candidate,
                    api_key,
                    url,
                    repair_reasons,
                )
            except Exception as error:
                last_error = error
                log(f"Batch model {candidate} failed: {type(error).__name__}: {error}")
    raise last_error or RuntimeError("All batch models failed")


def call_missing_individually(
    missing: list[dict[str, Any]],
    models: list[str],
    api_key: str,
    url: str,
) -> dict[str, str]:
    deadline = active_deadline()
    recovered: dict[str, str] = {}
    for task in missing:
        if deadline - time.monotonic() <= 8:
            break
        task_id = str(task["task_id"])
        try:
            result = call_batch([task], models, api_key, url)
            answer = result.get(task_id, "").strip()
            valid, reason = validate_answer(task, answer)
            if valid:
                recovered[task_id] = answer
            else:
                log(f"Individual recovery rejected {task_id}: {reason}")
        except Exception as error:
            log(f"Individual recovery failed {task_id}: {type(error).__name__}: {error}")
    return recovered


def resolve_local_tasks(
    tasks: list[dict[str, Any]],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    answers: dict[str, str] = {}
    unresolved: list[dict[str, Any]] = []
    for task in tasks:
        task_id = str(task["task_id"])
        text = task_text(task)
        if not text:
            unresolved.append(task)
            continue
        arithmetic = solve_arithmetic(text)
        if arithmetic.accepted and arithmetic.answer:
            answers[task_id] = arithmetic.answer
            log(f"Local arithmetic accept {task_id}: {arithmetic.reason}")
            continue
        sentiment = solve_sentiment(task)
        if sentiment.accepted and sentiment.answer:
            answers[task_id] = sentiment.answer
            log(f"Local sentiment accept {task_id}: {sentiment.reason}")
            continue
        unresolved.append(task)
    return answers, unresolved


def main() -> int:
    global ACTIVE_DEADLINE
    deadline = time.monotonic() + GLOBAL_DEADLINE_SECONDS
    ACTIVE_DEADLINE = deadline
    try:
        tasks = load_tasks()
    except Exception as error:
        log(f"Input error: {error}")
        try:
            write_results([])
        except Exception as write_error:
            log(f"Could not write empty results: {write_error}")
        return 0

    local_answers, remote_tasks = resolve_local_tasks(tasks)
    answers = dict(local_answers)

    if remote_tasks:
        try:
            models = parse_allowed_models()
            url = completion_url()
            api_key = os.getenv("FIREWORKS_API_KEY", "").strip()
            if not api_key:
                raise ValueError("FIREWORKS_API_KEY is missing")

            first: dict[str, str] = {}
            try:
                first = call_batch(remote_tasks, models, api_key, url)
            except Exception as error:
                log(f"Primary remote batch failed: {type(error).__name__}: {error}")

            repair_tasks: list[dict[str, Any]] = []
            repair_reasons: dict[str, str] = {}
            for task in remote_tasks:
                task_id = str(task["task_id"])
                answer = first.get(task_id, "").strip()
                valid, reason = validate_answer(task, answer)
                if valid:
                    answers[task_id] = answer
                else:
                    repair_tasks.append(task)
                    repair_reasons[task_id] = reason

            if repair_tasks and deadline - time.monotonic() > 10:
                log(f"Repairing {len(repair_tasks)} invalid or missing answers in one batch")
                repaired: dict[str, str] = {}
                try:
                    repaired = call_batch(
                        repair_tasks,
                        models,
                        api_key,
                        url,
                        repair_reasons,
                    )
                except Exception as error:
                    log(f"Repair batch failed: {type(error).__name__}: {error}")
                for task in repair_tasks:
                    task_id = str(task["task_id"])
                    answer = repaired.get(task_id, "").strip()
                    valid, reason = validate_answer(task, answer)
                    if valid:
                        answers[task_id] = answer
                    else:
                        log(f"Repair rejected {task_id}: {reason}")

            missing = [
                task for task in remote_tasks
                if not answers.get(str(task["task_id"]), "").strip()
            ]
            if missing and deadline - time.monotonic() > 8:
                log(f"Recovering {len(missing)} answers individually within the remaining deadline")
                answers.update(
                    call_missing_individually(missing, models, api_key, url)
                )
        except Exception as error:
            log(f"Remote configuration/inference failed safely: {type(error).__name__}: {error}")

    results = [
        {"task_id": task["task_id"], "answer": answers.get(str(task["task_id"]), "")}
        for task in tasks
    ]
    try:
        write_results(results)
    except Exception as error:
        log(f"Result write failed: {type(error).__name__}: {error}")
        return 0

    completed = sum(1 for result in results if result["answer"])
    log(
        f"Wrote {len(results)} results; completed={completed}; "
        f"missing={len(results) - completed}; local={len(local_answers)}; "
        f"remote={len(remote_tasks)}"
    )
    # Always exit successfully after writing evaluator-readable output. Missing answers
    # should be scored as incorrect, not misreported as a container runtime crash.
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException as error:
        log(f"Unhandled error contained safely: {type(error).__name__}: {error}")
        try:
            write_results([])
        except BaseException:
            pass
        raise SystemExit(0)
