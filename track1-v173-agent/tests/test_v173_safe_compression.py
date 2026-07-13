import importlib.util, json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('routeiq_v173',ROOT/'agent.py')
AGENT=importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(AGENT)

class SafeCompressionTests(unittest.TestCase):
    def setUp(self):
        self.tasks=[
            {'task_id':'f','task_type':'factual knowledge','prompt':'Capital of Japan?'},
            {'task_id':'m','task_type':'logic','prompt':'Return only A or B.'},
        ]

    def test_primary_payload_uses_pair_protocol_and_json_mode(self):
        captured={}
        def fake(payload, api_key, url, deadline=None):
            captured.update(payload)
            return {'choices':[{'message':{'content':'{"r":[[0,"Tokyo"],[1,"B"]]}'}}]}
        AGENT._perform_request=fake
        result=AGENT.request_batch(self.tasks,'model','key','https://example.invalid')
        self.assertEqual(result,{'f':'Tokyo','m':'B'})
        self.assertEqual(captured['response_format'],{'type':'json_object'})
        self.assertIsInstance(json.loads(captured['messages'][1]['content']),list)
        self.assertEqual(captured['max_tokens'],AGENT.completion_budget(self.tasks))
        self.assertLess(len(captured['messages'][0]['content']),230)

    def test_repair_keeps_q_and_issue_notes(self):
        captured={}
        def fake(payload, api_key, url, deadline=None):
            captured.update(payload)
            return {'choices':[{'message':{'content':'{"r":[[0,"Tokyo"],[1,"B"]]}'}}]}
        AGENT._perform_request=fake
        AGENT.request_batch(self.tasks,'model','key','https://example.invalid',{'f':'missing'})
        body=json.loads(captured['messages'][1]['content'])
        self.assertIn('q',body)
        self.assertIn('x',body)
        self.assertEqual(body['x'][0],[0,'missing'])

if __name__=='__main__': unittest.main()
