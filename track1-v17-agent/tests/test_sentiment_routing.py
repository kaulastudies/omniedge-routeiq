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

    spec = importlib.util.spec_from_file_location(
        "routeiq_v11_sentiment_agent",
        AGENT_PATH,
    )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


class SentimentRoutingTests(unittest.TestCase):
    def setUp(self):
        self.module = load_agent()

    def test_math_and_sentiment_bypass_remote(self):
        tasks = [
            {
                "task_id": "math-001",
                "task_type": "mathematical reasoning",
                "prompt": (
                    "Calculate 18 * 7. "
                    "Return only the number."
                ),
            },
            {
                "task_id": "sentiment-001",
                "task_type": "sentiment classification",
                "prompt": (
                    "Classify as positive, negative, "
                    "or neutral: "
                    "The deployment completed successfully."
                ),
            },
            {
                "task_id": "fact-001",
                "task_type": "factual knowledge",
                "prompt": (
                    "What is the capital of Japan?"
                ),
            },
        ]

        remote_calls = []

        def fake_call_batch(
            remote_tasks,
            models,
            api_key,
            url,
        ):
            remote_calls.append([
                str(task["task_id"])
                for task in remote_tasks
            ])

            return {
                "fact-001": "Tokyo",
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
            [["fact-001"]],
        )

        self.assertEqual(
            results,
            [
                {
                    "task_id": "math-001",
                    "answer": "126",
                },
                {
                    "task_id": "sentiment-001",
                    "answer": "positive",
                },
                {
                    "task_id": "fact-001",
                    "answer": "Tokyo",
                },
            ],
        )

    def test_all_local_requires_no_api_key(self):
        tasks = [
            {
                "task_id": "math-001",
                "task_type": "mathematical reasoning",
                "prompt": "Calculate 9 * 9.",
            },
            {
                "task_id": "sentiment-001",
                "task_type": "sentiment classification",
                "prompt": (
                    "Classify as positive, negative, "
                    "or neutral: "
                    "The application crashed."
                ),
            },
        ]

        def forbidden_remote_call(*args, **kwargs):
            raise AssertionError(
                "Remote inference must not be called"
            )

        self.module.call_batch = forbidden_remote_call

        previous = {
            key: os.environ.pop(key, None)
            for key in (
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
            for key, value in previous.items():
                if value is not None:
                    os.environ[key] = value

        self.assertEqual(status, 0)

        self.assertEqual(
            results,
            [
                {
                    "task_id": "math-001",
                    "answer": "81",
                },
                {
                    "task_id": "sentiment-001",
                    "answer": "negative",
                },
            ],
        )

    def test_mixed_sentiment_remains_remote(self):
        task = {
            "task_id": "mixed-001",
            "task_type": "sentiment classification",
            "prompt": (
                "Classify as positive, negative, "
                "or neutral: "
                "Some features are good, "
                "but others are terrible."
            ),
        }

        local, unresolved = (
            self.module.resolve_local_tasks([task])
        )

        self.assertEqual(local, {})
        self.assertEqual(unresolved, [task])


if __name__ == "__main__":
    unittest.main()
