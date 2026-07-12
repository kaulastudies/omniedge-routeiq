import unittest

from local.qwen import (
    clean_qwen_output,
    parse_qwen_results,
)


class QwenParserTests(unittest.TestCase):
    def setUp(self):
        self.tasks = [
            {
                "task_id": "fact-1",
                "prompt": "Capital of Japan?",
            },
            {
                "task_id": "math-1",
                "prompt": "2 + 2",
            },
        ]

    def test_removes_reasoning_and_end_marker(self):
        content = (
            "<think>hidden reasoning</think>"
            '[{"task_id":"fact-1","answer":"Tokyo"}]'
            "[end of text]"
        )

        cleaned = clean_qwen_output(content)

        self.assertNotIn(
            "<think>",
            cleaned,
        )

        self.assertNotIn(
            "[end of text]",
            cleaned,
        )

    def test_parses_valid_answers(self):
        content = (
            "```json\n"
            "["
            '{"task_id":"fact-1","answer":"Tokyo"},'
            '{"task_id":"math-1","answer":4}'
            "]"
            "\n```"
        )

        answers = parse_qwen_results(
            content,
            self.tasks,
        )

        self.assertEqual(
            answers,
            {
                "fact-1": "Tokyo",
                "math-1": "4",
            },
        )

    def test_ignores_unknown_ids(self):
        content = (
            "["
            '{"task_id":"unknown","answer":"bad"},'
            '{"task_id":"fact-1","answer":"Tokyo"}'
            "]"
        )

        answers = parse_qwen_results(
            content,
            self.tasks,
        )

        self.assertEqual(
            answers,
            {
                "fact-1": "Tokyo",
            },
        )


if __name__ == "__main__":
    unittest.main()
