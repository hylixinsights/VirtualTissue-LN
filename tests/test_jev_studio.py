"""Jev wiring tests use an injected synthetic transport; no paid requests."""
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import Simulation
from jev import ProviderError
from server import Studio
from scripts import start_jev


def synthetic_transport(body):
    answers = {}
    for cid, question in body['questions'].items():
        options = question['criteria']
        choice = 'MOVE' if 'MOVE' in options else 'WAIT'
        answers[cid] = dict(type='choice', choice=choice, confidence=1,
                            probabilities={action: float(action == choice) for action in options})
    return dict(model='synthetic-wire-test', answers=answers, usage=dict(input_tokens=0, output_tokens=0))


def ui_fixture():
    """In-memory packets for browser interception only; never a saved Jev run."""
    with patch.dict(os.environ, {'TYPESAFE_API_KEY': 'test-only-no-network'}, clear=True):
        studio = Studio(enable_jev=True, limit=5, initial_cells=100, initial_provider='jev')
        studio.jev.transport = synthetic_transport
        before = dict(studio.state(), token='test-session-token')
        with patch.object(Simulation, 'fixture', side_effect=AssertionError('Fixture fallback called')):
            after = studio.dispatch('/api/step', {})
        return {'test_fixture': True, 'before': before, 'after': after}


class JevStudioTests(unittest.TestCase):
    def test_direct_start_requires_enable_key_and_cap(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                Studio(enable_jev=True, limit=5, initial_provider='jev')
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': 'test-only-no-network'}, clear=True):
            for enabled, cap in ((False, 5), (True, 0), (True, -1)):
                with self.subTest(enabled=enabled, cap=cap), self.assertRaises(ValueError):
                    Studio(enable_jev=enabled, limit=cap, initial_provider='jev')

    def test_jev_choices_update_the_same_cell_agents_without_fixture(self):
        packets = ui_fixture()
        before, after = packets['before'], packets['after']
        self.assertEqual(before['provider']['provider'], 'jev')
        self.assertEqual(before['provider']['requests'], 0)
        self.assertEqual(after['provider']['requests'], 5)
        self.assertEqual(after['tissue']['round'], 1)
        self.assertEqual(after['tissue']['metrics']['decisions'], 100)
        self.assertEqual([c['id'] for c in before['tissue']['cells']], [c['id'] for c in after['tissue']['cells']])
        self.assertTrue(any((a['x'],a['y']) != (b['x'],b['y']) for a,b in zip(before['tissue']['cells'],after['tissue']['cells'])))
        self.assertTrue(all(c['last_decision']['source'] == 'jev' for c in after['tissue']['cells']))
        self.assertNotIn('test-only-no-network', json.dumps(packets))

    def test_failure_pauses_without_fixture_or_retry(self):
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': 'test-only-no-network'}, clear=True):
            studio = Studio(enable_jev=True, limit=5, initial_cells=100, initial_provider='jev')
        studio.jev.transport = lambda body: (_ for _ in ()).throw(ProviderError('synthetic timeout'))
        with patch.object(Simulation, 'fixture', side_effect=AssertionError('Fixture fallback called')):
            with self.assertRaises(ProviderError):
                studio.dispatch('/api/step', {})
        self.assertEqual(studio.sim.round, 0)
        self.assertEqual(studio.sim.time, 0)
        self.assertEqual(studio.jev.requests, 1)
        self.assertEqual(studio.jev.unknown_usage, 1)
        self.assertEqual(studio.provider, 'jev')

    def test_session_cap_blocks_a_second_round(self):
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': 'test-only-no-network'}, clear=True):
            studio = Studio(enable_jev=True, limit=5, initial_cells=100, initial_provider='jev')
        studio.jev.transport = synthetic_transport
        studio.dispatch('/api/step', {})
        with self.assertRaises(ProviderError):
            studio.dispatch('/api/step', {})
        self.assertEqual(studio.sim.round, 1)
        self.assertEqual(studio.jev.requests, 5)

    def test_windows_entrypoint_selects_jev_without_sending_requests(self):
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': 'test-only-no-network'}, clear=True), \
             patch.object(start_jev.server, 'load_env'), patch.object(start_jev.server, 'main') as launch:
            start_jev.main(['--preview','--max-requests', '7', '--no-browser'])
        options = launch.call_args.args[0]
        self.assertEqual(options[options.index('--provider')+1], 'jev')
        self.assertEqual(options[options.index('--max-requests')+1], '7')
        self.assertEqual(options[options.index('--port')+1], '8022')
        self.assertNotIn('test-only-no-network', ' '.join(options))

    def test_recording_launcher_uses_user_cap_without_ten_decision_limit(self):
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': 'test-only-no-network'}, clear=True), \
             patch.object(start_jev.server, 'load_env'), patch.object(start_jev.record_reactive, 'main') as launch:
            start_jev.main(['--max-requests','5000','--no-browser'])
        options=launch.call_args.args[0]
        self.assertEqual(options[options.index('--max-requests')+1],'5000')
        self.assertNotIn('--max-decisions',options)
        self.assertNotIn('test-only-no-network',' '.join(options))


if __name__ == '__main__':
    unittest.main()
