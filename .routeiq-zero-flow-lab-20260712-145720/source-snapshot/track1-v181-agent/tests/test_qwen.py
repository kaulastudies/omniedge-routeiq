import unittest
from local.qwen import parse_qwen_results


class QwenParserTests(unittest.TestCase):
    def setUp(self):
        self.tasks = [
            {"task_id": "a", "prompt": "Capital of Japan?"},
            {"task_id": "b", "prompt": "2+2"},
            {"task_id": "c", "prompt": "Write code"},
        ]

    def test_ndjson(self):
        content = '{"i":"a","a":"Tokyo"}\n{"i":"b","a":"4"}'
        self.assertEqual(parse_qwen_results(content, self.tasks), {"a": "Tokyo", "b": "4"})

    def test_salvages_truncated_array(self):
        content = '[{"i":"a","a":"Tokyo"},{"i":"b","a":"4"},{"i":"c","a":"def broken'
        self.assertEqual(parse_qwen_results(content, self.tasks), {"a": "Tokyo", "b": "4"})

    def test_legacy_array(self):
        content = '[{"task_id":"a","answer":"Tokyo"}]'
        self.assertEqual(parse_qwen_results(content, self.tasks), {"a": "Tokyo"})


if __name__ == "__main__":
    unittest.main()
