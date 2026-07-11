import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT_PATH = ROOT / "agent.py"


def load_agent():
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("routeiq_v13_agent", AGENT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RoutingTests(unittest.TestCase):
    def test_deterministic_and_qwen_reduce_remote(self):
        module = load_agent()
        tasks = [
            {"task_id": "math", "prompt": "A store has 240 items. It sells 15% on Monday and 60 more on Tuesday. How many items remain?"},
            {"task_id": "fact", "prompt": "What is the capital of Japan?"},
            {"task_id": "code", "prompt": "Write a Python function called add that returns a+b."},
        ]
        module.call_qwen_batch = lambda unresolved: {"fact": "Tokyo", "code": "bad code"}
        calls = []
        def fake_remote(remote_tasks, models, api_key, url):
            calls.append([str(t["task_id"]) for t in remote_tasks])
            return {"code": "def add(a, b):\n    return a + b"}
        module.call_batch = fake_remote
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            module.INPUT_PATH = root / "tasks.json"
            module.OUTPUT_PATH = root / "results.json"
            module.INPUT_PATH.write_text(json.dumps(tasks), encoding="utf-8")
            os.environ["FIREWORKS_API_KEY"] = "mock"
            os.environ["FIREWORKS_BASE_URL"] = "https://example.invalid/v1"
            os.environ["ALLOWED_MODELS"] = "minimax-m3"
            status = module.main()
            results = json.loads(module.OUTPUT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(status, 0)
        self.assertEqual(calls, [["code"]])
        self.assertEqual(results[0]["answer"], "144")
        self.assertEqual(results[1]["answer"], "Tokyo")
        self.assertIn("def add", results[2]["answer"])


if __name__ == "__main__":
    unittest.main()
