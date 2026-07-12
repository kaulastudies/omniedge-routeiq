import unittest

from local.sentiment import solve_sentiment


class OfficialSampleTests(unittest.TestCase):
    def test_official_visible_sample(self):
        task = {
            "task_id": "sentiment-001",
            "task_type": "sentiment classification",
            "prompt": (
                "Classify as positive, negative, or neutral: "
                "The deployment completed successfully."
            ),
        }

        decision = solve_sentiment(task)

        self.assertTrue(
            decision.accepted,
            decision.reason,
        )
        self.assertEqual(
            decision.answer,
            "positive",
        )


class PositiveSentimentTests(unittest.TestCase):
    def test_strong_positive_cases(self):
        statements = [
            "The service was excellent.",
            "I loved the final result.",
            "The rollout was smooth and successful.",
            "The customer is very satisfied.",
            "This was an outstanding experience.",
        ]

        for statement in statements:
            with self.subTest(statement=statement):
                task = {
                    "task_type": "sentiment classification",
                    "prompt": (
                        "Classify as positive, negative, or neutral: "
                        + statement
                    ),
                }

                decision = solve_sentiment(task)

                self.assertTrue(
                    decision.accepted,
                    decision.reason,
                )
                self.assertEqual(
                    decision.answer,
                    "positive",
                )


class NegativeSentimentTests(unittest.TestCase):
    def test_strong_negative_cases(self):
        statements = [
            "The deployment failed.",
            "The experience was terrible.",
            "The customer was disappointed.",
            "The application crashed.",
            "This is the worst result.",
        ]

        for statement in statements:
            with self.subTest(statement=statement):
                task = {
                    "task_type": "sentiment classification",
                    "prompt": (
                        "Classify as positive, negative, or neutral: "
                        + statement
                    ),
                }

                decision = solve_sentiment(task)

                self.assertTrue(
                    decision.accepted,
                    decision.reason,
                )
                self.assertEqual(
                    decision.answer,
                    "negative",
                )


class NeutralSentimentTests(unittest.TestCase):
    def test_explicit_neutral_cases(self):
        statements = [
            "The opinion is neutral.",
            "It was neither good nor bad.",
            "The experience was average.",
            "There is no strong opinion.",
        ]

        for statement in statements:
            with self.subTest(statement=statement):
                task = {
                    "task_type": "sentiment classification",
                    "prompt": (
                        "Classify as positive, negative, or neutral: "
                        + statement
                    ),
                }

                decision = solve_sentiment(task)

                self.assertTrue(
                    decision.accepted,
                    decision.reason,
                )
                self.assertEqual(
                    decision.answer,
                    "neutral",
                )


class RejectionTests(unittest.TestCase):
    def test_rejects_uncertain_cases(self):
        tasks = [
            {
                "task_type": "sentiment classification",
                "prompt": (
                    "Classify as positive, negative, or neutral: "
                    "Some features are good, but others are terrible."
                ),
            },
            {
                "task_type": "sentiment classification",
                "prompt": (
                    "Classify as positive, negative, or neutral: "
                    "The deployment was not successful."
                ),
            },
            {
                "task_type": "sentiment classification",
                "prompt": (
                    "Classify as positive, negative, or neutral: "
                    "Yeah right, that was excellent."
                ),
            },
            {
                "task_type": "sentiment classification",
                "prompt": (
                    "Classify as positive, negative, or neutral: "
                    "The meeting starts at 3 PM."
                ),
            },
            {
                "task_type": "factual knowledge",
                "prompt": (
                    "Classify as positive, negative, or neutral: "
                    "The service was excellent."
                ),
            },
            {
                "task_type": "sentiment classification",
                "prompt": "What is the capital of Japan?",
            },
        ]

        for task in tasks:
            with self.subTest(task=task):
                decision = solve_sentiment(task)

                self.assertFalse(
                    decision.accepted,
                    (
                        f"Unexpectedly accepted: "
                        f"{decision.answer}"
                    ),
                )


if __name__ == "__main__":
    unittest.main()
