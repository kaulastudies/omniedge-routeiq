import random
import unittest
from fractions import Fraction

from local.arithmetic import (
    _format_fraction,
    solve_arithmetic,
)


class DirectArithmeticTests(unittest.TestCase):
    def test_known_expressions(self):
        cases = {
            "What is 17 * 8?": "136",
            "Calculate (12 + 8) / 5": "4",
            "Evaluate 2 ** 10": "1024",
            "Compute 29 % 6": "5",
            "₹2,400 + ₹600": "3000",
            "7 / 2": "3.5",
        }

        for text, expected in cases.items():
            with self.subTest(text=text):
                decision = solve_arithmetic(text)

                self.assertTrue(
                    decision.accepted,
                    decision.reason,
                )
                self.assertEqual(
                    decision.answer,
                    expected,
                )

    def test_random_integer_operations(self):
        generator = random.Random(42)

        operations = {
            "+": lambda a, b: Fraction(a + b),
            "-": lambda a, b: Fraction(a - b),
            "*": lambda a, b: Fraction(a * b),
            "/": lambda a, b: Fraction(a, b),
        }

        for _ in range(200):
            a = generator.randint(-5000, 5000)
            b = generator.randint(1, 5000)
            symbol = generator.choice(
                list(operations)
            )

            decision = solve_arithmetic(
                f"Calculate {a} {symbol} {b}"
            )

            expected = _format_fraction(
                operations[symbol](a, b)
            )

            self.assertTrue(
                decision.accepted,
                decision.reason,
            )
            self.assertEqual(
                decision.answer,
                expected,
            )


class PercentageTests(unittest.TestCase):
    def test_percentage_of(self):
        cases = {
            "What is 15% of 2400?": "360",
            "Calculate 12.5% of 800": "100",
            "Compute 7% of 350": "24.5",
        }

        for text, expected in cases.items():
            with self.subTest(text=text):
                decision = solve_arithmetic(text)

                self.assertTrue(
                    decision.accepted,
                    decision.reason,
                )
                self.assertEqual(
                    decision.answer,
                    expected,
                )

    def test_random_percentages(self):
        generator = random.Random(84)

        for _ in range(100):
            percentage = generator.randint(0, 100)
            base = generator.randint(1, 10000)

            decision = solve_arithmetic(
                f"What is {percentage}% of {base}?"
            )

            expected = _format_fraction(
                Fraction(
                    percentage * base,
                    100,
                )
            )

            self.assertTrue(
                decision.accepted,
                decision.reason,
            )
            self.assertEqual(
                decision.answer,
                expected,
            )

    def test_discount_then_tax(self):
        text = (
            "A store discounts a ₹2,400 product by 15%, "
            "then applies 18% GST to the discounted price."
        )

        decision = solve_arithmetic(text)

        self.assertTrue(
            decision.accepted,
            decision.reason,
        )
        self.assertEqual(
            decision.answer,
            "2407.2",
        )

    def test_single_percentage_change(self):
        cases = {
            "Increase 500 by 20%": "600",
            "Decrease 500 by 20%": "400",
            "A 2400 item is discounted by 15%": "2040",
        }

        for text, expected in cases.items():
            with self.subTest(text=text):
                decision = solve_arithmetic(text)

                self.assertTrue(
                    decision.accepted,
                    decision.reason,
                )
                self.assertEqual(
                    decision.answer,
                    expected,
                )


class RejectionTests(unittest.TestCase):
    def test_rejects_unsafe_or_ambiguous_tasks(self):
        rejected = [
            "What is 10 / 0?",
            "What is 2 ^ 8?",
            "Explain why 2 + 2 equals 4.",
            "Write code to calculate 5 + 6.",
            "A product has several discounts and taxes.",
            "Increase 500 by 20% and then by 10%.",
            "Discount 500 by 120%.",
            "__import__('os').system('echo unsafe')",
            "Some features are good, but others are terrible.",
        ]

        for text in rejected:
            with self.subTest(text=text):
                decision = solve_arithmetic(text)

                self.assertFalse(
                    decision.accepted,
                    (
                        f"Unexpectedly accepted {text!r}: "
                        f"{decision.answer}"
                    ),
                )


if __name__ == "__main__":
    unittest.main()
