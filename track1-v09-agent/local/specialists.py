#!/usr/bin/env python3

import ast
import math
import operator
import re
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class LocalDecision:
    category: str
    accepted: bool
    answer: Optional[str]
    reason: str


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def combined_task_text(task: dict[str, Any]) -> str:
    fields = (
        "instruction",
        "input",
        "prompt",
        "question",
        "query",
        "text",
        "content",
        "context",
    )

    parts: list[str] = []
    seen: set[str] = set()

    for field in fields:
        value = task.get(field)

        if value in (None, ""):
            continue

        rendered = str(value).strip()

        if rendered and rendered not in seen:
            seen.add(rendered)
            parts.append(rendered)

    return "\n\n".join(parts)


def _evaluate_arithmetic_node(node: ast.AST) -> float | int:
    if isinstance(node, ast.Expression):
        return _evaluate_arithmetic_node(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            raise ValueError("Boolean value rejected")

        if isinstance(node.value, (int, float)):
            return node.value

        raise ValueError("Non-numeric constant rejected")

    if isinstance(node, ast.UnaryOp):
        operation = _UNARY_OPERATORS.get(type(node.op))

        if operation is None:
            raise ValueError("Unsupported unary operator")

        return operation(
            _evaluate_arithmetic_node(node.operand)
        )

    if isinstance(node, ast.BinOp):
        operation = _BINARY_OPERATORS.get(type(node.op))

        if operation is None:
            raise ValueError("Unsupported binary operator")

        left = _evaluate_arithmetic_node(node.left)
        right = _evaluate_arithmetic_node(node.right)

        if isinstance(node.op, ast.Pow):
            if abs(right) > 10:
                raise ValueError("Exponent exceeds safe limit")

            if abs(left) > 1_000_000:
                raise ValueError("Power base exceeds safe limit")

        result = operation(left, right)

        if not isinstance(result, (int, float)):
            raise ValueError("Non-numeric result")

        if isinstance(result, float) and not math.isfinite(result):
            raise ValueError("Non-finite result")

        if abs(result) > 1_000_000_000_000_000:
            raise ValueError("Result exceeds safe limit")

        return result

    raise ValueError(
        f"Unsupported AST node: {type(node).__name__}"
    )


def _arithmetic_candidates(
    task: dict[str, Any],
) -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()

    for field in (
        "input",
        "prompt",
        "question",
        "query",
        "text",
        "content",
    ):
        value = task.get(field)

        if not isinstance(value, (str, int, float)):
            continue

        rendered = str(value).strip()

        if rendered and rendered not in seen:
            seen.add(rendered)
            candidates.append(rendered)

    return candidates


def _extract_expression(text: str) -> Optional[str]:
    normalized = (
        text.strip()
        .replace("×", "*")
        .replace("÷", "/")
        .replace("−", "-")
    )

    if not normalized or len(normalized) > 160:
        return None

    patterns = (
        r"(?is)^(?:what\s+is|calculate|compute|evaluate|solve)"
        r"\s+(.+?)[?.!]?$",

        r"(?is)^(.+?)\s*=\s*\??$",

        r"(?is)^([0-9eE.\s+\-*/%()^]+)[?.!]?$",
    )

    for pattern in patterns:
        match = re.fullmatch(pattern, normalized)

        if not match:
            continue

        expression = match.group(1).strip()
        expression = expression.replace("^", "**")

        if not re.fullmatch(
            r"[0-9eE.\s+\-*/%()]+",
            expression,
        ):
            return None

        if len(expression) > 100:
            return None

        return expression

    return None


def solve_arithmetic(
    task: dict[str, Any],
) -> LocalDecision:
    for candidate in _arithmetic_candidates(task):
        expression = _extract_expression(candidate)

        if expression is None:
            continue

        try:
            tree = ast.parse(
                expression,
                mode="eval",
            )

            if len(list(ast.walk(tree))) > 40:
                continue

            value = _evaluate_arithmetic_node(tree)

        except Exception:
            continue

        if isinstance(value, float):
            if value.is_integer():
                answer = str(int(value))
            else:
                answer = format(value, ".12g")
        else:
            answer = str(value)

        return LocalDecision(
            category="arithmetic",
            accepted=True,
            answer=answer,
            reason="expression independently parsed and recomputed",
        )

    return LocalDecision(
        category="arithmetic",
        accepted=False,
        answer=None,
        reason="task was not provably exact arithmetic",
    )


_POSITIVE_WEIGHTS = {
    "excellent": 3,
    "amazing": 3,
    "outstanding": 3,
    "fantastic": 3,
    "wonderful": 3,
    "perfect": 3,
    "superb": 3,
    "brilliant": 3,
    "love": 2,
    "loved": 2,
    "delighted": 2,
    "impressed": 2,
    "recommend": 2,
    "satisfied": 2,
    "enjoyable": 2,
    "great": 2,
    "happy": 2,
}

_NEGATIVE_WEIGHTS = {
    "terrible": 3,
    "awful": 3,
    "horrible": 3,
    "worst": 3,
    "useless": 3,
    "unacceptable": 3,
    "broken": 3,
    "hate": 2,
    "hated": 2,
    "disappointing": 2,
    "disappointed": 2,
    "frustrating": 2,
    "refund": 2,
    "dissatisfied": 2,
    "poor": 2,
    "bad": 2,
}

_NEGATIONS = {
    "not",
    "never",
    "no",
    "hardly",
    "barely",
    "isn't",
    "wasn't",
    "didn't",
    "don't",
    "doesn't",
}

_SARCASM_MARKERS = {
    "yeah right",
    "as if",
    "sure, great",
    "what a surprise",
    "totally great",
}


def _asks_for_sentiment(task: dict[str, Any]) -> bool:
    metadata = " ".join(
        str(task.get(field, ""))
        for field in (
            "task_type",
            "category",
            "type",
            "instruction",
            "prompt",
            "question",
        )
    ).lower()

    markers = (
        "sentiment",
        "positive or negative",
        "positive, negative",
        "classify the review",
        "classify this review",
    )

    return any(marker in metadata for marker in markers)


def _sentiment_payload(task: dict[str, Any]) -> str:
    for field in (
        "input",
        "text",
        "content",
        "context",
    ):
        value = task.get(field)

        if isinstance(value, str) and value.strip():
            return value.strip()

    prompt = task.get("prompt")

    if isinstance(prompt, str):
        separators = (
            "review:",
            "text:",
            "sentence:",
            "input:",
        )

        lowered = prompt.lower()

        for separator in separators:
            index = lowered.find(separator)

            if index != -1:
                return prompt[
                    index + len(separator):
                ].strip()

    return ""


def solve_sentiment(
    task: dict[str, Any],
) -> LocalDecision:
    if not _asks_for_sentiment(task):
        return LocalDecision(
            category="sentiment",
            accepted=False,
            answer=None,
            reason="task did not explicitly request sentiment",
        )

    payload = _sentiment_payload(task)

    if not payload or len(payload) > 1_200:
        return LocalDecision(
            category="sentiment",
            accepted=False,
            answer=None,
            reason="sentiment payload missing or too long",
        )

    lowered = payload.lower()

    if any(marker in lowered for marker in _SARCASM_MARKERS):
        return LocalDecision(
            category="sentiment",
            accepted=False,
            answer=None,
            reason="possible sarcasm detected",
        )

    tokens = re.findall(
        r"[a-z]+(?:'[a-z]+)?",
        lowered,
    )

    positive = 0
    negative = 0
    negated_signal = False

    for index, token in enumerate(tokens):
        window = tokens[max(0, index - 3):index]
        negated = any(
            item in _NEGATIONS
            for item in window
        )

        if token in _POSITIVE_WEIGHTS:
            if negated:
                negated_signal = True
            else:
                positive += _POSITIVE_WEIGHTS[token]

        if token in _NEGATIVE_WEIGHTS:
            if negated:
                negated_signal = True
            else:
                negative += _NEGATIVE_WEIGHTS[token]

    if negated_signal:
        return LocalDecision(
            category="sentiment",
            accepted=False,
            answer=None,
            reason="negated sentiment requires escalation",
        )

    if positive >= 2 and negative == 0:
        return LocalDecision(
            category="sentiment",
            accepted=True,
            answer="positive",
            reason="strong unopposed positive lexical signal",
        )

    if negative >= 2 and positive == 0:
        return LocalDecision(
            category="sentiment",
            accepted=True,
            answer="negative",
            reason="strong unopposed negative lexical signal",
        )

    return LocalDecision(
        category="sentiment",
        accepted=False,
        answer=None,
        reason="sentiment signal was weak, neutral, or mixed",
    )
