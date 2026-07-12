#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Callable


def words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def has_all(text: str, required: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return all(item.lower() in lowered for item in required)


def numeric(text: str, target: float, tolerance: float = 1e-6) -> bool:
    values = [float(value.replace(",", "")) for value in re.findall(r"-?\d[\d,]*(?:\.\d+)?", text)]
    return any(abs(value - target) <= tolerance for value in values)


def sentence_count(text: str) -> int:
    return len(re.findall(r"[^.!?\n]+[.!?](?:\s|$)", text.strip()))


def bullets(text: str) -> list[str]:
    result = []
    for line in text.splitlines():
        match = re.match(r"^\s*(?:[-*•]|\d+[.)])\s+(.+)$", line)
        if match:
            result.append(match.group(1).strip())
    return result


def extract_code(answer: str) -> str:
    fenced = re.search(r"```(?:python)?\s*(.*?)```", answer, flags=re.I | re.S)
    if fenced:
        return fenced.group(1).strip()
    index = answer.find("def ")
    return answer[index:].strip() if index != -1 else answer.strip()


def run_function(answer: str, names: tuple[str, ...], tests: Callable[[Callable], bool]) -> bool:
    code = extract_code(answer)
    try:
        ast.parse(code)
        namespace: dict[str, object] = {"__builtins__": {"max": max, "sorted": sorted, "set": set, "list": list, "len": len, "ValueError": ValueError}}
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
    lowered = answer.lower()
    if task_id == "T01":
        return has_all(answer, ("red", "green", "blue", "additive")) and ("pigment" in lowered or "subtractive" in lowered)
    if task_id == "T01b":
        return "subset" in lowered and "neural" in lowered and "feature" in lowered and "machine learning" in lowered
    if task_id == "T01c":
        return has_all(answer, ("ram", "rom", "volatile", "non-volatile")) and ("firmware" in lowered or "bios" in lowered) and ("temporary" in lowered or "active" in lowered)
    if task_id == "T02":
        return numeric(answer, 1672)
    if task_id == "T02b":
        return numeric(answer, 1.875, 0.01) and numeric(answer, 4.5, 0.01)
    if task_id == "M03":
        return numeric(answer, 144)
    if task_id == "M04":
        return numeric(answer, 2407.2, 0.01)
    if task_id in ("T03", "T03b"):
        label_ok = re.match(r"^(positive|neutral|mixed)\b", lowered) is not None
        negative_ok = any(term in lowered for term in ("late", "damaged", "dented", "missing", "packaging", "box"))
        positive_ok = any(term in lowered for term in ("worked", "perfect", "flawless", "resolved", "support", "setup", "set up"))
        return label_ok and negative_ok and positive_ok and sentence_count(answer) == 1
    if task_id == "S03":
        return re.match(r"^(neutral|mixed|positive)\b", lowered) is not None
    if task_id == "T04":
        opportunity = any(term in lowered for term in ("diagnosis", "medical images", "deterioration", "patient", "clinical"))
        challenge = any(term in lowered for term in ("privacy", "bias", "liability", "interpretability", "regulatory"))
        return sentence_count(answer) == 2 and opportunity and challenge
    if task_id == "T04b":
        lines = bullets(answer)
        if len(lines) != 3 or any(len(re.findall(r"\b[\w'-]+\b", line)) > 15 for line in lines):
            return False
        joined = " ".join(lines).lower()
        return any(term in joined for term in ("flexibility", "work-life", "commute")) and any(term in joined for term in ("collaboration", "culture", "boundaries")) and any(term in joined for term in ("tools", "office", "digital"))
    if task_id == "T05":
        pairs = (
            ("sundar pichai", "person"), ("march 15 2023", "date"), ("google", "organization"),
            ("zurich", "location"), ("eth zurich", "organization"),
        )
        return all(entity in lowered and label in lowered[lowered.find(entity):lowered.find(entity)+120] for entity, label in pairs)
    if task_id == "N02":
        return has_all(answer, ("Maria Sanchez", "PERSON", "Fireworks AI", "ORGANIZATION", "Berlin", "LOCATION", "last March", "DATE"))
    if task_id == "D01":
        return run_function(answer, ("get_max",), lambda fn: fn([1, 8, 3, 7]) == 8 and fn([-5, -2, -9]) == -2)
    if task_id == "L01":
        return "sam" in lowered and "cat" in lowered
    if task_id == "C01":
        def tests(fn: Callable) -> bool:
            return fn([5, 5, 3, 2]) == 3 and fn([1, 4, 2, 4, 3]) == 3
        return run_function(answer, ("second_largest", "second_largest_number", "find_second_largest"), tests)
    if task_id == "F04":
        return "canberra" in lowered and ("lake burley griffin" in lowered or "molonglo" in lowered)
    if task_id == "L02":
        return "ava" in lowered and "juice" in lowered
    return False


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: score_benchmark.py TASKS RESULTS RUNTIME_SECONDS", file=sys.stderr)
        return 2
    tasks_path, results_path, runtime_path = map(Path, sys.argv[1:])
    tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
    results = json.loads(results_path.read_text(encoding="utf-8"))
    runtime = float(runtime_path.read_text(encoding="utf-8").strip())
    result_map = {str(item.get("task_id")): str(item.get("answer", "")) for item in results if isinstance(item, dict)}
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
    print(f"BENCHMARK passed={len(passed)}/{len(tasks)} wrong={wrong} missing={missing} runtime={runtime:.2f}s")
    for task_id in wrong:
        preview = result_map.get(task_id, "").replace("\n", " ")[:500]
        print(f"WRONG {task_id}: {preview}")
    report = {
        "passed": len(passed), "total": len(tasks), "wrong": wrong,
        "missing": missing, "runtime_seconds": runtime,
    }
    (results_path.parent / "benchmark-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if wrong or missing or len(passed) != len(tasks) or runtime > 420:
        print("GATE FAILED: require 19/19 correct, zero missing answers, and runtime <=420s", file=sys.stderr)
        return 1
    print("GATE PASSED: 19/19 local answers; no Fireworks fallback required on this benchmark.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
