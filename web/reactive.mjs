import {atlasURL,frameRect,framePlacement,poseAt,phaseFor} from './cell-atlas.mjs';
import {readRecording,recordedStateLabels} from './replay.mjs';
const $=id=>document.getElementById(id),canvas=$('tissue'),ctx=canvas.getContext('2d');
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
const palette={B:'#d4a273',CD4:'#ebc749',DC:'#c8b8ec',FDC:'#b2a0c4',MAC:'#c9879e',FRC:'#82a99c',LEC:'#84adb0'};
const names={B:'B cell',CD4:'CD4 T cell',DC:'Dendritic cell',FDC:'Follicular dendritic cell',FRC:'Reticular stromal cell',LEC:'Lymphatic endothelial cell',MAC:'Macrophage'};
const labels={ARRIVE:'Entry through the afferent boundary',LOAD:'Peptide–HLA loading',MOVE:'Local migration',PROCESS:'Antigen processing',PRIME:'Cognate DC–CD4 contact',HELPER:'Helper differentiation',HELP:'Linked B–T helper contact',PLASMA:'Plasmablast commitment',ENTER_GC:'Germinal-center founder program',DIVIDE:'Licensed cell division',SECRETE:'IgM secretion',MATURE:'Plasma-cell maturation',CONTACT:'Reserved cellular contact',WAIT:'Wait and observe',CAPTURE:'Native antigen uptake',MEMORY:'Memory commitment',RECYCLE:'GC recycling'};
let state,token,playing=false,pending=false,selected=null,focused=false,showSignals=true,images={},width=0,height=0;
let previous=new Map(),receivedAt=0,interval=650,lastStep=0,points=[],camera={x:0,y:0,scale:1},trails=new Map(),lastFrame=0;
let cameraView={x:0,y:0,zoom:1},fitScale=1,drag=null,suppressPick=false;
const pointers=new Map();
let replay=null,replayRunning=false,replayIndex=0,replayTime=0,replayEnd=0,replayURL=null,replayLoading=false;
const clamp=x=>Math.max(0,Math.min(1,x)),mix=(a,b,t)=>a+(b-a)*t;
const name=c=>c.state==='apoptotic'?'Apoptotic '+names[c.kind]:c.state==='plasmablast'?'Plasmablast':c.state==='plasma'?'Plasma cell':c.state==='tfh'?'T follicular helper':names[c.kind];
function escape(text){const el=document.createElement('span');el.textContent=String(text);return el.innerHTML;}
function updateState(data){
 const old=state?.tissue;
 previous=new Map((old?.cells||data.tissue.cells).map(c=>[c.id,c]));
 state=data;token=data.token||token;receivedAt=performance.now();
 if(state.run_control?.outcome&&!selected)selected=state.run_control.outcome.cell;
 for(const c of state.tissue.cells){
  const tail=trails.get(c.id)||[],last=tail.at(-1);
  if(!last||last.x!==c.x||last.y!==c.y)tail.push({x:c.x,y:c.y});
  trails.set(c.id,tail.slice(-10));
 }
 update();
}
async function api(path,body){
 const response=await fetch('/api/'+path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json','X-LN-Token':token}:{},body:body?JSON.stringify(body):undefined});
 const data=await response.json();if(!response.ok)throw Error(data.error||'The local server could not complete this step.');return data;
}
function playUI(){
 $('view').textContent=focused?'Whole tissue':'Focus response';
 $('stopRecording').hidden=replay||!state?.run_control?.user_stoppable||state.run_control.status!=='running';
 $('stopRecording').disabled=!!state?.run_control?.stop_requested;
 if(replay){
  for(const id of ['introduce','applyPrompt','reset','cells','seed','prompt'])$(id).disabled=true;
  $('play').disabled=false;$('step').disabled=replayRunning;$('speed').disabled=false;
  $('play').textContent=replayRunning?'Ⅱ Pause recording':'▶ Play recording';$('play').setAttribute('aria-pressed',String(replayRunning));
  $('runState').textContent=replayRunning?'Playing saved decisions':'Recorded Jev experiment';
  $('provider').textContent=`Recorded Jev · ${replay.episode.provider.requests.toLocaleString('en-US')} API calls`;
  $('runDescription').textContent=(replay.episode.recording_status==='running'?'In-progress review snapshot. ':'')+replay.episode.run_control.policy_description;
  $('providerScope').textContent='This player reads recorded positions, biological events and individual Jev receipts. Playback makes zero inference calls. The published demonstration policy is uncalibrated.';
  return;
 }
 $('introduce').disabled=pending||!!state?.tissue.entries;
 $('applyPrompt').disabled=pending||!!state?.tissue.entries;
 $('play').textContent=playing?'Ⅱ Pause tissue':state?.provider.provider==='jev'?'▶ Run with Jev':'▶ Run tissue';
 $('play').setAttribute('aria-pressed',String(playing));
 $('step').disabled=pending||playing||!!state?.tissue.stop_reason;
 $('runState').textContent=state?.tissue.stop_reason?'Run complete':playing?'Tissue running':state?.tissue.entries?'Paused':'Steady state';
 if(state?.run_control?.managed){
  playing=false;
  $('runDescription').textContent=state.run_control.policy_description||'Recorded Jev decisions with local biological eligibility checks.';
  for(const id of ['introduce','applyPrompt','play','step','reset','cells','seed','speed','prompt'])$(id).disabled=true;
  $('play').textContent=state.run_control.status==='running'?'Jev run in progress':'Recorded Jev run';
  $('runState').textContent=state.run_control.status==='complete'?'IgM secretion verified':state.run_control.status==='running'?'Jev is running':state.run_control.status;
  $('provider').textContent=`Jev · ${(state.run_control.cumulative_requests??state.provider.requests).toLocaleString('en-US')} / ${state.run_control.request_cap.toLocaleString('en-US')} API calls`;
  $('providerScope').textContent=`${state.run_control.policy_description||'Local model semantics.'} This read-only view makes no inference calls. The displayed total includes ${state.run_control.prior_requests||0} calls from prior attempts.`;
  message(state.run_control.message);
 }
}
function message(text){$('message').textContent=text;}
async function advance(){
 if(pending||!state)return;pending=true;playUI();
 try{updateState(await api('step',{}));if(state.tissue.stop_reason){playing=false;message(state.tissue.stop_reason);}}
 catch(error){playing=false;message(error.message);}
 finally{pending=false;lastStep=performance.now();playUI();}
}
$('play').onclick=()=>{if(replay){if(replayTime>=replayEnd)showReplay(0);replayRunning=!replayRunning;playUI();return;}if(state.tissue.stop_reason)return;playing=!playing;lastStep=performance.now();playUI();};
$('step').onclick=()=>replay?showReplay(Math.min(replay.frames.length-1,replayIndex+1)):advance();
$('stopRecording').onclick=async()=>{try{$('stopRecording').disabled=true;updateState(await api('stop',{}));}catch(error){message(error.message);}};
$('speed').onchange=()=>interval=650/+$('speed').value;
$('perturbation').onsubmit=async event=>{
 event.preventDefault();if(pending)return;pending=true;$('introduce').disabled=true;
 try{updateState(await api('perturb',{prompt:$('prompt').value}));selected=state.tissue.cells.find(c=>c.arrival)?.id;playing=!reduced.matches;lastStep=performance.now();message('One dendritic cell entered with nine finite antigen packets. Local responses can now begin.');update();}
 catch(error){message(error.message);}
 finally{pending=false;$('introduce').disabled=!!state.tissue.entries;playUI();}
};
$('reset').onclick=async()=>{
 if(pending)return;
 if((state.tissue.round||state.tissue.entries)&&!confirm('Start a new quiet tissue? This replaces the current run. Save the experiment first if you want to keep it.'))return;
 playing=false;pending=true;playUI();
 try{trails.clear();selected=null;resetCamera();updateState(await api('reset',{cells:+$('cells').value,seed:+$('seed').value,discard:true}));message('New quiet tissue. Introduce a dendritic cell when ready.');$('introduce').disabled=false;}
 catch(error){message(error.message);}finally{pending=false;playUI();}
};
$('export').onclick=()=>{const a=document.createElement('a');a.href=replayURL||'/api/export';a.download='lymph-node.ln.json.gz';a.click();};
$('view').onclick=()=>focused?resetCamera():focusResponse();
$('signals').onclick=()=>{showSignals=!showSignals;$('signals').setAttribute('aria-pressed',String(showSignals));};
$('follow').onclick=()=>{
 const list=state.tissue.cells.filter(c=>c.response.active||c.program),index=list.findIndex(c=>c.id===selected);
 selected=list[(index+1)%list.length]?.id||state.tissue.cells[0].id;updateInspector();
};
$('cellSelect').onchange=event=>{selected=event.target.value;updateInspector();};
reduced.addEventListener('change',event=>{if(event.matches){playing=false;replayRunning=false;playUI();}});
function showReplay(index){
 replayIndex=Math.max(0,Math.min(replay.frames.length-1,index));replayTime=replay.frames[replayIndex].time_min;
 const e=replay.episode;updateState({tissue:replay.tissue(replayIndex),states:state?.states||e.states||recordedStateLabels,registry:e.contract.registry,provider:{...e.provider,provider:'jev'}});
 $('seek').value=String(replayTime);$('replayTime').textContent=(replayTime/60).toFixed(1)+' h';
 $('activity').textContent=`Frame ${replayIndex+1} / ${replay.frames.length}`;
 $('sceneNote').textContent=`${state.tissue.metrics.never_queried} cells never queried · saved frame · ${state.tissue.metrics.net_births} division${state.tissue.metrics.net_births===1?'':'s'}`;
 message(replayTime>72*60?'Extended output phase: plasma-cell lifespan and antibody decay are not modeled. Playback makes no Jev calls.':'Recorded positions and decisions. Playing, pausing, and seeking use no Jev calls.');
}
function replayWindow(){
 replayEnd=$('replayWindow').value==='full'?replay.duration:replay.highlightEnd;
 $('seek').max=String(replayEnd);$('replayEnd').textContent=(replayEnd/60).toFixed(1)+' h';
 $('replayNote').textContent=$('replayWindow').value==='full'?'Full saved time range, including sustained antibody output. Playback uses no inference.':'The initial response is shown at a slower pace. Choose Full recording to inspect the extended output phase.';
 if(replayTime>replayEnd)showReplay(replay.indexAt(replayEnd));
}
async function openReplay(url,hash){
 if(replayLoading)return;replayLoading=true;
 try{
  replay=await readRecording(url,hash);replayURL=url;playing=false;document.body.dataset.mode='replay';
  document.querySelector('.tissue-panel').insertBefore(document.querySelector('.transport'),document.querySelector('.camera-toolbar'));
  $('replayControls').hidden=false;$('export').textContent='Download recording ↓';
  $('speed').innerHTML='<option value="0.5">0.5 h / sec</option><option value="2">2 h / sec</option><option value="12">12 h / sec</option><option value="72">72 h / sec</option>';
  $('speed').value='0.5';$('chapters').replaceChildren();
  for(const chapter of replay.chapters){const button=document.createElement('button');button.textContent=`${chapter.label} · ${(chapter.time/60).toFixed(1)} h`;button.onclick=()=>{replayRunning=false;selected=chapter.cell;focusResponse();if(chapter.time>replayEnd){$('replayWindow').value='full';replayWindow();}showReplay(chapter.index);};$('chapters').append(button);}
  $('seek').oninput=()=>{replayRunning=false;trails.clear();showReplay(replay.indexAt(+$('seek').value));};
  $('replayWindow').onchange=replayWindow;
  $('lastFrame').onclick=()=>{replayRunning=false;$('replayWindow').value='full';replayWindow();selected=replay.episode.run_control.outcome?.cell;showReplay(replay.frames.length-1);};
  replayWindow();selected=replay.episode.inputs[0]?.cell;showReplay(0);replayRunning=!reduced.matches;playUI();
 }finally{replayLoading=false;}
}
function update(){
 const t=state.tissue,m=t.metrics;
 $('population').textContent=m.live;$('never').textContent=m.never_queried;$('responding').textContent=m.responding;
 $('decisions').textContent=m.decisions;$('divisions').textContent=m.net_births;$('antibodies').textContent=m.antibodies;$('clock').textContent=(t.time_min/60).toFixed(1)+' h';
 $('provider').textContent=state.provider.provider==='jev'?`Jev · ${state.provider.requests} requests · cap ${state.decision_cap} choices`:'Local policy preview · 0 AI calls';
 if(state.provider.provider==='jev')$('providerScope').textContent=`Live Jev chooses only for eligible local responders. This experiment is capped at ${state.decision_cap} individual decisions, with a separate server request cap. Empty steps use no API calls. A provider error pauses the run.`;
 $('sceneNote').textContent=t.entries?`${m.never_queried} of ${m.live} cells have never been queried. ${m.busy} timed processes running.`:`${m.live} quiet cells. No perturbation. No decisions.`;
 $('activity').textContent=m.queried_last_step?`${m.queried_last_step} cell${m.queried_last_step===1?'':'s'} queried this step`:'No cellular questions this step';
 $('cells').value=String(t.metrics.initial);$('seed').value=t.seed;$('introduce').disabled=!!t.entries||pending;$('applyPrompt').disabled=!!t.entries||pending;
 $('cellSelect').innerHTML='<option value="">Select a cell…</option>'+t.cells.map(c=>`<option value="${c.id}">${c.id} · ${escape(name(c))}${c.response.active?' · responding':''}</option>`).join('');
 const important=t.events.filter(e=>!['program_started','program_completed'].includes(e.event)||!['MOVE','CONTACT','ARRIVE'].includes(e.action));
 $('events').innerHTML=important.slice(-5).reverse().map(e=>`<li><time>${(e.time_min/60).toFixed(1)} h${e.cell?' · '+e.cell:''}</time>${escape(eventLabel(e))}</li>`).join('')||'<li>The undisturbed tissue is at steady state.</li>';
 canvas.dataset.time=t.time_min;canvas.dataset.decisions=m.decisions;canvas.dataset.neverQueried=m.never_queried;
 canvas.setAttribute('aria-label',`${m.live} individual cells; ${m.never_queried} never queried; ${m.responding} sensing a local change; ${m.antibodies} IgM output units.`);
 updateInspector();playUI();
}
function eventLabel(e){
 if(e.event==='dendritic_cell_arrived')return 'Antigen-bearing dendritic cell arrived';
 if(e.event==='antibody_secreted')return 'Secreted IgM · clone preserved';
 if(e.event==='capture')return 'Acquired one native antigen packet';
 if(e.event==='program_started'||e.event==='program_completed')return `${labels[e.action]||e.action} ${e.event==='program_started'?'started':'completed'}`;
 return e.event.replaceAll('_',' ');
}
function updateInspector(){
 const c=state.tissue.cells.find(c=>c.id===selected);$('cellSelect').value=c?.id||'';
 if(!c){$('cellName').textContent='Select a cell';$('cellIdentity').textContent='Click any cell, including a quiet one.';$('cellStatus').textContent='Steady state means no decision is requested.';$('reasons').innerHTML='<li>No cell selected.</li>';$('choice').textContent='No decision recorded.';$('program').innerHTML='';$('menu').innerHTML='';$('receipt').textContent='Select a cell to inspect its own view.';return;}
 $('cellName').textContent=name(c);$('cellIdentity').textContent=`${c.id} · ${state.states[c.state]||c.state} · ${c.decision_count||0} decisions${c.parent?' · parent '+c.parent+' · clone '+c.clone:''}`;
 $('cellStatus').textContent=c.state==='apoptotic'?'This cell underwent apoptosis after failed selection. It no longer makes decisions.':c.program?`Process in progress: ${labels[c.program.action]||c.program.action}. No new decision while busy.`:c.response.active?'A local change is present. Eligibility and the decision interval determine the next question.':'Steady state. No local activation cue; no decision requested.';
 $('reasons').innerHTML=c.response.reasons.map(r=>`<li>${escape(r.label)}${r.distance_um!==undefined?` · ${r.distance_um} μm`:''}${r.target?' · '+escape(r.target):''}</li>`).join('')||'<li>No departure from this cell’s local baseline.</li>';
 const d=c.last_decision;$('choice').textContent=d?`${labels[d.action]||d.action} · ${(d.time_min/60).toFixed(1)} h · ${d.source==='jev'?'Jev':'local policy'}. ${d.result}.`:'This cell has never been asked to decide.';
 if(c.program){const remaining=Math.max(0,c.program.due-state.tissue.time_min);$('program').innerHTML=`${remaining} biological min remaining${c.program.target?' · '+c.program.target:''}<div class="progress"><i style="width:${100*(1-remaining/Math.max(1,c.program.due-(c.program.started??c.program.due-180)))}%"></i></div>`;}else $('program').innerHTML='';
 $('menu').innerHTML=Object.keys(c.options).map(a=>`<span>${escape(labels[a]||a)}</span>`).join('');
 $('receipt').textContent=JSON.stringify({cell:c.id,state:c.state,local_activation:c.response,permitted_actions:c.options,last_decision:c.last_decision,program:c.program},null,2);
}
function point(x,y){return [width/2+(x-camera.x)*camera.scale,height/2+5-(y-camera.y)*camera.scale*.78];}
function circle(x,y,r,fill,stroke){ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);if(fill){ctx.fillStyle=fill;ctx.fill();}if(stroke){ctx.strokeStyle=stroke;ctx.stroke();}}
function text(label,x,y,color='#c8d7c1',size=10){ctx.fillStyle=color;ctx.font=`${size}px Segoe UI`;ctx.textAlign='center';ctx.fillText(label,x,y);}
function label(label,x,y){ctx.font='10px Segoe UI';const w=ctx.measureText(label).width+16;ctx.fillStyle='#133736e8';ctx.beginPath();ctx.roundRect(x-w/2,y-13,w,22,5);ctx.fill();text(label,x,y+1,'#f2eed4',10);}
function drawArt(c,x,y,size,clock){
 const key=['plasmablast','plasma'].includes(c.state)?'PLASMA':c.kind,img=c.state==='apoptotic'?null:images[key];
 if(!img){
  const r=size*.31;circle(x+1,y+3,r,'#15363233');
  if(c.kind==='FDC'||c.kind==='FRC'){ctx.strokeStyle=palette[c.kind]+'b0';ctx.lineWidth=2;for(let k=0;k<6;k++){ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+Math.cos(k*Math.PI/3)*r*1.6,y+Math.sin(k*Math.PI/3)*r*1.1);ctx.stroke();}}
  const g=ctx.createRadialGradient(x-r*.3,y-r*.4,0,x,y,r);g.addColorStop(0,'#ebdfcf');g.addColorStop(.4,c.state==='apoptotic'?'#968f9a':palette[c.kind]);g.addColorStop(1,'#63897c');circle(x,y,r,g);circle(x-r*.1,y,r*.46,'#695d8366');return;
 }
 const pose=poseAt(reduced.matches?0:clock,phaseFor(c.id));ctx.save();ctx.translate(x-size/2,y-size/2);
 ctx.globalAlpha=1-pose.blend;ctx.drawImage(img,...frameRect(img,pose.from,key),...framePlacement(img,pose.from,key,size));
 if(pose.blend){ctx.globalAlpha=pose.blend;ctx.drawImage(img,...frameRect(img,pose.to,key),...framePlacement(img,pose.to,key,size));}ctx.restore();
}
function draw(now){
 requestAnimationFrame(draw);if(!state)return;
 const dt=Math.min(60,now-lastFrame);lastFrame=now;
 if(replayRunning&&replay){
  const time=Math.min(replayEnd,replayTime+dt/1000*60*+$('speed').value),index=replay.indexAt(time);
  if(index!==replayIndex)showReplay(index);
  replayTime=time;
  if(time>=replayEnd){replayRunning=false;playUI();}
 }
 if(playing&&!pending&&now-lastStep>=interval)advance();
 const bounds=canvas.getBoundingClientRect(),ratio=Math.min(2,devicePixelRatio||1);
 if(width!==bounds.width||height!==bounds.height){width=bounds.width;height=bounds.height;canvas.width=Math.round(width*ratio);canvas.height=Math.round(height*ratio);ctx.setTransform(ratio,0,0,ratio,0,0);}
 const t=state.tissue,R=t.params.radius_um,responders=t.cells.filter(c=>c.response.active||c.program);
 const anchor=focused?(t.cells.find(c=>c.id===selected)||responders[0]):null;
 fitScale=Math.max(.01,Math.min((width-60)/(R*2.25),(height-80)/(R*1.9)));
 const desired={x:anchor?.x??cameraView.x,y:anchor?.y??cameraView.y,scale:fitScale*cameraView.zoom};
 const f=reduced.matches?1:1-Math.exp(-dt/180);for(const k of ['x','y','scale'])camera[k]=mix(camera[k],desired[k],f);
 $('scaleBar').style.width=(20*camera.scale)+'px';
 canvas.dataset.cameraX=camera.x.toFixed(3);canvas.dataset.cameraY=camera.y.toFixed(3);canvas.dataset.cameraZoom=(camera.scale/fitScale).toFixed(3);
 ctx.clearRect(0,0,width,height);ctx.fillStyle='#203f40';ctx.fillRect(0,0,width,height);
 const [cx,cy]=point(0,0),rx=R*camera.scale,ry=rx*.78;
 ctx.save();ctx.shadowColor='#0b292e99';ctx.shadowBlur=26;ctx.shadowOffsetY=20;
 ctx.fillStyle='#b87875';ctx.beginPath();ctx.ellipse(cx,cy+10,rx,ry,0,0,Math.PI*2);ctx.fill();ctx.restore();
 const tissue=ctx.createRadialGradient(cx-rx*.25,cy-ry*.3,20,cx,cy,rx);tissue.addColorStop(0,'#e6b7a6');tissue.addColorStop(.7,'#dca99d');tissue.addColorStop(1,'#c79791');
 ctx.fillStyle=tissue;ctx.strokeStyle='#e6c5b1';ctx.lineWidth=3;ctx.beginPath();ctx.ellipse(cx,cy,rx,ry,0,0,Math.PI*2);ctx.fill();ctx.stroke();
 ctx.save();ctx.clip();ctx.strokeStyle='#9b797231';ctx.lineWidth=.6;
 for(let k=0;k<34;k++){const a=k*2.399;ctx.beginPath();ctx.moveTo(cx+Math.cos(a)*rx,cy+Math.sin(a)*ry);ctx.quadraticCurveTo(cx+Math.cos(a+1)*rx*.25,cy+Math.sin(a-1)*ry*.35,cx+Math.cos(a+2)*rx,cy+Math.sin(a+2)*ry);ctx.stroke();}ctx.restore();
 if(t.gc){const [gx,gy]=point(...(t.gc_center||t.follicle));ctx.setLineDash([5,5]);ctx.lineWidth=1.5;ctx.strokeStyle='#f7f0ae';ctx.beginPath();ctx.ellipse(gx,gy,42*camera.scale,32*camera.scale,0,0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);label('Germinal center · formed',gx,gy-35*camera.scale);}
 if(!focused){text('AFFERENT LYMPH',cx-rx*.37,cy-ry-19,'#a6c5b1',9);text('B-CELL TERRITORY',cx-rx*.37,cy+ry*.5,'#815f62',8);text('T-CELL TERRITORY',cx+rx*.47,cy+ry*.45,'#815f62',8);}
 const tween=reduced.matches?1:clamp((now-receivedAt)/Math.min(600,interval));
 const display=new Map(t.cells.map(c=>{const old=previous.get(c.id)||c;return [c.id,{...c,x:mix(old.x,c.x,tween),y:mix(old.y,c.y,tween)}];}));
 for(const c of t.cells){if(c.program?.action!=='MOVE')continue;const trail=trails.get(c.id)||[];ctx.strokeStyle='#fcf4c87a';ctx.lineWidth=1.2;ctx.beginPath();trail.forEach((p,i)=>{const q=point(p.x,p.y);if(i)ctx.lineTo(...q);else ctx.moveTo(...q);});ctx.stroke();}
 for(const c of display.values()){
  if(!['PRIME','HELP'].includes(c.program?.action))continue;
  const partner=display.get(c.program.target);if(!partner)continue;
  ctx.strokeStyle=c.program.action==='HELP'?'#d9f5b0':'#ffebb0';ctx.lineWidth=4;ctx.beginPath();ctx.moveTo(...point(c.x,c.y));ctx.lineTo(...point(partner.x,partner.y));ctx.stroke();
 }
 points=[];
 for(const c of [...display.values()].sort((a,b)=>b.y-a.y)){
  const [x,y]=point(c.x,c.y),r=c.radius*camera.scale,size=r*(c.kind==='DC'?3.8:3.15);
  points.push({id:c.id,x,y,r:Math.max(8,size*.45)});
  if(showSignals&&c.response.active){ctx.strokeStyle='#ffda89';ctx.lineWidth=1.5;circle(x,y,r*1.7,null,'#ffda89');circle(x,y-r*1.7,2,'#ffda89');}
  if(c.id===selected){ctx.lineWidth=2;circle(x,y,r*2.1,null,'#f4f6d4');}
  drawArt(c,x,y,size,now/1000);
  const owned=t.antigens.filter(a=>a.owner===c.id&&!['degraded','surface_pmhc'].includes(a.pool));
  for(let k=0;k<owned.length;k++){const a=k*2.4;circle(x+Math.cos(a)*r*.7,y+Math.sin(a)*r*.5,Math.max(1.4,r*.16),'#ff7852','#ffdb86');}
  if(c.pmhc){ctx.fillStyle='#fded9c';for(let k=0;k<3;k++){const a=-2.6+k*.5;ctx.save();ctx.translate(x+Math.cos(a)*r*1.3,y+Math.sin(a)*r*1.3);ctx.rotate(a);ctx.fillRect(-2,-2,4,4);ctx.restore();}}
  if(c.program){const total=Math.max(1,c.program.due-(c.program.started??c.program.due-180));const p=1-clamp((c.program.due-t.time_min)/total);ctx.strokeStyle='#f4f5c6';ctx.lineWidth=2;ctx.beginPath();ctx.arc(x,y,r*1.9,-Math.PI/2,-Math.PI/2+p*Math.PI*2);ctx.stroke();}
  if(c.antibodies){for(let k=0;k<Math.min(8,c.antibodies);k++){const a=k*2.4+.2,spread=r*(2.5+(k%3)*.7);const px=x+Math.cos(a)*spread,py=y+Math.sin(a)*spread*.75;ctx.strokeStyle='#e6f7aa';ctx.lineWidth=1.5;ctx.beginPath();ctx.moveTo(px,py+3);ctx.lineTo(px,py-1);ctx.lineTo(px-3,py-4);ctx.moveTo(px,py-1);ctx.lineTo(px+3,py-4);ctx.stroke();}}
 }
 const entrant=t.cells.find(c=>c.arrival);
 if(entrant&&t.time_min-entrant.arrival.time_min<60){const [ex,ey]=point(entrant.x,entrant.y);label('Incoming DC · antigen inside',ex,ey-32);}
 const chosen=display.get(selected);if(chosen){const [x,y]=point(chosen.x,chosen.y);label(`${chosen.id} · ${name(chosen)}`,Math.min(width-90,Math.max(90,x)),Math.min(height-45,y+chosen.radius*camera.scale*3.5));}
 $('tissue').dataset.renderedCells=points.length;
}
function cameraUI(){
 $('zoom').value=String(cameraView.zoom);$('zoomValue').textContent=cameraView.zoom.toFixed(1)+'×';
 $('zoomOut').disabled=cameraView.zoom<=1;$('zoomIn').disabled=cameraView.zoom>=6;
 $('view').textContent=focused?'Whole tissue':'Focus response';$('view').setAttribute('aria-pressed',String(focused));
}
function resetCamera(){focused=false;cameraView={x:0,y:0,zoom:1};cameraUI();}
function focusResponse(){focused=true;cameraView={x:0,y:0,zoom:1.85};cameraUI();}
function detachCamera(){
 if(focused){cameraView.x=camera.x;cameraView.y=camera.y;focused=false;}
}
function boundCamera(){
 const r=state?.tissue.params.radius_um||1;
 cameraView.x=Math.max(-r,Math.min(r,cameraView.x));cameraView.y=Math.max(-r,Math.min(r,cameraView.y));
}
function panCamera(dx,dy,immediate=false){
 if(!state)return;detachCamera();
 const scale=immediate?camera.scale:fitScale*cameraView.zoom;
 cameraView.x+=dx/scale;cameraView.y-=dy/(scale*.78);boundCamera();
 if(immediate){camera.x=cameraView.x;camera.y=cameraView.y;}
 cameraUI();
}
function zoomCamera(value,at=null){
 if(!state)return;const zoom=Math.max(1,Math.min(6,value));
 if(at){
  // Keep the world location under the pointer fixed while changing magnification.
  const x=(at.x-width/2),y=(at.y-height/2-5),scale=fitScale*zoom;
  focused=false;cameraView.x=camera.x+x/camera.scale-x/scale;cameraView.y=camera.y-y/(camera.scale*.78)+y/(scale*.78);
  boundCamera();camera={x:cameraView.x,y:cameraView.y,scale};
 }
 cameraView.zoom=zoom;cameraUI();
}
$('zoom').oninput=()=>zoomCamera(+$('zoom').value);
$('zoomIn').onclick=()=>zoomCamera(cameraView.zoom*1.25);
$('zoomOut').onclick=()=>zoomCamera(cameraView.zoom/1.25);
$('resetView').onclick=resetCamera;
for(const [id,dx,dy] of [['panLeft',-90,0],['panRight',90,0],['panUp',0,-90],['panDown',0,90]])$(id).onclick=()=>panCamera(dx,dy);
canvas.addEventListener('wheel',event=>{
 if(!state)return;event.preventDefault();const rect=canvas.getBoundingClientRect();
 const delta=event.deltaY*(event.deltaMode===1?16:event.deltaMode===2?height:1);
 zoomCamera(cameraView.zoom*Math.exp(-Math.max(-500,Math.min(500,delta))*.002),{x:event.clientX-rect.left,y:event.clientY-rect.top});
},{passive:false});
function gesture(){
 const [a,b]=[...pointers.values()];if(!a)return null;
 return b?{x:(a.x+b.x)/2,y:(a.y+b.y)/2,distance:Math.hypot(a.x-b.x,a.y-b.y)}:{...a,distance:0};
}
canvas.onpointerdown=event=>{
 if(!state||event.button!==0)return;
 if(!pointers.size){suppressPick=false;canvas.focus({preventScroll:true});}
 pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});drag=gesture();
 if(pointers.size>1)suppressPick=true;
 canvas.setPointerCapture(event.pointerId);canvas.classList.add('dragging');
};
canvas.onpointermove=event=>{
 if(!pointers.has(event.pointerId))return;
 pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});const next=gesture();
 if(!suppressPick&&Math.hypot(next.x-drag.x,next.y-drag.y)<4)return;
 suppressPick=true;
 // Start a drag from the camera actually on screen, even during a focus transition.
 cameraView={x:camera.x,y:camera.y,zoom:camera.scale/fitScale};focused=false;
 panCamera(drag.x-next.x,drag.y-next.y,true);
 if(next.distance&&drag.distance){const rect=canvas.getBoundingClientRect();zoomCamera(cameraView.zoom*next.distance/drag.distance,{x:next.x-rect.left,y:next.y-rect.top});}
 drag=next;
};
function endPointer(event){pointers.delete(event.pointerId);drag=gesture();if(!pointers.size)canvas.classList.remove('dragging');}
canvas.onpointerup=endPointer;canvas.onpointercancel=endPointer;canvas.onlostpointercapture=endPointer;
canvas.onclick=event=>{if(suppressPick)return;const rect=canvas.getBoundingClientRect(),x=event.clientX-rect.left,y=event.clientY-rect.top;const hit=points.filter(p=>Math.hypot(x-p.x,y-p.y)<p.r).sort((a,b)=>Math.hypot(x-a.x,y-a.y)-Math.hypot(x-b.x,y-b.y))[0];if(hit){selected=hit.id;updateInspector();}};
canvas.onkeydown=event=>{
 if(!state)return;
 if(event.shiftKey&&['ArrowRight','ArrowLeft'].includes(event.key)){
  event.preventDefault();const cells=state.tissue.cells,i=cells.findIndex(c=>c.id===selected);selected=cells[(i+(event.key==='ArrowRight'?1:cells.length-1))%cells.length].id;updateInspector();return;
 }
 const direction={ArrowLeft:[-90,0],ArrowRight:[90,0],ArrowUp:[0,-90],ArrowDown:[0,90]}[event.key];
 if(direction){event.preventDefault();panCamera(...direction);}
 else if(['+','=','-','_','Home'].includes(event.key)){event.preventDefault();if(event.key==='Home')resetCamera();else zoomCamera(cameraView.zoom*(['+','='].includes(event.key)?1.25:.8));}
};
cameraUI();
try{
 const assets=await Promise.all(['B','CD4','DC','PLASMA'].map(async key=>{const image=new Image();image.src=key==='PLASMA'?new URL('./assets/cells/PlasmaBcells_green.png',import.meta.url).href:atlasURL(key);await image.decode();return [key,image];}));images=Object.fromEntries(assets);
 if(document.body.dataset.mode==='replay'){
  const response=await fetch(new URL('./recording.json',location.href));if(!response.ok)throw Error('Recording manifest unavailable.');
  const manifest=await response.json();if(!/^[-a-z0-9]+\.ln\.json\.gz$/.test(manifest.file))throw Error('Invalid recording filename.');
  await openReplay(new URL('./recordings/'+manifest.file,location.href).href,manifest.sha256);
 }else{
  updateState(await api('state'));
  if(state.run_control?.playback_available)await openReplay('/api/export');
 }
 $('loading').hidden=true;$('loading').style.display='none';
 requestAnimationFrame(draw);
 if(!replay&&state.run_control?.managed){
  let polling=false;
  const observer=setInterval(async()=>{
   if(polling)return;polling=true;
   try{updateState(await api('state'));if(!['prepared','running'].includes(state.run_control.status)){clearInterval(observer);if(state.run_control.playback_available)await openReplay('/api/export');}}
   catch(error){message('Viewer connection: '+error.message);}
   finally{polling=false;}
  },800);
 }
}catch(error){$('loading').textContent='The tissue could not load. '+error.message;message(error.message);}
