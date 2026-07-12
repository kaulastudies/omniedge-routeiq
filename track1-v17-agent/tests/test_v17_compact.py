import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("routeiq_v17", ROOT / "agent.py")
AGENT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(AGENT)


class CompactProtocolTests(unittest.TestCase):
    def test_compact_payload_preserves_meaning(self):
        tasks = [{"task_id": "abc", "task_type": "factual knowledge", "prompt": "Capital of Japan?"}]
        payload = json.loads(AGENT.compact_tasks(tasks))
        self.assertEqual(payload, [[0, {"t": "factual knowledge", "p": "Capital of Japan?"}]])

    def test_parse_pair_wrapper(self):
        tasks = [{"task_id": "a"}, {"task_id": "b"}]
        parsed = AGENT.parse_batch_results('{"r":[[0,"one"],[1,"two"]]}', tasks)
        self.assertEqual(parsed, {"a": "one", "b": "two"})

    def test_parse_legacy_objects(self):
        tasks = [{"task_id": "a"}]
        parsed = AGENT.parse_batch_results('[{"task_id":"a","answer":"one"}]', tasks)
        self.assertEqual(parsed, {"a": "one"})

    def test_completion_budget(self):
        tasks = [{"task_type": "factual knowledge", "prompt": "A?"}]
        self.assertEqual(AGENT.completion_budget(tasks), 160)

    def test_exact_bullet_validation(self):
        task = {"prompt": "Return exactly 3 bullets, at most 4 words each."}
        valid, _ = AGENT.validate_answer(task, "- One short line\n- Two short line\n- Three short line")
        self.assertTrue(valid)
        valid, _ = AGENT.validate_answer(task, "- One\n- Two")
        self.assertFalse(valid)

    def test_python_syntax_validation(self):
        task = {"task_type": "code generation", "prompt": "Write Python code."}
        self.assertTrue(AGENT.validate_answer(task, "def f():\n    return 1")[0])
        self.assertFalse(AGENT.validate_answer(task, "def f(:")[0])


class RoutingTests(unittest.TestCase):
    def test_local_tasks_do_not_need_remote(self):
        tasks = [
            {"task_id": "m", "task_type": "mathematical reasoning", "prompt": "Calculate 8 * 7."},
            {"task_id": "s", "task_type": "sentiment classification", "prompt": "Classify as positive, negative, or neutral: The result was excellent."},
        ]
        local, unresolved = AGENT.resolve_local_tasks(tasks)
        self.assertEqual(local, {"m": "56", "s": "positive"})
        self.assertEqual(unresolved, [])

    def test_one_compact_remote_batch(self):
        tasks = [
            {"task_id": "m", "task_type": "mathematical reasoning", "prompt": "Calculate 8 * 7."},
            {"task_id": "f", "task_type": "factual knowledge", "prompt": "Capital of Japan?"},
        ]
        calls = []
        def fake_call(remote_tasks, models, api_key, url, repair_reasons=None):
            calls.append([task["task_id"] for task in remote_tasks])
            return {"f": "Tokyo"}
        AGENT.call_batch = fake_call
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            AGENT.INPUT_PATH = root / "tasks.json"
            AGENT.OUTPUT_PATH = root / "results.json"
            AGENT.INPUT_PATH.write_text(json.dumps(tasks), encoding="utf-8")
            previous = {key: os.environ.get(key) for key in ("ALLOWED_MODELS", "FIREWORKS_BASE_URL", "FIREWORKS_API_KEY")}
            os.environ["ALLOWED_MODELS"] = '["minimax-m3"]'
            os.environ["FIREWORKS_BASE_URL"] = "https://example.invalid/v1"
            os.environ["FIREWORKS_API_KEY"] = "x"
            try:
                status = AGENT.main()
            finally:
                for key, value in previous.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
            self.assertEqual(status, 0)
            self.assertEqual(calls, [["f"]])
            self.assertEqual(json.loads(AGENT.OUTPUT_PATH.read_text()), [
                {"task_id": "m", "answer": "56"},
                {"task_id": "f", "answer": "Tokyo"},
            ])


if __name__ == "__main__":
    unittest.main()
