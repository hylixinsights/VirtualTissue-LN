#!/usr/bin/env python3
"""Local-only independent lymph-node studio. Python standard library only."""
import argparse
import hashlib
import gzip
import json
import mimetypes
import os
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from engine import Simulation, REGISTRY, STATES, SCENARIOS
from jev import Jev, ProviderError

ROOT=Path(__file__).resolve().parent

def load_env():
 path=ROOT/'.env'
 if path.is_file():
  for line in path.read_text().splitlines():
   if '=' not in line or line.strip().startswith('#'): continue
   key,val=line.split('=',1)
   if key.strip() in ('TYPESAFE_API_KEY','JEV_MODEL'): os.environ.setdefault(key.strip(),val.strip().strip('\"\''))

class Studio:
 def __init__(self,enable_jev=False,limit=0,initial_cells=300):
  self.lock=threading.Lock();self.token=secrets.token_urlsafe(32);self.sim=Simulation(initial_cells=initial_cells)
  self.provider='fixture';self.enabled=enable_jev;self.jev=Jev(limit=limit);self.run_requests=0
  self.budget=limit;self.session_limit=limit;self.history_source=None
 def status(self): return dict(enabled=self.enabled,provider=self.provider,**self.jev.status())
 def state(self): return dict(tissue=self.sim.snapshot(),provider=self.status(),registry=self.sim.registry,states=STATES,scenarios=SCENARIOS)
 def dispatch(self,path,body):
  if path=='/api/reset':
   if self.sim.round and not body.get('discard'): raise ValueError('Export or explicitly discard the current run before reset')
   scenario=body.get('scenario','vaccine');seed=body.get('seed',21);provider=body.get('provider','fixture')
   if type(seed) is not int or not 0<=seed<=2**32: raise ValueError('Seed must be an integer from 0 to 4294967296')
   if provider not in ('fixture','jev'): raise ValueError('Unknown decision provider')
   budget=body.get('budget',0)
   if provider=='jev' and (not self.enabled or not self.jev.key): raise ValueError('Start the server with --enable-jev and configure its own TYPESAFE_API_KEY')
   if type(budget) is not int or not 0<=budget<=self.session_limit: raise ValueError('Budget exceeds server limit')
   sim=Simulation(seed,scenario,initial_cells=body.get('cells',self.sim.initial_cells));self.sim=sim;self.provider=provider;self.budget=budget
   self.run_requests=self.jev.requests;self.history_source=provider
  elif path=='/api/step':
   rows=self.sim.proposals()
   try:
    answers=self.sim.fixture(rows) if self.provider=='fixture' else self.jev.choose(rows,min(self.session_limit,self.run_requests+self.budget))
    self.sim.step(answers,rows,self.provider)
   except (ProviderError,ValueError) as e:
    self.sim.failures.append(dict(time_min=self.sim.time,message=str(e),provider=self.provider,requests=self.jev.requests))
    raise
  elif path=='/api/inject':
   if self.sim.scenario=='baseline': raise ValueError('Use an antigen scenario to add a pulse')
   self.sim.inject(round(80*self.sim.initial_cells/300))
  else: raise ValueError('Unknown operation')
  return self.state()

def recordings_catalog():
 base=(ROOT/'recordings/private').resolve();entries=[];files={}
 if not base.is_dir():return entries,files
 for summary_path in sorted(base.glob('*/summary.json'),reverse=True):
  try:
   summary=json.loads(summary_path.read_text())
   if summary.get('format')!='lymph-node-live-session-v1':continue
   for run in summary.get('scenarios',[]):
    target=(summary_path.parent/run['file']).resolve()
    if base.resolve() not in target.parents or not target.is_file() or not target.name.endswith('.ln.json.gz'):continue
    rid=hashlib.sha256(str(target.relative_to(base)).encode()).hexdigest()[:20]
    files[rid]=target
    entries.append(dict(id=rid,scenario=run['scenario'],provider='jev',status=run['status'],
       time_min=run.get('time_min',0),rounds=run.get('rounds',0),requests=run.get('usage',{}).get('requests',0),
       started_utc=summary.get('started_utc'),model=run.get('usage',{}).get('resolved_model')))
  except (OSError,ValueError,KeyError,TypeError):continue
 return entries,files

class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args): pass
 @property
 def app(self): return self.server.studio
 def send(self,status,data,kind='application/json; charset=utf-8',headers=None):
  raw=json.dumps(data,allow_nan=False,separators=(',',':')).encode() if kind.startswith('application/json') else data
  self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(raw)))
  self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','no-store')
  self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'")
  for k,v in (headers or {}).items():self.send_header(k,v)
  self.end_headers();self.wfile.write(raw)
 def host_ok(self): return self.headers.get('Host') in ('127.0.0.1:%d'%self.server.server_port,'localhost:%d'%self.server.server_port)
 def do_GET(self):
  if not self.host_ok(): return self.send(403,{'error':'Local host required'})
  path=urlparse(self.path).path
  if path=='/api/recordings':return self.send(200,{'recordings':recordings_catalog()[0]})
  if path.startswith('/api/recordings/'):
   target=recordings_catalog()[1].get(path.rsplit('/',1)[-1])
   if target is None:return self.send(404,{'error':'Unknown recording'})
   return self.send(200,target.read_bytes(),'application/gzip')
  if path in ('/api/state','/api/export'):
   with self.app.lock:
    if path=='/api/state': return self.send(200,dict(**self.app.state(),token=self.app.token))
    episode=self.app.sim.export();episode['provider']=self.app.status();episode['request_audit']=[r for r in self.app.jev.audit if r['request']>self.app.run_requests];episode['provider_label']=self.app.provider
    raw=gzip.compress(json.dumps(episode,allow_nan=False).encode())
    return self.send(200,raw,'application/gzip',{'Content-Disposition':'attachment; filename="lymph-node-%s-%d.ln.json.gz"'%(self.app.provider,self.app.sim.seed)})
  if path=='/': path='/web/index.html'
  allowed=('/web/','/vendor/')
  target=(ROOT/path.lstrip('/')).resolve()
  if not path.startswith(allowed) or ROOT not in target.parents or not target.is_file() or target.suffix not in ('.html','.css','.js','.mjs','.txt','.svg'):
   return self.send(404,{'error':'Not found'})
  kind='text/javascript' if target.suffix in ('.js','.mjs') else mimetypes.guess_type(str(target))[0] or 'text/plain'
  return self.send(200,target.read_bytes(),kind)
 def do_POST(self):
  origin=self.headers.get('Origin');valid_origins=('http://127.0.0.1:%d'%self.server.server_port,'http://localhost:%d'%self.server.server_port)
  if not self.host_ok() or (origin and origin not in valid_origins) or self.headers.get('X-LN-Token')!=self.app.token: return self.send(403,{'error':'Local session token required'})
  try:
   n=int(self.headers.get('Content-Length','0'))
   if not 0<n<=8192:raise ValueError('Invalid request size')
   body=json.loads(self.rfile.read(n))
   if not isinstance(body,dict): raise ValueError('Expected JSON object')
   with self.app.lock: result=self.app.dispatch(urlparse(self.path).path,body)
   self.send(200,result)
  except (ValueError,ProviderError) as e:self.send(400,{'error':str(e),'provider':self.app.status()})
  except Exception as e:
   print('Kernel error:',type(e).__name__,str(e));self.send(500,{'error':'Kernel check failed; run paused. Inspect server terminal.'})

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8010)
 parser.add_argument('--cells',type=int,choices=[100,300],default=300)
 parser.add_argument('--open-browser',action='store_true')
 parser.add_argument('--enable-jev',action='store_true');parser.add_argument('--max-requests',type=int,default=0)
 args=parser.parse_args()
 if not 0<=args.max_requests<=100000:parser.error('Invalid request cap')
 if args.enable_jev and args.max_requests==0:parser.error('--enable-jev requires an explicit positive --max-requests budget')
 load_env();server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);server.studio=Studio(args.enable_jev,args.max_requests,args.cells)
 print('Lymph Node Studio: http://127.0.0.1:%d'%args.port,flush=True)
 print('Jev enabled with request cap %d'%args.max_requests if args.enable_jev else 'Offline demonstration ready. No paid calls enabled.',flush=True)
 if args.open_browser: threading.Timer(.3,lambda:webbrowser.open('http://127.0.0.1:%d'%args.port)).start()
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
if __name__=='__main__': main()
