#!/usr/bin/env python3
"""Record local Jev decisions through the user-defined request budget."""
import argparse
import copy
import datetime
import gzip
import json
import math
import os
import shutil
import socket
from pathlib import Path
import sys
import threading
import uuid
import webbrowser
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import STATES,alive
from jev import Jev
from reactive import PROMPT
from recording import RecordingSimulation
from server import Handler,ThreadingHTTPServer,ROOT,load_env
from scripts.record_jev import atomic_json

POLICIES={
    'development':'Competing-fate demonstration: a proposed local affinity threshold favors early output or GC expansion; output cells can mature and secrete. Uncalibrated.',
    'local':'Local model semantics with no requested fate preference. Biological outcomes are not guaranteed.',
    'plasmablast':'High conditional plasmablast/secretion preference. Proposed demonstration policy; uncalibrated.'}


class ReactiveRecorder:
    homepage='/web/reactive.html'
    def __init__(self,folder,cap,seed=21,cells=120,policy='development',workers=4,batch_size=1,provider=None,resume=False):
        if type(cap) is not int or not 1<=cap<=100000:raise ValueError('Set a per-run request cap between 1 and 100,000.')
        if policy not in POLICIES:raise ValueError('Unknown decision policy')
        if not 1<=workers<=4 or not 1<=batch_size<=20:raise ValueError('Invalid request concurrency or batch size')
        self.lock=threading.RLock();self.audit_lock=threading.Lock();self.token=uuid.uuid4().hex
        self.stop_requested=threading.Event();self.workers=workers;self.batch_size=batch_size
        self.provider=provider or Jev(limit=cap,biological_context=True,development_context=policy=='development',plasmablast_context=policy=='plasmablast')
        if not self.provider.key or self.provider.limit!=cap:raise ValueError('A server-side key and matching request cap are required.')
        self.resumed=resume;self.folder=Path(folder)
        previous=None
        if resume:
            path=self.folder/'episode.ln.json.gz'
            previous=json.loads(gzip.decompress(path.read_bytes()));control=previous['run_control'];usage=previous['provider']
            if previous['recording_status'] not in ('failed','stopped') or previous.get('pending_round') is not None:
                raise ValueError('Resume requires a stopped/failed checkpoint with no incomplete decision round.')
            if (previous['seed'],previous['contract']['initial_cells'],control['request_cap'],control['policy_name'])!=(seed,cells,cap,policy):
                raise ValueError('Resume must preserve seed, population, policy and the total call cap.')
            if usage['model']!=self.provider.model or previous['provider_prompt_version']!=self.provider.prompt_version:
                raise ValueError('Resume must preserve the Jev model and prompt version.')
            from scripts.review_reactive_recording import review
            review(path)
            # A checkpoint must include every journaled attempt and completed tick.
            with (self.folder/'audit.jsonl').open(encoding='utf-8') as journal:
                for line in journal:
                    entry=json.loads(line)
                    if entry['event']=='provider_request' and entry['record']['request']>usage['requests']:
                        raise ValueError('Uncheckpointed paid request exists; explicit audit recovery is required.')
                    if entry['event']=='round_completed' and entry['round']>previous['final']['round']:
                        raise ValueError('Uncheckpointed biological tick exists; explicit audit recovery is required.')
            self.sim=RecordingSimulation.restore(previous)
            for attr in ('requests','input_tokens','output_tokens','unknown_usage','resolved_model'):setattr(self.provider,attr,usage[attr])
            self.provider.audit=previous['request_audit']
            backup=self.folder/('episode.before-resume-'+uuid.uuid4().hex[:8]+'.ln.json.gz');shutil.copy2(path,backup)
        else:
            self.sim=RecordingSimulation(seed=seed,initial_cells=cells,params={'max_rounds':cap*12+1000})
            self.folder.mkdir(parents=True,exist_ok=False)
        self.journal=(self.folder/'audit.jsonl').open('a' if resume else 'x',encoding='utf-8')
        self.provider.on_audit=lambda record:self.write(dict(event='provider_request',round=self.sim.round,time_min=self.sim.time,record=record))
        self.control=dict(managed=True,status='prepared',request_cap=cap,cumulative_requests=0,prior_requests=0,
            policy=self.provider.prompt_version,policy_name=policy,policy_description=POLICIES[policy],
            stop_condition='Continue beyond all biological milestones until the request cap, a provider failure, or a terminal quiet response.',
            message='Preparing a continuous recording.',outcome=None,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            batch_size=batch_size,workers=workers,playback_available=False,user_stoppable=True)
        self.pending_round=None;self.idle_ticks=0;self.last_checkpoint=0;self.last_print=-25
        if previous:
            self.control=copy.deepcopy(previous['run_control'])
            self.control.update(status='prepared',message='Saved state verified; continuing within the original call allowance.',playback_available=False,user_stoppable=True)
            self.control.pop('stop_requested',None)
            history=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),previous_status=previous['recording_status'],
                requests_already_spent=self.provider.requests,round=self.sim.round,
                reason='Explicit continuation after exact saved-state reconstruction; no previous API request repeated.')
            self.control.setdefault('resume_history',[]).append(history);self.write(dict(event='resume_verified',**history))
            for frame in reversed(self.sim.timeline):
                if frame['metrics']['queried_last_step'] or frame['metrics']['busy']:break
                self.idle_ticks+=1
        self.save(checkpoint=True)

    def write(self,entry):
        with self.audit_lock:
            self.journal.write(json.dumps(entry,separators=(',',':'),allow_nan=False)+'\n')
            self.journal.flush();os.fsync(self.journal.fileno())

    def status(self):return dict(provider='jev',enabled=False,**self.provider.status())
    def state(self):return dict(tissue=self.sim.snapshot(),provider=self.status(),registry=self.sim.registry,states=STATES,
        mode='reactive',decision_cap=self.provider.limit*20,run_control=copy.deepcopy(self.control))
    def dispatch(self,path,body):
        if path=='/api/stop':
            self.stop_requested.set();self.control['stop_requested']=True
            self.control['message']='Finishing and saving any in-flight requests. No new round will start.'
            return self.state()
        raise ValueError('The recorder owns this run. Playback and inspection make no inference calls.')
    def export(self):
        result=self.sim.export()
        result.update(provider_label='jev',provider=self.status(),request_audit=copy.deepcopy(self.provider.audit),
            provider_prompt_version=self.provider.prompt_version,run_control=copy.deepcopy(self.control),
            pending_round=copy.deepcopy(self.pending_round),recording_status=self.control['status'])
        return result

    def save(self,checkpoint=False):
        self.control['cumulative_requests']=self.provider.requests
        atomic_json(self.folder/'summary.json',dict(format='lymph-node-reactive-recording-summary-v1',**self.control,
            seed=self.sim.seed,round=self.sim.round,time_min=self.sim.time,metrics=self.sim.metrics(),usage=self.provider.status()))
        if checkpoint:
            atomic_json(self.folder/'episode.ln.json.gz',self.export(),compressed=True)
            atomic_json(self.folder/'live.json',self.state())
            self.last_checkpoint=self.provider.requests

    def tick(self):
        with self.lock:
            if self.control['status']!='running':return False
            if self.stop_requested.is_set():
                self.control.update(status='stopped',message='Stopped after recording all completed requests.',playback_available=True);self.save(True);return False
            remaining=self.provider.limit-self.provider.requests
            rows=self.sim.proposals()
            # Near the ceiling, pack the remaining independent questions together
            # to preserve complete atomic rounds without exceeding the HTTP cap.
            size=max(self.batch_size,math.ceil(len(rows)/max(1,remaining)))
            if remaining<=0 or size>20:
                message='The per-run request limit was reached.' if remaining<=0 else 'The remaining allowance cannot cover a complete decision round.'
                self.control.update(status='budget_reached',message=message+' Recording is ready for playback.',playback_available=True);self.save(True);return False
            self.pending_round=dict(round=self.sim.round,time_min=self.sim.time,rows=rows,batch_size=size)
            self.control['message']=f'Recording {len(rows)} local cell decisions; the run continues after antibody output.' if rows else 'Advancing timed biological processes; no Jev call is needed.'
            if rows:self.write(dict(event='round_started',**self.pending_round))
        answers=self.provider.choose(rows,self.provider.limit,workers=self.workers,batch_size=size) if rows else {}
        with self.lock:
            before_events=len(self.sim.events);before_decisions=len(self.sim.decisions)
            self.sim.step(answers,rows,'jev');self.pending_round=None
            self.write(dict(event='round_completed',round=self.sim.round,time_min=self.sim.time,
                decisions=self.sim.decisions[before_decisions:],events=self.sim.events[before_events:],frame=self.sim.timeline[-1]))
            if not self.control['outcome']:
                secretion=next((e for e in self.sim.events[before_events:] if e['event']=='antibody_secreted'),None)
                if secretion:self.control['outcome']=dict(cell=secretion['cell'],time_min=secretion['time_min'],isotype='IgM')
            self.idle_ticks=self.idle_ticks+1 if not rows and not any(c['program'] for c in self.sim.cells if alive(c)) else 0
            exhausted=self.sim.injected and all(a['pool']=='degraded' for a in self.sim.antigens) and not any(
                alive(c) and c['kind']=='B' and (c['state'] not in ('naive','resting','memory') or c['program']) for c in self.sim.cells)
            if self.provider.requests>=self.provider.limit:
                self.control.update(status='budget_reached',message='The per-run request limit was reached. Recording is ready for playback.')
            elif exhausted or self.idle_ticks>=72:
                self.control.update(status='quiescent',message='The local response is exhausted; no additional perturbation was inserted.')
            done=self.control['status']!='running'
            self.control['playback_available']=done
            self.save(checkpoint=done or self.provider.requests-self.last_checkpoint>=100)
            if self.provider.requests-self.last_print>=25 or done:
                m=self.sim.metrics();print(json.dumps(dict(status=self.control['status'],requests=self.provider.requests,time_h=round(self.sim.time/60,2),
                    decisions=m['decisions'],divisions=m['net_births'],plasma=m['plasma'],IgM=m['antibodies'],never_queried=m['never_queried'])),flush=True)
                self.last_print=self.provider.requests
            return not done

    def run(self):
        try:
            with self.lock:
                if not self.resumed:self.sim.perturb(PROMPT);self.sim.save_frame()
                self.control['status']='running';self.save(True)
            while self.tick():pass
        except BaseException as error:
            with self.lock:
                message=str(error).replace(self.provider.key,'[redacted]') if isinstance(error,Exception) else 'Interrupted by operator'
                self.control.update(status='failed',message=message,playback_available=True)
                self.sim.failures.append(dict(time_min=self.sim.time,message=message,requests=self.provider.requests))
                self.save(True)
                print(json.dumps(dict(status='failed',message=message,usage=self.provider.status())),flush=True)
        finally:
            self.journal.close();print('Recording stopped: '+json.dumps(self.control),flush=True)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-requests',type=int,required=True)
    parser.add_argument('--seed',type=int,default=21);parser.add_argument('--cells',type=int,default=120)
    parser.add_argument('--policy',choices=POLICIES,default='development')
    parser.add_argument('--workers',type=int,default=4);parser.add_argument('--batch-size',type=int,default=1)
    parser.add_argument('--port',type=int,default=8022);parser.add_argument('--output',type=Path)
    parser.add_argument('--open-browser',action='store_true')
    parser.add_argument('--resume',action='store_true',help='Explicitly verify and continue a fully checkpointed stopped run; retain the total call cap.')
    args=parser.parse_args(argv);load_env()
    if args.resume and not args.output:parser.error('--resume requires the existing --output folder.')
    folder=args.output or ROOT/'recordings/private'/('continuous-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6])
    # Reserve the address before creating or changing any saved run.
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler,bind_and_activate=False)
    try:
        # SO_REUSEADDR permits duplicate listeners on Windows. Reserve this
        # address exclusively before a paid recorder can be initialized.
        if hasattr(socket,'SO_EXCLUSIVEADDRUSE'):
            server.allow_reuse_address=False
            server.socket.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
        server.server_bind();server.server_activate()
    except OSError:
        server.server_close()
        raise OSError(f'Local LN port {args.port} is unavailable. Close the previous LN server or choose another --port.') from None
    except BaseException:server.server_close();raise
    try:app=ReactiveRecorder(folder,args.max_requests,args.seed,args.cells,args.policy,args.workers,args.batch_size,resume=args.resume)
    except BaseException:server.server_close();raise
    server.studio=app
    worker=threading.Thread(target=app.run,daemon=False);worker.start()
    print(f'Continuous recording: http://127.0.0.1:{args.port}/ ; saved in {folder}',flush=True)
    if args.open_browser:webbrowser.open(f'http://127.0.0.1:{args.port}/')
    try:server.serve_forever()
    except KeyboardInterrupt:
        app.stop_requested.set();print('Finishing and saving any in-flight requests…',flush=True);worker.join()
    finally:server.server_close()

if __name__=='__main__':main()
