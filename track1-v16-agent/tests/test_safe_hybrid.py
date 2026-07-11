import unittest
from agent import remote_token_budget, requires_verified_geography

class SafeHybridTests(unittest.TestCase):
    def test_geography_is_fail_closed(self):
        task = {"task_id":"g1","task_type":"factual_knowledge","prompt":"What is the capital, and what body of water is it near?"}
        self.assertTrue(requires_verified_geography(task))

    def test_concept_comparison_stays_local(self):
        task = {"task_id":"f1","task_type":"factual_knowledge","prompt":"Briefly compare machine learning and deep learning."}
        self.assertFalse(requires_verified_geography(task))

    def test_factual_fallback_budget(self):
        task = {"task_id":"f2","task_type":"factual_knowledge","prompt":"Name a capital city."}
        self.assertEqual(remote_token_budget([task]), 192)
