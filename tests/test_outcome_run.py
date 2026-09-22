"""The outcome runner uses synthetic transports in tests, never real inference."""
import copy
import json
import tempfile
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.run_reactive_jev import OutcomeRun,SavedOutcome
from jev import Jev,ProviderError,request_body
from reactive import PROMPT

def synthetic(body):
    answers={}
    for cid,q in body['questions'].items():
        opts=q['criteria'];choice='PROCESS' if 'PROCESS' in opts else 'WAIT'
        answers[cid]=dict(type='choice',choice=choice,confidence=1,probabilities={a:float(a==choice) for a in opts})
    return dict(model='synthetic-outcome-test',answers=answers,usage=dict(input_tokens=0,output_tokens=0))

class OutcomeRunTests(unittest.TestCase):
    def test_proposed_preference_only_for_eligible_output_cells(self):
        rows=[dict(id='quiet',observation={'cell':{'kind':'B','state':'naive'}},options={'WAIT':None}),
            dict(id='helped',observation={'cell':{'kind':'B','state':'activated'}},options={'PLASMA':None,'WAIT':None}),
            dict(id='producer',observation={'cell':{'kind':'B','state':'plasmablast'}},options={'SECRETE':None,'WAIT':None})]
        baseline=request_body(rows,'synthetic',True)
        guided=request_body(rows,'synthetic',True,plasmablast_context=True)
        self.assertEqual(baseline['questions']['quiet'],guided['questions']['quiet'])
        for cid in ('helped','producer'):
            self.assertNotIn('proposed_local_policy',baseline['questions'][cid]['instructions'])
            self.assertIn('proposed_local_policy',guided['questions'][cid]['instructions'])
            self.assertEqual(baseline['questions'][cid]['criteria'],guided['questions'][cid]['criteria'])

    def test_prior_attempts_reduce_remaining_budget(self):
        with tempfile.TemporaryDirectory() as folder:
            run=OutcomeRun(Path(folder)/'new',5,prior_requests=4,provider=Jev(key='test-only',limit=1,transport=synthetic))
            run.sim.perturb(PROMPT);run.run_info['status']='running'
            for _ in range(4):run.tick()
            self.assertEqual(run.run_info['cumulative_requests'],5)
            self.assertEqual(run.run_info['status'],'budget_reached')
            self.assertFalse(run.tick());run.journal.close()

    def test_graceful_stop_does_not_call_provider(self):
        with tempfile.TemporaryDirectory() as folder:
            run=self.make(folder);run.run_info['status']='running';run.stop_requested.set()
            self.assertFalse(run.tick());self.assertEqual(run.jev.requests,0)
            self.assertEqual(run.run_info['status'],'stopped');run.journal.close()
            viewer=SavedOutcome(run.folder)
            self.assertEqual(viewer.state()['run_control']['status'],'stopped')
            self.assertFalse(hasattr(viewer,'jev'))
            self.assertEqual(viewer.export()['provider_label'],'jev')
            with self.assertRaises(ValueError):viewer.dispatch('/api/step',{})

    def test_antigen_exhaustion_stops_nonproductive_t_cell_loop(self):
        with tempfile.TemporaryDirectory() as folder:
            run=self.make(folder);run.sim.perturb(PROMPT)
            dc=next(c for c in run.sim.cells if c.get('arrival'));dc['cargo']=None;dc['program']=None
            for a in run.sim.antigens:a.update(pool='degraded',owner=None)
            run.run_info['status']='running'
            self.assertFalse(run.tick());self.assertEqual(run.run_info['status'],'antigen_exhausted')
            self.assertEqual(run.jev.requests,0);run.journal.close()

    def make(self,folder,cap=3,transport=synthetic):
        return OutcomeRun(Path(folder)/'new-run',cap,provider=Jev(key='test-only-no-network',limit=cap,transport=transport,biological_context=True))

    def test_empty_ticks_no_calls_and_budget_stop_no_extra_request(self):
        with tempfile.TemporaryDirectory() as folder:
            run=self.make(folder,1);run.sim.perturb(PROMPT);run.run_info['status']='running'
            for _ in range(3):self.assertTrue(run.tick())
            self.assertEqual(run.jev.requests,0)
            self.assertFalse(run.tick());self.assertEqual(run.jev.requests,1)
            self.assertEqual(run.run_info['status'],'budget_reached')
            self.assertFalse(run.tick());self.assertEqual(run.jev.requests,1)
            self.assertNotIn('test-only-no-network',(run.folder/'live.json').read_text())
            with self.assertRaises(ValueError):run.dispatch('/api/step',{})
            run.journal.close()

    def test_success_needs_applied_secretion_after_completed_differentiation(self):
        with tempfile.TemporaryDirectory() as folder:
            run=self.make(folder);cell=next(c for c in run.sim.cells if c['kind']=='B')
            cell.update(state='plasmablast',antibodies=1)
            self.assertIsNone(run.outcome())
            run.sim.events.append(dict(cell=cell['id'],event='program_completed',action='PLASMA',time_min=300))
            run.sim.decisions.append(dict(cell=cell['id'],source='jev',time_min=310,result='deferred',proposal={'choice':'SECRETE'},observation={'cell':{'state':'plasmablast'}}))
            self.assertIsNone(run.outcome())
            run.sim.decisions[-1]['result']='applied'
            self.assertEqual(run.outcome()['cell'],cell['id'])
            run.run_info['status']='complete'
            self.assertFalse(run.tick());self.assertEqual(run.jev.requests,0)
            run.journal.close()

    def test_provider_failure_saved_without_retry(self):
        def fail(body):raise ProviderError('Synthetic transport failure')
        with tempfile.TemporaryDirectory() as folder:
            run=self.make(folder,3,fail);run.run()
            self.assertEqual(run.run_info['status'],'failed')
            self.assertEqual(run.jev.requests,1);self.assertEqual(run.jev.unknown_usage,1)
            self.assertEqual(run.sim.time,30)
            self.assertIsNotNone(run.pending_round)
            saved=json.loads((run.folder/'summary.json').read_text())
            self.assertEqual(saved['status'],'failed')

if __name__=='__main__':unittest.main()
