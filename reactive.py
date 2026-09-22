"""Event-driven LN extension. All spatial/temporal thresholds are proposed priors.

No Gut runtime dependency. The legacy kernel remains available for old episodes.
"""
import copy
import hashlib
import json
import math
import re
from engine import Simulation, REGISTRY, FOLLICLE, DZ, LZ, alive, occupied, distance

REACTIVE_RULES = dict(version='ln-local-response-v1', decision_interval_min=60,
    motility_min=60, motility_speed_um_min=.3, native_sensing_um=28,
    presentation_sensing_um=36, entry_min=30, antigen_packets=9,
    site_spacing_um=20, radius_at_120_um=135,
    decision_contract='Only locally stimulated, non-busy, due cells with an executable action are queried.',
    evidence='P: uncalibrated demonstration assumptions; not measured human rates.')
PROMPT = 'An antigen-bearing dendritic cell enters the lymph node.'


class ReactiveSimulation(Simulation):
    def __init__(self, seed=21, initial_cells=120, params=None):
        if type(initial_cells) is not int or not 100 <= initial_cells <= 149:
            raise ValueError('Choose 100–149 resident cells, leaving room for the incoming dendritic cell.')
        self.residents = initial_cells
        self.entries = 0
        self.gc_center = None
        self.gc_candidate_id = None
        self.last_queried = []
        self.last_prompt = None
        super().__init__(seed, 'baseline', {**dict(step_min=10, movement_um=3,
            max_rounds=180, max_cells=150, pmhc_lifetime_min=720), **(params or {})}, initial_cells=100)

    def _initialize(self):
        self.initial_cells = self.residents
        self.scale = math.sqrt(self.initial_cells / 300)
        self.p['radius_um'] = REACTIVE_RULES['radius_at_120_um'] * math.sqrt(self.residents/120)
        self.population = dict(B=round(self.residents*.46), CD4=round(self.residents*.29),
            DC=5, MAC=6, FDC=6, FRC=5, LEC=3)
        self.population['B'] += self.residents - sum(self.population.values())
        self.registry = {k:dict(v, count=self.population[k]) for k,v in REGISTRY.items()}
        self.follicle, self.dz, self.lz = [tuple(v*self.scale for v in p) for p in (FOLLICLE,DZ,LZ)]
        # Open intercellular corridors permit actual migration without moving quiet cells.
        spacing=REACTIVE_RULES['site_spacing_um']
        sites=[((i+(j%2)*.5)*spacing,j*spacing*math.sqrt(3)/2)
            for j in range(-12,13) for i in range(-12,13)
            if math.hypot((i+(j%2)*.5)*spacing,j*spacing*math.sqrt(3)/2)<self.p['radius_um']-10]
        self.rng.shuffle(sites)
        for kind in ('LEC','FDC','MAC','DC','FRC','B','CD4'):
            center=self.follicle if kind in ('B','FDC') else (22,10)
            sites.sort(key=lambda p: abs(math.hypot(*p)-self.p['radius_um']+16) if kind=='LEC'
                else math.hypot(p[0]-center[0],p[1]-center[1])+self.rng.random()*70)
            self.cells.extend(self.new_cell(kind,*p) for p in sites[:self.population[kind]])
            sites=sites[self.population[kind]:]
        for c in self.cells:
            c.update(next_decision=0, decision_count=0, arrival=None)

    def perturb(self, prompt):
        # A declared, narrow grammar: prompts introduce inputs, never cell fates.
        normalized = re.sub(r'[^a-z0-9 ]', ' ', str(prompt).lower())
        words = set(normalized.split())
        if not {'antigen','dendritic','cell'} <= words or not words.intersection({'enters','enter','arrives','arrive','introduce','add'}):
            raise ValueError('Supported prompt: “An antigen-bearing dendritic cell enters the lymph node.” Prompts introduce the perturbation; cells choose their own responses.')
        if words.intersection({'force','guarantee','become','differentiate','plasmablast','antibodies','germinal','not','never','without','no'}):
            raise ValueError('Describe the incoming antigen-bearing dendritic cell. A prompt cannot assign a cell fate or create a germinal center.')
        if self.entries or self.stop_reason:
            raise ValueError('This experiment already received its dendritic cell. Reset for another independent experiment.')
        angle = math.radians(112)
        edge = self.p['radius_um'] - self.p['cell_radius_um'] - .5
        point = next(((edge*math.cos(angle+i*.05),edge*math.sin(angle+i*.05))
            for i in range(40) if self.can_place(edge*math.cos(angle+i*.05),edge*math.sin(angle+i*.05))), None)
        if point is None: raise ValueError('The afferent boundary is occupied; no entry was applied.')
        c = self.new_cell('DC', *point)
        c.update(costim=True, next_decision=0, decision_count=0,
            arrival=dict(time_min=self.time, from_x=point[0]*1.2, from_y=point[1]*1.2))
        self.cells.append(c); self.entries += 1
        self.config['antigen'] = True
        for i in range(REACTIVE_RULES['antigen_packets']):
            self._aid += 1
            a = dict(id='AG-%05d'%self._aid, source='incoming-dc-'+c['id'],
                epitope='E1',peptide='P1',hla='HLA-II-A' if self.config['hla_match'] else 'HLA-II-X',
                pool='native_cargo' if i==0 else 'dc_native',owner=c['id'],
                x=c['x'],y=c['y'],created=self.time,mass=1,complex=False)
            self.antigens.append(a)
            if i==0: c['cargo']=a['id']
        self.injected += REACTIVE_RULES['antigen_packets']
        self.last_prompt = str(prompt)[:500]
        self.inputs.append(dict(time_min=self.time, prompt=self.last_prompt, kind='antigen_bearing_dc',
            cell=c['id'], amount=REACTIVE_RULES['antigen_packets'], route='afferent boundary',
            assumption='One processing packet plus eight conserved native packets available at DC–B contact; proposed compartment abstraction.'))
        self.program(c,'ARRIVE',REACTIVE_RULES['entry_min'])
        self.log('dendritic_cell_arrived', c['id'],'LN-R002',antigen_packets=REACTIVE_RULES['antigen_packets'])
        self.assert_invariants()
        return c['id']

    def visible_antigen(self,c,radius):
        return [a for a in self.antigens if a['pool'] in ('free_native','fdc_retained','dc_native')
            and math.hypot(c['x']-a['x'],c['y']-a['y'])<=radius
            and (c['kind']!='B' or c['bcr']==a['epitope'])
            and (a['pool']!='dc_native' or (c['kind']=='B' and
                (self.get(a['owner'])['program'] or {}).get('action')!='ARRIVE'))]

    def local_antigen(self,c):
        return self.visible_antigen(c,self.p['contact_um'])

    def local_response(self,c):
        reasons=[];target=None
        if not alive(c): return dict(active=False,reasons=[],target=None)
        own = c['cargo'] or c['pmhc'] or c['state'] in ('activated','pre_tfh','tfh','founder','dz','lz','selected','plasmablast','plasma')
        if own: reasons.append(dict(code='own',label='Own antigen or an acquired cellular program'))
        if c['kind']=='B' and not c['cargo'] and not c['pmhc'] and c['state'] not in ('memory','plasmablast','plasma'):
            ag = self.visible_antigen(c,REACTIVE_RULES['native_sensing_um'])
            if ag:
                target=min(ag,key=lambda a:distance(c,a))
                reasons.append(dict(code='native',label='Local cognate native antigen',
                    target=target['id'],distance_um=round(distance(c,target),2)))
        near=self.neighbors(c,REACTIVE_RULES['presentation_sensing_um'])
        if c['kind']=='CD4' and c['state']=='naive':
            partners=[n for n in near if n['kind']=='DC' and n['costim'] and self.compatible(c,n['pmhc'])]
        elif c['kind']=='B' and c['pmhc'] and c['help_until']<=self.time and c['state'] in ('activated','lz'):
            partners=[n for n in near if n['kind']=='CD4' and n['state'] in ('pre_tfh','tfh') and self.compatible(n,c['pmhc'])]
        elif c['kind']=='CD4' and c['state'] in ('pre_tfh','tfh'):
            partners=[n for n in near if n['kind']=='B' and n['state'] in ('activated','lz') and
                self.compatible(c,n['pmhc']) and n['help_until']<=self.time]
        else: partners=[]
        if partners:
            target=min(partners,key=lambda n:distance(c,n))
            reasons.append(dict(code='partner',label='Nearby compatible presentation / help contact',
                target=target['id'],distance_um=round(distance(c,target),2)))
        if c['kind']=='MAC':
            corpses=[n for n in self.neighbors(c,self.p['contact_um']) if n['state']=='apoptotic']
            if corpses: reasons.append(dict(code='debris',label='Local apoptotic debris',target=corpses[0]['id']))
        return dict(active=bool(reasons),reasons=reasons,target=target)

    def eligible(self,c):
        options=super().eligible(c)
        options.pop('MAINTAIN',None)  # Constitutive scaffold is a physical baseline process.
        local=self.local_response(c)
        target=local['target']
        move=False
        if local['active'] and not c['program']:
            if target: move=distance(c,target)>self.p['contact_um']-1
            elif c['kind']=='DC' and c.get('arrival') and (c['cargo'] or c['pmhc']):
                move=self.cues(c)['value']<.97
            elif c['kind']=='CD4' and c['state'] in ('pre_tfh','tfh'):
                move=self.cues(c)['value']<.97
            elif c['kind']=='B' and c['state']=='activated' and c['pmhc'] and c['help_until']<=self.time:
                # Finite exploratory response to own antigen; quiet again until a local contact appears.
                move=self.time<c['pmhc']['expires']-180
            elif c['kind']=='B' and c['state']=='activated' and c['help_until']>self.time:
                move=self.cues(c)['value']<.9
            elif c['kind']=='B' and c['state']=='founder':
                move=self.cues(c)['value']<.94
        if not move: options.pop('MOVE',None)
        return options

    def observation(self,c):
        o=super().observation(c)
        o['activation']={k:v for k,v in self.local_response(c).items() if k!='target'}
        o['decision_policy']=REACTIVE_RULES['decision_contract']
        o['movement_program']='MOVE starts up to 60 min of collision-checked local migration; no additional choice while busy.'
        return o

    def proposals(self):
        rows=[]
        for c in self.cells:
            if not alive(c) or c['program'] or self.time<c.get('next_decision',0): continue
            options=self.eligible(c)
            if self.local_response(c)['active'] and any(a!='WAIT' for a in options):
                rows.append(dict(id=c['id'],observation=self.observation(c),options=options))
        return rows

    def fixture(self,rows):
        answers={}
        for r in rows:
            c=self.get(r['id']);options=r['options']
            priority=['CLEAR','RETAIN','CAPTURE','PROCESS','PRIME','HELPER','HELP']
            if c['kind']=='B' and c['state']=='activated':
                priority += ['PLASMA','ENTER_GC'] if int(c['id'][-4:])%3==0 else ['ENTER_GC']
            if c['state']=='selected': priority+=['MEMORY','RECYCLE','PLASMA']
            priority+=['DIVIDE','SECRETE','MATURE','MOVE','WAIT']
            choice=next(a for a in priority if a in options)
            answers[c['id']]=dict(choice=choice,probabilities={a:float(a==choice) for a in options},confidence=1,source='fixture')
        return answers

    def apply(self,c,action,target):
        if action=='MOVE': self.program(c,'MOVE',REACTIVE_RULES['motility_min'])
        else:
            super().apply(c,action,target)
            if action in ('PRIME','HELP'):self.get(target)['program']['started']=self.time

    def program(self,c,action,duration,target=None):
        super().program(c,action,duration,target)
        c['program']['started']=self.time

    def move(self,c):
        local=self.local_response(c); target=local['target']
        if target:
            gap=distance(c,target)
            if gap<=self.p['contact_um']-1: return False
            direction=math.atan2(target['y']-c['y'],target['x']-c['x'])
            length=min(self.p['movement_um'],gap-(self.p['contact_um']-1))
        else:
            cue=self.cues(c)['gradient'];direction=math.atan2(cue[1],cue[0]);length=self.p['movement_um']
        for offset in (0,.5,-.5,1,-1,1.5,-1.5):
            dx=math.cos(direction+offset)*length;dy=math.sin(direction+offset)*length
            if all(self.can_place(c['x']+dx*t,c['y']+dy*t,(c['id'],)) for t in (.25,.5,.75,1)):
                c['x']+=dx;c['y']+=dy;return True
        return False

    def clocks(self):
        for c in self.cells:
            p=c['program']
            if alive(c) and p and p['action']=='MOVE':
                if not self.move(c): p['due']=self.time
            if c['kind'] in ('FDC','FRC','LEC') and alive(c): c['cue_until']=self.time+self.p['step_min']
        super().clocks()

    def transport(self):
        super().transport()
        for a in self.antigens:
            if a['pool']=='dc_native' and self.time-a['created']>=self.p['antigen_lifetime_min']:
                a.update(pool='degraded',owner=None)

    def divide(self,c):
        before=len(self.cells)
        super().divide(c)
        for child in self.cells[before:]:
            child.update(decision_count=0,next_decision=self.time,arrival=None,last_action='WAIT')

    def step(self,answers,rows,source='fixture'):
        if rows!=self.proposals(): raise ValueError('Stale or incomplete local decision set')
        if self.round>=self.p['max_rounds'] or self.stop_reason:raise ValueError(self.stop_reason or 'Duration limit reached')
        if set(answers)!={r['id'] for r in rows}:raise ValueError('Missing or extra local cell choices')
        for row in rows:
            answer=answers[row['id']];probs=answer.get('probabilities',{})
            if answer.get('choice') not in row['options']:raise ValueError('Unsupported action')
            if set(probs)!=set(row['options']) or any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1 for v in probs.values()) or abs(sum(probs.values())-1)>1e-6:
                raise ValueError('Invalid action probabilities')
        reserved=set();ordered=list(rows);self.rng.shuffle(ordered)
        for row in ordered:
            c=self.get(row['id']);answer=answers[c['id']];choice=answer['choice'];target=row['options'][choice]
            receipt=dict(round=self.round,time_min=self.time,cell=c['id'],source=source,
                observation=row['observation'],options=row['options'],proposal=copy.deepcopy(answer),result='applied')
            if c['id'] in reserved or (target and target in reserved):receipt['result']='deferred: target already reserved'
            else:
                if choice!='WAIT':reserved.add(c['id'])
                if target:reserved.add(target)
                self.apply(c,choice,target);c['last_action']=choice
            c['decision_count']=c.get('decision_count',0)+1
            c['next_decision']=self.time+REACTIVE_RULES['decision_interval_min']
            c['last_decision']=dict(action=choice,source=source,probabilities=answer['probabilities'],
                result=receipt['result'],time_min=self.time,observation=copy.deepcopy(row['observation']),options=copy.deepcopy(row['options']))
            self.decisions.append(receipt)
        self.last_queried=[r['id'] for r in rows]
        self.time+=self.p['step_min'];self.round+=1
        self.clocks();self.transport();self.organize_gc();self.assert_invariants();self.save_frame()
        if self.round>=self.p['max_rounds']:self.stop_reason='Configured duration reached; save or start a new run'
        return self.snapshot()

    def organize_gc(self):
        founders=[c for c in self.cells if c['kind']=='B' and c['state']=='founder' and c['help_until']>self.time]
        supported=[]
        if self.config['fdc']:
            for support in self.cells:
                if support['kind']!='FDC' or not alive(support) or support['cue_until']<self.time:continue
                local=[c for c in founders if distance(c,support)<=REACTIVE_RULES['presentation_sensing_um']]
                if len(local)>=self.p['gc_founders']:supported.append((support,local))
        if not self.gc:
            if supported:
                if self.gc_candidate_since is None or self.gc_candidate_id!=supported[0][0]['id']:
                    self.gc_candidate_since=self.time;self.gc_candidate_id=supported[0][0]['id']
                if self.time-self.gc_candidate_since>=self.p['gc_organization_min']:
                    support,local=supported[0];self.gc=True;self.gc_since=self.time
                    self.gc_center=[support['x'],support['y']]
                    self.log('germinal_center_formed',support['id'],'LN-R013',founders=[c['id'] for c in local])
            else:self.gc_candidate_since=None;self.gc_candidate_id=None
        if self.gc:
            for c in founders:
                if math.hypot(c['x']-self.gc_center[0],c['y']-self.gc_center[1])<=REACTIVE_RULES['presentation_sensing_um']:c['state']='dz';c['gc_member']=True
            if not any(c['state'] in ('dz','lz','selected','founder') and alive(c) for c in self.cells):
                self.gc=False;self.gc_candidate_since=None;self.gc_center=None;self.log('germinal_center_resolved',rule='LN-R013')

    def assert_invariants(self):
        assert sum(alive(c) for c in self.cells)==self.initial_cells+self.entries+self.births-self.deaths
        assert len({c['id'] for c in self.cells})==len(self.cells)
        assert len(self.antigens)==self.injected
        occ=[c for c in self.cells if occupied(c)]
        for i,c in enumerate(occ):
            assert c['z']==0 and math.hypot(c['x'],c['y'])<=self.p['radius_um']-c['radius']+1e-8
            assert all(distance(c,n)>=c['radius']+n['radius']-1e-6 for n in occ[i+1:]),'Cell overlap'
            assert c['kind']!='B' or c['lineage']=='B'
            assert not(c['state']=='plasma' and c['division_budget'])
        for a in self.antigens:
            assert a['mass']==1 and (not a['owner'] or occupied(self.get(a['owner'])))
        assert sum(alive(c) for c in self.cells)<=self.p['max_cells']

    def metrics(self):
        m=super().metrics()
        m.update(entries=self.entries,never_queried=sum(alive(c) and not c.get('decision_count',0) for c in self.cells),
            busy=sum(alive(c) and c['program'] is not None for c in self.cells),
            quiet=sum(alive(c) and not c['program'] and not self.local_response(c)['active'] for c in self.cells),
            responding=sum(alive(c) and self.local_response(c)['active'] for c in self.cells),
            queried_last_step=len(self.last_queried))
        return m

    def snapshot(self):
        s=super().snapshot()
        s.update(mode='reactive',last_prompt=self.last_prompt,entries=self.entries,queried=self.last_queried,
            response_rules=REACTIVE_RULES,follicle=self.follicle,gc_center=self.gc_center,antigens=copy.deepcopy(self.antigens))
        for c in s['cells']:
            local=self.local_response(c)
            c['response']={k:v for k,v in local.items() if k!='target'}
            c['options']=self.eligible(c)
        return s

    def export(self):
        e=super().export()
        e['contract'].update(reactive=REACTIVE_RULES,entries=self.entries)
        e['fingerprint']=hashlib.sha256(json.dumps(e['contract'],sort_keys=True).encode()).hexdigest()
        return e
