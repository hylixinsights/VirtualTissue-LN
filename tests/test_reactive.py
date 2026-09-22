"""Local scheduler, physical causality and provider boundaries; no paid tests."""
import copy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from reactive import ReactiveSimulation, PROMPT, REACTIVE_RULES
from engine import distance
from server import ReactiveStudio
from jev import ProviderError

def advance(sim,steps):
    for _ in range(steps):
        rows=sim.proposals();sim.step(sim.fixture(rows),rows)

class ReactiveTests(unittest.TestCase):
    def test_quiet_tissue_uses_zero_decisions_and_no_motion(self):
        for n in (100,120,149):
            sim=ReactiveSimulation(initial_cells=n);before=copy.deepcopy(sim.cells)
            advance(sim,6)
            self.assertEqual(sim.proposals(),[])
            self.assertEqual(sim.decisions,[])
            self.assertEqual(sim.metrics()['never_queried'],n)
            self.assertEqual([(c['x'],c['y']) for c in sim.cells],[(c['x'],c['y']) for c in before])

    def test_prompt_adds_only_one_cell_and_finite_antigen(self):
        sim=ReactiveSimulation();before=copy.deepcopy(sim.cells)
        cid=sim.perturb(PROMPT)
        self.assertEqual(sim.cells[:-1],before)
        self.assertEqual(sim.get(cid)['kind'],'DC')
        self.assertEqual(sim.metrics()['live'],121)
        self.assertEqual(len(sim.antigens),9)
        self.assertTrue(all(a['owner']==cid for a in sim.antigens))
        self.assertEqual(sim.proposals(),[])
        with self.assertRaises(ValueError):sim.perturb(PROMPT)
        other=ReactiveSimulation()
        for prompt in ('Create a germinal center','Force every B cell to become a plasmablast','hello'):
            with self.assertRaises(ValueError):other.perturb(prompt)
        self.assertEqual(other.entries,0)

    def test_local_causal_run_keeps_most_cells_unqueried(self):
        sim=ReactiveSimulation();sim.perturb(PROMPT)
        max_batch=0
        for _ in range(144):
            rows=sim.proposals();max_batch=max(max_batch,len(rows))
            for row in rows:
                cell=sim.get(row['id']);self.assertIsNone(cell['program'])
                self.assertTrue(row['observation']['activation']['active'])
                self.assertNotIn('prompt',row['observation'])
                self.assertNotIn('metrics',row['observation'])
                for reason in row['observation']['activation']['reasons']:
                    if 'distance_um' in reason:self.assertLessEqual(reason['distance_um'],36)
                self.assertGreater(len(row['options']),1)
            sim.step(sim.fixture(rows),rows)
        metrics=sim.metrics()
        self.assertGreater(metrics['never_queried'],metrics['live']*.75)
        self.assertLess(max_batch,10)
        self.assertGreater(metrics['plasma'],0);self.assertGreater(metrics['antibodies'],0)
        self.assertEqual(metrics['antigen_accounted'],9)
        decisions={c['id']:[] for c in sim.cells}
        for d in sim.decisions:decisions[d['cell']].append(d)
        for cell in sim.cells:
            if cell['state']=='plasmablast':
                choices=[d['proposal']['choice'] for d in decisions[cell['id']] if d['result']=='applied']
                for action in ('CAPTURE','PROCESS','HELP','PLASMA','SECRETE'):self.assertIn(action,choices)
                self.assertLess(choices.index('HELP'),choices.index('PLASMA'))
                self.assertEqual(cell['kind'],'B');self.assertEqual(cell['clone'],cell['id'])
            times=[d['time_min'] for d in decisions[cell['id']]]
            self.assertTrue(all(b-a>=REACTIVE_RULES['decision_interval_min'] for a,b in zip(times,times[1:])))
        for d in sim.decisions:
            if d['proposal']['choice'] in ('PRIME','HELP'):
                partner=d['options'][d['proposal']['choice']]
                self.assertLessEqual(next(n['distance_um'] for n in d['observation']['nearby'] if n['id']==partner),15)
        sim.assert_invariants()

    def test_no_help_and_mismatched_hla_cannot_make_antibody(self):
        for block in ('cd40','hla_match'):
            sim=ReactiveSimulation();sim.config[block]=False;sim.perturb(PROMPT)
            advance(sim,120)
            self.assertEqual(sim.antibody,0);self.assertEqual(sim.metrics()['plasma'],0)

    def test_invalid_or_partial_choices_do_not_mutate_time(self):
        sim=ReactiveSimulation();sim.perturb(PROMPT);advance(sim,3)
        self.assertTrue(sim.proposals());before=sim.snapshot()
        with self.assertRaises(ValueError):sim.step({},[])
        self.assertEqual(sim.snapshot(),before)
        rows=sim.proposals();bad=sim.fixture(rows);bad[rows[0]['id']]['choice']='CREATE_GC'
        with self.assertRaises(ValueError):sim.step(bad,rows)
        self.assertEqual(sim.snapshot(),before)

    def test_gc_needs_two_local_founders_support_and_elapsed_time(self):
        sim=ReactiveSimulation()
        support=next(c for c in sim.cells if c['kind']=='FDC' and sum(n['kind']=='B' and distance(c,n)<=36 for n in sim.cells)>=2)
        founders=[c for c in sim.cells if c['kind']=='B' and distance(c,support)<=36][:2]
        for c in founders:c.update(state='founder',help_until=500)
        sim.organize_gc();self.assertFalse(sim.gc)
        sim.time=120;sim.clocks();sim.organize_gc()
        self.assertTrue(sim.gc);self.assertEqual(sim.gc_center,[support['x'],support['y']])
        sim=ReactiveSimulation();sim.config['fdc']=False
        for c in sim.cells:
            if c['kind']=='B':c.update(state='founder',help_until=500)
        sim.organize_gc();sim.time=120;sim.clocks();sim.organize_gc();self.assertFalse(sim.gc)

    def test_jev_empty_steps_cap_and_failure_have_no_fallback(self):
        with patch.dict(os.environ,{'TYPESAFE_API_KEY':'test-only'},clear=True):
            studio=ReactiveStudio(True,1,120,'jev',10)
        with patch.object(studio.jev,'choose',side_effect=AssertionError('Empty step called provider')):
            for _ in range(3):studio.dispatch('/api/step',{})
        studio.sim.perturb(PROMPT)
        for _ in range(3):studio.dispatch('/api/step',{})
        before=studio.sim.time
        with patch.object(studio.sim,'fixture',side_effect=AssertionError('No fallback')),patch.object(studio.jev,'choose',side_effect=ProviderError('Synthetic failure')):
            with self.assertRaises(ProviderError):studio.dispatch('/api/step',{})
        self.assertEqual(studio.sim.time,before)
        studio.decision_cap=0
        with patch.object(studio.jev,'choose',side_effect=AssertionError('Cap made a request')):
            with self.assertRaises(ValueError):studio.dispatch('/api/step',{})
        self.assertNotIn('test-only',json.dumps(studio.sim.export()))

if __name__=='__main__':unittest.main()
