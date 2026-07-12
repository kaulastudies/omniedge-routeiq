#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Callable


def lowered(text: str) -> str:
    return text.lower().replace("organisation", "organization")


def has_all(text: str, terms: tuple[str, ...]) -> bool:
    value = lowered(text)
    return all(term.lower() in value for term in terms)


def has_any(text: str, terms: tuple[str, ...]) -> bool:
    value = lowered(text)
    return any(term.lower() in value for term in terms)


def numeric(text: str, target: float, tolerance: float = 0.02) -> bool:
    values = [
        float(value.replace(",", ""))
        for value in re.findall(r"-?\d[\d,]*(?:\.\d+)?", text)
    ]
    return any(abs(value - target) <= tolerance for value in values)


def sentence_count(text: str) -> int:
    return len(re.findall(r"[^.!?\n]+[.!?](?:\s|$)", text.strip()))


def bullet_lines(text: str) -> list[str]:
    output: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^\s*(?:[-*•]|\d+[.)])\s+(.+)$", line)
        if match:
            output.append(match.group(1).strip())
    return output


def extract_code(answer: str) -> str:
    fenced = re.search(r"```(?:python)?\s*(.*?)```", answer, flags=re.I | re.S)
    if fenced:
        return fenced.group(1).strip()
    index = answer.find("def ")
    return answer[index:].strip() if index >= 0 else answer.strip()


def run_function(answer: str, names: tuple[str, ...], tests: Callable[[Callable], bool]) -> bool:
    code = extract_code(answer)
    namespace: dict[str, object] = {
        "__builtins__": {
            "sum": sum,
            "sorted": sorted,
            "set": set,
            "list": list,
            "len": len,
            "ValueError": ValueError,
            "min": min,
            "max": max,
        }
    }
    try:
        ast.parse(code)
        exec(code, namespace, namespace)
    except Exception:
        return False
    function = next((namespace.get(name) for name in names if callable(namespace.get(name))), None)
    if not callable(function):
        function = next((value for value in namespace.values() if callable(value)), None)
    if not callable(function):
        return False
    try:
        return bool(tests(function))
    except Exception:
        return False


def check(task_id: str, answer: str) -> bool:
    value = lowered(answer)

    if task_id == "X01":
        return (
            has_all(answer, ("tcp", "udp"))
            and has_any(answer, ("connection-oriented", "connection oriented", "handshake"))
            and has_any(answer, ("connectionless", "no connection", "without a connection"))
            and has_any(answer, ("reliable", "reliability", "ordered"))
            and has_any(answer, ("stream", "web", "file", "video", "gaming", "dns", "voice"))
        )
    if task_id == "X01b":
        return has_all(answer, ("carbon dioxide", "water", "oxygen")) and has_any(answer, ("glucose", "sugar"))
    if task_id == "X01c":
        return (
            has_all(answer, ("ssd", "hdd"))
            and has_any(answer, ("flash", "solid-state", "solid state"))
            and has_any(answer, ("magnetic", "spinning", "disk", "platter"))
            and has_any(answer, ("faster", "speed", "durable", "no moving parts"))
        )
    if task_id == "X02":
        return numeric(answer, 2250)
    if task_id == "X02b":
        quantity_ok = numeric(answer, 1.666666, 0.03) or "5/3" in answer or "1 2/3" in answer
        return quantity_ok and numeric(answer, 5.0, 0.02)
    if task_id == "X03":
        return numeric(answer, 335)
    if task_id == "X04":
        return numeric(answer, 1612.8, 0.03)
    if task_id in {"X05", "X05b"}:
        label_ok = re.match(r"^(mixed|positive|neutral)\b", value) is not None
        positive_ok = has_any(answer, ("excellent", "performs", "support", "replaced", "fast", "sharp", "camera"))
        negative_ok = has_any(answer, ("late", "torn", "missing", "battery", "drains", "although", "but"))
        return label_ok and positive_ok and negative_ok and sentence_count(answer) == 1
    if task_id == "X05c":
        return re.match(r"^(mixed|neutral|positive)\b", value) is not None
    if task_id == "X06":
        opportunity = has_any(answer, ("disease", "yield", "water", "productivity", "waste"))
        challenge = has_any(answer, ("cost", "connectivity", "language", "data", "ownership"))
        return sentence_count(answer) == 2 and opportunity and challenge
    if task_id == "X06b":
        bullets = bullet_lines(answer)
        if len(bullets) != 3:
            return False
        if any(len(re.findall(r"\b[\w'-]+\b", bullet)) > 15 for bullet in bullets):
            return False
        joined = " ".join(bullets)
        return (
            has_any(joined, ("access", "schedule", "cost", "travel"))
            and has_any(joined, ("engagement", "internet", "practice"))
            and has_any(joined, ("platform", "mentoring", "hybrid"))
        )
    if task_id == "X07":
        pairs = (
            ("satya nadella", "person"),
            ("microsoft", "organization"),
            ("london", "location"),
            ("university college london", "organization"),
            ("april 8 2024", "date"),
        )
        entities_ok = all(entity in value and label in value[value.find(entity):value.find(entity) + 140] for entity, label in pairs[:-1])
        date_ok = re.search(r"april\s+8[,]?\s+2024", value) is not None and "date" in value
        return entities_ok and date_ok
    if task_id == "X07b":
        return has_all(answer, ("Aisha Khan", "PERSON", "Anthropic", "ORGANIZATION", "Singapore", "LOCATION", "last Tuesday", "DATE"))
    if task_id == "X08":
        return run_function(answer, ("total", "sum_list", "list_sum"), lambda fn: fn([1, 2, 3, 4]) == 10 and fn([-2, 5]) == 3 and fn([]) == 0)
    if task_id == "X09":
        return "noah" in value and "dog" in value
    if task_id == "X10":
        def tests(fn: Callable) -> bool:
            return fn([4, 1, 1, 3, 2]) == 2 and fn([9, 9, 5, 7, 5]) == 7
        return run_function(answer, ("second_smallest", "find_second_smallest", "second_smallest_number"), tests)
    if task_id == "X11":
        return "ottawa" in value and "ottawa river" in value
    if task_id == "X12":
        return "ira" in value and "fruit" in value
    return False


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: score_shadow.py TASKS RESULTS RUNTIME_SECONDS", file=sys.stderr)
        return 2

    tasks_path, results_path, runtime_path = map(Path, sys.argv[1:])
    tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
    results = json.loads(results_path.read_text(encoding="utf-8"))
    runtime = float(runtime_path.read_text(encoding="utf-8").strip())

    if isinstance(results, dict) and isinstance(results.get("results"), list):
        results = results["results"]

    result_map = {
        str(item.get("task_id", item.get("id", ""))): str(item.get("answer", ""))
        for item in results
        if isinstance(item, dict)
    }

    passed: list[str] = []
    wrong: list[str] = []
    missing: list[str] = []

    for task in tasks:
        task_id = str(task["task_id"])
        answer = result_map.get(task_id, "").strip()
        if not answer:
            missing.append(task_id)
        elif check(task_id, answer):
            passed.append(task_id)
        else:
            wrong.append(task_id)

    accuracy = 100.0 * len(passed) / len(tasks)
    print(
        f"SHADOW passed={len(passed)}/{len(tasks)} accuracy={accuracy:.1f}% "
        f"wrong={wrong} missing={missing} runtime={runtime:.2f}s"
    )
    for task_id in wrong:
        preview = result_map.get(task_id, "").replace("\n", " ")[:500]
        print(f"WRONG {task_id}: {preview}")

    report = {
        "passed": len(passed),
        "total": len(tasks),
        "accuracy": accuracy,
        "wrong": wrong,
        "missing": missing,
        "runtime_seconds": runtime,
    }
    (results_path.parent / "benchmark-report.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    return 0 if not wrong and not missing and runtime <= 420 else 1


if __name__ == "__main__":
    raise SystemExit(main())
