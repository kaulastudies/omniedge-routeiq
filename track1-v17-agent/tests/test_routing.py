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
    sys.path.insert(
        0,
        str(ROOT),
    )

    spec = importlib.util.spec_from_file_location(
        "routeiq_v11_agent",
        AGENT_PATH,
    )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


class GuardedRoutingTests(unittest.TestCase):
    def setUp(self):
        self.module = load_agent()

    def test_local_math_is_removed_from_remote_batch(self):
        tasks = [
            {
                "task_id": "math-1",
                "prompt": "What is 17 * 8?",
            },
            {
                "task_id": "fact-1",
                "prompt": "What is the capital of Australia?",
            },
            {
                "task_id": "explain-1",
                "prompt": "Explain why 2 + 2 equals 4.",
            },
        ]

        remote_calls = []

        def fake_call_batch(
            remote_tasks,
            models,
            api_key,
            url,
        ):
            remote_calls.append(
                [
                    str(task["task_id"])
                    for task in remote_tasks
                ]
            )

            return {
                "fact-1": "Canberra",
                "explain-1": (
                    "Because adding two units to two units "
                    "produces four units."
                ),
            }

        self.module.call_batch = fake_call_batch

        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)

            self.module.INPUT_PATH = (
                directory_path / "tasks.json"
            )

            self.module.OUTPUT_PATH = (
                directory_path / "results.json"
            )

            self.module.INPUT_PATH.write_text(
                json.dumps(tasks),
                encoding="utf-8",
            )

            os.environ["FIREWORKS_API_KEY"] = "mock-key"
            os.environ["FIREWORKS_BASE_URL"] = (
                "https://example.invalid/v1"
            )
            os.environ["ALLOWED_MODELS"] = json.dumps([
                "minimax-m3",
            ])

            status = self.module.main()

            results = json.loads(
                self.module.OUTPUT_PATH.read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(status, 0)

        self.assertEqual(
            remote_calls,
            [["fact-1", "explain-1"]],
        )

        self.assertEqual(
            results,
            [
                {
                    "task_id": "math-1",
                    "answer": "136",
                },
                {
                    "task_id": "fact-1",
                    "answer": "Canberra",
                },
                {
                    "task_id": "explain-1",
                    "answer": (
                        "Because adding two units to two units "
                        "produces four units."
                    ),
                },
            ],
        )

    def test_all_local_tasks_require_no_remote_configuration(self):
        tasks = [
            {
                "task_id": "math-1",
                "prompt": "What is 15% of 2400?",
            },
            {
                "task_id": "math-2",
                "task": {
                    "question": "Calculate (12 + 8) / 5",
                },
            },
        ]

        def forbidden_call(*args, **kwargs):
            raise AssertionError(
                "Remote inference must not be called"
            )

        self.module.call_batch = forbidden_call

        previous_environment = {
            name: os.environ.pop(name, None)
            for name in (
                "FIREWORKS_API_KEY",
                "FIREWORKS_BASE_URL",
                "ALLOWED_MODELS",
            )
        }

        try:
            with tempfile.TemporaryDirectory() as directory:
                directory_path = Path(directory)

                self.module.INPUT_PATH = (
                    directory_path / "tasks.json"
                )

                self.module.OUTPUT_PATH = (
                    directory_path / "results.json"
                )

                self.module.INPUT_PATH.write_text(
                    json.dumps(tasks),
                    encoding="utf-8",
                )

                status = self.module.main()

                results = json.loads(
                    self.module.OUTPUT_PATH.read_text(
                        encoding="utf-8"
                    )
                )

        finally:
            for name, value in previous_environment.items():
                if value is not None:
                    os.environ[name] = value

        self.assertEqual(status, 0)

        self.assertEqual(
            results,
            [
                {
                    "task_id": "math-1",
                    "answer": "360",
                },
                {
                    "task_id": "math-2",
                    "answer": "4",
                },
            ],
        )

    def test_ambiguous_multi_string_task_is_remote(self):
        task = {
            "task_id": "ambiguous-1",
            "title": "Arithmetic exercise",
            "description": "What is 5 + 6?",
        }

        text = self.module.task_text_for_local(task)

        self.assertEqual(text, "")

        local, unresolved = (
            self.module.resolve_local_tasks([task])
        )

        self.assertEqual(local, {})
        self.assertEqual(unresolved, [task])


if __name__ == "__main__":
    unittest.main()
