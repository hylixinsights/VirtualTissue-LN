"""Scripted vaccination: outcome, negative gates and causal provenance."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.build_vaccine_story import build_story


class VaccineStoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.story = build_story()

    def test_response_preserves_identity_and_has_no_paid_decisions(self):
        s=self.story;ep=s['episode'];b=s['cast']['b'];final=s['frames'][-1]
        self.assertEqual(s['provider'],'scripted')
        self.assertEqual(s['paid_requests'],0)
        self.assertTrue(all(d['source']=='scripted' for d in ep['decisions']))
        self.assertEqual(final['metrics']['antibodies'],3)
        self.assertEqual(final['metrics']['states']['plasmablast'],1)
        self.assertEqual(final['metrics']['tfh'],1)
        self.assertEqual(final['metrics']['live'],100)
        cell=next(c for c in final['cells'] if c['id']==b)
        self.assertEqual(cell['clone'],b)
        self.assertEqual(cell['kind'],'B')
        self.assertEqual(cell['isotype'],'IgM')
        self.assertEqual(cell['antibodies'],3)
        self.assertIsNone(cell['parent'])
        self.assertEqual(final['metrics']['net_births'],0)
        self.assertEqual(final['metrics']['gc_b'],0)

    def test_causal_chain_and_clocks(self):
        s=self.story;ep=s['episode'];cast=s['cast'];events=ep['events']
        def event_time(kind,cell,action=None):
            return next(e['time_min'] for e in events if e['event']==kind and e['cell']==cell and (action is None or e.get('action')==action))
        self.assertEqual(event_time('capture',cast['dc']),0)
        self.assertEqual(event_time('program_completed',cast['dc'],'LOAD'),120)
        self.assertEqual(event_time('program_started',cast['helper'],'PRIME'),120)
        self.assertEqual(event_time('program_completed',cast['helper'],'PRIME'),180)
        self.assertEqual(event_time('program_completed',cast['helper'],'HELPER'),300)
        self.assertEqual(event_time('program_completed',cast['b'],'HELP'),330)
        self.assertEqual(event_time('program_completed',cast['b'],'PLASMA'),510)
        self.assertEqual(event_time('antibody_secreted',cast['b']),510)
        for d in ep['decisions']:
            self.assertIn(d['proposal']['choice'],d['options'])
            if d['cell'] not in cast.values():self.assertEqual(d['proposal']['choice'],'WAIT')
        # Both capture independent finite packets of the same antigen.
        captures=[e for e in events if e['event']=='capture']
        self.assertEqual(len(captures),2)
        self.assertEqual(len({e['antigen'] for e in captures}),2)
        self.assertEqual(s['frames'][0]['metrics']['antigen_input'],2)
        for f in s['frames']:
            self.assertEqual(len(f['antigen_ledger']),2)
            self.assertEqual(sum(a['mass'] for a in f['antigen_ledger']),2)
            self.assertTrue(all(c['z']==0 for c in f['cells']))
            expected=sum(c['program'] is None and c['state'] not in ('apoptotic','divided','cleared') for c in f['cells'])
            rows=[d for d in ep['decisions'] if d['round']==f['round']]
            if f is not s['frames'][-1]:self.assertEqual(len(rows),expected,'Every eligible cell receives a decision in each full round')

    def test_blocked_help_prevents_plasmablast_and_antibody(self):
        for kwargs in ({'cd40':False},{'hla_match':False}):
            with self.subTest(**kwargs):
                final=build_story(**kwargs)['frames'][-1]
                self.assertEqual(final['metrics']['antibodies'],0)
                self.assertEqual(final['metrics']['plasma'],0)

    def test_checked_in_story_matches_generator(self):
        saved=json.loads((Path(__file__).resolve().parents[1]/'web/vaccine-story.json').read_text(encoding='utf-8'))
        self.assertEqual(saved,json.loads(json.dumps(self.story)))


if __name__=='__main__':unittest.main()
