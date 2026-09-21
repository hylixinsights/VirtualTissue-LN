import copy,gzip,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import Simulation
from jev import Jev,ProviderError,validate,request_body
from scripts.record_jev import Recorder
from test_live_recording import answer

class PrecisionTests(unittest.TestCase):
 def test_observed_099_rounding_preserved_and_explicitly_normalized(self):
  rows=[dict(id='B1',observation={},options={'MOVE':None,'WAIT':None,'PROCESS':'AG1'})]
  body={'model':'jev-1.13.0','answers':{'B1':{'type':'choice','choice':'PROCESS','confidence':.72,'probabilities':{'MOVE':.08,'WAIT':.1,'PROCESS':.81}}}}
  original=copy.deepcopy(body);result=validate(body,rows)['B1']
  self.assertEqual(body,original);self.assertEqual(result['raw_probabilities'],original['answers']['B1']['probabilities'])
  self.assertAlmostEqual(sum(result['probabilities'].values()),1)
  self.assertEqual(result['choice'],'PROCESS');self.assertFalse(result['probability_adjustment']['changes_choice'])
 def test_large_probability_deficit_remains_invalid(self):
  rows=Simulation(initial_cells=100).proposals()[:1];body=answer(request_body(rows,'jev-1.13.0'));a=body['answers'][rows[0]['id']]
  a['probabilities']={k:.1 for k in rows[0]['options']}
  with self.assertRaises(ProviderError):validate(body,rows)
 def test_resume_replays_completed_round_and_reuses_four_paid_batches(self):
  with tempfile.TemporaryDirectory() as t:
   folder=Path(t)/'session';p=Jev('synthetic',limit=10,transport=answer)
   original=p.choose;calls=0
   def pause(rows,budget,workers=1):
    nonlocal calls
    calls+=1
    if calls==1:return original(rows,budget,workers)
    original(rows[:80],budget,workers)
    raise ProviderError('synthetic review pause after four paid responses')
   p.choose=pause
   r=Recorder(folder,p,2,['baseline'],21,100);self.assertFalse(r.run())
   self.assertEqual(p.requests,9)
   newcalls=[]
   def counted(body):newcalls.append(body);return answer(body)
   q=Jev('synthetic',limit=10,transport=counted)
   resumed=Recorder(folder,q,2,['baseline'],21,100,resume=True);self.assertTrue(resumed.run())
   self.assertEqual(q.requests,10);self.assertEqual(len(newcalls),1)
   with gzip.open(folder/'baseline.ln.json.gz','rt') as f:ep=json.load(f)
   self.assertEqual(ep['final']['round'],2);self.assertEqual(len(ep['decisions']),200)
   self.assertEqual(ep['provider']['requests'],10);self.assertEqual(len(ep['failures']),1)
if __name__=='__main__':unittest.main()
