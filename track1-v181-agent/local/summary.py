from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SummaryDecision:
    accepted: bool
    answer: str = ""
    reason: str = ""


BENEFIT_TERMS = {
    "benefit", "benefits", "opportunity", "opportunities", "gain", "gains",
    "improve", "improves", "improved", "enhance", "enhances", "enable",
    "enables", "allow", "allows", "flexibility", "efficient", "efficiency",
    "reduce", "reduced", "support", "supports", "help", "helps", "accurate",
    "accuracy", "transform", "transformed", "innovation", "growth",
}
CHALLENGE_TERMS = {
    "challenge", "challenges", "concern", "concerns", "risk", "risks",
    "however", "but", "privacy", "bias", "liability", "uncertainty",
    "problem", "problems", "issue", "issues", "limitation", "limitations",
    "barrier", "barriers", "drawback", "drawbacks", "difficult", "blurring",
    "regulatory", "security", "cost", "costs",
}
RESPONSE_TERMS = {
    "respond", "responding", "response", "address", "addressing", "mitigate",
    "mitigation", "invest", "investing", "adopt", "adopting", "rethink",
    "rethinking", "adapt", "adapting", "policy", "policies", "framework",
    "frameworks", "regulation", "regulations", "solution", "solutions",
    "training", "tools", "strategy", "strategies",
}

NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}


def _reject(reason: str) -> SummaryDecision:
    return SummaryDecision(False, reason=reason)


def _accept(answer: str, reason: str) -> SummaryDecision:
    return SummaryDecision(True, answer.strip(), reason)


def _task_prompt(task: dict[str, Any]) -> str:
    for key in ("prompt", "question", "instruction", "query", "text", "input"):
        value = task.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _source_text(prompt: str) -> str:
    quoted = re.findall(r"['\"](.+?)['\"]", prompt, flags=re.DOTALL)
    if quoted:
        return max(quoted, key=len).strip()
    colon = prompt.find(":")
    return prompt[colon + 1 :].strip() if colon >= 0 else ""


def _sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    pieces = re.split(r"(?<=[.!?])\s+", text)
    return [piece.strip() for piece in pieces if piece.strip()]


def _words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*", text)


def _score(sentence: str, terms: set[str]) -> int:
    tokens = {token.lower() for token in _words(sentence)}
    return sum(1 for term in terms if term in tokens)


def _pick(sentences: list[str], terms: set[str], used: set[int]) -> int | None:
    candidates = [
        (_score(sentence, terms), -index, index)
        for index, sentence in enumerate(sentences)
        if index not in used
    ]
    if not candidates:
        return None
    score, _, index = max(candidates)
    return index if score > 0 else None


def _ensure_sentence(text: str) -> str:
    value = text.strip(" -•\t\n")
    if not value:
        return ""
    if value[-1] not in ".!?":
        value += "."
    return value


def _compress(text: str, limit: int | None) -> str:
    tokens = _words(text)
    if limit is not None and len(tokens) > limit:
        tokens = tokens[:limit]
    return " ".join(tokens).strip()


def _requested_number(match: re.Match[str]) -> int | None:
    raw = match.group(1).lower()
    if raw in NUMBER_WORDS:
        return NUMBER_WORDS[raw]
    try:
        return int(raw)
    except ValueError:
        return None


def _select_diverse(sentences: list[str], count: int) -> list[str]:
    used: set[int] = set()
    selected: list[int] = []

    # Lead with the most informative opportunity/overview sentence. Some passages
    # describe benefits through concrete applications without using words such as
    # "benefit" or "improve", so fall back to the longest non-risk sentence.
    opportunity = _pick(sentences, BENEFIT_TERMS, used)
    if opportunity is None:
        safe_candidates = [
            index for index, sentence in enumerate(sentences)
            if _score(sentence, CHALLENGE_TERMS) == 0 and _score(sentence, RESPONSE_TERMS) == 0
        ]
        if safe_candidates:
            opportunity = max(safe_candidates, key=lambda index: len(_words(sentences[index])))
    if opportunity is not None:
        used.add(opportunity)
        selected.append(opportunity)

    for terms in (CHALLENGE_TERMS, RESPONSE_TERMS):
        if len(selected) >= count:
            break
        index = _pick(sentences, terms, used)
        if index is not None:
            used.add(index)
            selected.append(index)

    for index in range(len(sentences)):
        if len(selected) >= count:
            break
        if index not in used:
            used.add(index)
            selected.append(index)
    return [sentences[index] for index in selected[:count]]


def solve_summary(task: dict[str, Any]) -> SummaryDecision:
    if not isinstance(task, dict):
        return _reject("summary task is not an object")
    prompt = _task_prompt(task)
    raw_type = str(task.get("task_type", "")).lower()
    if "summar" not in raw_type and not re.match(r"^\s*summari[sz]e\b", prompt, flags=re.I):
        return _reject("task is not recognizably summarization")
    source = _source_text(prompt)
    sentences = _sentences(source)
    if len(sentences) < 2:
        return _reject("source passage could not be split confidently")

    bullet_match = re.search(r"exactly\s+(\w+|\d+)\s+bullet", prompt, flags=re.I)
    if bullet_match:
        count = _requested_number(bullet_match)
        if count is None or count < 1 or count > 5:
            return _reject("unsupported bullet count")
        limit_match = re.search(r"(?:no longer than|at most)\s+(\d+)\s+words", prompt, flags=re.I)
        limit = int(limit_match.group(1)) if limit_match else None
        selected = _select_diverse(sentences, count)
        bullets = [f"- {_compress(sentence, limit)}" for sentence in selected]
        if len(bullets) != count or any(not line.strip("- ") for line in bullets):
            return _reject("could not construct required bullets")
        return _accept("\n".join(bullets), "extractive constraint-aware bullet summary")

    sentence_match = re.search(r"exactly\s+(\w+|\d+)\s+sentences?", prompt, flags=re.I)
    if sentence_match:
        count = _requested_number(sentence_match)
        if count is None or count < 1 or count > 5:
            return _reject("unsupported sentence count")
        selected = _select_diverse(sentences, count)
        answer = " ".join(_ensure_sentence(sentence) for sentence in selected)
        return _accept(answer, "extractive constraint-aware sentence summary")

    return _reject("summary has no safely enforceable exact format")
