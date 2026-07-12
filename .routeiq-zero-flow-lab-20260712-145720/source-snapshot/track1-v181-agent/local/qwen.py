import json
import os
import re
import subprocess
from json import JSONDecoder
from pathlib import Path
from typing import Any

from .validation import infer_category, task_prompt


DEFAULT_BINARY = Path(os.getenv("QWEN_BINARY", "/app/llama-completion"))
DEFAULT_MODEL = Path(os.getenv("QWEN_MODEL_PATH", "/app/models/Qwen3-4B-Q4_K_M.gguf"))


def clean_qwen_output(content: str) -> str:
    cleaned = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", content)
    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = cleaned.replace("[end of text]", "")
    cleaned = re.sub(r"```(?:json)?", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _answer_to_string(answer: Any) -> str:
    if isinstance(answer, str):
        return answer.strip()
    if answer is None:
        return ""
    if isinstance(answer, bool):
        return "true" if answer else "false"
    if isinstance(answer, (int, float)):
        return str(answer)
    return json.dumps(answer, ensure_ascii=False, separators=(",", ":"))


def _objects_from_text(content: str) -> list[dict[str, Any]]:
    cleaned = clean_qwen_output(content)
    decoder = JSONDecoder()
    objects: list[dict[str, Any]] = []

    for candidate in (cleaned, cleaned[cleaned.find("[") :] if "[" in cleaned else ""):
        if not candidate:
            continue
        try:
            decoded = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(decoded, list):
            objects.extend(item for item in decoded if isinstance(item, dict))
        elif isinstance(decoded, dict):
            for key in ("r", "results", "answers", "data"):
                if isinstance(decoded.get(key), list):
                    objects.extend(item for item in decoded[key] if isinstance(item, dict))
                    break
            else:
                objects.append(decoded)
        if objects:
            return objects

    index = 0
    while index < len(cleaned):
        start = cleaned.find("{", index)
        if start == -1:
            break
        try:
            value, consumed = decoder.raw_decode(cleaned[start:])
        except json.JSONDecodeError:
            index = start + 1
            continue
        if isinstance(value, dict):
            objects.append(value)
        index = start + consumed
    return objects


def parse_qwen_results(content: str, tasks: list[dict[str, Any]]) -> dict[str, str]:
    expected_ids = {str(task["task_id"]) for task in tasks}
    answers: dict[str, str] = {}
    for item in _objects_from_text(content):
        task_id = str(item.get("i", item.get("task_id", item.get("id", "")))).strip()
        if task_id not in expected_ids or task_id in answers:
            continue
        answer = _answer_to_string(item.get("a", item.get("answer", item.get("output"))))
        if answer:
            answers[task_id] = answer
    if not answers:
        raise ValueError("Qwen returned no recoverable task answers")
    return answers


def _priority(task: dict[str, Any]) -> tuple[int, int]:
    category_order = {
        "factual": 0,
        "logic": 1,
        "code": 2,
        "ner": 3,
        "sentiment": 4,
        "math": 5,
        "summary": 6,
    }
    prompt = task_prompt(task)
    return category_order.get(infer_category(task), 7), len(prompt)


def _run_qwen(
    tasks: list[dict[str, Any]],
    *,
    mode: str,
    audit: bool = False,
    drafts: dict[str, str] | None = None,
) -> dict[str, str]:
    if not tasks:
        return {}
    if os.getenv("QWEN_ENABLED", "1").strip() != "1":
        raise RuntimeError("Qwen local inference is disabled")

    binary = Path(os.getenv("QWEN_BINARY", str(DEFAULT_BINARY)))
    model = Path(os.getenv("QWEN_MODEL_PATH", str(DEFAULT_MODEL)))
    if not binary.is_file():
        raise FileNotFoundError(f"Qwen binary not found: {binary}")
    if not model.is_file():
        raise FileNotFoundError(f"Qwen model not found: {model}")

    ordered_tasks = sorted(tasks, key=_priority)
    drafts = drafts or {}
    compact_tasks = []
    for task in ordered_tasks:
        item = {
            "i": str(task["task_id"]),
            "c": infer_category(task),
            "p": task_prompt(task),
        }
        if audit:
            item["d"] = drafts.get(str(task["task_id"]), "")
        compact_tasks.append(item)

    normalized_mode = mode.strip().lower()
    thinking = normalized_mode not in {"off", "false", "0", "nonthinking", "non-thinking"}
    mode_suffix = "/think" if thinking else "/no_think"

    if audit:
        prompt = (
            "You are a meticulous independent fact-checker and final-answer editor. "
            "Each task includes a draft answer that may be incomplete or wrong. Re-solve the task from scratch, "
            "compare against the draft, and output the corrected final answer only. Verify every named entity, date, "
            "scientific claim, and geographic relationship. For a city near water, name the exact nearby river, lake, "
            "bay, harbour, canal, or reservoir; never substitute a distant ocean. For comparisons, define both items, "
            "state how they work, and give the decisive distinction. Preserve exact requested sentence, bullet, word, "
            "NER, and code constraints. Output one compact JSON object per line only: "
            '{"i":"ID","a":"FINAL ANSWER"}. No array, markdown, or commentary outside answer strings. '
            "Escape newlines inside JSON strings. Items:"
            + json.dumps(compact_tasks, ensure_ascii=False, separators=(",", ":"))
            + " "
            + mode_suffix
        )
    else:
        prompt = (
            "Solve every task independently and accurately. Keep final answers concise while covering every requested "
            "part. For comparisons, define both sides and state the decisive distinction. For code, return complete "
            "executable Python. For NER, include every entity and allowed label. For constrained summaries, obey all "
            "counts and limits exactly. Output one compact JSON object per line only: "
            '{"i":"ID","a":"FINAL ANSWER"}. No array, markdown, or commentary outside answer strings. '
            "Escape newlines inside JSON strings. Tasks:"
            + json.dumps(compact_tasks, ensure_ascii=False, separators=(",", ":"))
            + " "
            + mode_suffix
        )

    environment = os.environ.copy()
    environment["LLAMA_ARG_CTX_SIZE"] = os.getenv("QWEN_CONTEXT_SIZE", "4096")
    if audit:
        max_tokens = os.getenv("QWEN_AUDIT_MAX_TOKENS", "1400")
        seed = os.getenv("QWEN_AUDIT_SEED", "7")
    else:
        max_tokens = os.getenv("QWEN_PROPOSAL_MAX_TOKENS", "1600")
        seed = os.getenv("QWEN_PROPOSAL_SEED", "42")

    command = [
        str(binary),
        "-m", str(model),
        "-t", os.getenv("QWEN_THREADS", "2"),
        "-n", max_tokens,
        "--seed", seed,
        "--jinja",
        "--single-turn",
        "--simple-io",
        "--no-display-prompt",
        "--no-context-shift",
    ]
    if thinking:
        command += [
            "--temp", os.getenv("QWEN_THINK_TEMP", "0.25"),
            "--top-k", os.getenv("QWEN_THINK_TOP_K", "20"),
            "--top-p", os.getenv("QWEN_THINK_TOP_P", "0.90"),
            "--min-p", "0",
            "--presence-penalty", os.getenv("QWEN_PRESENCE_PENALTY", "0.0"),
            "--reasoning", "on",
            "--reasoning-budget", os.getenv("QWEN_REASONING_BUDGET", "640"),
        ]
    else:
        command += [
            "--temp", os.getenv("QWEN_CHAT_TEMP", "0.20"),
            "--top-k", os.getenv("QWEN_CHAT_TOP_K", "20"),
            "--top-p", os.getenv("QWEN_CHAT_TOP_P", "0.85"),
            "--min-p", "0",
            "--presence-penalty", os.getenv("QWEN_PRESENCE_PENALTY", "0.0"),
            "--reasoning", "off",
            "--reasoning-budget", "0",
        ]
    command += ["-p", prompt]

    timeout_name = "QWEN_AUDIT_TIMEOUT_SECONDS" if audit else "QWEN_PROPOSAL_TIMEOUT_SECONDS"
    timeout_default = "300" if audit else "220"
    timeout_seconds = int(os.getenv(timeout_name, timeout_default))
    try:
        completed = subprocess.run(
            command,
            env=environment,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        partial = error.stdout or ""
        if isinstance(partial, bytes):
            partial = partial.decode("utf-8", errors="replace")
        if partial.strip():
            try:
                return parse_qwen_results(partial, ordered_tasks)
            except Exception:
                pass
        stage = "audit" if audit else "proposal"
        raise RuntimeError(f"Qwen {stage} timed out after {timeout_seconds}s with no recoverable answers") from error

    if completed.returncode != 0:
        stage = "audit" if audit else "proposal"
        raise RuntimeError(
            f"Qwen {stage} failed with status {completed.returncode}: {completed.stderr[-1600:]}"
        )
    return parse_qwen_results(completed.stdout, ordered_tasks)


def call_qwen_batch(tasks: list[dict[str, Any]]) -> dict[str, str]:
    mode = os.getenv("QWEN_PROPOSAL_MODE", "nonthinking")
    return _run_qwen(tasks, mode=mode)


def call_qwen_audit(tasks: list[dict[str, Any]], drafts: dict[str, str]) -> dict[str, str]:
    mode = os.getenv("QWEN_AUDIT_MODE", "thinking")
    return _run_qwen(tasks, mode=mode, audit=True, drafts=drafts)
