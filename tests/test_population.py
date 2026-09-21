import math,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import Simulation

class PopulationTests(unittest.TestCase):
 def test_exact_100_cells_all_lineages_no_overlap(self):
  for seed in (1,21,42):
   s=Simulation(seed=seed,initial_cells=100);s.assert_invariants()
   self.assertEqual(len(s.cells),100);self.assertEqual(s.metrics()['initial'],100)
   self.assertEqual(s.metrics()['types'],dict(B=46,CD4=29,DC=5,MAC=6,FDC=6,FRC=5,LEC=3))
 def test_density_radius_and_antigen_scaling(self):
  a=Simulation(initial_cells=100);b=Simulation()
  self.assertAlmostEqual(a.p['radius_um']**2/b.p['radius_um']**2,1/3)
  self.assertEqual(a.p['cell_radius_um'],b.p['cell_radius_um']);self.assertEqual(a.injected,160)
  self.assertAlmostEqual(a.follicle[0],b.follicle[0]/math.sqrt(3))
 def test_100_cell_round_accounting_and_export(self):
  s=Simulation(initial_cells=100);rows=s.proposals();s.step(s.fixture(rows),rows)
  self.assertEqual(len(s.decisions),100);s.assert_invariants();ex=s.export()
  self.assertEqual(ex['contract']['initial_cells'],100)
  self.assertEqual(sum(r['count'] for r in ex['contract']['registry'].values()),100)
 def test_invalid_population_rejected(self):
  for n in (0,99,101,True,100.0):
   with self.assertRaises(ValueError):Simulation(initial_cells=n)
if __name__=='__main__':unittest.main()
