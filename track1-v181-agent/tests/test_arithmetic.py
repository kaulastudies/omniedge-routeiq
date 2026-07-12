import unittest
from local.arithmetic import solve_arithmetic


class ArithmeticTests(unittest.TestCase):
    def check(self, prompt, expected_parts):
        decision = solve_arithmetic(prompt)
        self.assertTrue(decision.accepted, decision.reason)
        for part in expected_parts:
            self.assertIn(part, decision.answer)

    def test_direct_and_percent(self):
        self.check("Calculate 18 * 7. Return only the number.", ["126"])
        self.check("What is 15% of 2400?", ["360"])

    def test_public_inventory(self):
        self.check(
            "A warehouse starts with 2,400 units. In Q1 it sells 37% of stock. "
            "In Q2 it restocks 800 units. In Q3 it sells 640 units. "
            "How many units remain at the end of Q3?",
            ["1672"],
        )

    def test_practice_inventory(self):
        self.check(
            "A store has 240 items. It sells 15% on Monday and 60 more on Tuesday. "
            "How many items remain?",
            ["144"],
        )

    def test_recipe_scaling(self):
        self.check(
            "A recipe requires 3/4 cup of sugar for 12 cookies. How much sugar is needed "
            "for 30 cookies? If sugar costs $2.40 per cup, what is the total cost of sugar "
            "for 30 cookies?",
            ["1.875", "4.5"],
        )

    def test_rejects_other_categories(self):
        self.assertFalse(solve_arithmetic("Write a Python function to add 2 + 2.").accepted)


if __name__ == "__main__":
    unittest.main()
