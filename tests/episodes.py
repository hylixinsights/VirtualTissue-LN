"""Bounded integration scenarios; fixtures only, zero external API calls."""
import gzip,json,sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import Simulation
ROOT=Path(__file__).resolve().parents[1]
report=ROOT/'docs/episode-verification.json'
results=json.loads(report.read_text()) if report.exists() else {}
for scenario in (sys.argv[1:] or ('vaccine','baseline','no_help','mismatch','no_fdc')):
 s=Simulation(seed=21,scenario=scenario)
 for i in range(90):
  rows=s.proposals();s.step(s.fixture(rows),rows)
  if scenario!='vaccine':s.decisions.clear();s.frames.clear()
 metrics=s.metrics();events=Counter(e['event'] for e in s.events)
 if scenario=='vaccine':
  assert events['germinal_center_formed']>=1
  assert events['division']>=1 and metrics['memory']>=1 and metrics['plasma']>=1 and metrics['antibodies']>0
  episode=s.export();episode['provider_label']='fixture';episode['paid_requests']=0
  with gzip.open(ROOT/'recordings/demo-fixture.ln.json.gz','wt') as f:json.dump(episode,f,separators=(',',':'))
 else:
  assert events['germinal_center_formed']==0
  if scenario in ('baseline','no_help','mismatch'):assert metrics['plasma']==0 and metrics['memory']==0
  if scenario=='baseline':assert metrics['presenting']==0 and not s.antigens
 results[scenario]=dict(seed=21,time_min=s.time,metrics=metrics,event_counts=dict(events),paid_requests=0)
 print(scenario,metrics['live'],'cells;',metrics['gc_b'],'GC B;',metrics['plasma'],'plasma;',metrics['memory'],'memory',flush=True)
(ROOT/'docs/episode-verification.json').write_text(json.dumps(results,indent=2))
