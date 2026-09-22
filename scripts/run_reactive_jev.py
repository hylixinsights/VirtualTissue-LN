#!/usr/bin/env python3
"""Budgeted, server-managed reactive LN run; stop on verified IgM secretion."""
import argparse
import copy
import datetime
import gzip
import json
import os
from pathlib import Path
import sys
import threading
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from reactive import ReactiveSimulation, PROMPT
from server import ReactiveStudio, Handler, ThreadingHTTPServer, load_env, ROOT
from jev import Jev
from engine import alive
from scripts.record_jev import atomic_json


class SavedOutcome:
    """View an existing result without constructing a provider or reading a key."""
    homepage='/web/reactive.html'
    def __init__(self,folder):
        self.lock=threading.RLock();self.token=uuid.uuid4().hex
        folder=Path(folder)
        self.saved_state=json.loads((folder/'live.json').read_text(encoding='utf-8'))
        self.episode=json.loads(gzip.decompress((folder/'episode.ln.json.gz').read_bytes()))
        if self.saved_state['run_control']['status'] in ('prepared','running'):
            raise ValueError('This record is still marked active. Review its audit before opening it as a completed result.')
    def state(self):return copy.deepcopy(self.saved_state)
    def export(self):return copy.deepcopy(self.episode)
    def status(self):return copy.deepcopy(self.saved_state['provider'])
    def dispatch(self,path,body):raise ValueError('Saved Jev results are read-only; no inference provider is connected.')


class OutcomeRun(ReactiveStudio):
    def __init__(self,folder,max_requests=50000,seed=21,provider=None,prior_requests=0,plasmablast_context=False):
        # No inherited paid startup or fixture substitution. The supplied provider
        # is only for synthetic tests; the command constructs the real adapter.
        super().__init__(False,0,120,'fixture')
        if not 0<=prior_requests<max_requests<=50000:raise ValueError('The combined request cap must be at most 50,000 and cover prior attempts.')
        episode_cap=max_requests-prior_requests
        self.jev=provider or Jev(limit=episode_cap,biological_context=True,plasmablast_context=plasmablast_context)
        if not self.jev.key:raise ValueError('Configure this LN project’s server-side key first.')
        if self.jev.limit!=episode_cap:raise ValueError('Provider cap must equal the remaining authorized requests.')
        self.provider='jev';self.enabled=True;self.session_limit=episode_cap;self.budget=episode_cap
        self.decision_cap=episode_cap*20
        self.folder=Path(folder);self.folder.mkdir(parents=True,exist_ok=False)
        self.sim=ReactiveSimulation(seed=seed,initial_cells=120,
            params={'max_rounds':episode_cap*6+1000})
        self.run_info=dict(status='prepared',managed=True,request_cap=max_requests,
            prior_requests=prior_requests,episode_request_cap=episode_cap,cumulative_requests=prior_requests,
            policy=self.jev.prompt_version,
            policy_description=('High conditional plasmablast/secretion preference; proposed demonstration policy, not measured biological probabilities.' if self.jev.plasmablast_context else 'Local model semantics; no requested fate preference.'),
            started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            stop_condition='First recorded IgM secretion by a B cell that completed plasmablast differentiation.',
            message='Preparing the antigen-bearing dendritic-cell entry.',outcome=None)
        self.pending_round=None;self.idle_ticks=0;self.run_requests=0
        self.stop_requested=threading.Event()
        self.journal=open(self.folder/'audit.jsonl','x',encoding='utf-8')
        self.jev.on_audit=self.audit
        self.persist()

    def audit(self,record):
        self.journal.write(json.dumps(dict(event='provider_request',round=self.sim.round,
            time_min=self.sim.time,record=record),allow_nan=False)+'\n')
        self.journal.flush();os.fsync(self.journal.fileno())

    def state(self):
        result=super().state()
        result['run_control']=copy.deepcopy(self.run_info)
        return result

    def dispatch(self,path,body):
        raise ValueError('This recorded Jev run is controlled by its stop condition. Viewing and saving are read-only.')

    def export(self):
        episode=self.sim.export()
        episode.update(provider_label='jev',provider=self.status(),request_audit=copy.deepcopy(self.jev.audit),
            provider_prompt_version=self.jev.prompt_version,run_control=copy.deepcopy(self.run_info),
            pending_round=copy.deepcopy(self.pending_round),recording_status=self.run_info['status'])
        return episode

    def outcome(self):
        for c in self.sim.cells:
            if c['kind']=='B' and c['state'] in ('plasmablast','plasma') and c['isotype']=='IgM' and c['antibodies']>0:
                secretion=next((d for d in self.sim.decisions if d['cell']==c['id'] and
                    d['proposal']['choice']=='SECRETE' and d['result']=='applied'),None)
                differentiation=next((e for e in self.sim.events if e['cell']==c['id'] and
                    e['event']=='program_completed' and e.get('action')=='PLASMA'),None)
                if secretion and differentiation:
                    return dict(cell=c['id'],clone=c['clone'],state_at_secretion=secretion['observation']['cell']['state'],
                        differentiation_time_min=differentiation['time_min'],secretion_time_min=secretion['time_min'],
                        isotype='IgM',units=c['antibodies'],decision_source=secretion['source'])
        return None

    def persist(self):
        self.run_info['cumulative_requests']=self.run_info['prior_requests']+self.jev.requests
        atomic_json(self.folder/'summary.json',dict(format='lymph-node-reactive-outcome-v1',
            **self.run_info,seed=self.sim.seed,round=self.sim.round,time_min=self.sim.time,
            metrics=self.sim.metrics(),usage=self.jev.status()))
        atomic_json(self.folder/'live.json',self.state())
        atomic_json(self.folder/'episode.ln.json.gz',self.export(),compressed=True)

    def tick(self):
        # Network work is outside the scene lock, so live inspection stays responsive.
        with self.lock:
            if self.run_info['status']!='running':return False
            if self.stop_requested.is_set():
                self.run_info.update(status='stopped',message='Stopped by operator after saving all completed requests.');self.persist();return False
            rows=self.sim.proposals()
            self.pending_round=dict(round=self.sim.round,time_min=self.sim.time,rows=rows)
            self.run_info['message']=f'Jev is considering {len(rows)} local cell question(s).' if rows else 'Advancing biological clocks; no cell question is needed.'
            if rows:
                self.journal.write(json.dumps(dict(event='round_started',**self.pending_round),allow_nan=False)+'\n')
                self.journal.flush();os.fsync(self.journal.fileno())
        answers=self.jev.choose(rows,self.jev.limit) if rows else {}
        with self.lock:
            self.sim.step(answers,rows,'jev');self.pending_round=None
            found=self.outcome()
            if found:
                self.run_info.update(status='complete',outcome=found,
                    message=f"{found['cell']} secreted IgM after plasmablast differentiation. The run stopped automatically.")
            elif self.jev.requests>=self.jev.limit:
                self.run_info.update(status='budget_reached',message='The authorized API-call ceiling was reached; no further requests will be made.')
            elif self.sim.injected and all(a['pool']=='degraded' for a in self.sim.antigens) and not any(
                alive(c) and c['kind']=='B' and (c['state'] not in ('naive','resting','memory') or c['program']) for c in self.sim.cells):
                self.run_info.update(status='antigen_exhausted',message='All antigen has degraded and no active B-cell response remains. No further requests will be made.')
            # A genuinely quiet, process-free terminal state cannot benefit from
            # provider calls. Do not inject replacement antigen or fabricate cells.
            self.idle_ticks=self.idle_ticks+1 if not rows and not any(c['program'] for c in self.sim.cells) else 0
            if self.idle_ticks>=72 and not found:
                self.run_info.update(status='quiescent',message='No eligible cells or active programs for 12 biological hours; the run stopped without adding a new perturbation.')
            self.persist()
            if rows or found or self.sim.round%12==0:
                print(json.dumps(dict(status=self.run_info['status'],time_h=round(self.sim.time/60,2),
                    requests=self.jev.requests,decisions=len(self.sim.decisions),
                    tfh=self.sim.metrics()['tfh'],plasmablasts=self.sim.metrics()['plasma'],
                    IgM=self.sim.antibody,never_queried=self.sim.metrics()['never_queried'])),flush=True)
            return self.run_info['status']=='running'

    def run(self):
        try:
            with self.lock:
                self.sim.perturb(PROMPT);self.run_info['status']='running';self.persist()
            while self.tick():pass
        except BaseException as error:
            with self.lock:
                message=str(error) if isinstance(error,Exception) else 'Interrupted by operator'
                if self.jev.key:message=message.replace(self.jev.key,'[redacted]')
                self.run_info.update(status='failed',message=message)
                self.sim.failures.append(dict(time_min=self.sim.time,message=message,provider='jev',requests=self.jev.requests))
                self.persist()
                print(json.dumps(dict(status='failed',message=message,usage=self.jev.status())),flush=True)
        finally:
            self.journal.close()
            print('RUN FINISHED: '+json.dumps(self.run_info),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-requests',type=int)
    parser.add_argument('--seed',type=int,default=21)
    parser.add_argument('--port',type=int,default=8018)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--view',action='store_true',help='Open the saved --output result read-only, without loading credentials or calling Jev.')
    parser.add_argument('--prior-requests',type=int,default=0,help='All already attempted requests under the same cumulative authorization.')
    parser.add_argument('--plasmablast-preference',action='store_true',help='Explicitly select the proposed high conditional plasmablast/secretion preference.')
    args=parser.parse_args()
    if args.view:
        if not args.output:parser.error('--view requires --output.')
        app=SavedOutcome(args.output)
        server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);server.studio=app
        print(f'Saved Jev result: http://127.0.0.1:{args.port} (read-only; no inference provider)',flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
        finally:server.server_close()
        return
    if args.max_requests is None or not 1<=args.max_requests<=50000:parser.error('Run requires --max-requests 1–50,000.')
    load_env()
    folder=args.output or ROOT/'recordings/private'/('reactive-jev-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6])
    app=OutcomeRun(folder,args.max_requests,args.seed,prior_requests=args.prior_requests,plasmablast_context=args.plasmablast_preference)
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);server.studio=app
    print('Saved run: '+str(folder),flush=True)
    print('Live Jev viewer: http://127.0.0.1:'+str(args.port),flush=True)
    worker=threading.Thread(target=app.run,daemon=False);worker.start()
    try:server.serve_forever()
    except KeyboardInterrupt:
        app.stop_requested.set()
        print('Stopping after the current request is recorded; no automatic retry.',flush=True)
        worker.join()
    finally:server.server_close()

if __name__=='__main__':main()
