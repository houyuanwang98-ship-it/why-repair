import json
from pathlib import Path
import tempfile
import unittest

from scripts.run_live_repair_pilot import ROOT, run_case, write_once
from harness.m5_person_a_review import CHECKS


class StubCalls:
    model = 'test-stub'
    max_calls = 12
    max_tokens = 60000
    tokens = 0

    def __init__(self, verdict):
        self.verdict = verdict
        self.count = 0
        self.revalidated = []

    def call(self, phase, payload):
        self.count += 1
        if phase == 'generate':
            patch = json.loads((ROOT / 'data/benchmarks/m5/provisional_codex_interactive_v1/m2-011.patch.json').read_text(encoding='utf-8'))
            patch['generator_id'] = 'live-generator'
            return patch
        if phase == 'review':
            return {'schema_version': '0.1', 'review_id': 'test-review',
                'context_id': payload['context']['context_id'], 'reviewer_id': 'live-reviewer',
                'checks': {k: True for k in CHECKS}, 'hidden_assumptions': [], 'introduced_errors': [],
                'deletion_trials': [{'edit_id': e, 'removal_breaks_repair': True, 'reason': 'stub'} for e in payload['edit_ids']],
                'evidence_used': payload['context']['allowed_evidence'], 'accepted': True,
                'rejection_codes': [], 'reason': 'stub acceptance; not mathematical evidence'}
        self.revalidated.append(payload['target'])
        return {'schema_version': '0.1', 'evaluation_id': payload['evaluation_id'],
            'evaluator_id': 'live-reviewer', 'target': payload['target'], 'verdict': self.verdict,
            'reason': 'stub node judgment; not mathematical evidence'}


class LivePilotTest(unittest.TestCase):
    def test_patch_acceptance_does_not_override_node_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            calls = StubCalls('rejected')
            run_case('m2-011', Path(directory), calls, 1)
            result = json.loads((Path(directory) / 'result.json').read_text())
            self.assertEqual('round_budget_exhausted', result['status'])
            self.assertEqual(1, len(calls.revalidated))
            self.assertNotEqual('accepted', result['final_state']['stop_reason'])

    def test_inserted_node_and_descendant_are_separately_revalidated(self):
        with tempfile.TemporaryDirectory() as directory:
            calls = StubCalls('accepted')
            run_case('m2-011', Path(directory), calls, 1)
            result = json.loads((Path(directory) / 'result.json').read_text())
            self.assertEqual('accepted', result['status'])
            self.assertEqual(['2a', 2], [r['node_id'] for r in calls.revalidated])
            self.assertFalse(result['human_verified'])

    def test_checkpoint_refuses_changed_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'evidence.json'
            write_once(path, {'verdict': 'rejected'})
            with self.assertRaises(RuntimeError):
                write_once(path, {'verdict': 'accepted'})
