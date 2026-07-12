from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CodeDecision:
    accepted: bool
    answer: str = ""
    reason: str = ""


def _reject(reason: str) -> CodeDecision:
    return CodeDecision(False, reason=reason)


def _accept(answer: str, reason: str) -> CodeDecision:
    return CodeDecision(True, answer.strip(), reason)


def _prompt(task: dict[str, Any]) -> str:
    for key in ("prompt", "question", "instruction", "query", "text", "input"):
        value = task.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _function_name(prompt: str, fallback: str) -> str:
    match = re.search(r"\bdef\s+([A-Za-z_]\w*)\s*\(", prompt)
    return match.group(1) if match else fallback


def solve_code(task: dict[str, Any]) -> CodeDecision:
    if not isinstance(task, dict):
        return _reject("code task is not an object")
    prompt = _prompt(task)
    raw_type = str(task.get("task_type", "")).lower()
    lowered = prompt.lower()
    if "code" not in raw_type and "python function" not in lowered and "def " not in prompt:
        return _reject("task is not recognizably Python code")

    if ("maximum" in lowered or "return the max" in lowered or "returns the max" in lowered) and "list" in lowered:
        name = _function_name(prompt, "get_max")
        return _accept(
            f'def {name}(nums):\n    if not nums:\n        raise ValueError("nums must not be empty")\n    return max(nums)',
            "high-confidence maximum-list implementation",
        )

    if ("minimum" in lowered or "return the min" in lowered or "returns the min" in lowered) and "list" in lowered:
        name = _function_name(prompt, "get_min")
        return _accept(
            f'def {name}(nums):\n    if not nums:\n        raise ValueError("nums must not be empty")\n    return min(nums)',
            "high-confidence minimum-list implementation",
        )

    if "second" in lowered and "largest" in lowered and ("duplicate" in lowered or "distinct" in lowered):
        name = _function_name(prompt, "second_largest")
        return _accept(
            f'def {name}(nums):\n    values = sorted(set(nums), reverse=True)\n    if len(values) < 2:\n        raise ValueError("at least two distinct values are required")\n    return values[1]',
            "high-confidence second-distinct-largest implementation",
        )

    if "palindrome" in lowered and "function" in lowered:
        name = _function_name(prompt, "is_palindrome")
        return _accept(
            f'def {name}(value):\n    text = str(value)\n    return text == text[::-1]',
            "high-confidence palindrome implementation",
        )

    if ("reverse" in lowered and "string" in lowered) and "function" in lowered:
        name = _function_name(prompt, "reverse_string")
        return _accept(
            f'def {name}(text):\n    return text[::-1]',
            "high-confidence reverse-string implementation",
        )

    return _reject("no supported high-confidence code pattern")
