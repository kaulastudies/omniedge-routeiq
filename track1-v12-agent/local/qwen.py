import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


DEFAULT_BINARY = Path(
    os.getenv(
        "QWEN_BINARY",
        "/app/llama-completion",
    )
)

DEFAULT_MODEL = Path(
    os.getenv(
        "QWEN_MODEL_PATH",
        "/app/models/Qwen3-1.7B-Q8_0.gguf",
    )
)


def _task_prompt(
    task: dict[str, Any],
) -> str:
    for key in (
        "prompt",
        "question",
        "instruction",
        "query",
        "text",
        "input",
    ):
        value = task.get(key)

        if isinstance(value, str) and value.strip():
            return value.strip()

    values = [
        value.strip()
        for key, value in task.items()
        if (
            key not in ("task_id", "id", "task_type")
            and isinstance(value, str)
            and value.strip()
        )
    ]

    if values:
        return max(
            values,
            key=len,
        )

    return ""


def clean_qwen_output(
    content: str,
) -> str:
    cleaned = re.sub(
        r"\x1b\[[0-?]*[ -/]*[@-~]",
        "",
        content,
    )

    cleaned = re.sub(
        r"<think>.*?</think>",
        "",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )

    cleaned = cleaned.replace(
        "[end of text]",
        "",
    )

    cleaned = re.sub(
        r"```(?:json)?",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    return cleaned.strip()


def _answer_to_string(
    answer: Any,
) -> str:
    if isinstance(answer, str):
        return answer.strip()

    if answer is None:
        return ""

    if isinstance(answer, bool):
        return "true" if answer else "false"

    if isinstance(answer, (int, float)):
        return str(answer)

    return json.dumps(
        answer,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def parse_qwen_results(
    content: str,
    tasks: list[dict[str, Any]],
) -> dict[str, str]:
    cleaned = clean_qwen_output(content)

    start = cleaned.find("[")
    end = cleaned.rfind("]")

    if start == -1 or end == -1 or end <= start:
        raise ValueError(
            "Qwen output contains no complete JSON array"
        )

    payload = json.loads(
        cleaned[start : end + 1]
    )

    if not isinstance(payload, list):
        raise ValueError(
            "Qwen output is not a JSON array"
        )

    expected_ids = {
        str(task["task_id"])
        for task in tasks
    }

    answers: dict[str, str] = {}

    for item in payload:
        if not isinstance(item, dict):
            continue

        task_id = str(
            item.get(
                "task_id",
                "",
            )
        ).strip()

        if task_id not in expected_ids:
            continue

        if task_id in answers:
            continue

        answer = _answer_to_string(
            item.get("answer")
        )

        if answer:
            answers[task_id] = answer

    if not answers:
        raise ValueError(
            "Qwen returned no valid task answers"
        )

    return answers


def call_qwen_batch(
    tasks: list[dict[str, Any]],
) -> dict[str, str]:
    if not tasks:
        return {}

    if os.getenv(
        "QWEN_ENABLED",
        "1",
    ).strip() != "1":
        raise RuntimeError(
            "Qwen local inference is disabled"
        )

    binary = Path(
        os.getenv(
            "QWEN_BINARY",
            str(DEFAULT_BINARY),
        )
    )

    model = Path(
        os.getenv(
            "QWEN_MODEL_PATH",
            str(DEFAULT_MODEL),
        )
    )

    if not binary.is_file():
        raise FileNotFoundError(
            f"Qwen binary not found: {binary}"
        )

    if not model.is_file():
        raise FileNotFoundError(
            f"Qwen model not found: {model}"
        )

    compact_tasks = []

    for task in tasks:
        compact_tasks.append(
            {
                "task_id": str(task["task_id"]),
                "task_type": str(
                    task.get(
                        "task_type",
                        "",
                    )
                ),
                "prompt": _task_prompt(task),
            }
        )

    prompt = (
        "Return only a valid compact JSON array. "
        "Do not use markdown. Do not explain. "
        "Do not include reasoning. "
        "Answer every task independently. "
        "Preserve every task_id exactly. "
        "Every object must contain task_id and answer. "
        "The answer field must be a string. "
        "Follow each task's requested output format. "
        "Tasks:"
        + json.dumps(
            compact_tasks,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + " /no_think"
    )

    environment = os.environ.copy()

    environment["LLAMA_ARG_CTX_SIZE"] = os.getenv(
        "QWEN_CONTEXT_SIZE",
        "4096",
    )

    command = [
        str(binary),
        "-m",
        str(model),
        "-t",
        os.getenv(
            "QWEN_THREADS",
            "2",
        ),
        "-n",
        os.getenv(
            "QWEN_MAX_TOKENS",
            "1024",
        ),
        "--temp",
        "0",
        "--jinja",
        "--single-turn",
        "--reasoning",
        "off",
        "--reasoning-budget",
        "0",
        "--simple-io",
        "--no-display-prompt",
        "-p",
        prompt,
    ]

    timeout_seconds = int(
        os.getenv(
            "QWEN_TIMEOUT_SECONDS",
            "240",
        )
    )

    completed = subprocess.run(
        command,
        env=environment,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )

    if completed.returncode != 0:
        error_tail = completed.stderr[-1200:]

        raise RuntimeError(
            "Qwen inference failed with "
            f"status {completed.returncode}: "
            f"{error_tail}"
        )

    return parse_qwen_results(
        completed.stdout,
        tasks,
    )
