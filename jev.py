"""Server-side TypeSafe Choice integration. No implicit retries or paid tests."""
import json
import copy
import math
import os
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.error
import urllib.request
from engine import ACTIONS, STATES

ENDPOINT='https://api.typesafe.ai/v1/systemone'
class ProviderError(Exception): pass
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs): return None

def request_body_v1(rows,model):
 return dict(model=model,state={'setting':'One individual cell in a proposed, uncalibrated lymph-node tissue simulation.',
   'constraint':'Each question is independent. Use only its local observation and legal options. Select a suitable action or WAIT. Code owns physical effects, clocks, and constraints. Probabilities are preferences, never biological rates.'},
   questions={r['id']:dict(type='choice',instructions={'task':'Choose the next legal action for this individual cell. Do not invent remote events.',
      'local_observation':r['observation']},criteria={a:{'description':ACTIONS[a][0],'rule':ACTIONS[a][1],'target':t} for a,t in r['options'].items()}) for r in rows})

def pack_observation(observation):
 # Lossless tables remove repeated field names; cell identity/cues stay named.
 packed=copy.deepcopy(observation)
 for field in ('nearby','accessible_antigen','cargo'):
  values=packed.get(field)
  if isinstance(values,list) and values and all(isinstance(v,dict) and set(v)==set(values[0]) for v in values):
   columns=list(values[0]);packed[field]={'columns':columns,'rows':[[v[k] for k in columns] for v in values]}
 return packed

def request_body(rows,model,biological_context=False,fate_context=False,plasmablast_context=False,development_context=False):
 body=request_body_v1(rows,model)
 body['state']['table_format']='In each local observation, a columns/rows object is a lossless table: each row supplies values in the named column order. Empty arrays mean no observed entities.'
 for r in rows:body['questions'][r['id']]['instructions']['local_observation']=pack_observation(r['observation'])
 if biological_context or fate_context:
  body['state']['model_semantics']={
   'states':STATES,
   'eligibility':'Every listed option has already passed the kernel prerequisites for this cell. An omitted option is forbidden. Do not invent additional global prerequisites or require a second approval to use an eligible cellular program.',
   'licenses':'help_until is the absolute expiry time in minutes of cognate T-cell help. division_budget is the finite count of cell cycles licensed by that help, not money or an API budget.',
   'dark_zone':'dz denotes a germinal-center B cell in the proliferative program. DIVIDE starts its licensed cell cycle; the kernel owns the clock, collision checks, finite resources and creation of two daughters.',
   'selection':'lz denotes the antigen-capture/selection phase. selected means this individual GC B cell has already obtained renewed cognate help. Eligible outputs are recycling into the proliferative phase, memory commitment, or plasmablast commitment. No particular output is mandated.',
   'movement_and_wait':'MOVE is physical migration or scanning during one time step; WAIT starts no new program. Neither action starts a cell cycle nor commits a differentiation program.',
   'output':'PLASMA starts plasmablast commitment, MATURE starts its transition to a mature plasma cell. SECRETE is antibody secretion by that clone. MEMORY starts the memory program without constitutive secretion.',
   'scope':'These are definitions of the implemented toy model, not measured human rates. Choose using this individual cell state and its local context; do not optimize a requested demonstration outcome.'}
  for r in rows:
   body['questions'][r['id']]['instructions']['task']='Choose the biologically appropriate next eligible program or physical action for this individual cell, interpreting its state and licenses using model_semantics. Use only its local observation.'
 if fate_context:
  body['state']['proposed_fate_policy']='P: qualitative demonstration policy, not measured transition rates. For an already selected GC B cell, compare continued expansion, preservation as memory, and antibody production using only its local antigen availability, own generation and remaining help license. Local scarcity of accessible cognate native antigen favors memory preservation over starting another antigen-dependent selection cycle. Continued accessible antigen and renewed help favor further cycling or antibody-secreting differentiation. A division license permits cycling but does not require spending it. Do not invent antigen, help or a requested output.'
  for q in body['questions'].values():
   for action,description in {
    'RECYCLE':'Return a selected B cell to another finite proliferative cycle. Assess whether its local cognate antigen supply supports the next selection cycle; an unused license is permission, not an obligation.',
    'MEMORY':'Preserve this already selected, antigen-experienced B clone as a quiescent memory cell. Under this proposed policy, local scarcity of cognate native antigen supports this alternative to further antigen-dependent cycling. No constitutive antibody secretion.',
    'PLASMA':'Commit this helped B cell to the antibody-secreting plasmablast program. This trades further GC cycling for antibody output by its existing clone and specificity; consider its current help and local antigen context.'}.items():
    if action in q['criteria']:q['criteria'][action]['description']=description
 for r in rows:
  if r['observation'].get('movement_program') and 'MOVE' in body['questions'][r['id']]['criteria']:
   body['questions'][r['id']]['criteria']['MOVE']['description']=r['observation']['movement_program']
 if plasmablast_context:
  for r in rows:
   q=body['questions'][r['id']];cell=r['observation'].get('cell',{})
   if cell.get('kind')!='B':continue
   if 'PLASMA' in q['criteria']:
    q['instructions']['proposed_local_policy']='Explicit user-selected antibody-output demonstration policy, P: uncalibrated. This individual B cell has already passed the kernel prerequisites for PLASMA, including cognate help. Strongly favor its eligible plasmablast commitment over continued migration or GC founding/cycling (suggested preference 0.90). Return your own normalized preferences over the supplied legal menu. This preference is not a measured fate probability; do not invent antigen or help or change eligibility.'
   elif 'SECRETE' in q['criteria'] and cell.get('state') in ('plasmablast','plasma'):
    q['instructions']['proposed_local_policy']='Explicit user-selected antibody-output demonstration policy, P: uncalibrated. This differentiated antibody-producing B cell can legally secrete its existing isotype. Strongly favor SECRETE now (suggested preference 0.90); return your own normalized preferences over its legal menu. Do not change isotype or invent output; the kernel applies secretion.'
  if any('proposed_local_policy' in q['instructions'] for q in body['questions'].values()) and 'model_semantics' in body['state']:
   body['state']['model_semantics']['scope']='These are definitions of an uncalibrated toy model. Use only each cell’s local state and legal options. Where present, proposed_local_policy explicitly declares the user-selected demonstration preference; other cells receive no outcome instruction.'
 if development_context:
  body['state']['proposed_development_policy']='P: explicitly selected qualitative demonstration policy, not measured biology. Preserve individual local eligibility. For a helped activated B cell, its own toy affinity annotation at or above 0.79 favors early PLASMA commitment; below 0.79 favor eligible ENTER_GC, or MOVE toward its local stromal field until founding is eligible. This uncalibrated threshold illustrates competing fates, not a validated affinity-to-fate law. In a licensed DZ cell favor DIVIDE. In an already selected GC cell favor PLASMA after a daughter generation, otherwise eligible recycling. For a plasmablast, favor SECRETE until its own recorded output reaches three units, then favor MATURE. Mature plasma cells favor SECRETE. Recognition, help, antigen and contact gates remain mandatory; never invent omitted options or distant information. For other states use their local cues and eligible programs normally.'
  if 'model_semantics' in body['state']:
   body['state']['model_semantics']['scope']='Uncalibrated toy model with a disclosed competing-fate demonstration policy. Evaluate each individual using only its local observation and legal menu; no global counts or target cells are provided.'
 return body

def validate(body,rows):
 if not isinstance(body,dict) or not isinstance(body.get('model'),str) or not body['model']: raise ProviderError('Missing model provenance')
 answers=copy.deepcopy(body.get('answers'))
 if not isinstance(answers,dict) or set(answers)!={r['id'] for r in rows}: raise ProviderError('Missing or unexpected cell answers')
 for r in rows:
  a=answers[r['id']]; opts=r['options']
  if not isinstance(a,dict): raise ProviderError('Malformed individual cell answer')
  p=a.get('probabilities',{})
  if a.get('type')!='choice' or a.get('choice') not in opts: raise ProviderError('Illegal action returned by Jev')
  if not isinstance(p,dict) or set(p)!=set(opts) or any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1 for v in p.values()): raise ProviderError('Invalid Jev probabilities')
  total=math.fsum(p.values())
  if abs(total-1)>1e-6:
   rounded=all(abs(v*100-round(v*100))<=1e-8 for v in p.values())
   if not rounded or total<=0 or abs(total-1)>0.005*len(p)+1e-8: raise ProviderError('Invalid Jev probabilities')
   a['raw_probabilities']=p.copy()
   a['probability_adjustment']={'method':'unit-sum normalization within two-decimal rounding bound','raw_sum':total,'bound':0.005*len(p),'changes_choice':False}
   p={k:v/total for k,v in p.items()};a['probabilities']=p
  v=a.get('confidence')
  if type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1: raise ProviderError('Invalid confidence')
  if p[a['choice']]+1e-6<max(p.values()): raise ProviderError('Choice disagrees with probability distribution')
  a['source']='Jev'
 return answers

class Jev:
 def __init__(self,key=None,limit=0,model=None,transport=None,on_audit=None,biological_context=False,fate_context=False,plasmablast_context=False,development_context=False):
  self.fate_context=fate_context;self.biological_context=biological_context;self.prompt_version='lymph-node-choice-v3-model-semantics' if biological_context else 'lymph-node-choice-v2-lossless-tables'
  if fate_context:self.prompt_version='lymph-node-choice-v4-proposed-fate-context'
  self.plasmablast_context=plasmablast_context
  if plasmablast_context:self.prompt_version='lymph-node-choice-v5-proposed-plasmablast-preference'
  self.development_context=development_context
  if development_context:self.prompt_version='lymph-node-choice-v6-proposed-development-policy'
  self.key=key or os.environ.get('TYPESAFE_API_KEY','');self.limit=limit
  self.model=model or os.environ.get('JEV_MODEL','jev-1.13.0');self.resolved_model=None
  self.requests=0;self.input_tokens=0;self.output_tokens=0;self.unknown_usage=0;self.audit=[]
  self.transport=transport or self._remote
  self.on_audit=on_audit;self._lock=threading.Lock();self.replay_cache={}
 def _remote(self,body):
  req=urllib.request.Request(ENDPOINT,data=json.dumps(body,allow_nan=False).encode(),headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json'},method='POST')
  try:
   with urllib.request.build_opener(NoRedirect()).open(req,timeout=20) as response:
    raw=response.read(2_000_001)
   if len(raw)>2_000_000: raise ProviderError('Response exceeds size limit')
   return json.loads(raw,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite number')))
  except urllib.error.HTTPError as e:
   detail=e.read(4096).decode('utf-8',errors='replace').replace(self.key,'[redacted]') if self.key else ''
   raise ProviderError('Jev HTTP %d: %s; round paused. No automatic retry.'%(e.code,detail[:2000])) from None
  except (OSError,ValueError,urllib.error.URLError): raise ProviderError('Jev connection/JSON failure. Usage may be unknown; round paused.') from None
 def _notify(self,record):
  if self.on_audit: self.on_audit(record)
 def choose(self,rows,budget,workers=1,batch_size=20):
  if not self.key: raise ProviderError('Set TYPESAFE_API_KEY in this project or server environment')
  if type(workers) is not int or not 1<=workers<=4: raise ValueError('Workers must be 1–4')
  if type(batch_size) is not int or not 1<=batch_size<=20:raise ValueError('Batch size must be 1–20')
  batches=[rows[i:i+batch_size] for i in range(0,len(rows),batch_size)]
  results={};uncached=[]
  for batch in batches:
   fingerprint=hashlib.sha256(json.dumps(request_body(batch,self.model,self.biological_context,self.fate_context,self.plasmablast_context,self.development_context),sort_keys=True,allow_nan=False).encode()).hexdigest()
   cached=self.replay_cache.get(fingerprint)
   if not cached:
    legacy=hashlib.sha256(json.dumps(request_body_v1(batch,self.model),sort_keys=True,allow_nan=False).encode()).hexdigest()
    cached=self.replay_cache.get(legacy)
   if cached:
    validated=validate(cached['response'],batch);results.update(validated)
    cached.setdefault('original_status',cached['status']);cached['status']='validated_after_review'
    cached['adjusted_cells']=[k for k,a in validated.items() if a.get('probability_adjustment')]
    cached['review']='Revalidated exact paid response on explicit resume; no new request'
    self._notify(cached)
   else:uncached.append(batch)
  batches=uncached
  if self.requests+len(batches)>min(budget,self.limit): raise ProviderError('Request budget cannot cover a full round. Export the partial run or increase the explicit budget.')
  def call(batch):
   body=request_body(batch,self.model,self.biological_context,self.fate_context,self.plasmablast_context,self.development_context)
   with self._lock:
    self.requests+=1
    record={'request':self.requests,'model_requested':self.model,'cells':[r['id'] for r in batch],
      'prompt_version':self.prompt_version,'request_sha256':hashlib.sha256(json.dumps(body,sort_keys=True,allow_nan=False).encode()).hexdigest(),'status':'started'}
    self.audit.append(record);self._notify(record)
   try: result=self.transport(body)
   except Exception as error:
    with self._lock:
     self.unknown_usage+=1;record['status']='failed; usage unknown';record['error']=str(error);self._notify(record)
    raise
   with self._lock:
    usage=result.get('usage',{}) if isinstance(result,dict) else {}
    if isinstance(usage,dict) and all(type(usage.get(k)) is int and usage[k]>=0 for k in ('input_tokens','output_tokens')):
     self.input_tokens+=usage['input_tokens'];self.output_tokens+=usage['output_tokens'];record['usage']=usage
    else: self.unknown_usage+=1;record['usage']='unknown'
    record['response']=result
    try:
     validated=validate(result,batch)
     if self.resolved_model and self.resolved_model!=result['model']: raise ProviderError('Model changed during the run; no round applied')
     self.resolved_model=result['model'];record['status']='validated';record['adjusted_cells']=[k for k,a in validated.items() if a.get('probability_adjustment')];self._notify(record)
     return validated
    except Exception as error:
     record['status']='invalid response; no round applied';record['error']=str(error);self._notify(record);raise
  # Waves bound in-flight spending. After a failed wave, no further batches start.
  for start in range(0,len(batches),workers):
   wave=batches[start:start+workers]
   if workers==1: results.update(call(wave[0]));continue
   with ThreadPoolExecutor(max_workers=workers) as pool:
    futures=[pool.submit(call,batch) for batch in wave];failure=None
    for future in as_completed(futures):
     try: results.update(future.result())
     except Exception as e: failure=failure or e
    if failure: raise failure
  return results
 def status(self):
  return dict(configured=bool(self.key),model=self.model,resolved_model=self.resolved_model,requests=self.requests,
   server_limit=self.limit,input_tokens=self.input_tokens,output_tokens=self.output_tokens,unknown_usage=self.unknown_usage)
