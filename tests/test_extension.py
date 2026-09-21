import contextlib,gzip,io,json,tempfile,unittest
from pathlib import Path
from jev import Jev
from scripts.record_jev import Recorder

def fixture(body):
 return {'model':'test','usage':{'input_tokens':10,'output_tokens':2},'answers':{k:{'type':'choice','choice':'WAIT','confidence':1,'probabilities':{a:int(a=='WAIT') for a in q['criteria']}} for k,q in body['questions'].items()}}
class Extension(unittest.TestCase):
 def test_completed_run_extends_without_repaying_prefix(self):
  with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
   folder=Path(tmp)/'run';p=Jev(key='fixture',model='test',limit=10,transport=fixture)
   self.assertTrue(Recorder(folder,p,2,['baseline'],21,100).run())
   before=json.load(gzip.open(folder/'baseline.ln.json.gz','rt'))
   p=Jev(key='fixture',model='test',limit=20,transport=fixture)
   self.assertTrue(Recorder(folder,p,3,['baseline'],21,100,resume=True,extend=True).run())
   after=json.load(gzip.open(folder/'baseline.ln.json.gz','rt'))
   self.assertEqual(p.requests,15);self.assertEqual(after['decisions'][:200],before['decisions'])
   self.assertEqual(after['initial'],before['initial']);self.assertEqual(after['final']['round'],3)
   self.assertEqual(after['extensions'][-1]['old_limit'],10)
 def test_budget_cannot_shrink(self):
  with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
   folder=Path(tmp)/'run';p=Jev(key='fixture',model='test',limit=10,transport=fixture)
   Recorder(folder,p,1,['baseline'],21,100).run()
   with self.assertRaises(ValueError):Recorder(folder,Jev(key='fixture',model='test',limit=9),2,['baseline'],21,100,resume=True,extend=True)
