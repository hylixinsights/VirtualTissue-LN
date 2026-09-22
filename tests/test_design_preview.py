"""Bounded preview tests. All transports are synthetic; never paid calls."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from design_preview import DesignPreview, SavedPreview
from engine import Simulation
from jev import ProviderError
from test_jev_studio import synthetic_transport


def synthetic_preview(directory):
    with patch.dict(os.environ, {'TYPESAFE_API_KEY': 'test-only-no-network'}, clear=True):
        preview = DesignPreview(directory)
    preview.jev.transport = synthetic_transport
    with patch.object(Simulation, 'fixture', side_effect=AssertionError('No fixture substitution allowed')):
        preview.dispatch('/api/step', {})
    return preview


def ui_fixture():
    with tempfile.TemporaryDirectory() as directory:
        preview = synthetic_preview(Path(directory) / 'sample')
        return dict(test_fixture=True, state=dict(preview.state(), token='test-session-token'))


class PreviewTests(unittest.TestCase):
    def test_exactly_ten_choices_one_request_and_no_continuation(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'sample'
            preview = synthetic_preview(target)
            self.assertEqual(len(preview.sim.decisions), 10)
            self.assertEqual(preview.jev.requests, 1)
            self.assertEqual(len(preview.jev.audit[0]['cells']), 10)
            self.assertEqual(preview.preview['status'], 'complete')
            selected = set(preview.preview['selected_ids'])
            before = {c['id']:c for c in preview.preview['before']['cells']}
            self.assertEqual({c['kind'] for c in preview.sim.cells if c['id'] in selected}, {'B','CD4','DC'})
            for cell in preview.sim.cells:
                if cell['id'] not in selected:
                    self.assertIsNone(cell['last_decision'])
                    self.assertEqual((cell['x'],cell['y']), (before[cell['id']]['x'],before[cell['id']]['y']))
            for operation in ('step','reset','inject'):
                with self.assertRaises(ValueError):
                    preview.dispatch('/api/'+operation, {})
            self.assertEqual(preview.jev.requests, 1)
            text = (target/'preview.json').read_text(encoding='utf-8')
            self.assertNotIn('test-only-no-network', text)
            self.assertEqual(json.loads(text)['episode']['design_preview']['status'], 'complete')
            saved = SavedPreview(target/'preview.json')
            self.assertFalse(saved.status()['configured'])
            self.assertFalse(saved.status()['enabled'])
            self.assertEqual(saved.state()['tissue'], preview.sim.snapshot())
            self.assertEqual(saved.export()['seed'], preview.sim.seed)
            with self.assertRaises(ValueError):
                saved.dispatch('/api/step', {})
            with patch.dict(os.environ, {'TYPESAFE_API_KEY':'test-only-no-network'}), self.assertRaises(FileExistsError):
                DesignPreview(target)

    def test_failed_attempt_is_saved_and_never_retried(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'TYPESAFE_API_KEY':'test-only-no-network'}):
            target = Path(directory) / 'sample'
            preview = DesignPreview(target)
            preview.jev.transport = lambda body: (_ for _ in ()).throw(ProviderError('synthetic timeout'))
            with self.assertRaises(ProviderError):
                preview.dispatch('/api/step', {})
            self.assertEqual(preview.jev.requests, 1)
            self.assertEqual(preview.jev.unknown_usage, 1)
            self.assertEqual(preview.sim.time, 0)
            self.assertEqual(preview.preview['status'], 'failed')
            with self.assertRaises(ValueError):
                preview.dispatch('/api/step', {})
            self.assertEqual(SavedPreview(target/'preview.json').state()['design_preview']['status'], 'failed')


if __name__ == '__main__':
    unittest.main()
