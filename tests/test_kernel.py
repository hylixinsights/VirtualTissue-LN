import copy
import json
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import Simulation,REGISTRY,alive,distance
from jev import Jev,ProviderError,request_body,validate
from server import Studio

class KernelTests(unittest.TestCase):
 def setUp(self): self.s=Simulation(scenario='baseline')
 def cell(self,kind): return next(c for c in self.s.cells if c['kind']==kind)
 def isolate(self,*cells):
  # Functional fixtures explicitly place a few interacting cells; not a whole-run calibration.
  for i,c in enumerate(cells):c['x']=i*10;c['y']=0
  for c in self.s.cells:
   if c not in cells:c['x']+=1000
 def prime_pair(self):
  t=self.cell('CD4');d=self.cell('DC');self.isolate(t,d)
  d['pmhc']=dict(antigen='fixture',source='fixture',peptide='P1',hla='HLA-II-A',expires=1000);d['costim']=True
  return t,d
 def help_pair(self):
  b=self.cell('B');t=self.cell('CD4');self.isolate(b,t)
  b.update(state='activated',pmhc=dict(antigen='fixture',source='fixture',peptide='P1',hla='HLA-II-A',expires=1000));t['state']='pre_tfh'
  return b,t
 def test_exact_population_geometry_and_identities(self):
  s=self.s;s.assert_invariants();self.assertEqual(len(s.cells),300)
  for k,r in REGISTRY.items():self.assertEqual(sum(c['kind']==k for c in s.cells),r['count'])
  self.assertTrue(all(c['z']==0 for c in s.cells));self.assertFalse(s.gc)
 def test_seed_is_reproducible(self):
  b=Simulation(scenario='baseline')
  for s in (self.s,b):
   for _ in range(3):r=s.proposals();s.step(s.fixture(r),r)
  self.assertEqual(self.s.export(),b.export())
 def test_baseline_does_not_activate(self):
  for _ in range(8):r=self.s.proposals();self.s.step(self.s.fixture(r),r)
  self.assertEqual(self.s.metrics()['presenting'],0);self.assertEqual(self.s.metrics()['gc_b'],0)
 def test_no_remote_neighbors_or_private_neighbor_clonotypes(self):
  c=self.cell('B');obs=self.s.observation(c)
  self.assertTrue(all(n['distance_um']<=42.01 for n in obs['nearby']))
  self.assertTrue(all('clone' not in n and 'affinity' not in n and 'bcr' not in n for n in obs['nearby']))
  self.assertNotIn('metrics',obs)
 def test_mismatch_cannot_prime(self):
  t,d=self.prime_pair();self.assertIn('PRIME',self.s.eligible(t));d['pmhc']['hla']='HLA-II-X';self.assertNotIn('PRIME',self.s.eligible(t))
 def test_costimulation_and_distance_are_required(self):
  t,d=self.prime_pair();d['costim']=False;self.assertNotIn('PRIME',self.s.eligible(t));d['costim']=True;d['x']=100;self.assertNotIn('PRIME',self.s.eligible(t))
 def test_linked_help_requires_matching_display_and_cd40(self):
  b,t=self.help_pair();self.assertIn('HELP',self.s.eligible(b));self.s.config['cd40']=False;self.assertNotIn('HELP',self.s.eligible(b));self.s.config['cd40']=True;b['pmhc']['peptide']='unrelated';self.assertNotIn('HELP',self.s.eligible(b))
 def test_gc_and_outputs_cannot_be_chosen_by_naive_b(self):
  c=self.cell('B');self.assertFalse(set(self.s.eligible(c))&{'ENTER_GC','DIVIDE','MEMORY','PLASMA','RECYCLE'})
 def test_no_gc_by_button_or_antigen_alone(self):
  self.s.inject();self.s.organize_gc();self.assertFalse(self.s.gc)
 def test_founders_require_delay_and_support(self):
  bs=[c for c in self.s.cells if c['kind']=='B'][:2]
  for c in bs:c.update(x=-48,y=25,state='founder',help_until=2000)
  self.s.organize_gc();self.assertFalse(self.s.gc)
  self.s.time=120
  for c in self.s.cells:
   if c['kind']=='FDC':c['cue_until']=150
  self.s.organize_gc();self.assertTrue(self.s.gc)
  self.assertTrue(all(c['state']=='dz' and c['gc_member'] for c in bs))
 def test_no_fdc_prevents_gc(self):
  for c in [c for c in self.s.cells if c['kind']=='B'][:3]:c.update(x=-48,y=25,state='founder',help_until=2000)
  self.s.config['fdc']=False;self.s.organize_gc();self.s.time=500;self.s.organize_gc();self.assertFalse(self.s.gc)
 def test_unqualified_founder_cannot_skip_gc(self):
  c=self.cell('B');c.update(state='founder',help_until=0)
  self.s.clocks();self.assertEqual(c['state'],'activated');self.assertFalse(c['gc_member'])
 def test_antigen_processing_is_timed_and_conservative(self):
  c=self.cell('DC');self.s.inject(1);a=self.s.antigens[0];a.update(x=c['x'],y=c['y']);aid=a['id']
  self.s.apply(c,'CAPTURE',aid);self.assertIsNone(c['pmhc']);self.assertEqual(a['pool'],'native_cargo')
  self.s.apply(c,'PROCESS',aid);self.s.time=59;self.s.clocks();self.assertIsNone(c['pmhc'])
  self.s.time=60;self.s.clocks();self.assertEqual(a['pool'],'processed_peptide');self.assertIsNone(c['pmhc'])
  self.s.time=90;self.s.clocks();self.assertEqual(c['pmhc']['antigen'],aid);self.assertEqual(a['pool'],'surface_pmhc');self.assertEqual(len(self.s.antigens),1)
 def test_two_consumers_do_not_duplicate_antigen(self):
  b1,b2=[c for c in self.s.cells if c['kind']=='B'][:2];self.isolate(b1,b2);b1['bcr']=b2['bcr']='E1';self.s.inject(1);a=self.s.antigens[0];a.update(x=5,y=0)
  # Full round conflict resolution is checked without changing the fixture's deliberate geometry.
  self.s.assert_invariants=lambda:None
  rows=self.s.proposals();ans=self.s.fixture(rows);self.s.step(ans,rows)
  self.assertEqual(sum(c['cargo']==a['id'] for c in (b1,b2)),1)
  self.assertTrue(any(d['result'].startswith('deferred') for d in self.s.decisions))
 def test_invalid_round_has_no_partial_biology(self):
  rows=self.s.proposals();a=self.s.fixture(rows);before=copy.deepcopy(self.s.snapshot());a[rows[-1]['id']]['choice']='BECOME_TUMOR'
  with self.assertRaises(ValueError):self.s.step(a,rows)
  self.assertEqual(self.s.snapshot(),before)
 def test_probabilities_must_be_finite_and_complete(self):
  rows=self.s.proposals();a=self.s.fixture(rows);a[rows[0]['id']]['probabilities']['WAIT']=float('nan')
  with self.assertRaises(ValueError):self.s.step(a,rows)
 def test_division_replaces_parent_and_preserves_ancestry(self):
  c=self.cell('B');self.isolate(c);c.update(state='dz',division_budget=0,gc_member=True)
  self.s.divide(c);children=[n for n in self.s.cells if n['parent']==c['id']]
  self.assertEqual(c['state'],'divided');self.assertEqual(len(children),2);self.assertEqual(self.s.births,1)
  self.assertTrue(all(n['clone']==c['clone'] and n['lineage']=='B' and n['division_budget']==0 and n['help_until']==0 for n in children))
 def test_space_restriction_does_not_delete_unrelated_cells(self):
  c=self.cell('B');self.s.can_place=lambda *args:False;n=len(self.s.cells);self.s.divide(c)
  self.assertEqual(len(self.s.cells),n);self.assertEqual(self.s.births,0)
 def test_apoptosis_cancels_pending_division(self):
  c=self.cell('B');c.update(state='lz',selection_since=0,program=dict(action='DIVIDE',due=1440,target=None));self.s.time=1440;self.s.clocks()
  self.assertEqual(c['state'],'apoptotic');self.assertIsNone(c['program']);self.assertEqual(self.s.births,0)
 def test_terminal_and_memory_cells_do_not_divide(self):
  c=self.cell('B');c['division_budget']=3
  for state in ('plasma','memory','apoptotic'):
   c['state']=state;self.assertNotIn('DIVIDE',self.s.eligible(c))
  c['state']='memory';self.assertNotIn('SECRETE',self.s.eligible(c))
 def test_export_contains_every_decision_and_frame(self):
  r=self.s.proposals();self.s.step(self.s.fixture(r),r);ex=self.s.export()
  self.assertEqual(len(ex['decisions']),300);self.assertEqual(len(ex['frames']),2);self.assertEqual(len(ex['fingerprint']),64)

class RecordingTests(unittest.TestCase):
 def test_frame_prefixes_exclude_future_decisions_and_events(self):
  s=Simulation(scenario='baseline');s.inject(1)
  for _ in range(2):
   r=s.proposals();s.step(s.fixture(r),r)
  f=s.frames[1];prefix=s.decisions[:f['metrics']['decisions']]
  self.assertEqual(len(prefix),300)
  self.assertTrue(all(d['time_min']<f['time_min'] for d in prefix))
  self.assertLessEqual(f['event_count'],len(s.events))

class JevTests(unittest.TestCase):
 def setUp(self):self.rows=Simulation(scenario='baseline').proposals()[:2]
 def answer(self,body):
  return dict(model='jev-1.13.0',usage=dict(input_tokens=20,output_tokens=10),answers={k:dict(type='choice',choice='WAIT',probabilities={a:float(a=='WAIT') for a in q['criteria']},confidence=1) for k,q in body['questions'].items()})
 def test_one_independent_question_per_cell(self):
  b=request_body(self.rows,'jev-1.13.0');self.assertEqual(len(b['questions']),2);self.assertNotIn('cells',b['state'])
  self.assertTrue(all('local_observation' in q['instructions'] for q in b['questions'].values()))
 def test_valid_response_and_usage(self):
  p=Jev('synthetic-key',limit=1,transport=self.answer);a=p.choose(self.rows,1);self.assertEqual(len(a),2);self.assertEqual(p.requests,1);self.assertEqual(p.input_tokens,20)
 def test_cap_is_enforced_before_remote_call(self):
  p=Jev('synthetic',limit=0,transport=lambda _:self.fail('Must not call'))
  with self.assertRaises(ProviderError):p.choose(self.rows,0)
  self.assertEqual(p.requests,0)
 def test_missing_or_invalid_response_rejected(self):
  body=request_body(self.rows,'jev-1.13.0');result=self.answer(body);result['answers'].pop(self.rows[0]['id'])
  with self.assertRaises(ProviderError):validate(result,self.rows)
 def test_timeout_preserves_unknown_usage_without_retry(self):
  def fail(_):raise ProviderError('timeout')
  p=Jev('synthetic',limit=5,transport=fail)
  with self.assertRaises(ProviderError):p.choose(self.rows,5)
  self.assertEqual(p.requests,1);self.assertEqual(p.unknown_usage,1)
 def test_no_secret_in_status_or_audit(self):
  p=Jev('secret-placeholder',limit=1,transport=self.answer);p.choose(self.rows,1)
  self.assertNotIn('secret-placeholder',json.dumps([p.status(),p.audit]))
 def test_studio_requires_explicit_live_enablement(self):
  s=Studio()
  with self.assertRaises(ValueError):s.dispatch('/api/reset',dict(provider='jev',budget=100))
  self.assertEqual(s.provider,'fixture')

if __name__=='__main__':unittest.main(verbosity=2)
