from __future__ import annotations

import re
from typing import Any

from .summary import solve_summary
from .validation import infer_category


def _extract_python(answer: str) -> str:
    fenced = re.search(r"```(?:python)?\s*(.*?)```", answer, flags=re.I | re.S)
    if fenced:
        return fenced.group(1).strip()
    index = answer.find("def ")
    return answer[index:].strip() if index >= 0 else answer.strip()


def repair_answer(task: dict[str, Any], answer: str) -> str:
    if not isinstance(answer, str):
        return ""
    value = answer.strip()
    category = infer_category(task)

    if category == "summary":
        deterministic = solve_summary(task)
        if deterministic.accepted and deterministic.answer:
            return deterministic.answer

    if category == "code":
        return _extract_python(value)

    if category == "sentiment":
        value = re.sub(r"\s+", " ", value).strip()
        # Preserve one requested explanation while removing accidental extra sentences.
        if re.search(r"\b(reason|explain|justify)\b", str(task), flags=re.I):
            first = re.match(r"(.+?[.!?])(?:\s|$)", value)
            if first:
                return first.group(1).strip()

    return value
