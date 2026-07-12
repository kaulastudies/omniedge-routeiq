import unittest
from local.ner import solve_ner


class NerTests(unittest.TestCase):
    def test_public_ner(self):
        prompt = (
            "Extract all named entities from the following text and label each as PERSON, ORGANIZATION, LOCATION, or DATE: "
            "'On March 15 2023, Sundar Pichai announced that Google would open a new AI research lab in Zurich, "
            "partnering with ETH Zurich to focus on large language model safety.'"
        )
        decision = solve_ner(prompt)
        self.assertTrue(decision.accepted, decision.reason)
        for value in ("March 15 2023", "Sundar Pichai", "Google", "Zurich", "ETH Zurich"):
            self.assertIn(value, decision.answer)

    def test_practice_ner(self):
        prompt = "Extract all named entities and their types from: Maria Sanchez joined Fireworks AI in Berlin last March."
        decision = solve_ner(prompt)
        self.assertTrue(decision.accepted, decision.reason)
        for value in ("Maria Sanchez", "Fireworks AI", "Berlin", "last March"):
            self.assertIn(value, decision.answer)


if __name__ == "__main__":
    unittest.main()
