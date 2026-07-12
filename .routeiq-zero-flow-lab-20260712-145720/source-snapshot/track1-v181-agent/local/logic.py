from __future__ import annotations

import itertools
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LogicDecision:
    accepted: bool
    answer: str = ""
    reason: str = ""


def _reject(reason: str) -> LogicDecision:
    return LogicDecision(False, reason=reason)


def _accept(answer: str, reason: str) -> LogicDecision:
    return LogicDecision(True, answer.strip(), reason)


def _split_list(value: str) -> list[str]:
    value = re.sub(r"\s+and\s+", ", ", value, flags=re.I)
    return [item.strip(" .") for item in value.split(",") if item.strip(" .")]


def _normal_item(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower().strip(" .?!'\""))


def solve_logic(text: str) -> LogicDecision:
    if not isinstance(text, str) or not text.strip():
        return _reject("logic task text is empty")
    if "who" not in text.lower() or "different" not in text.lower():
        return _reject("no supported assignment-puzzle signature")

    names_match = re.search(
        r"(?:friends|people|students|colleagues|children|players)\s*,?\s*"
        r"([A-Z][a-z]+(?:\s*,\s*[A-Z][a-z]+)*(?:\s*,?\s*and\s+[A-Z][a-z]+))"
        r"\s*,?\s*each",
        text,
    )
    items_match = re.search(
        r"different\s+(?:pet|pets|drink|drinks|color|colors|job|jobs|book|books|item|items|option|options)\s*:\s*"
        r"([^.!?]+)",
        text,
        flags=re.I,
    )
    query_match = re.search(
        r"who\s+(owns?|has|chose|chooses|picked|selects?)\s+(?:the\s+)?([^?]+)\?",
        text,
        flags=re.I,
    )
    if not names_match or not items_match or not query_match:
        return _reject("assignment puzzle could not be parsed confidently")

    names = _split_list(names_match.group(1))
    items = [_normal_item(item) for item in _split_list(items_match.group(1))]
    query_verb = query_match.group(1).lower()
    target = _normal_item(query_match.group(2))

    if len(names) < 2 or len(names) != len(items) or target not in items or len(names) > 7:
        return _reject("assignment puzzle dimensions are unsupported")

    positive: list[tuple[str, str]] = []
    negative: list[tuple[str, str]] = []
    name_pattern = "|".join(re.escape(name) for name in names)
    item_pattern = "|".join(re.escape(item) for item in sorted(items, key=len, reverse=True))

    for match in re.finditer(
        rf"\b({name_pattern})\b\s+(?:does\s+not|doesn't|did\s+not|didn't)\s+"
        rf"(?:own|have|choose|chose|pick|select)\s+(?:the\s+)?({item_pattern})\b",
        text,
        flags=re.I,
    ):
        negative.append((match.group(1).lower(), _normal_item(match.group(2))))

    for match in re.finditer(
        rf"\b({name_pattern})\b\s+(?:owns?|has|chose|chooses|picked|selects?)\s+"
        rf"(?:the\s+)?({item_pattern})\b",
        text,
        flags=re.I,
    ):
        positive.append((match.group(1).lower(), _normal_item(match.group(2))))

    if not positive and not negative:
        return _reject("assignment puzzle contained no parseable constraints")

    solutions: list[dict[str, str]] = []
    for permutation in itertools.permutations(items):
        assignment = {names[index].lower(): permutation[index] for index in range(len(names))}
        if any(assignment.get(name) != item for name, item in positive):
            continue
        if any(assignment.get(name) == item for name, item in negative):
            continue
        solutions.append(assignment)

    owners = {
        next(name for name, item in solution.items() if item == target)
        for solution in solutions
    }
    if len(owners) != 1:
        return _reject("assignment puzzle did not produce a unique owner")

    owner_lower = next(iter(owners))
    owner = next(name for name in names if name.lower() == owner_lower)
    verb = "owns"
    if query_verb in {"chose", "chooses", "picked", "selects"}:
        verb = "chose"
    elif query_verb == "has":
        verb = "has"
    return _accept(f"{owner} {verb} the {target}.", "uniquely solved assignment puzzle")
