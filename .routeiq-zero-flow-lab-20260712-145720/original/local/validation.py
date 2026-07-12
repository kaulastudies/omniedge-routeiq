from __future__ import annotations

import ast
import re
from typing import Any


BAD_MARKERS = (
    "[end of text]", "<think>", "</think>", "i cannot answer", "i don't know",
    "as an ai language model",
)


def task_prompt(task: dict[str, Any]) -> str:
    for key in ("prompt", "question", "instruction", "query", "text", "input"):
        value = task.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for key in ("task", "payload", "data"):
        value = task.get(key)
        if isinstance(value, dict):
            nested = task_prompt(value)
            if nested:
                return nested
    return ""


def infer_category(task: dict[str, Any]) -> str:
    raw_type = str(task.get("task_type", "")).lower().replace("-", "_").replace(" ", "_")
    prompt = task_prompt(task).lower()
    if "sentiment" in raw_type or "classify the sentiment" in prompt or "classify as positive" in prompt:
        return "sentiment"
    if "summar" in raw_type or prompt.startswith("summarize") or prompt.startswith("summarise"):
        return "summary"
    if "named_entity" in raw_type or "extract all named entities" in prompt or "named entities" in prompt:
        return "ner"
    if "code_debug" in raw_type or ("bug" in prompt and ("function" in prompt or "def " in prompt)):
        return "code"
    if "code_generation" in raw_type or "write a python function" in prompt or "write a function" in prompt:
        return "code"
    if "logical" in raw_type or "deductive" in raw_type or ("who" in prompt and "different" in prompt):
        return "logic"
    if "mathemat" in raw_type or "calculate" in prompt or re.search(r"\d\s*[%+*/-]", prompt):
        return "math"
    return "factual"


def _sentence_count(answer: str) -> int:
    cleaned = re.sub(r"\b(?:e\.g|i\.e|mr|mrs|dr)\.", lambda m: m.group(0).replace(".", ""), answer, flags=re.I)
    return len(re.findall(r"[^.!?\n]+[.!?](?:\s|$)", cleaned.strip()))


def _bullet_lines(answer: str) -> list[str]:
    lines = []
    for line in answer.splitlines():
        stripped = line.strip()
        match = re.match(r"^(?:[-*•]|\d+[.)])\s+(.+)$", stripped)
        if match:
            lines.append(match.group(1).strip())
    return lines


def _extract_python(answer: str) -> str:
    fenced = re.search(r"```(?:python)?\s*(.*?)```", answer, flags=re.I | re.S)
    if fenced:
        return fenced.group(1).strip()
    index = answer.find("def ")
    if index != -1:
        return answer[index:].strip()
    return answer.strip()


def validate_answer(task: dict[str, Any], answer: str) -> tuple[bool, str]:
    if not isinstance(answer, str) or not answer.strip():
        return False, "empty answer"
    answer = answer.strip()
    lowered = answer.lower()
    if any(marker in lowered for marker in BAD_MARKERS):
        return False, "model artifact or refusal"
    prompt = task_prompt(task)
    category = infer_category(task)

    if category == "sentiment":
        if not re.match(r"^(positive|negative|neutral|mixed)\b", lowered):
            return False, "sentiment label missing"
        if any(word in prompt.lower() for word in ("reason", "explain", "justify")):
            if "—" not in answer and "-" not in answer and ":" not in answer:
                return False, "sentiment reason missing"
            if _sentence_count(answer) != 1:
                return False, "sentiment reason is not exactly one sentence"
        statement = prompt.split(":", 1)[-1].lower()
        reason_requested = any(word in prompt.lower() for word in ("reason", "explain", "justify"))
        if reason_requested and any(marker in statement for marker in (" but ", " however ", " although ", " yet ")):
            positive = any(word in lowered for word in ("positive", "worked", "perfect", "great", "flawless", "resolved", "fast", "benefit"))
            negative = any(word in lowered for word in ("negative", "late", "damaged", "dented", "missing", "scratches", "problem", "challenge", "although", "but"))
            if not (positive and negative):
                return False, "mixed sentiment reason does not acknowledge both sides"

    elif category == "summary":
        sentence_match = re.search(r"exactly\s+(\w+|\d+)\s+sentences?", prompt, flags=re.I)
        if sentence_match:
            words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
            expected = words.get(sentence_match.group(1).lower())
            if expected is None:
                expected = int(sentence_match.group(1))
            if _sentence_count(answer) != expected:
                return False, f"expected exactly {expected} sentences"
        bullet_match = re.search(r"exactly\s+(\w+|\d+)\s+bullet", prompt, flags=re.I)
        if bullet_match:
            words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
            expected = words.get(bullet_match.group(1).lower())
            if expected is None:
                expected = int(bullet_match.group(1))
            bullets = _bullet_lines(answer)
            if len(bullets) != expected:
                return False, f"expected exactly {expected} bullets"
            limit_match = re.search(r"(?:no longer than|at most)\s+(\d+)\s+words", prompt, flags=re.I)
            if limit_match:
                limit = int(limit_match.group(1))
                if any(len(re.findall(r"\b[\w'-]+\b", bullet)) > limit for bullet in bullets):
                    return False, "bullet word limit exceeded"

    elif category == "ner":
        labels = set(re.findall(r"\b(PERSON|ORGANIZATION|ORGANISATION|LOCATION|DATE)\b", answer, flags=re.I))
        if not labels:
            return False, "NER labels missing"
        if len(answer.splitlines()) < 2 and answer.count(",") < 1 and answer.count(";") < 1:
            return False, "NER answer appears incomplete"

    elif category == "code":
        code = _extract_python(answer)
        if "python" in prompt.lower() or "def " in prompt:
            try:
                parsed = ast.parse(code)
            except SyntaxError:
                return False, "generated Python is not syntactically valid"
            if not any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) for node in ast.walk(parsed)):
                return False, "generated Python contains no function"

    elif category == "math":
        if not re.search(r"\d", answer):
            return False, "mathematical answer contains no number"

    elif category == "factual":
        if not re.search(r"[A-Za-z0-9]", answer):
            return False, "factual answer has no substantive content"

    return True, "format validation passed"
