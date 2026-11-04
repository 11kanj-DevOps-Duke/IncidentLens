import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import load_examples, load_rules, analyze_incident, from_alertmanager

class TestEngine(unittest.TestCase):
    def test_examples_are_valid(self):
        for x in load_examples():
            result=analyze_incident(x)
            self.assertGreaterEqual(len(result['evidence']),1)
            self.assertGreaterEqual(len(result['hypotheses']),1)
            self.assertTrue(result['approval_required'])
            self.assertEqual(result['mode'],'rules')
    def test_oom_rule(self):
        result=analyze_incident(next(x for x in load_examples() if x['id']=='crashloop'))
        self.assertIn('memory', ' '.join(h['name'] for h in result['hypotheses']).lower())
    def test_webhook_does_not_invent_metrics(self):
        inc=from_alertmanager({'alerts':[{'labels':{'alertname':'SomeAlert'},'annotations':{}}]})
        self.assertEqual(inc['snapshot'], {})
        self.assertEqual(inc['events'], [])
        result=analyze_incident(inc)
        self.assertEqual(len([e for e in result['evidence'] if e['source']=='metric snapshot']),0)
    def test_invalid_webhook(self):
        with self.assertRaises(ValueError): from_alertmanager({'alerts':[]})

if __name__=='__main__': unittest.main()
