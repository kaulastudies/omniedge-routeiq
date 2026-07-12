import unittest
from local.validation import validate_answer


class ValidationTests(unittest.TestCase):
    def test_two_sentences(self):
        task = {"prompt": "Summarize the passage in exactly two sentences: text"}
        self.assertTrue(validate_answer(task, "One sentence. Two sentence.")[0])
        self.assertFalse(validate_answer(task, "Only one sentence.")[0])

    def test_three_bullets_word_limit(self):
        task = {"prompt": "Summarize in exactly three bullet points, each no longer than 5 words: text"}
        valid = "- Flexible work improves balance\n- Collaboration challenges remain\n- Companies invest in tools"
        invalid = "- This bullet contains far too many words for the requested limit\n- Two\n- Three"
        self.assertTrue(validate_answer(task, valid)[0])
        self.assertFalse(validate_answer(task, invalid)[0])

    def test_python_syntax(self):
        task = {"prompt": "Write a Python function that returns the maximum."}
        self.assertTrue(validate_answer(task, "def get_max(values):\n    return max(values)")[0])
        self.assertFalse(validate_answer(task, "def get_max(values) return max(values)")[0])


if __name__ == "__main__":
    unittest.main()
