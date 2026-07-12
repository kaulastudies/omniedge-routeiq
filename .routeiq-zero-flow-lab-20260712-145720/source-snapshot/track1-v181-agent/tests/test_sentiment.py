import unittest
from local.sentiment import solve_sentiment


class SentimentTests(unittest.TestCase):
    def test_simple(self):
        task = {
            "prompt": "Classify as positive, negative, or neutral: The service was excellent.",
        }
        decision = solve_sentiment(task)
        self.assertTrue(decision.accepted, decision.reason)
        self.assertTrue(decision.answer.lower().startswith("positive"))

    def test_public_mixed_negative_then_positive(self):
        task = {
            "task_type": "sentiment_classification",
            "prompt": (
                "Classify the sentiment of this customer review as Positive, Negative, or Neutral "
                "and give a one-sentence reason: 'The product arrived two days late and the packaging "
                "was damaged, but the item worked perfectly and customer support resolved my complaint "
                "within an hour.'"
            ),
        }
        decision = solve_sentiment(task)
        self.assertTrue(decision.accepted, decision.reason)
        self.assertRegex(decision.answer, r"^(Positive|Neutral|Mixed)")
        self.assertIn("late", decision.answer.lower())
        self.assertIn("worked", decision.answer.lower())

    def test_practice_mixed_positive_then_negative(self):
        task = {
            "prompt": "Classify the sentiment of this review: The battery life is great, but the screen scratches too easily.",
        }
        decision = solve_sentiment(task)
        self.assertTrue(decision.accepted, decision.reason)
        self.assertTrue(decision.answer.lower().startswith("neutral"))


if __name__ == "__main__":
    unittest.main()
