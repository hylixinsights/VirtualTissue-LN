#!/usr/bin/env python3
"""Verify a completed recording against paid responses, hashes and visual deltas."""
import argparse
from collections import Counter,defaultdict,deque
import gzip
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from jev import request_body,validate
from engine import alive


def review(path):
    raw=Path(path).read_bytes();e=json.loads(gzip.decompress(raw))
    assert e['format']=='lymph-node-reactive-recording-v1'
    assert e['recording_status'] not in ('running','prepared')
    pending=defaultdict(deque)
    for d in e['decisions']:
        assert d['source']=='jev'
        pending[d['cell']].append(d)
    receipts=0;input_tokens=0;output_tokens=0;unknown=0
    for a in sorted(e['request_audit'],key=lambda a:a['request']):
        assert a['status']=='validated','This reviewer requires all requests to have validated responses.'
        decisions=[pending[cid].popleft() for cid in a['cells']]
        assert len({d['round'] for d in decisions})==1
        rows=[dict(id=d['cell'],observation=d['observation'],options=d['options']) for d in decisions]
        version=a['prompt_version'];v5=version=='lymph-node-choice-v5-proposed-plasmablast-preference';v6=version=='lymph-node-choice-v6-proposed-development-policy'
        assert version in ('lymph-node-choice-v3-model-semantics','lymph-node-choice-v5-proposed-plasmablast-preference','lymph-node-choice-v6-proposed-development-policy')
        body=request_body(rows,a['model_requested'],True,plasmablast_context=v5,development_context=v6)
        assert hashlib.sha256(json.dumps(body,sort_keys=True,allow_nan=False).encode()).hexdigest()==a['request_sha256']
        answers=validate(a['response'],rows)
        for d in decisions:assert d['proposal']==answers[d['cell']]
        receipts+=len(decisions)
        if isinstance(a.get('usage'),dict):input_tokens+=a['usage']['input_tokens'];output_tokens+=a['usage']['output_tokens']
        else:unknown+=1
    assert all(not q for q in pending.values())
    assert receipts==len(e['decisions'])
    u=e['provider'];assert u['requests']==len(e['request_audit'])<=e['run_control']['request_cap']
    assert sorted(a['request'] for a in e['request_audit'])==list(range(1,u['requests']+1))
    assert (input_tokens,output_tokens,unknown)==(u['input_tokens'],u['output_tokens'],u['unknown_usage'])
    cells={}
    for f in e['timeline']:
        for cid in f['removed']:cells.pop(cid,None)
        for delta in f['changes']:cells.setdefault(delta['id'],{}).update(delta)
        assert sum(alive(c) for c in cells.values())==f['metrics']['live']
        assert f['metrics']['live']==f['metrics']['initial']+f['metrics']['entries']+f['metrics']['net_births']-f['metrics']['deaths']
        assert all(c['z']==0 for c in cells.values())
    final={c['id']:c for c in e['final']['cells']};assert set(cells)==set(final)
    for cid,c in cells.items():
        assert {k:v for k,v in c.items() if k!='receipt_index'}=={k:v for k,v in final[cid].items() if k!='last_decision'}
    assert e['timeline'][-1]['metrics']==e['final']['metrics']
    assert len(e['antigen_ledger'])==e['final']['metrics']['antigen_input']==9
    events=Counter(v['event'] for v in e['events'])
    assert events['division']==e['final']['metrics']['net_births']
    assert events['antibody_secreted']==e['final']['metrics']['antibodies']
    for event in e['events']:
        if event['event']=='division':
            daughters=[c for c in e['cell_ancestry'] if c['parent']==event['cell']]
            assert len(daughters)==2 and {c['id'] for c in daughters}==set(event['daughters'])
            assert all(c['clone']==event['clone'] for c in daughters)
    milestones=[]
    for event_name,action,label in [('dendritic_cell_arrived',None,'DC entry'),('program_completed','HELPER','Border helper'),('program_completed','HELP','Linked help completed; helper becomes Tfh'),('germinal_center_formed',None,'GC'),('division',None,'Division'),('program_completed','PLASMA','Plasmablast'),('antibody_secreted',None,'First IgM'),('program_completed','MATURE','Plasma cell')]:
        event=next((v for v in e['events'] if v['event']==event_name and (action is None or v.get('action')==action)),None)
        if event:milestones.append(dict(event=label,time_min=event['time_min'],cell=event.get('cell')))
    return dict(format='lymph-node-continuous-review-v1',sha256=hashlib.sha256(raw).hexdigest(),status=e['recording_status'],
        model=u['resolved_model'],requests=u['requests'],input_tokens=input_tokens,output_tokens=output_tokens,unknown_usage=unknown,
        decisions=receipts,frames=len(e['timeline']),time_min=e['final']['time_min'],metrics=e['final']['metrics'],
        milestones=milestones,all_request_hashes_verified=True,all_choices_match_provider=True,all_visual_frames_accounted=True,
        daughter_lineages_verified=True,recorded_interruptions=len(e['failures']),resumptions=e['run_control'].get('resume_history',[]),policy=e['run_control']['policy_description'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('recording',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=review(args.recording);args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
