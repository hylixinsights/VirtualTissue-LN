import gzip,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import Simulation
from jev import Jev,ProviderError,validate,request_body
from scripts.record_jev import Recorder
import server

def answer(body):
 return dict(model='jev-1.13.0',usage={'input_tokens':30,'output_tokens':10},answers={k:{'type':'choice','choice':'WAIT','probabilities':{a:float(a=='WAIT') for a in q['criteria']},'confidence':1} for k,q in body['questions'].items()})

class LiveRecorderTests(unittest.TestCase):
 def test_parallel_round_retains_all_unique_requests(self):
  rows=Simulation().proposals();p=Jev('synthetic',limit=15,transport=answer)
  result=p.choose(rows,15,workers=4)
  self.assertEqual(len(result),300);self.assertEqual(p.requests,15)
  self.assertEqual(len({r['request'] for r in p.audit}),15);self.assertEqual(p.input_tokens,450)
 def test_failed_wave_does_not_start_later_batches(self):
  def fail(body):raise ProviderError('synthetic outage')
  p=Jev('synthetic',limit=15,transport=fail)
  with self.assertRaises(ProviderError):p.choose(Simulation().proposals(),15,workers=4)
  self.assertEqual(p.requests,4);self.assertEqual(p.unknown_usage,4)
 def test_budget_checked_before_any_concurrent_call(self):
  p=Jev('synthetic',limit=14,transport=lambda _:self.fail('Unexpected call'))
  with self.assertRaises(ProviderError):p.choose(Simulation().proposals(),14,workers=4)
  self.assertEqual(p.requests,0)
 def test_nonobject_answer_is_rejected_cleanly(self):
  rows=Simulation().proposals()[:1];body=answer(request_body(rows,'jev-1.13.0'));body['answers'][rows[0]['id']]=None
  with self.assertRaises(ProviderError):validate(body,rows)
 def test_real_provider_path_never_calls_fixture(self):
  with tempfile.TemporaryDirectory() as t:
   folder=Path(t)/'session';p=Jev('synthetic-test-secret',limit=30,transport=answer)
   with patch.object(Simulation,'fixture',side_effect=AssertionError('Fixture must not execute')):
    r=Recorder(folder,p,1,['vaccine','baseline'],21);self.assertTrue(r.run(workers=4))
   self.assertEqual(p.requests,30)
   for scenario in ('vaccine','baseline'):
    with gzip.open(folder/(scenario+'.ln.json.gz'),'rt') as f:ep=json.load(f)
    self.assertEqual(ep['recording_status'],'complete');self.assertEqual(ep['provider']['requests'],15)
    self.assertEqual(len(ep['request_audit']),15);self.assertTrue(all(d['source']=='jev' for d in ep['decisions']))
    self.assertNotIn('synthetic-test-secret',json.dumps(ep))
   with patch.object(server,'ROOT',Path(t)):
    # Catalog exposes only approved summary entries, never arbitrary files.
    private=Path(t)/'recordings/private';private.mkdir(parents=True)
    folder.rename(private/'session');items,files=server.recordings_catalog()
    self.assertEqual(len(items),2);self.assertTrue(all(len(k)==20 for k in files))
 def test_failed_request_saves_pending_observations_and_partial_file(self):
  def fail(_):raise ProviderError('synthetic timeout')
  with tempfile.TemporaryDirectory() as t:
   folder=Path(t)/'session';p=Jev('synthetic',limit=30,transport=fail)
   r=Recorder(folder,p,1,['vaccine','baseline'],21);self.assertFalse(r.run())
   with gzip.open(folder/'vaccine.ln.json.gz','rt') as f:ep=json.load(f)
   self.assertEqual(ep['final']['round'],0);self.assertEqual(ep['recording_status'],'partial')
   self.assertEqual(len(ep['pending_round']['rows']),300);self.assertEqual(ep['provider']['unknown_usage'],1)
   self.assertFalse((folder/'baseline.ln.json.gz').exists())
   lines=[json.loads(s) for s in (folder/'audit.jsonl').read_text().splitlines()]
   self.assertTrue(any(e['event']=='round_started' for e in lines));self.assertEqual(p.requests,1)

if __name__=='__main__':unittest.main(verbosity=2)
