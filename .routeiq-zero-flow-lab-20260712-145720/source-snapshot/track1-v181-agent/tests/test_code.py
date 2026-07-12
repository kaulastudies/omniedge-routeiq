import unittest

from local.code import solve_code
from local.validation import validate_answer


class CodeTests(unittest.TestCase):
    def test_debug_max(self):
        task = {
            "task_id": "D01",
            "task_type": "code_debugging",
            "prompt": "This function should return the max of a list but has a bug: def get_max(nums): return nums[0]. Find and fix it.",
        }
        decision = solve_code(task)
        self.assertTrue(decision.accepted, decision.reason)
        valid, reason = validate_answer(task, decision.answer)
        self.assertTrue(valid, reason)
        namespace = {}
        exec(decision.answer, namespace, namespace)
        self.assertEqual(8, namespace["get_max"]([1, 8, 3]))

    def test_second_largest_distinct(self):
        task = {
            "task_id": "C01",
            "task_type": "code_generation",
            "prompt": "Write a Python function that returns the second-largest number in a list, handling duplicates correctly.",
        }
        decision = solve_code(task)
        self.assertTrue(decision.accepted, decision.reason)
        namespace = {}
        exec(decision.answer, namespace, namespace)
        self.assertEqual(3, namespace["second_largest"]([5, 5, 3, 2]))


if __name__ == "__main__":
    unittest.main()
