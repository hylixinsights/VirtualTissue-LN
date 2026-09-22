"""Lossless visual deltas for a reactive recording; biological gates are inherited."""
import copy
import hashlib
import json
from collections import defaultdict
from reactive import ReactiveSimulation


class RecordingSimulation(ReactiveSimulation):
    def __init__(self,*args,**kwargs):
        self.timeline=[];self._visual_cells={};self._last_receipts={};self._receipt_count=0
        super().__init__(*args,**kwargs)

    def observation(self,c):
        result=super().observation(c)
        result['own_antibody_units']=c['antibodies']
        return result

    def save_frame(self):
        snapshot=self.snapshot()
        for i in range(self._receipt_count,len(self.decisions)):
            self._last_receipts[self.decisions[i]['cell']]=i
        self._receipt_count=len(self.decisions)
        current={};changes=[]
        for cell in snapshot['cells']:
            cell.pop('last_decision',None)
            cell['receipt_index']=self._last_receipts.get(cell['id'])
            current[cell['id']]=cell
            previous=self._visual_cells.get(cell['id'],{})
            delta={k:v for k,v in cell.items() if k not in previous or previous[k]!=v}
            if delta:changes.append(dict(id=cell['id'],**{k:v for k,v in delta.items() if k!='id'}))
        self.timeline.append(dict(time_min=self.time,round=self.round,gc=self.gc,gc_center=copy.deepcopy(self.gc_center),
            metrics=snapshot['metrics'],event_count=len(self.events),decision_count=len(self.decisions),
            changes=changes,removed=list(self._visual_cells.keys()-current.keys()),antigens=snapshot['antigens']))
        self._visual_cells=current

    def export(self):
        result=super().export()
        result.update(format='lymph-node-reactive-recording-v1',timeline=self.timeline,
            recording_observations='Own cumulative antibody output is included; all other observations and biological gates are inherited from the reactive kernel.')
        result['contract']['recording_observations']=['own_antibody_units']
        result['fingerprint']=hashlib.sha256(json.dumps(result['contract'],sort_keys=True).encode()).hexdigest()
        return result

    @classmethod
    def restore(cls,episode):
        """Rebuild exact kernel/RNG state from recorded choices, with no inference."""
        canonical=lambda value:json.dumps(value,sort_keys=True,allow_nan=False)
        sim=cls(seed=episode['seed'],initial_cells=episode['contract']['initial_cells'],params=episode['contract']['parameters'])
        if len(episode['inputs'])!=1:raise ValueError('Resume requires exactly one recorded perturbation.')
        sim.perturb(episode['inputs'][0]['prompt'])
        saved=defaultdict(list)
        for decision in episode['decisions']:saved[decision['round']].append(decision)
        # Reuse the verified original visual history after replaying the kernel.
        # Avoid recreating thousands of redundant visual copies during recovery.
        sim.save_frame=lambda:None
        for round_number in range(episode['final']['round']):
            rows=sim.proposals();receipts={d['cell']:d for d in saved[round_number]}
            if {r['id'] for r in rows}!=set(receipts):raise ValueError('Replay decision eligibility differs; no request sent.')
            for row in rows:
                d=receipts[row['id']]
                if canonical([row['observation'],row['options']])!=canonical([d['observation'],d['options']]):raise ValueError('Replay local observations differ; no request sent.')
            sim.step({cid:d['proposal'] for cid,d in receipts.items()},rows,'jev')
            if round_number and round_number%2000==0:print(f'Verifying saved biological tick {round_number:,} / {episode["final"]["round"]:,}; no API calls.',flush=True)
        for actual,expected in [(sim.snapshot(),episode['final']),(sim.decisions,episode['decisions']),(sim.events,episode['events']),(sim.antigens,episode['antigen_ledger'])]:
            if canonical(actual)!=canonical(expected):raise ValueError('Exact saved-state replay failed; no request sent.')
        del sim.save_frame
        sim.failures=episode['failures'];sim.timeline=episode['timeline']
        cells={}
        for frame in sim.timeline:
            for cid in frame['removed']:cells.pop(cid,None)
            for delta in frame['changes']:cells.setdefault(delta['id'],{}).update(copy.deepcopy(delta))
        sim._visual_cells=cells;sim._receipt_count=len(sim.decisions)
        sim._last_receipts={d['cell']:i for i,d in enumerate(sim.decisions)}
        return sim


def replay_cells(episode):
    """Reconstruct frames for verification without running a policy or inference."""
    cells={}
    for frame in episode['timeline']:
        for cid in frame['removed']:cells.pop(cid,None)
        for delta in frame['changes']:cells.setdefault(delta['id'],{}).update(copy.deepcopy(delta))
        yield frame,copy.deepcopy(cells)
