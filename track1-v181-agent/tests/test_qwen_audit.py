import json
import os
import unittest
from unittest.mock import patch

from local.qwen import call_qwen_audit


class _Done:
    returncode = 0
    stderr = ""
    stdout = json.dumps({"i": "f", "a": "Corrected answer"})


class AuditTests(unittest.TestCase):
    @patch("local.qwen.subprocess.run", return_value=_Done())
    def test_audit_recovers_corrected_answer(self, run):
        with patch.dict(os.environ, {
            "QWEN_BINARY": __file__,
            "QWEN_MODEL_PATH": __file__,
            "QWEN_AUDIT_MODE": "thinking",
        }, clear=False):
            tasks = [{"task_id": "f", "task_type": "factual_knowledge", "prompt": "Question?"}]
            result = call_qwen_audit(tasks, {"f": "Draft"})
        self.assertEqual(result["f"], "Corrected answer")
        command = run.call_args.args[0]
        self.assertIn("/think", command[-1])


if __name__ == "__main__":
    unittest.main()
