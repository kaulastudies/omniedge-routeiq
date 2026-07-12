from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SentimentDecision:
    accepted: bool
    answer: str = ""
    reason: str = ""


POSITIVE_TERMS = {
    "amazing",
    "approved",
    "awesome",
    "beneficial",
    "delighted",
    "excellent",
    "fantastic",
    "glad",
    "great",
    "happy",
    "impressive",
    "love",
    "loved",
    "outstanding",
    "perfect",
    "pleased",
    "positive",
    "reliable",
    "satisfied",
    "smooth",
    "success",
    "successful",
    "successfully",
    "wonderful",
}

NEGATIVE_TERMS = {
    "angry",
    "awful",
    "bad",
    "broken",
    "crashed",
    "disappointed",
    "disaster",
    "error",
    "failed",
    "failure",
    "frustrated",
    "horrible",
    "negative",
    "poor",
    "problem",
    "rejected",
    "terrible",
    "unhappy",
    "unreliable",
    "unsatisfied",
    "worst",
}

EXPLICIT_NEUTRAL_PATTERNS = (
    r"\bneutral\b",
    r"\bneither positive nor negative\b",
    r"\bneither good nor bad\b",
    r"\baverage\b",
    r"\bordinary\b",
    r"\bno strong opinion\b",
)

NEGATION_TERMS = {
    "not",
    "never",
    "no",
    "hardly",
    "barely",
    "isn't",
    "wasn't",
    "weren't",
    "don't",
    "didn't",
    "cannot",
    "can't",
}

MIXED_MARKERS = {
    "but",
    "however",
    "although",
    "though",
    "yet",
    "despite",
}

SARCASM_MARKERS = (
    "/s",
    "yeah right",
    "as if",
    "what a surprise",
    "just great",
    "thanks a lot",
)


def _reject(reason: str) -> SentimentDecision:
    return SentimentDecision(
        accepted=False,
        reason=reason,
    )


def _accept(
    answer: str,
    reason: str,
) -> SentimentDecision:
    return SentimentDecision(
        accepted=True,
        answer=answer,
        reason=reason,
    )


def _normalise(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("’", "'")
    text = re.sub(r"\s+", " ", text)
    return text


def _extract_prompt(task: dict[str, Any]) -> str:
    for key in (
        "prompt",
        "question",
        "instruction",
        "text",
        "input",
        "query",
    ):
        value = task.get(key)

        if isinstance(value, str) and value.strip():
            return value.strip()

    return ""


def _extract_statement(prompt: str) -> str:
    match = re.match(
        r"^\s*classify\s+as\s+"
        r"positive\s*,\s*negative\s*,\s*or\s*neutral\s*:\s*(.+)$",
        prompt,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if match:
        return match.group(1).strip()

    match = re.match(
        r"^\s*classify\s+the\s+sentiment\s*:\s*(.+)$",
        prompt,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if match:
        return match.group(1).strip()

    return ""


def _tokens(text: str) -> list[str]:
    return re.findall(
        r"[a-z]+(?:'[a-z]+)?",
        text,
    )


def _has_negated_signal(
    tokens: list[str],
    signal_terms: set[str],
) -> bool:
    for index, token in enumerate(tokens):
        if token not in signal_terms:
            continue

        window_start = max(0, index - 3)
        window = tokens[window_start:index]

        if any(
            item in NEGATION_TERMS
            for item in window
        ):
            return True

    return False


def solve_sentiment(
    task: dict[str, Any],
) -> SentimentDecision:
    if not isinstance(task, dict):
        return _reject("task is not an object")

    task_type = task.get("task_type", "")

    if not isinstance(task_type, str):
        return _reject("task_type is not a string")

    if "sentiment" not in task_type.lower():
        return _reject(
            "task_type is not explicitly sentiment"
        )

    prompt = _extract_prompt(task)

    if not prompt:
        return _reject("sentiment prompt is missing")

    statement = _extract_statement(prompt)

    if not statement:
        return _reject(
            "prompt does not match supported sentiment format"
        )

    normalised = _normalise(statement)

    if not normalised:
        return _reject("statement is empty")

    if any(
        marker in normalised
        for marker in SARCASM_MARKERS
    ):
        return _reject("possible sarcasm detected")

    tokens = _tokens(normalised)
    token_set = set(tokens)

    if token_set & MIXED_MARKERS:
        return _reject("mixed-clause marker detected")

    for pattern in EXPLICIT_NEUTRAL_PATTERNS:
        if re.search(pattern, normalised):
            return _accept(
                "neutral",
                "explicit neutral expression",
            )

    positive_hits = token_set & POSITIVE_TERMS
    negative_hits = token_set & NEGATIVE_TERMS

    if positive_hits and negative_hits:
        return _reject(
            "both positive and negative signals detected"
        )

    if _has_negated_signal(
        tokens,
        POSITIVE_TERMS | NEGATIVE_TERMS,
    ):
        return _reject(
            "negated sentiment signal detected"
        )

    if positive_hits:
        return _accept(
            "positive",
            "single strong positive signal",
        )

    if negative_hits:
        return _accept(
            "negative",
            "single strong negative signal",
        )

    return _reject(
        "no strong unambiguous sentiment signal"
    )
