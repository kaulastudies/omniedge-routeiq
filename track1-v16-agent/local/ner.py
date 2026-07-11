from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class NerDecision:
    accepted: bool
    answer: str = ""
    reason: str = ""


MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)
ORG_SUFFIXES = (
    "University", "Institute", "Laboratory", "Laboratories", "Labs",
    "Corporation", "Corp", "Inc", "Ltd", "LLC", "Foundation", "College",
)


def _reject(reason: str) -> NerDecision:
    return NerDecision(False, reason=reason)


def _accept(answer: str, reason: str) -> NerDecision:
    return NerDecision(True, answer.strip(), reason)


def _add(entities: list[tuple[str, str]], value: str, label: str) -> None:
    value = re.sub(r"\s+", " ", value.strip(" ,.'\""))
    if not value:
        return
    pair = (value, label)
    if pair not in entities:
        entities.append(pair)


def solve_ner(text: str) -> NerDecision:
    if not isinstance(text, str) or not text.strip():
        return _reject("NER task text is empty")
    lowered = text.lower()
    if "named entit" not in lowered and not ("extract" in lowered and "label" in lowered):
        return _reject("task is not recognizably named-entity extraction")

    quoted = re.search(r"['\"](.+?)['\"]\s*$", text, flags=re.DOTALL)
    source = quoted.group(1) if quoted else text.split(":", 1)[-1]
    entities: list[tuple[str, str]] = []

    month_pattern = "|".join(MONTHS)
    for match in re.finditer(
        rf"\b(?:{month_pattern})\s+\d{{1,2}}(?:,)?\s+\d{{4}}\b|\b(?:last|next|this)\s+(?:{month_pattern})\b",
        source,
        flags=re.I,
    ):
        _add(entities, match.group(0), "DATE")

    for match in re.finditer(
        r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s+"
        r"(?:announced|joined|said|stated|founded|visited|met|became|presented)\b",
        source,
    ):
        _add(entities, match.group(1), "PERSON")

    org_patterns = (
        r"\bjoined\s+([A-Z][A-Za-z0-9&.-]*(?:\s+[A-Z][A-Za-z0-9&.-]*){0,3})(?=\s+in\b|\s+at\b|[,.])",
        r"\bannounced\s+that\s+([A-Z][A-Za-z0-9&.-]*(?:\s+[A-Z][A-Za-z0-9&.-]*){0,3})(?=\s+(?:would|will|is|was)\b)",
        r"\bpartnering\s+with\s+([A-Z][A-Za-z0-9&.-]*(?:\s+[A-Z][A-Za-z0-9&.-]*){0,3})(?=\s+to\b|[,.])",
        r"\b(?:at|for)\s+([A-Z][A-Za-z0-9&.-]*(?:\s+[A-Z][A-Za-z0-9&.-]*){0,3})(?=\s+in\b|[,.])",
    )
    for pattern in org_patterns:
        for match in re.finditer(pattern, source):
            _add(entities, match.group(1), "ORGANIZATION")

    for match in re.finditer(
        r"\b([A-Z][A-Za-z0-9&.-]*(?:\s+[A-Z][A-Za-z0-9&.-]*){0,3})\b",
        source,
    ):
        candidate = match.group(1)
        if any(candidate.endswith(suffix) for suffix in ORG_SUFFIXES):
            _add(entities, candidate, "ORGANIZATION")

    org_values = {value for value, label in entities if label == "ORGANIZATION"}
    date_values = {value for value, label in entities if label == "DATE"}
    for match in re.finditer(
        r"\b(?:in|near|from|to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})(?=\s*,|\s+on\b|\s+last\b|\s+next\b|\s+to\b|[.])",
        source,
    ):
        candidate = match.group(1).strip()
        if candidate not in org_values and candidate not in date_values:
            _add(entities, candidate, "LOCATION")

    labels = {label for _, label in entities}
    if not {"PERSON", "ORGANIZATION", "LOCATION"}.issubset(labels):
        return _reject("NER pattern lacked a complete high-confidence entity set")

    # Dates are optional in general, but when the source visibly contains a month,
    # require it to have been captured before accepting locally.
    if re.search(rf"\b(?:{month_pattern})\b", source, flags=re.I) and "DATE" not in labels:
        return _reject("month-like date was not captured")

    answer = "\n".join(f"{value} — {label}" for value, label in entities)
    return _accept(answer, "high-confidence contextual NER pattern")
