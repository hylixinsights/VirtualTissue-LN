"""Independent LN kernel. All numerical parameters are proposed, uncalibrated.
One cell per agent; micrometers, minutes, antigen mass-equivalent packets.
"""
import copy
import hashlib
import json
import math
import random
from collections import Counter
from pathlib import Path

SOURCES = json.loads((Path(__file__).resolve().parent / "docs/sources.json").read_text())

VERSION = '0.2.0'
PARAMS = dict(radius_um=150, cell_radius_um=4.2, step_min=30, movement_um=9,
              sensing_um=42, contact_um=15, processing_min=60, loading_min=30,
              priming_min=60, helper_min=120, help_min=30, help_lifetime_min=1440,
              founder_min=240, gc_organization_min=120, gc_founders=2,
              division_min=240, differentiation_min=180, selection_timeout_min=1440,
              pmhc_lifetime_min=360, antigen_lifetime_min=5760, max_cells=600,
              max_rounds=120, selection_divisions=1)
REGISTRY = {
 'B':dict(label='B cell',manual='B-01',color='#7e8eff',count=140),
 'CD4':dict(label='CD4 T cell',manual='T-01',color='#52d6b1',count=85),
 'DC':dict(label='cDC2',manual='D-02',color='#ffb75e',count=15),
 'MAC':dict(label='Macrophage',manual='M-01 / M-03',color='#ea829e',count=16),
 'FDC':dict(label='Follicular dendritic cell',manual='S-03',color='#d3a0fa',count=16),
 'FRC':dict(label='Reticular stromal cell',manual='S-01',color='#8eabbc',count=18),
 'LEC':dict(label='Lymphatic endothelial cell',manual='S-06',color='#78999d',count=10),
}
STATES={'naive':'Naive','activated':'Antigen activated','pre_tfh':'Border helper',
 'tfh':'T follicular helper','founder':'GC founder','dz':'GC · dark zone',
 'lz':'GC · light zone','selected':'GC · selected','memory':'Memory B',
 'plasmablast':'Plasmablast','plasma':'Plasma cell','resting':'Resting',
 'presenting':'Antigen presenting','apoptotic':'Apoptotic','cleared':'Cleared',
 'divided':'Replaced by daughters'}
ACTIONS={
 'WAIT':('Observe; start no new program.', 'LN-R030'),
 'MOVE':('Move continuously along a local cue or scan; collision checked.', 'LN-R003'),
 'CAPTURE':('Acquire one accessible cognate native antigen packet.', 'LN-R005'),
 'RETAIN':('Retain a local immune complex on an FDC.', 'LN-R005'),
 'PROCESS':('Start timed antigen processing, then peptide loading.', 'LN-R007'),
 'PRIME':('Maintain a cognate DC contact with costimulation to prime CD4.', 'LN-R009'),
 'HELPER':('Start the activated CD4 border-helper program.', 'LN-R011'),
 'HELP':('Maintain a local, linked B–helper contact; finite license.', 'LN-R011'),
 'ENTER_GC':('Start a timed founder program near follicular support.', 'LN-R013'),
 'DIVIDE':('Spend one division license and complete a timed cell cycle.', 'LN-R021'),
 'RECYCLE':('Use renewed help to return to the proliferative program.', 'LN-R016'),
 'MEMORY':('Commit to memory; no constitutive antibody secretion.', 'LN-R019'),
 'PLASMA':('Commit to antibody-secreting plasmablast differentiation.', 'LN-R012'),
 'MATURE':('Mature a plasmablast into a noncycling plasma cell.', 'LN-R020'),
 'SECRETE':('Secrete antibody of the existing clone and isotype.', 'LN-R026'),
 'CLEAR':('Engulf one adjacent apoptotic cell into a finite debris queue.', 'LN-R025'),
 'MAINTAIN':('Maintain local stromal support for follicular programs.', 'LN-R026'),
}
SCENARIOS={
 'vaccine':{'label':'Protein antigen + adjuvant','antigen':True,'hla_match':True,'cd40':True,'fdc':True},
 'baseline':{'label':'Quiet baseline','antigen':False,'hla_match':True,'cd40':True,'fdc':True},
 'no_help':{'label':'CD40–CD40L blocked','antigen':True,'hla_match':True,'cd40':False,'fdc':True},
 'mismatch':{'label':'Peptide–HLA mismatch','antigen':True,'hla_match':False,'cd40':True,'fdc':True},
 'no_fdc':{'label':'FDC retention blocked','antigen':True,'hla_match':True,'cd40':True,'fdc':False},
}
FOLLICLE=(-48,25); DZ=(-65,9); LZ=(-32,43)
def distance(a,b): return math.hypot(a['x']-b['x'],a['y']-b['y'])
def dpoint(c,p): return math.hypot(c['x']-p[0],c['y']-p[1])
def alive(c): return c['state'] not in ('apoptotic','cleared','divided')
def occupied(c): return c['state'] not in ('cleared','divided')

class Simulation:
 def __init__(self, seed=21, scenario='vaccine', params=None, initial_cells=300):
  if scenario not in SCENARIOS: raise ValueError('Unknown scenario')
  if type(initial_cells) is not int or initial_cells not in (100,300): raise ValueError('Supported populations: 100 or 300')
  self.initial_cells=initial_cells;self.scale=math.sqrt(initial_cells/300)
  self.population=({k:v['count'] for k,v in REGISTRY.items()} if initial_cells==300 else dict(B=46,CD4=29,DC=5,MAC=6,FDC=6,FRC=5,LEC=3))
  self.registry={k:{**v,'count':self.population[k]} for k,v in REGISTRY.items()}
  self.follicle=tuple(v*self.scale for v in FOLLICLE);self.dz=tuple(v*self.scale for v in DZ);self.lz=tuple(v*self.scale for v in LZ)
  self.p={**PARAMS,'radius_um':150*self.scale,'max_cells':initial_cells*2,**(params or {})}; self.rng=random.Random(seed)
  self.seed=seed; self.scenario=scenario; self.config=SCENARIOS[scenario].copy()
  self.time=0; self.round=0; self.cells=[]; self.antigens=[]; self.events=[]
  self.decisions=[]; self.frames=[]; self.inputs=[]; self.failures=[]
  self.gc=False; self.gc_since=None; self.gc_candidate_since=None
  self.injected=0; self.antibody=0; self.antibody_clones=Counter(); self.births=0; self.deaths=0; self.cleared=0
  self.valid=True; self.stop_reason=None; self._id=0; self._aid=0
  self._initialize()
  if self.config['antigen']: self.inject()
  self.initial=self.snapshot(); self.save_frame()

 def _initialize(self):
  # Density-preserving patch preset; physical cell size and hexagonal spacing stay fixed.
  sites=[]
  for j in range(-13,14):
   for i in range(-13,14):
    x=(i+(j%2)*.5)*13.2; y=j*13.2*math.sqrt(3)/2
    if math.hypot(x,y)<self.p['radius_um']-self.p['cell_radius_um']-1: sites.append((x,y))
  # Mix occupancy while retaining abundant contiguous empty sites for migration.
  self.rng.shuffle(sites)
  def add(kind,n,score):
   nonlocal sites
   sites.sort(key=score)
   for x,y in sites[:n]: self.cells.append(self.new_cell(kind,x,y))
   sites=sites[n:]
  q=self.scale
  add('LEC',self.population['LEC'],lambda p:abs(math.hypot(*p)-138*q)+abs(p[0])*.1)
  add('FDC',self.population['FDC'],lambda p:math.hypot(p[0]+40*q,p[1]-42*q)+self.rng.random()*45*q)
  add('MAC',self.population['MAC'],lambda p:min(math.hypot(p[0]+65*q,p[1]-112*q),math.hypot(p[0]+42*q,p[1]-25*q))+self.rng.random()*30*q)
  add('DC',self.population['DC'],lambda p:math.hypot(p[0]+2*q,p[1]-45*q)+self.rng.random()*30*q)
  add('FRC',self.population['FRC'],lambda p:math.hypot(p[0]-45*q,p[1])+self.rng.random()*70*q)
  add('B',self.population['B'],lambda p:math.hypot(p[0]+48*q,p[1]-25*q)+self.rng.random()*35*q)
  add('CD4',self.population['CD4'],lambda p:math.hypot(p[0]-25*q,p[1])+self.rng.random()*75*q)

 def new_cell(self,kind,x,y):
  self._id+=1; cid='LN-%04d'%self._id
  return dict(id=cid,kind=kind,lineage=('B' if kind=='B' else 'T' if kind=='CD4' else 'stromal' if kind in ('FDC','FRC','LEC') else 'myeloid'),
    state='naive' if kind in ('B','CD4') else 'resting',x=x,y=y,z=0,
    radius=self.p['cell_radius_um'],clone=cid if kind in ('B','CD4') else None,parent=None,
    generation=0,bcr='E1' if self.rng.random()<.68 else 'E2',tcr='P1',hla='HLA-II-A',
    affinity=round(self.rng.uniform(.2,.8),3),bcr_variant=0,isotype='IgM',
    cargo=None,pmhc=None,program=None,help_until=0,division_budget=0,
    gc_member=False,last_help=None,selection_since=None,last_action='WAIT',last_decision=None,
    costim=False,antibodies=0,debris_until=0,cue_until=0)

 def log(self,kind,cell=None,rule='LN-R030',**data):
  self.events.append(dict(time_min=self.time,event=kind,cell=cell,rule=rule,evidence='P',**data))

 def inject(self,amount=None):
  if amount is None: amount=round(480*self.initial_cells/300)
  if self.round>=self.p['max_rounds']: raise ValueError('Run has reached its duration limit')
  for _ in range(amount):
   self._aid+=1
   self.antigens.append(dict(id='AG-%05d'%self._aid,source='afferent-pulse-%d'%len(self.inputs),
     epitope='E1',peptide='P1',hla='HLA-II-A' if self.config['hla_match'] else 'HLA-II-X',
     pool='free_native',owner=None,x=(-62+self.rng.uniform(-16,16))*self.scale,y=(126+self.rng.uniform(-7,7))*self.scale,
     created=self.time,mass=1,complex=True))
  self.injected+=amount
  self.inputs.append(dict(time_min=self.time,amount=amount,route='LN-S01 → LN-S02',
    formulation='Nonreplicating protein + adjuvant; pre-opsonized complexes (proposed)'))
  self.log('antigen_pulse',rule='LN-R002',amount=amount)

 def get(self,cid): return next((c for c in self.cells if c['id']==cid),None)
 def antigen(self,aid): return next((a for a in self.antigens if a['id']==aid),None)
 def neighbors(self,c,r=None): return [n for n in self.cells if n['id']!=c['id'] and occupied(n) and distance(c,n)<= (r or self.p['sensing_um'])]
 def compatible(self,t,p): return p and p['peptide']==t['tcr'] and p['hla']==t['hla']
 def local_antigen(self,c):
  return [a for a in self.antigens if a['pool'] in ('free_native','fdc_retained') and
    math.hypot(a['x']-c['x'],a['y']-c['y'])<=self.p['contact_um'] and
    (c['kind']!='B' or a['epitope']==c['bcr']) and
    (a['pool']!='fdc_retained' or c['kind']=='B')]
 def eligible(self,c):
  options={'WAIT':None}
  if not alive(c) or c['program']: return options
  if c['kind'] not in ('FDC','FRC','LEC'): options['MOVE']=None
  else: options['MAINTAIN']=None
  near=self.neighbors(c,self.p['contact_um'])
  if c['kind'] in ('B','DC','MAC') and not c['cargo'] and not c['pmhc'] and c['state'] not in ('plasma','plasmablast','memory'):
   ag=self.local_antigen(c)
   if ag: options['CAPTURE']=ag[0]['id']
  if c['kind']=='FDC' and self.config['fdc'] and sum(a['owner']==c['id'] and a['pool']=='fdc_retained' for a in self.antigens)<8:
   ag=[a for a in self.local_antigen(c) if a['pool']=='free_native' and a['complex']]
   if ag: options['RETAIN']=ag[0]['id']
  if c['cargo'] and self.antigen(c['cargo'])['pool']=='native_cargo': options['PROCESS']=c['cargo']
  if c['kind']=='CD4':
   if c['state']=='naive':
    n=next((n for n in near if n['kind']=='DC' and n['costim'] and self.compatible(c,n['pmhc']) and not n['program']),None)
    if n: options['PRIME']=n['id']
   elif c['state']=='activated': options['HELPER']=None
  if c['kind']=='B':
   if c['pmhc'] and self.config['cd40'] and c['state'] in ('activated','lz') and self.time>=c['help_until']:
    n=next((n for n in near if n['kind']=='CD4' and n['state'] in ('pre_tfh','tfh') and self.compatible(n,c['pmhc']) and not n['program']),None)
    if n: options['HELP']=n['id']
   if c['help_until']>self.time:
    if c['state']=='activated':
     options['PLASMA']=None
     if dpoint(c,self.follicle)<78*self.scale and any(n['kind']=='FDC' and n['cue_until']>=self.time for n in self.neighbors(c)) and self.config['fdc']: options['ENTER_GC']=None
    if c['state']=='selected' and c['gc_member'] and self.gc:
     options.update(RECYCLE=None,MEMORY=None,PLASMA=None)
   if c['state']=='dz' and c['division_budget']>0 and c['help_until']>self.time: options['DIVIDE']=None
   if c['state']=='plasmablast': options['MATURE']=None
   if c['state'] in ('plasmablast','plasma'): options['SECRETE']=None
  if c['kind']=='MAC' and c['debris_until']<=self.time:
   n=next((n for n in near if n['state']=='apoptotic'),None)
   if n: options['CLEAR']=n['id']
  return options

 def observation(self,c):
  # No global counts, hidden neighboring receptor, affinity or future state.
  return dict(cell={k:copy.deepcopy(c[k]) for k in ('id','kind','lineage','state','x','y','z','bcr','tcr','hla','affinity','isotype','generation','division_budget','help_until','pmhc','program')},
   time_min=self.time,units={'length':'um','time':'min'},
   nearby=[dict(id=n['id'],kind=n['kind'],distance_um=round(distance(c,n),2),
     surface_pmhc=copy.deepcopy(n['pmhc']),costimulation=n['costim'],apoptotic=n['state']=='apoptotic') for n in self.neighbors(c)],
   accessible_antigen=[{k:a[k] for k in ('id','epitope','peptide','pool','source')} for a in self.local_antigen(c)],
   cues=self.cues(c),cargo=copy.deepcopy(self.antigen(c['cargo'])) if c['cargo'] else None)

 def cues(self,c):
  # Fixed stromal-positioning scaffold, sampled only at the cell. No global target readout.
  def field(p,center,scale): return math.exp(-((p[0]-center[0])**2+(p[1]-center[1])**2)/(2*scale**2))
  center=self.follicle if c['kind']=='B' and c['state']=='activated' and c['help_until']>self.time else self.dz if c['state']=='dz' else self.lz if c['state'] in ('lz','selected') else (-7*self.scale,35*self.scale) if c['state'] in ('activated','pre_tfh') else self.follicle if c['kind']=='B' or c['state']=='tfh' else (28*self.scale,12*self.scale)
  x,y=c['x'],c['y']; f=field((x,y),center,75*self.scale)
  return dict(scaffold='proposed static positioning field',value=round(f,5),
    gradient=[round(field((x+1,y),center,75*self.scale)-f,6),round(field((x,y+1),center,75*self.scale)-f,6)])

 def proposals(self):
  return [dict(id=c['id'],observation=self.observation(c),options=self.eligible(c)) for c in self.cells if alive(c) and not c['program']]

 def fixture(self,rows):
  """Explicit test policy, never masquerades as Jev. Competing fates vary by clone."""
  answers={}
  for r in rows:
   c=self.get(r['id']); opts=r['options']; pref=['CLEAR','RETAIN','CAPTURE','PROCESS','PRIME','HELPER','HELP']
   if c['state']=='activated' and c['kind']=='B': pref+=['PLASMA','ENTER_GC'] if int(c['id'][-4:])%7==0 else ['ENTER_GC']
   if c['state']=='selected': pref+=[['RECYCLE','MEMORY','PLASMA'][int(c['id'][-4:])%3]]
   pref+=['DIVIDE','MATURE','SECRETE','MAINTAIN','MOVE','WAIT']
   choice=next(a for a in pref if a in opts)
   answers[r['id']]=dict(choice=choice,probabilities={a:float(a==choice) for a in opts},confidence=1,source='fixture')
  return answers

 def step(self,answers,rows,source='fixture'):
  if self.round>=self.p['max_rounds'] or self.stop_reason: raise ValueError(self.stop_reason or 'Duration limit reached')
  expected={r['id'] for r in rows}
  if expected!=set(answers): raise ValueError('Missing or extra cell decisions; round not applied')
  # Prevalidate every answer before any physical mutation.
  for r in rows:
   if r['options']!=self.eligible(self.get(r['id'])): raise ValueError('Stale decision snapshot')
   a=answers[r['id']]
   if a.get('choice') not in r['options']: raise ValueError('Unsupported action')
   probs=a.get('probabilities',{})
   if set(probs)!=set(r['options']) or any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1 for v in probs.values()) or abs(sum(probs.values())-1)>1e-6: raise ValueError('Invalid action probabilities')
  reserved=set(); shuffled=list(rows); self.rng.shuffle(shuffled)
  for r in shuffled:
   c=self.get(r['id']); a=answers[c['id']]; choice=a['choice']; target=r['options'][choice]
   receipt=dict(round=self.round,time_min=self.time,cell=c['id'],source=source,
     observation=r['observation'],options=r['options'],proposal=copy.deepcopy(a),result='applied')
   if c['id'] in reserved or (target and target in reserved): receipt['result']='deferred: target already reserved'
   else:
    if target: reserved.update((target,c['id']))
    self.apply(c,choice,target)
    c['last_action']=choice
   c['last_decision']=dict(action=choice,source=source,probabilities=a['probabilities'],result=receipt['result'],time_min=self.time)
   self.decisions.append(receipt)
  self.time+=self.p['step_min']; self.round+=1
  self.clocks(); self.transport(); self.organize_gc(); self.assert_invariants(); self.save_frame()
  if self.round>=self.p['max_rounds']: self.stop_reason='Configured duration reached; export or start a new run'
  return self.snapshot()

 def program(self,c,action,duration,target=None):
  c['program']=dict(action=action,due=self.time+duration,target=target)
  self.log('program_started',c['id'],ACTIONS[action][1] if action in ACTIONS else 'LN-R007',action=action,due=c['program']['due'],target=target)

 def apply(self,c,action,target):
  if action=='MOVE': self.move(c)
  elif action in ('CAPTURE','RETAIN'):
   a=self.antigen(target); a.update(owner=c['id'],x=c['x'],y=c['y'],pool='fdc_retained' if action=='RETAIN' else 'native_cargo')
   if action=='CAPTURE':
    c['cargo']=a['id']
    if c['kind']=='B' and c['state']=='naive': c['state']='activated'
    if c['kind']=='DC': c['costim']=True
   self.log(action.lower(),c['id'],'LN-R005',antigen=a['id'],source=a['source'])
  elif action=='PROCESS':
   self.antigen(c['cargo'])['pool']='internalized'; self.program(c,action,self.p['processing_min'])
  elif action in ('PRIME','HELP'):
   self.program(c,action,self.p['priming_min'] if action=='PRIME' else self.p['help_min'],target)
   n=self.get(target); n['program']=dict(action='CONTACT',due=c['program']['due'],target=c['id'])
  elif action in ('HELPER','ENTER_GC','DIVIDE','MEMORY','PLASMA','MATURE'):
   duration=self.p['helper_min'] if action=='HELPER' else self.p['founder_min'] if action=='ENTER_GC' else self.p['division_min'] if action=='DIVIDE' else self.p['differentiation_min']
   if action=='DIVIDE': c['division_budget']-=1
   self.program(c,action,duration)
  elif action=='RECYCLE':
   c['state']='dz'; c['division_budget']=self.p['selection_divisions']; c['selection_since']=None
  elif action=='SECRETE':
   c['antibodies']+=1; self.antibody+=1; self.antibody_clones[c['clone']+'|'+c['isotype']]+=1
   self.log('antibody_secreted',c['id'],'LN-R026',clone=c['clone'],epitope=c['bcr'],isotype=c['isotype'],units='arbitrary secretion units')
  elif action=='CLEAR':
   corpse=self.get(target); corpse['state']='cleared'; self.cleared+=1; c['debris_until']=self.time+120
   self.release_antigen(corpse); self.log('corpse_cleared',c['id'],'LN-R025',target=target)
  elif action=='MAINTAIN': c['cue_until']=self.time+2*self.p['step_min']

 def can_place(self,x,y,exclude=()):
  r=self.p['cell_radius_um']
  return math.hypot(x,y)<=self.p['radius_um']-r and all(math.hypot(x-n['x'],y-n['y'])>=2*r+.05 for n in self.cells if occupied(n) and n['id'] not in exclude)

 def move(self,c):
  cue=self.cues(c)['gradient']; near=self.neighbors(c)
  target=None
  if c['kind']=='CD4' and c['state']=='naive': target=next((n for n in near if n['kind']=='DC' and n['pmhc'] and self.compatible(c,n['pmhc'])),None)
  elif c['kind']=='B' and c['pmhc'] and c['state'] in ('activated','lz') and c['help_until']<=self.time:
   target=next((n for n in near if n['kind']=='CD4' and n['state'] in ('pre_tfh','tfh')),None)
  if target: angle=math.atan2(target['y']-c['y'],target['x']-c['x'])
  elif c['kind'] in ('B','DC') and not c['cargo'] and not c['pmhc']:
   ag=next((a for a in self.antigens if a['pool'] in ('free_native','fdc_retained') and math.hypot(a['x']-c['x'],a['y']-c['y'])<self.p['sensing_um'] and (c['kind']!='B' or a['epitope']==c['bcr'])),None)
   angle=math.atan2(ag['y']-c['y'],ag['x']-c['x']) if ag else math.atan2(cue[1],cue[0])+self.rng.uniform(-2,2)
  else: angle=math.atan2(cue[1],cue[0])+self.rng.uniform(-2,2)
  for offset in [0,.8,-.8,1.6,-1.6,3.14]:
   x=c['x']+math.cos(angle+offset)*self.p['movement_um']; y=c['y']+math.sin(angle+offset)*self.p['movement_um']
   # Check the swept path, not only the endpoint.
   if all(self.can_place(c['x']+(x-c['x'])*t,c['y']+(y-c['y'])*t,(c['id'],)) for t in (.25,.5,.75,1)):
    c['x']=x;c['y']=y;break

 def release_antigen(self,c):
  for a in self.antigens:
   if a['owner']==c['id']: a['pool']='degraded';a['owner']=None
  c['cargo']=None;c['pmhc']=None

 def clocks(self):
  for c in list(self.cells):
   if not alive(c): continue
   if c['pmhc'] and c['pmhc']['expires']<=self.time:
    a=self.antigen(c['pmhc']['antigen']); a.update(pool='degraded',owner=None); c['pmhc']=None
   # Failed selection is an explicit proposed deadline, not an AI death choice.
   if c['state'] in ('founder','dz') and not c['program'] and c['help_until']<=self.time:
    c['state']='lz' if c['gc_member'] else 'activated';c['selection_since']=self.time if c['gc_member'] else None;c['division_budget']=0
   if c['state']=='lz' and c['selection_since'] is not None and self.time-c['selection_since']>=self.p['selection_timeout_min']:
    c['state']='apoptotic';c['program']=None;self.deaths+=1
    self.log('failed_selection_apoptosis',c['id'],'LN-R023');continue
   p=c['program']
   if not p or p['due']>self.time: continue
   action=p['action']; c['program']=None
   if action=='CONTACT': continue
   if action in ('PRIME','HELP'):
    n=self.get(p['target']); valid=n and alive(n) and distance(c,n)<=self.p['contact_um']
    valid=valid and (n['costim'] and self.compatible(c,n['pmhc']) if action=='PRIME' else self.config['cd40'] and self.compatible(n,c['pmhc']))
    if not valid:
     self.log('contact_cancelled',c['id'],'LN-R009',action=action);continue
    if action=='PRIME': c['state']='activated'
    else:
     c['help_until']=self.time+self.p['help_lifetime_min'];c['last_help']=n['id'];c['division_budget']=self.p['selection_divisions'];n['state']='tfh'
     if c['state']=='lz': c['state']='selected';c['selection_since']=None
   elif action=='PROCESS':
    self.antigen(c['cargo'])['pool']='processed_peptide';self.program(c,'LOAD',self.p['loading_min'])
   elif action=='LOAD':
    a=self.antigen(c['cargo']); a['pool']='surface_pmhc';c['pmhc']=dict(antigen=a['id'],source=a['source'],peptide=a['peptide'],hla=a['hla'],expires=self.time+self.p['pmhc_lifetime_min']);c['cargo']=None
    if c['kind']=='DC': c['state']='presenting'
   elif action=='HELPER': c['state']='pre_tfh'
   elif action=='ENTER_GC': c['state']='founder'
   elif action=='DIVIDE': self.divide(c)
   elif action=='MEMORY': c['state']='memory';c['division_budget']=0
   elif action=='PLASMA': c['state']='plasmablast';c['division_budget']=0
   elif action=='MATURE': c['state']='plasma';c['division_budget']=0
   self.log('program_completed',c['id'],ACTIONS.get(action,('', 'LN-R007'))[1],action=action)

 def divide(self,c):
  if sum(alive(n) for n in self.cells)>=self.p['max_cells']:
   self.valid=False; self.stop_reason='Population safety cap reached'; self.log('population_cap',c['id'],'LN-R022');return
  r=self.p['cell_radius_um']+.2; pair=None
  for k in range(24):
   angle=k*math.pi/12; dx=math.cos(angle)*r;dy=math.sin(angle)*r
   if self.can_place(c['x']+dx,c['y']+dy,(c['id'],)) and self.can_place(c['x']-dx,c['y']-dy,(c['id'],)):
    pair=[(c['x']+dx,c['y']+dy),(c['x']-dx,c['y']-dy)];break
  if pair is None:
   # A failed cycle cannot repeatedly produce daughters; license is returned for a new attempt.
   c['division_budget']+=1;self.log('division_crowding',c['id'],'LN-R022');return
  self.release_antigen(c); c['state']='divided';self.births+=1
  children=[]
  for x,y in pair:
   child=copy.deepcopy(c);self._id+=1;child.update(id='LN-%04d'%self._id,parent=c['id'],generation=c['generation']+1,
     state='lz',x=x,y=y,division_budget=0,help_until=0,selection_since=self.time,program=None,last_decision=None,
     bcr_variant=c['bcr_variant']+1,affinity=round(max(.01,min(1,c['affinity']+self.rng.choice([-.15,0,.1]))),3))
   self.cells.append(child);children.append(child['id'])
  self.log('division',c['id'],'LN-R021',daughters=children,clone=c['clone'],mutation='toy affinity kernel; not sequence-based SHM')

 def transport(self):
  for a in self.antigens:
   if a['owner']:
    c=self.get(a['owner']);a['x']=c['x'];a['y']=c['y']
   if a['pool']=='free_native':
    # Conservative biased diffusion from sinus into follicular tissue. No replication.
    a['x']+=self.rng.uniform(-10,10)+(self.follicle[0]-a['x'])*.025
    a['y']+=self.rng.uniform(-7,7)-1.5
    r=math.hypot(a['x'],a['y'])
    edge=self.p['radius_um']-5
    if r>edge: a['x']*=edge/r;a['y']*=edge/r
   if a['pool'] in ('free_native','fdc_retained') and self.time-a['created']>=self.p['antigen_lifetime_min']:
    a.update(pool='degraded',owner=None)

 def organize_gc(self):
  founders=[c for c in self.cells if c['kind']=='B' and c['state']=='founder' and c['help_until']>self.time and dpoint(c,self.follicle)<78*self.scale]
  support=any(c['kind']=='FDC' and alive(c) and c['cue_until']>=self.time for c in self.cells) and self.config['fdc']
  if not self.gc:
   if len(founders)>=self.p['gc_founders'] and support:
    if self.gc_candidate_since is None: self.gc_candidate_since=self.time
    if self.time-self.gc_candidate_since>=self.p['gc_organization_min']:
     self.gc=True;self.gc_since=self.time;self.log('germinal_center_formed',rule='LN-R013',founders=[c['id'] for c in founders])
   else: self.gc_candidate_since=None
  if self.gc:
   for c in founders: c['state']='dz';c['gc_member']=True
   active=[c for c in self.cells if c['state'] in ('dz','lz','selected','founder') and alive(c)]
   if not active: self.gc=False;self.gc_candidate_since=None;self.log('germinal_center_resolved',rule='LN-R013')

 def metrics(self):
  cells=[c for c in self.cells if alive(c)]; states=Counter(c['state'] for c in cells)
  pools=Counter(a['pool'] for a in self.antigens)
  return dict(live=len(cells),initial=self.initial_cells,net_births=self.births,deaths=self.deaths,cleared=self.cleared,
   gc_b=sum(states[s] for s in ('founder','dz','lz','selected')),tfh=states['tfh'],
   presenting=sum(c['pmhc'] is not None for c in cells),memory=states['memory'],plasma=states['plasma']+states['plasmablast'],
   antibodies=self.antibody,states=dict(states),types=dict(Counter(c['kind'] for c in cells)),pools=dict(pools),
   antigen_input=self.injected,antigen_accounted=len(self.antigens),decisions=len(self.decisions))

 def assert_invariants(self):
  assert len({c['id'] for c in self.cells})==len(self.cells)
  assert sum(alive(c) for c in self.cells)==self.initial_cells+self.births-self.deaths
  assert len(self.antigens)==self.injected
  for c in self.cells:
   assert c['z']==0 and math.hypot(c['x'],c['y'])<=self.p['radius_um']-c['radius']+1e-8
   assert not (c['state']=='plasma' and c['division_budget'])
   assert c['kind']!='B' or c['lineage']=='B'
   assert c['state'] not in ('apoptotic','cleared') or c['program'] is None
  occ=[c for c in self.cells if occupied(c)]
  for i,c in enumerate(occ):
   assert all(distance(c,n)>=c['radius']+n['radius']-1e-6 for n in occ[i+1:]),'Cell overlap'
  for a in self.antigens:
   assert a['mass']==1
   if a['owner']: assert occupied(self.get(a['owner']))

 def snapshot(self):
  return copy.deepcopy(dict(version=VERSION,seed=self.seed,scenario=self.scenario,time_min=self.time,round=self.round,
   gc=self.gc,gc_since=self.gc_since,valid=self.valid,stop_reason=self.stop_reason,params=self.p,
   cells=[c for c in self.cells if c['state'] not in ('cleared','divided')],
   antigens=[a for a in self.antigens if a['pool'] in ('free_native','fdc_retained')],metrics=self.metrics(),events=self.events[-35:]))

 def save_frame(self):
  self.frames.append(dict(time_min=self.time,gc=self.gc,metrics=self.metrics(),event_count=len(self.events),
   cells=[{k:copy.deepcopy(c[k]) for k in ('id','kind','state','x','y','z','clone','parent','affinity','isotype','pmhc','last_action')} for c in self.cells if occupied(c)]))

 def export(self):
  contract=dict(version=VERSION,sources=SOURCES,parameters=self.p,registry=self.registry,initial_cells=self.initial_cells,actions=ACTIONS,scenario=self.config)
  return dict(format='lymph-node-episode-v1',contract=contract,
   fingerprint=hashlib.sha256(json.dumps(contract,sort_keys=True).encode()).hexdigest(),
   seed=self.seed,initial=self.initial,final=self.snapshot(),inputs=self.inputs,events=self.events,
   decisions=self.decisions,frames=self.frames,failures=self.failures,
   antigen_ledger=self.antigens,cell_ancestry=[dict(id=c['id'],clone=c['clone'],parent=c['parent'],state=c['state']) for c in self.cells],
   assumptions='Uncalibrated representative monolayer; all numbers proposed. Fixtures are not Jev responses.')
