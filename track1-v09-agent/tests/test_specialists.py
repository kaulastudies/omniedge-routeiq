#!/usr/bin/env python3

import unittest

from local.specialists import (
    solve_arithmetic,
    solve_sentiment,
)


class ArithmeticSpecialistTests(unittest.TestCase):
    def test_accepts_exact_expressions(self):
        cases = (
            (
                {"prompt": "17 * 8"},
                "136",
            ),
            (
                {"prompt": "What is 25 + 15?"},
                "40",
            ),
            (
                {"prompt": "Calculate (25 + 5) / 3."},
                "10",
            ),
            (
                {"prompt": "Evaluate 2^8."},
                "256",
            ),
            (
                {"input": "7.5 * 4"},
                "30",
            ),
            (
                {"question": "-8 + 3"},
                "-5",
            ),
            (
                {"query": "144 / 12"},
                "12",
            ),
            (
                {"prompt": "9 % 4"},
                "1",
            ),
        )

        for task, expected in cases:
            with self.subTest(task=task):
                decision = solve_arithmetic(task)

                self.assertTrue(decision.accepted)
                self.assertEqual(decision.answer, expected)

    def test_rejects_ambiguous_or_unsafe_math(self):
        cases = (
            {"prompt": "What is the capital of Australia?"},
            {
                "prompt": (
                    "John has 8 apples and gives 3 away. "
                    "How many remain?"
                )
            },
            {"prompt": "What is 2 + unknown?"},
            {
                "prompt": (
                    "__import__('os').system('id')"
                )
            },
            {"prompt": "Calculate 2^100."},
            {"prompt": "Calculate 8 / 0."},
            {"prompt": "Is 17 greater than 8?"},
        )

        for task in cases:
            with self.subTest(task=task):
                decision = solve_arithmetic(task)

                self.assertFalse(decision.accepted)
                self.assertIsNone(decision.answer)


class SentimentSpecialistTests(unittest.TestCase):
    def test_accepts_strong_positive_sentiment(self):
        cases = (
            "The product is excellent and I loved it.",
            "Absolutely fantastic service.",
            "I am delighted and highly satisfied.",
            "This was an amazing and enjoyable experience.",
        )

        for text in cases:
            task = {
                "instruction": (
                    "Classify the sentiment as positive "
                    "or negative."
                ),
                "input": text,
            }

            with self.subTest(text=text):
                decision = solve_sentiment(task)

                self.assertTrue(decision.accepted)
                self.assertEqual(
                    decision.answer,
                    "positive",
                )

    def test_accepts_strong_negative_sentiment(self):
        cases = (
            "This was terrible and disappointing.",
            "The device is broken and useless.",
            "Absolutely awful service. I want a refund.",
            "The worst experience, completely unacceptable.",
        )

        for text in cases:
            task = {
                "category": "sentiment",
                "instruction": "Classify this review.",
                "input": text,
            }

            with self.subTest(text=text):
                decision = solve_sentiment(task)

                self.assertTrue(decision.accepted)
                self.assertEqual(
                    decision.answer,
                    "negative",
                )

    def test_rejects_uncertain_sentiment(self):
        cases = (
            "The product arrived yesterday.",
            "Some features are good, but others are terrible.",
            "It is not excellent.",
            "It is not bad.",
            "Yeah right, totally great.",
            "The experience was okay.",
            "I used it twice.",
        )

        for text in cases:
            task = {
                "instruction": (
                    "Classify the sentiment as positive "
                    "or negative."
                ),
                "input": text,
            }

            with self.subTest(text=text):
                decision = solve_sentiment(task)

                self.assertFalse(decision.accepted)
                self.assertIsNone(decision.answer)

    def test_rejects_non_sentiment_task(self):
        decision = solve_sentiment({
            "instruction": "Summarize this review.",
            "input": "The product was excellent.",
        })

        self.assertFalse(decision.accepted)


if __name__ == "__main__":
    unittest.main()
