import json
import os
import tempfile
import unittest
from unittest.mock import patch
from src.api.job_store import JOBS, TARGETS, CREDENTIALS, Job, TargetRecord, CredentialRecord
from src.api.persistence import save_state, load_state


class PersistenceTests(unittest.TestCase):
    def test_round_trip_preserves_dashboard_and_credentials(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'FENNEC_DATA_DIR': directory}):
            job = Job(id='j', name='test', target_url='https://example.test', status='completed', success=True, final_result='report', findings=[{'id': 'f', 'severity': 'high'}])
            JOBS.put(job)
            TARGETS['t'] = TargetRecord(id='t', domain='example.test', name='test')
            CREDENTIALS['c'] = CredentialRecord(id='c', target_id='t', name='test', username='user', password='secret')
            save_state()
            JOBS._jobs.clear(); TARGETS.clear(); CREDENTIALS.clear()
            load_state()
            self.assertEqual(JOBS.get('j').findings, job.findings)
            self.assertEqual(JOBS.get('j').final_result, 'report')
            self.assertEqual(TARGETS['t'].domain, 'example.test')
            self.assertEqual(CREDENTIALS['c'].password, 'secret')
            self.assertEqual(os.stat(directory + '/state.json').st_mode & 0o777, 0o600)
            JOBS._jobs.clear(); TARGETS.clear(); CREDENTIALS.clear()

    def test_interrupted_execution_keeps_partial_results(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'FENNEC_DATA_DIR': directory}):
            JOBS.put(Job(id='j', name='test', target_url='https://example.test', status='running', hypotheses=[{'id': 'h'}]))
            save_state(); JOBS._jobs.clear(); load_state()
            self.assertEqual(JOBS.get('j').status, 'failed')
            self.assertEqual(JOBS.get('j').hypotheses, [{'id': 'h'}])
            JOBS._jobs.clear()
