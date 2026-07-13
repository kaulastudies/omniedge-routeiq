import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("routeiq_v172", ROOT / "agent.py")
AGENT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(AGENT)

from local.arithmetic import solve_arithmetic
from local.sentiment import solve_sentiment


class V172OptimizationTests(unittest.TestCase):
    def test_dynamic_completion_budget_is_used(self):
        tasks = [
            {"task_id": "f", "task_type": "factual knowledge", "prompt": "Capital of Japan?"},
            {"task_id": "m", "task_type": "mathematical reasoning", "prompt": "What is 2 + 2?"},
        ]
        captured = {}

        def fake_request(payload, api_key, url, deadline=None):
            captured.update(payload)
            content = json.dumps({"r": [{"i": 0, "a": "Tokyo"}, {"i": 1, "a": "4"}]})
            return {"choices": [{"message": {"content": content}}]}

        original = AGENT._perform_request
        AGENT._perform_request = fake_request
        AGENT.ACTIVE_DEADLINE = AGENT.time.monotonic() + 20
        try:
            answers = AGENT.request_batch(tasks, "minimax-m3", "mock", "https://example.invalid")
        finally:
            AGENT._perform_request = original
            AGENT.ACTIVE_DEADLINE = None

        self.assertEqual(answers, {"f": "Tokyo", "m": "4"})
        self.assertEqual(captured["max_tokens"], AGENT.completion_budget(tasks))
        self.assertLess(captured["max_tokens"], 4096)

    def test_safe_answer_normalization(self):
        self.assertEqual(AGENT.normalize_answer("The answer is: 42"), "42")
        self.assertEqual(AGENT.normalize_answer("Final answer - Tokyo"), "Tokyo")
        self.assertEqual(AGENT.normalize_answer("Sentiment: Positive."), "positive")
        self.assertEqual(AGENT.normalize_answer("42."), "42")
        self.assertEqual(AGENT.normalize_answer("result = 4"), "result = 4")

    def test_additional_strict_arithmetic_phrasings(self):
        cases = {
            "Find the value of 21 * 4": "84",
            "How much is (18 + 6) / 3?": "8",
            "Work out 29 % 6": "5",
            "Determine the value of 12.5% of 800": "100",
        }
        for prompt, expected in cases.items():
            with self.subTest(prompt=prompt):
                decision = solve_arithmetic(prompt)
                self.assertTrue(decision.accepted, decision.reason)
                self.assertEqual(decision.answer, expected)

    def test_additional_sentiment_prompt_formats(self):
        tasks = [
            {
                "task_type": "sentiment classification",
                "prompt": "Determine whether the following text is positive, negative, or neutral: The rollout was excellent.",
                "expected": "positive",
            },
            {
                "task_type": "sentiment classification",
                "prompt": "Label the sentiment as positive, negative, or neutral: The application crashed.",
                "expected": "negative",
            },
            {
                "task_type": "sentiment classification",
                "prompt": "What is the sentiment of the following statement: The opinion is neutral.",
                "expected": "neutral",
            },
        ]
        for task in tasks:
            expected = task.pop("expected")
            decision = solve_sentiment(task)
            self.assertTrue(decision.accepted, decision.reason)
            self.assertEqual(decision.answer, expected)


if __name__ == "__main__":
    unittest.main()
