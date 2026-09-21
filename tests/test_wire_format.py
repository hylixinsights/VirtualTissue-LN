import hashlib,json,unittest
from engine import Simulation
from jev import Jev,pack_observation,request_body,request_body_v1

class WireFormat(unittest.TestCase):
 def test_lossless_local_observations(self):
  for row in Simulation(initial_cells=100).proposals():
   packed=pack_observation(row['observation'])
   for field in ('nearby','accessible_antigen','cargo'):
    table=packed.get(field)
    if isinstance(table,dict) and 'columns' in table:
     packed[field]=[dict(zip(table['columns'],r)) for r in table['rows']]
   self.assertEqual(packed,row['observation'])
 def test_legacy_paid_batch_is_reused(self):
  rows=Simulation(initial_cells=100).proposals()[:20]
  response={'model':'test','answers':{r['id']:{'type':'choice','choice':'WAIT','confidence':1,'probabilities':{k:int(k=='WAIT') for k in r['options']}} for r in rows}}
  provider=Jev(key='synthetic',model='test',limit=1,transport=lambda _:self.fail('Paid cache must prevent a request'))
  fingerprint=hashlib.sha256(json.dumps(request_body_v1(rows,'test'),sort_keys=True,allow_nan=False).encode()).hexdigest()
  provider.replay_cache[fingerprint]={'status':'validated','response':response}
  self.assertEqual(len(provider.choose(rows,1)),20);self.assertEqual(provider.requests,0)
 def test_smaller_request(self):
  rows=Simulation(initial_cells=100).proposals()[:20]
  self.assertLess(len(json.dumps(request_body(rows,'test'))),len(json.dumps(request_body_v1(rows,'test')))*0.8)
