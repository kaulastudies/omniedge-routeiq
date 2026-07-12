import unittest
from local.logic import solve_logic


class LogicTests(unittest.TestCase):
    def test_practice_assignment(self):
        decision = solve_logic(
            "Three friends, Sam, Jo, and Lee, each own a different pet: cat, dog, bird. "
            "Sam does not own the bird. Jo owns the dog. Who owns the cat?"
        )
        self.assertTrue(decision.accepted, decision.reason)
        self.assertEqual(decision.answer, "Sam owns the cat.")

    def test_variant(self):
        decision = solve_logic(
            "Three students, Ava, Ben, and Cara, each chose a different drink: tea, coffee, juice. "
            "Ava did not choose tea. Ben chose coffee. Cara chose tea. Who chose juice?"
        )
        self.assertTrue(decision.accepted, decision.reason)
        self.assertEqual(decision.answer, "Ava chose the juice.")


if __name__ == "__main__":
    unittest.main()
