"""Synthetic tests only. No real Jev requests."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.record_jev import atomic_json
from jev import Jev,ProviderError,request_body
from recording import RecordingSimulation,replay_cells
from reactive import PROMPT
from scripts.record_reactive import ReactiveRecorder,main
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from scripts.review_reactive_recording import review


def synthetic(body):
    answers={}
    for cid,q in body['questions'].items():
        o=q['instructions']['local_observation'];c=o['cell'];opts=q['criteria']
        priority=['CLEAR','CAPTURE','PROCESS','PRIME','HELPER','HELP']
        if c['kind']=='B' and c['state']=='activated':
            priority+=['PLASMA'] if c['affinity']>=.79 else ['ENTER_GC','MOVE']
        if c['state']=='selected':priority+=['PLASMA','MEMORY','RECYCLE']
        if c['state']=='plasmablast' and o.get('own_antibody_units',0)>=3:priority+=['MATURE']
        priority+=['DIVIDE','SECRETE','MATURE','MOVE','WAIT']
        choice=next(a for a in priority if a in opts)
        answers[cid]=dict(type='choice',choice=choice,confidence=1,probabilities={a:float(a==choice) for a in opts})
    return dict(model='synthetic',answers=answers,usage={'input_tokens':0,'output_tokens':0})


class ContinuousRecordingTests(unittest.TestCase):
    def test_existing_listener_cannot_start_another_paid_recorder(self):
        with ThreadingHTTPServer(('127.0.0.1',0),BaseHTTPRequestHandler) as existing:
            with patch('scripts.record_reactive.ReactiveRecorder') as recorder,patch('scripts.record_reactive.load_env'):
                with self.assertRaises(OSError):main(['--max-requests','1','--port',str(existing.server_port)])
                recorder.assert_not_called()

    def test_local_checkpoint_sharing_violation_does_not_repeat_inference(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'summary.json'
            import os
            replace=os.replace
            with patch('scripts.record_jev.os.replace',side_effect=[PermissionError('synthetic sharing violation'),None]) as mocked,patch('scripts.record_jev.time.sleep'):
                atomic_json(path,{'requests':1});self.assertEqual(mocked.call_count,2)
            replace(path.with_name(path.name+'.tmp'),path)
            self.assertEqual(json.loads(path.read_text()),{'requests':1})

    def test_explicit_resume_preserves_choices_state_and_total_cap(self):
        with tempfile.TemporaryDirectory() as folder,contextlib.redirect_stdout(io.StringIO()):
            def provider():return Jev(key='test',limit=4,transport=synthetic,biological_context=True,development_context=True)
            path=Path(folder)/'run';first=ReactiveRecorder(path,4,provider=provider())
            first.sim.perturb(PROMPT);first.sim.save_frame();first.control['status']='running'
            while first.provider.requests<1:first.tick()
            first.dispatch('/api/stop',{});first.tick();first.journal.close()
            state=first.sim.snapshot();decisions=list(first.sim.decisions)
            second=ReactiveRecorder(path,4,provider=provider(),resume=True)
            self.assertEqual(second.sim.snapshot(),state);self.assertEqual(second.provider.requests,1)
            second.run();self.assertEqual(second.provider.requests,4)
            self.assertEqual(second.sim.decisions[:len(decisions)],decisions)
            self.assertEqual(second.control['status'],'budget_reached')
            self.assertEqual(len(second.control['resume_history']),1)
            self.assertEqual(review(path/'episode.ln.json.gz')['requests'],4)

    def test_user_stop_saves_replay_without_new_requests(self):
        with tempfile.TemporaryDirectory() as folder,contextlib.redirect_stdout(io.StringIO()):
            rec=ReactiveRecorder(Path(folder)/'run',3,provider=Jev(key='test',limit=3,transport=synthetic))
            rec.control['status']='running';rec.dispatch('/api/stop',{})
            self.assertFalse(rec.tick());self.assertEqual(rec.provider.requests,0)
            self.assertEqual(rec.control['status'],'stopped');self.assertTrue(rec.control['playback_available'])
            rec.journal.close()
    def test_multicell_concurrency_and_hard_limit(self):
        sim=RecordingSimulation();sim.perturb(PROMPT)
        rows=[dict(id=str(i),observation=sim.observation(sim.cells[0]),options={'WAIT':None}) for i in range(9)]
        provider=Jev(key='test',limit=9,transport=synthetic)
        answers=provider.choose(rows,9,workers=4,batch_size=1)
        self.assertEqual(len(answers),9);self.assertEqual(provider.requests,9)
        with self.assertRaises(ProviderError):provider.choose(rows,9,workers=4,batch_size=1)
        self.assertEqual(provider.requests,9)

    def test_continues_after_output_and_delta_replay_preserves_lineage(self):
        sim=RecordingSimulation(params={'max_rounds':500});sim.perturb(PROMPT);sim.save_frame()
        for _ in range(432):
            rows=sim.proposals();answers=synthetic(request_body(rows,'synthetic',True,development_context=True))['answers']
            sim.step(answers,rows,'synthetic')
        self.assertGreater(sim.births,0);self.assertGreater(sim.antibody,3)
        self.assertTrue(any(c['state']=='plasma' for c in sim.cells))
        self.assertEqual(len(sim.antigens),9)
        episode=sim.export();self.assertEqual(episode['frames'],[])
        frame,cells=list(replay_cells(episode))[-1]
        self.assertEqual(frame['metrics'],sim.metrics())
        actual={c['id']:c for c in sim.snapshot()['cells']}
        self.assertEqual(set(cells),set(actual))
        for cid,c in cells.items():
            for field in ('state','x','y','clone','parent','antibodies','program','response','options'):
                self.assertEqual(c[field],actual[cid][field])
        self.assertGreater(frame['metrics']['never_queried'],100)

    def test_recorder_stops_at_exact_request_cap_and_never_retries(self):
        with tempfile.TemporaryDirectory() as folder,contextlib.redirect_stdout(io.StringIO()):
            provider=Jev(key='synthetic-secret',limit=3,transport=synthetic,biological_context=True,development_context=True)
            rec=ReactiveRecorder(Path(folder)/'run',3,provider=provider);rec.run()
            self.assertEqual(provider.requests,3);self.assertEqual(rec.control['status'],'budget_reached')
            self.assertEqual(rec.pending_round,None)
            self.assertNotIn('synthetic-secret',json.dumps(rec.export()))
            self.assertFalse(rec.tick())
            checked=review(rec.folder/'episode.ln.json.gz')
            self.assertEqual(checked['requests'],3);self.assertTrue(checked['all_choices_match_provider'])
        def failure(body):raise ProviderError('Synthetic transport failure')
        with tempfile.TemporaryDirectory() as folder,contextlib.redirect_stdout(io.StringIO()):
            rec=ReactiveRecorder(Path(folder)/'run',3,provider=Jev(key='test',limit=3,transport=failure));rec.run()
            self.assertEqual(rec.control['status'],'failed');self.assertEqual(rec.provider.requests,1)
            self.assertEqual(rec.provider.unknown_usage,1);self.assertIsNotNone(rec.pending_round)

if __name__=='__main__':unittest.main()
