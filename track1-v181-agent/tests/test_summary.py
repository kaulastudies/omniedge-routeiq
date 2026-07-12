import unittest

from local.summary import solve_summary
from local.validation import validate_answer


class SummaryTests(unittest.TestCase):
    def test_two_sentence_opportunity_and_challenge(self):
        task = {
            "task_id": "T04",
            "task_type": "text_summarization",
            "prompt": "Summarize the following passage in exactly two sentences, covering both opportunities and challenges: 'AI systems help doctors analyse images and predict deterioration. They can improve diagnosis and patient monitoring. However, privacy, bias, liability, and interpretability remain serious concerns. Regulators are still developing suitable frameworks.'",
        }
        decision = solve_summary(task)
        self.assertTrue(decision.accepted, decision.reason)
        valid, reason = validate_answer(task, decision.answer)
        self.assertTrue(valid, reason)
        self.assertTrue(any(term in decision.answer.lower() for term in ("help", "improve", "diagnosis")))
        self.assertIn("concerns", decision.answer.lower())

    def test_three_bullets_word_limit(self):
        task = {
            "task_id": "T04b",
            "task_type": "text_summarization",
            "prompt": "Summarize the following passage in exactly three bullet points, each no longer than 15 words: 'Remote work has transformed company operations. Employees gain flexibility and reduced commute times. However, collaboration, culture, and boundaries remain challenges. Organisations respond by investing in digital tools and rethinking office space.'",
        }
        decision = solve_summary(task)
        self.assertTrue(decision.accepted, decision.reason)
        valid, reason = validate_answer(task, decision.answer)
        self.assertTrue(valid, reason)
        self.assertEqual(3, len(decision.answer.splitlines()))


if __name__ == "__main__":
    unittest.main()
