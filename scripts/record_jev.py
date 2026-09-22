#!/usr/bin/env python3
"""Explicitly budgeted real Jev recordings. No fixture policy is called."""
import argparse
import datetime
import gzip
import json
import os
from pathlib import Path
import sys
import threading
import time
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import Simulation,SCENARIOS
from jev import Jev
from server import load_env
ROOT=Path(__file__).resolve().parents[1]

def atomic_json(path,data,compressed=False):
 tmp=path.with_name(path.name+'.tmp')
 opener=gzip.open if compressed else open
 kwargs={'compresslevel':3} if compressed else {}
 with opener(tmp,'wt',encoding='utf-8',**kwargs) as f:json.dump(data,f,allow_nan=False,separators=(',',':'))
 os.chmod(tmp,0o600)
 # Windows readers/scanners can briefly deny replacement. This retries only the
 # local rename of already-written bytes; it never repeats an inference request.
 for attempt in range(8):
  try:os.replace(tmp,path);break
  except PermissionError:
   if attempt==7:raise
   time.sleep(min(.025*2**attempt,.4))

class Recorder:
 def __init__(self,folder,provider,rounds,scenarios,seed,initial_cells=300,resume=False,extend=False,stop_on_demo=False):
  self.folder=Path(folder);self.folder.mkdir(parents=True,exist_ok=resume,mode=0o700)
  self.stop_on_demo=stop_on_demo;self.extend=extend
  self.initial_cells=initial_cells;self.provider=provider;self.rounds=rounds;self.scenarios=scenarios;self.seed=seed
  self.summary={'format':'lymph-node-live-session-v1','provider':'Jev','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'initial_cells':initial_cells,'authorized_request_limit':provider.limit,'target_rounds':rounds,'seed':seed,'scenarios':[],
    'status':'prepared','disclosure':'Uncalibrated simulation with actual Jev responses. Biological outcomes are not prescribed.'}
  self.resume_episode=None
  if resume:
   previous=json.loads((self.folder/'summary.json').read_text())
   if previous.get('status') not in (('partial','complete') if extend else ('partial',)) or len(previous.get('scenarios',[]))!=1 or scenarios!=[previous['scenarios'][0]['scenario']]:raise ValueError('Resume requires the same single partial scenario')
   if previous['seed']!=seed or (previous['target_rounds']!=rounds and not extend) or previous.get('initial_cells',300)!=initial_cells or (previous['authorized_request_limit']!=provider.limit and not extend):raise ValueError('Resume must preserve the original seed, population, duration and total request cap')
   if extend and (rounds<previous['target_rounds'] or provider.limit<previous['authorized_request_limit']):raise ValueError('Extension cannot reduce duration or cumulative budget')
   with gzip.open(self.folder/previous['scenarios'][0]['file'],'rt') as f:self.resume_episode=json.load(f)
   self.summary=previous;self.summary.setdefault('resume_history',[]).append({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason':'explicit protocol review; preserve exact paid batches and cumulative budget'})
   if extend:
    self.summary.setdefault('extensions',[]).append({'from_round':self.resume_episode['final']['round'],'old_target':previous['target_rounds'],'new_target':rounds,'old_limit':previous['authorized_request_limit'],'new_limit':provider.limit,'reason':'User authorized longer real demonstration within USD 5'})
    self.summary['target_rounds']=rounds;self.summary['authorized_request_limit']=provider.limit
   old_prompt=self.resume_episode.get('provider_prompt_version','lymph-node-choice-v1')
   if old_prompt!=provider.prompt_version:
    self.summary.setdefault('prompt_changes',[]).append({'round':self.resume_episode['final']['round'],'time_min':self.resume_episode['final']['time_min'],'old':old_prompt,'new':provider.prompt_version,'reason':'Explicitly revised decision context; see versioned prompt definitions. Kernel gates and clocks unchanged.'})
   usage=previous['usage']
   for attr in ('requests','input_tokens','output_tokens','unknown_usage','resolved_model'):setattr(provider,attr,usage[attr])
   if provider.model!=usage['model']:raise ValueError('Cannot change Jev model on resume')
   provider.audit=self.resume_episode['request_audit']
   pending=self.resume_episode.get('pending_round')
   if pending:
    ids={r['id'] for r in pending['rows']}
    provider.replay_cache={r['request_sha256']:r for r in provider.audit if r.get('response') and r.get('status')!='rejected_after_review' and set(r['cells'])<=ids}
  self.journal=open(self.folder/'audit.jsonl','a',encoding='utf-8');os.chmod(self.folder/'audit.jsonl',0o600)
  self.journal_lock=threading.Lock();self.current_scenario=None;self.current_round=None
  provider.on_audit=self.request_audit;self.save_summary()
 def write(self,entry):
  with self.journal_lock:
   self.journal.write(json.dumps(entry,allow_nan=False,separators=(',',':'))+'\n');self.journal.flush();os.fsync(self.journal.fileno())
 def request_audit(self,record):
  self.write({'event':'provider_request','scenario':self.current_scenario,'round':self.current_round,'record':record})
 def save_summary(self):
  self.summary['usage']=self.provider.status();atomic_json(self.folder/'summary.json',self.summary)
 def run(self,workers=1):
  self.summary['status']='running';self.save_summary();complete=True
  for scenario in self.scenarios:
   s=Simulation(seed=self.seed,scenario=scenario,initial_cells=self.initial_cells,params=self.resume_episode['contract']['parameters'] if self.resume_episode else None);self.current_scenario=scenario
   if self.resume_episode:
    ep=self.resume_episode
    for i in range(ep['final']['round']):
     rows=s.proposals();answers={d['cell']:d['proposal'] for d in ep['decisions'] if d['round']==i}
     s.step(answers,rows,source='jev')
    if s.snapshot()!=ep['final']:raise ValueError('Replay verification failed; no paid request sent')
    s.initial=ep['initial'];s.failures=ep['failures'];self.write({'event':'resume_verified','scenario':scenario,'round':s.round,'requests_already_spent':self.provider.requests})
   if self.extend:
    s.p['max_rounds']=max(s.p['max_rounds'],self.rounds)
    if s.stop_reason=='Configured duration reached; export or start a new run':s.stop_reason=None
   audit_start=0 if self.resume_episode else len(self.provider.audit);requests_start=0 if self.resume_episode else self.provider.requests
   usage_start=(0,0,0) if self.resume_episode else (self.provider.input_tokens,self.provider.output_tokens,self.provider.unknown_usage)
   path=self.folder/(scenario+'.ln.json.gz');pending=None
   entry=self.summary['scenarios'][0] if self.resume_episode else {'scenario':scenario,'file':path.name,'status':'running','rounds':0}
   if not self.resume_episode:self.summary['scenarios'].append(entry)
   def save(status):
    if status=='complete':entry.pop('error',None)
    ep=s.export();ep['provider_label']='jev';ep['recording_status']=status
    ep['provider']={**self.provider.status(),'provider':'jev','requests':self.provider.requests-requests_start,
      'input_tokens':self.provider.input_tokens-usage_start[0],'output_tokens':self.provider.output_tokens-usage_start[1],
      'unknown_usage':self.provider.unknown_usage-usage_start[2]}
    ep['branch_provenance']=self.summary.get('branch_provenance');ep['prompt_changes']=self.summary.get('prompt_changes',[]);ep['extensions']=self.summary.get('extensions',[]);ep['request_audit']=self.provider.audit[audit_start:];ep['pending_round']=pending
    ep['provider_validation_version']='choice-v2-rounded-probabilities';ep['provider_prompt_version']=self.provider.prompt_version;ep['prompt_version_note']='Earlier requests retain v1 full dictionaries; per-request hashes and optional prompt_version identify transitions.';ep['target_rounds']=self.rounds
    atomic_json(path,ep,compressed=True)
    entry.update(status=status,rounds=s.round,time_min=s.time,metrics=s.metrics(),usage=ep['provider'],
      gc_formed=any(e['event']=='germinal_center_formed' for e in s.events))
    self.save_summary()
   save('prepared')
   try:
    for i in range(s.round,self.rounds):
     self.current_round=i;rows=s.proposals();pending={'round':i,'time_min':s.time,'rows':rows}
     self.write({'event':'round_started','scenario':scenario,**pending})
     answers=self.provider.choose(rows,self.provider.limit,workers=workers)
     start_decisions=len(s.decisions);start_events=len(s.events)
     s.step(answers,rows,source='jev');pending=None
     self.write({'event':'round_completed','scenario':scenario,'round':i,'frame':s.frames[-1],
       'decision_receipts':[{k:v for k,v in d.items() if k not in ('observation','options')} for d in s.decisions[start_decisions:]],'events':s.events[start_events:]})
     entry.update(rounds=s.round,time_min=s.time,metrics=s.metrics());self.save_summary()
     if s.round%5==0:save('running')
     print(json.dumps({'scenario':scenario,'round':s.round,'target_rounds':self.rounds,
       'time_h':s.time/60,'requests_total':self.provider.requests,'gc_b':s.metrics()['gc_b'],
       'presenting':s.metrics()['presenting'],'memory':s.metrics()['memory'],'plasma':s.metrics()['plasma']},separators=(',',':')),flush=True)
     if self.stop_on_demo and s.births>0 and (s.metrics()['memory']>0 or any(c['state']=='plasma' for c in s.cells)):
      entry['completion_reason']='Observed physical division and memory or mature plasma output';break
    save('complete')
   except BaseException as e:
    message=str(e) if isinstance(e,Exception) else 'Interrupted by operator'
    s.failures.append({'time_min':s.time,'message':message,'provider':'jev','requests':self.provider.requests})
    entry['error']=message;save('partial');complete=False
    print(json.dumps({'status':'partial','scenario':scenario,'reason':message,'requests_total':self.provider.requests}),flush=True)
    break
  self.summary['status']='complete' if complete else 'partial';self.save_summary();self.journal.close()
  return complete

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--max-requests',type=int,required=True)
 p.add_argument('--rounds',type=int,default=90);p.add_argument('--scenarios',default='vaccine,baseline,no_help,mismatch,no_fdc')
 p.add_argument('--seed',type=int,default=21);p.add_argument('--workers',type=int,default=1)
 p.add_argument('--cells',type=int,choices=[100,300],default=300)
 p.add_argument('--output',type=Path)
 p.add_argument('--resume',action='store_true')
 p.add_argument('--extend',action='store_true',help='Explicitly authorize a longer duration/cumulative cap on resume')
 p.add_argument('--stop-on-demo',action='store_true')
 p.add_argument('--fate-context',action='store_true',help='Use explicit proposed qualitative competing fate rubric, prompt v4')
 p.add_argument('--biological-context',action='store_true',help='Explain implemented state names and program eligibility in Jev prompt v3')
 args=p.parse_args();scenarios=args.scenarios.split(',')
 if not 1<=args.max_requests<=100000 or not 1<=args.rounds<=480 or not 1<=args.workers<=4:p.error('Invalid request/round/worker limit')
 if len(set(scenarios))!=len(scenarios) or any(s not in SCENARIOS for s in scenarios):p.error('Unknown or repeated scenario')
 load_env();provider=Jev(limit=args.max_requests,biological_context=args.biological_context,fate_context=args.fate_context)
 if not provider.key:p.error('Configure the project server-side TYPESAFE_API_KEY first')
 folder=args.output or ROOT/'recordings/private'/('jev-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6])
 recorder=Recorder(folder,provider,args.rounds,scenarios,args.seed,args.cells,resume=args.resume,extend=args.extend,stop_on_demo=args.stop_on_demo)
 print('Live recording directory: '+str(folder),flush=True)
 sys.exit(0 if recorder.run(args.workers) else 2)
if __name__=='__main__':main()
