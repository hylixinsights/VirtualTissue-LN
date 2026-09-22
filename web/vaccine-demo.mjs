import {atlasURL, frameRect, framePlacement, phaseFor, poseAt} from './cell-atlas.mjs';

const $=selector=>document.querySelector(selector), canvas=$('#vaccineScene'), ctx=canvas.getContext('2d');
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
const duration=76, lengths=[8,6,8,9,8,8,13,16];
const starts=lengths.map((_,i)=>lengths.slice(0,i).reduce((a,b)=>a+b,0));
const smooth=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
const mix=(a,b,t)=>a+(b-a)*t;
let story, images={}, elapsed=0, playing=false, last=performance.now(), selected=null, follow=true;
let width=0,height=0, camera, frame, modelTime=0, currentStage=0;
const labels={dc:'Dendritic cell',helper:'CD4 T cell',b:'B cell'};
const cellColor={DC:'#c9baff',CD4:'#f7cf64',B:'#ddac7d',MAC:'#ce94b0',FDC:'#ab92c7',FRC:'#7aaba4',LEC:'#81adb8'};
const stateLabel={resting:'Resting',naive:'Naive',presenting:'Presenting antigen',activated:'Activated',pre_tfh:'Tfh precursor',tfh:'T follicular helper',plasmablast:'Plasmablast'};

function timeline(seconds){
 const index=Math.min(7,Math.max(0,starts.findLastIndex(t=>seconds>=t)));
 const progress=Math.min(1,(seconds-starts[index])/lengths[index]);
 const beat=story.beats[index];
 return {index,progress,time:index===0?0:mix(beat.time,beat.end,progress)};
}
function playbackAt(time){
 const i=story.beats.findIndex((b,i)=>i>0&&time>=b.time&&time<=b.end);
 return i<0?duration:starts[i]+(time-story.beats[i].time)/(story.beats[i].end-story.beats[i].time)*lengths[i];
}
function cellName(c){return c.state==='plasmablast'?'Plasmablast':c.state==='tfh'?'Tfh cell':c.kind==='DC'?'Dendritic cell':c.kind==='CD4'?'CD4 T cell':story.registry[c.kind].label;}
function playUI(){
 $('#playStory').textContent=playing?'Ⅱ Pause response':elapsed>=duration?'↺ Replay response':'▶ Play response';
 $('#playState').textContent=playing?'Response in progress':elapsed>=duration?'Response complete':'Paused · explore any stage';
 $('#playStory').setAttribute('aria-pressed',String(playing));
}
function chooseTime(seconds, pause=true){elapsed=Math.max(0,Math.min(duration,seconds));if(pause)playing=false;update();playUI();}
$('#playStory').onclick=()=>{if(elapsed>=duration)elapsed=0;playing=!playing;last=performance.now();playUI();};
$('#restart').onclick=()=>{selected=null;elapsed=0;playing=true;last=performance.now();update();playUI();};
$('#storySeek').oninput=e=>chooseTime(+e.target.value);
$('#focus').onclick=()=>{follow=true;$('#focus').setAttribute('aria-pressed','true');$('#overview').setAttribute('aria-pressed','false');};
$('#overview').onclick=()=>{follow=false;$('#focus').setAttribute('aria-pressed','false');$('#overview').setAttribute('aria-pressed','true');};
reduced.addEventListener('change',e=>{if(e.matches){playing=false;playUI();}});
function update(){
 if(!story)return;
 const point=timeline(elapsed);currentStage=point.index;modelTime=point.time;
 frame=currentStage===0&&elapsed<1?story.baseline:story.frames[Math.min(story.frames.length-1,Math.floor((modelTime+1e-7)/30))];
 const beat=story.beats[currentStage],cell=frame.cells.find(c=>c.id===beat.cell);
 $('#stageNumber').textContent=`${String(currentStage+1).padStart(2,'0')} / 08`;
 $('#stageTitle').textContent=beat.title;$('#stageDescription').textContent=beat.description;
 $('#decisionAction').textContent=beat.action;$('#decisionCell').textContent=`${cellName(cell)} · ${cell.id}`;
 $('#stageProgress').style.width=`${point.progress*100}%`;
 $('#decisionDetail').textContent=currentStage===0?'Controlled local perturbation · two finite antigen packets':currentStage===7?'Recorded IgM secretion · same B-cell clone':'Chosen by the scripted policy · enforced by the LN kernel';
 $('#clock').textContent=(modelTime/60).toFixed(1)+' h';
 $('#elapsed').textContent=`${Math.floor(elapsed/60)}:${String(Math.floor(elapsed%60)).padStart(2,'0')} / 1:16`;
 $('#storySeek').value=elapsed;
 $('#antibodyCount').textContent=frame.metrics.antibodies;
 $('#chapters').querySelectorAll('button').forEach((b,i)=>b.setAttribute('aria-current',String(i===currentStage)));
 for(const [role,id] of Object.entries(story.cast)){
  const c=frame.cells.find(c=>c.id===id),button=$(`[data-actor="${role}"]`);
  button.setAttribute('aria-pressed',String((selected||beat.cell)===id));
  button.querySelector('b').textContent=cellName(c);
  const status=c.kind==='DC'&&c.state==='presenting'&&!c.pmhc?'Presentation ended':stateLabel[c.state]||c.state;
  button.querySelector('small').textContent=`${c.id} · ${status}`;
  button.querySelector('.actor-art').style.backgroundImage=`url("${c.state==='plasmablast'?images.PLASMA.src:images[c.kind].src}")`;
 }
 canvas.dataset.stage=beat.id;canvas.dataset.modelTime=modelTime.toFixed(3);
 canvas.setAttribute('aria-label',`100-cell LN tissue. ${beat.title}. ${frame.metrics.antibodies} IgM secretion units. Scripted decisions; no AI calls.`);
}
function point(x,y){return [width/2+(x-camera.x)*camera.scale,height/2-(y-camera.y)*camera.scale];}
function circle(x,y,r,fill,stroke){ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);if(fill){ctx.fillStyle=fill;ctx.fill();}if(stroke){ctx.strokeStyle=stroke;ctx.stroke();}}
function badge(text,x,y,color='#d3e5da',font=11){
 ctx.font=`${font}px "Segoe UI",sans-serif`;const w=ctx.measureText(text).width+16;
 x=Math.max(w/2+8,Math.min(width-w/2-8,x));
 ctx.fillStyle='#10262ded';ctx.strokeStyle='#47655b';ctx.lineWidth=1;
 ctx.beginPath();ctx.roundRect(x-w/2,y-11,w,23,5);ctx.fill();ctx.stroke();
 ctx.fillStyle=color;ctx.textAlign='center';ctx.fillText(text,x,y+4);
}
function art(c,x,y,size,opacity=1,key=c.kind){
 const image=images[key];if(!image)return;
 const pose=poseAt(elapsed,phaseFor(c.id));
 ctx.save();ctx.translate(x-size/2,y-size/2);ctx.globalAlpha=opacity*(1-pose.blend);
 ctx.drawImage(image,...frameRect(image,pose.from,key),...framePlacement(image,pose.from,key,size));
 if(pose.blend){ctx.globalAlpha=opacity*pose.blend;ctx.drawImage(image,...frameRect(image,pose.to,key),...framePlacement(image,pose.to,key,size));}
 ctx.restore();
}
function drawCell(c,featured){
 const [x,y]=point(c.x,c.y),r=c.radius*camera.scale,size=r*2.65;
 if(x<-size||x>width+size||y<-size||y>height+size)return;
 const isSelected=(selected||story.beats[currentStage].cell)===c.id;
 ctx.save();
 if(featured){
  const gradient=ctx.createRadialGradient(x,y,r*.4,x,y,r*2.1);
  gradient.addColorStop(0,(c.state==='plasmablast'?'#bdd983':cellColor[c.kind])+'35');gradient.addColorStop(1,'#17313200');
  circle(x,y,r*2.1,gradient);
  if(isSelected){ctx.lineWidth=1.4;circle(x,y,r*1.48,null,'#bfe5cc');}
 }
 const alpha=featured?1:(follow?.12:.7);
 if(images[c.kind]){
  const transformation=c.state==='plasmablast'?smooth((modelTime-510)/25):0;
  if(transformation<1)art(c,x,y,size,alpha*(1-transformation));
  if(transformation>0)art(c,x,y,size,alpha*transformation,'PLASMA');
 }else{
  ctx.globalAlpha=alpha;circle(x,y,r,cellColor[c.kind]+'aa',cellColor[c.kind]);circle(x-r*.15,y,r*.5,cellColor[c.kind]+'77');
  if(['FDC','FRC','MAC'].includes(c.kind)){
   ctx.strokeStyle=cellColor[c.kind];ctx.lineWidth=1;
   for(let i=0;i<6;i++){const a=i*Math.PI/3;ctx.beginPath();ctx.moveTo(x+Math.cos(a)*r*.8,y+Math.sin(a)*r*.8);ctx.lineTo(x+Math.cos(a)*r*1.5,y+Math.sin(a)*r*1.5);ctx.stroke();}
  }
 }
 ctx.restore();
 if(!featured)return;
 if(c.pmhc){
  ctx.save();ctx.translate(x,y);
  for(let i=0;i<7;i++){
   const a=i*Math.PI*2/7+elapsed*.035;ctx.save();ctx.rotate(a);ctx.translate(0,-r*1.08);
   ctx.strokeStyle='#92edd9';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(-3,2);ctx.lineTo(-3,-5);ctx.lineTo(3,-5);ctx.lineTo(3,2);ctx.stroke();
   ctx.fillStyle='#ffc16c';ctx.fillRect(-2,-6,4,2);ctx.restore();
  }
  ctx.restore();
 }
 const antigen=frame.antigen_ledger.find(a=>a.owner===c.id&&['native_cargo','internalized','processed_peptide'].includes(a.pool));
 if(antigen){
  const processed=antigen.pool==='processed_peptide', color=processed?'#95f0dc':'#ffd28a';
  const count=antigen.pool==='native_cargo'?1:3;
  for(let j=0;j<count;j++){const angle=elapsed*.7+j*2.1,dx=Math.cos(angle)*r*.42,dy=Math.sin(angle)*r*.3;
   ctx.save();ctx.shadowColor=color;ctx.shadowBlur=14;circle(x+dx,y+dy,processed?2.5:4,color);ctx.restore();}
 }
 if(c.program&&['HELPER','PLASMA','PROCESS','LOAD'].includes(c.program.action)){
  const started=story.episode.events.findLast(e=>e.cell===c.id&&e.event==='program_started'&&e.action===c.program.action&&e.time_min<=modelTime);
  if(started){const p=Math.min(1,(modelTime-started.time_min)/(c.program.due-started.time_min));ctx.strokeStyle=c.program.action==='PLASMA'?'#c2db89':'#a7d7c1';ctx.lineWidth=3;ctx.beginPath();ctx.arc(x,y,r*1.35,-Math.PI/2,-Math.PI/2+Math.PI*2*p);ctx.stroke();}
 }
 const text=cellName(c), font=width<450?10:12;
 const labelY=c.kind==='B'?y+r*1.65+10:y-r*1.8-7;
 badge(text,x,labelY,c.state==='plasmablast'?'#d1e8a6':cellColor[c.kind],font);
 if(follow&&width>440){ctx.font='9px "Segoe UI",sans-serif';ctx.fillStyle='#aac5bf';ctx.textAlign='center';ctx.fillText(c.id,x,labelY+24);}
}
function drawAntigens(){
 const left=story.frames[Math.floor(modelTime/30)]||story.frames.at(-1),right=story.frames[Math.min(story.frames.length-1,Math.floor(modelTime/30)+1)];
 const transition=smooth((modelTime%30)/30);
 if(currentStage===0&&elapsed<1)return;
 for(const a of left.antigen_ledger){
  const b=right.antigen_ledger.find(b=>b.id===a.id);if(a.pool!=='free_native')continue;
  let x=mix(a.x,b.x,transition),y=mix(a.y,b.y,transition);
  if(currentStage===0){
   const p=smooth((elapsed-1)/6),entry={x:a.x-10,y:a.y+15};
   x=mix(entry.x,a.x,p);y=mix(entry.y,a.y,p);
  }
  const [sx,sy]=point(x,y),r=Math.max(4,Math.min(7,camera.scale*.7));
  ctx.save();ctx.shadowColor='#fbc071';ctx.shadowBlur=22;circle(sx,sy,r,'#ffcf7f');ctx.restore();
  ctx.strokeStyle='#ffc16c70';ctx.lineWidth=1;circle(sx,sy,r*2.1,null,'#ffc16c70');
  if(currentStage<2&&follow)badge('Vaccine antigen',sx,sy-23,'#ffd095',width<450?9:10);
 }
}
function drawContacts(){
 for(const event of story.episode.events){
  if(event.event!=='program_started'||!['PRIME','HELP'].includes(event.action)||event.time_min>modelTime||event.due<=modelTime)continue;
  const a=frame.cells.find(c=>c.id===event.cell),b=frame.cells.find(c=>c.id===event.target);
  if(!a||!b||Math.hypot(a.x-b.x,a.y-b.y)>frame.params.contact_um)return;
  const [ax,ay]=point(a.x,a.y),[bx,by]=point(b.x,b.y),dx=bx-ax,dy=by-ay,len=Math.hypot(dx,dy),ar=a.radius*camera.scale,br=b.radius*camera.scale;
  const start=[ax+dx/len*ar,ay+dy/len*ar],end=[bx-dx/len*br,by-dy/len*br];
  ctx.save();ctx.strokeStyle='#a7edcd';ctx.lineWidth=4;ctx.shadowColor='#8cdcb7';ctx.shadowBlur=15;ctx.beginPath();ctx.moveTo(...start);ctx.lineTo(...end);ctx.stroke();ctx.restore();
  for(let i=0;i<4;i++){const p=(elapsed*.45+i/4)%1;circle(mix(start[0],end[0],p),mix(start[1],end[1],p),3,'#e3ffe2');}
  if(follow)badge(event.action==='PRIME'?'Peptide–MHC II ↔ TCR':'Cognate B–T help',(ax+bx)/2,(ay+by)/2+(event.action==='PRIME'?31:-34),'#a5ead1',width<450?9:10);
 }
}
function igm(x,y,size,angle,alpha){
 ctx.save();ctx.translate(x,y);ctx.rotate(angle);ctx.globalAlpha=alpha;ctx.strokeStyle='#b4dfff';ctx.lineWidth=Math.max(1.2,size*.13);ctx.lineCap='round';
 for(let i=0;i<5;i++){ctx.save();ctx.rotate(i*Math.PI*2/5);ctx.beginPath();ctx.moveTo(0,-size*.18);ctx.lineTo(0,-size*.7);ctx.lineTo(-size*.28,-size);ctx.moveTo(0,-size*.7);ctx.lineTo(size*.28,-size);ctx.stroke();ctx.restore();}
 ctx.restore();
}
function drawAntibodies(){
 const b=frame.cells.find(c=>c.id===story.cast.b),[x,y]=point(b.x,b.y);
 const events=story.episode.events.filter(e=>e.event==='antibody_secreted'&&e.time_min+30<=modelTime+1e-7);
 for(let j=0;j<events.length;j++)for(let i=0;i<5;i++){
  const age=elapsed-playbackAt(events[j].time_min+30),a=-.1+i*.6+j*.13;
  const d=(b.radius+1+age*1.4)*camera.scale;
  igm(x+Math.cos(a)*d,y+Math.sin(a)*d,Math.max(5,Math.min(11,camera.scale*.8)),a+age*.1,Math.max(.15,1-age*.055));
 }
 if(events.length&&follow)badge('IgM release',x+7*camera.scale,y-9*camera.scale,'#bfdefb',11);
}
function draw(){
 if(!story)return;
 const rect=canvas.getBoundingClientRect(),dpr=Math.min(devicePixelRatio,2);
 width=rect.width;height=rect.height;
 if(canvas.width!==Math.round(width*dpr)||canvas.height!==Math.round(height*dpr)){canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);}
 ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,width,height);
 const zoom=follow?smooth(elapsed/4):0;
 camera={x:mix(0,10,zoom),y:mix(0,44,zoom),scale:mix(Math.min(width,height)/190,Math.min(width/57,height/48),zoom)};
 const [ox,oy]=point(0,0),radius=frame.params.radius_um*camera.scale;
 circle(ox,oy,radius,'#28514a17','#87bb9c60');ctx.lineWidth=1;circle(ox,oy,radius*.94,null,'#688f7326');
 // Faint local scaffold; every visible cell uses its recorded tissue position.
 for(const c of frame.cells.filter(c=>['FDC','FRC'].includes(c.kind))){
  for(const n of frame.cells.filter(n=>n.id!==c.id&&Math.hypot(n.x-c.x,n.y-c.y)<19)){
   ctx.strokeStyle=follow?'#749f9512':'#749f9524';ctx.lineWidth=.6;ctx.beginPath();ctx.moveTo(...point(c.x,c.y));ctx.lineTo(...point(n.x,n.y));ctx.stroke();
  }
 }
 const cast=new Set(Object.values(story.cast));
 for(const c of frame.cells)if(!cast.has(c.id))drawCell(c,false);
 for(const c of frame.cells)if(cast.has(c.id))drawCell(c,true);
 drawAntigens();drawContacts();drawAntibodies();
 // A small whole-patch locator preserves spatial context during the close-up.
 if(follow&&width>490){
  const mx=width-51,my=51,scale=32/frame.params.radius_um;
  circle(mx,my,37,'#10242ecc','#699a8580');
  for(const c of frame.cells)circle(mx+c.x*scale,my-c.y*scale,cast.has(c.id)?2:1,cast.has(c.id)?cellColor[c.kind]:'#62837b70');
  ctx.strokeStyle='#a8d6bd';ctx.strokeRect(mx+(camera.x-14)*scale,my-(camera.y+12)*scale,28*scale,24*scale);
 }
}
canvas.addEventListener('click',e=>{
 if(!story||!camera)return;const r=canvas.getBoundingClientRect(),x=(e.clientX-r.left-width/2)/camera.scale+camera.x,y=-(e.clientY-r.top-height/2)/camera.scale+camera.y;
 const c=frame.cells.find(c=>Object.values(story.cast).includes(c.id)&&Math.hypot(x-c.x,y-c.y)<=c.radius*1.4);
 if(c){selected=c.id;update();}
});
function tick(now){
 const dt=Math.min(.1,(now-last)/1000);last=now;
 if(playing&&!document.hidden){elapsed=Math.min(duration,elapsed+dt*+$('#speed').value);if(elapsed===duration){playing=false;playUI();}update();}
 draw();requestAnimationFrame(tick);
}
try{
 const response=await fetch(new URL('./vaccine-story.json',import.meta.url));
 if(!response.ok)throw Error('The scripted recording could not be loaded.');story=await response.json();
 if(story.format!=='lymph-node-vaccine-story-v1'||story.provider!=='scripted'||story.paid_requests!==0)throw Error('This page requires a scripted, API-free recording.');
 await Promise.all(['B','CD4','DC','PLASMA'].map(async key=>{const image=new Image();image.src=key==='PLASMA'?new URL('./assets/cells/PlasmaBcells_green.png',import.meta.url):atlasURL(key);await image.decode();images[key]=image;}));
 $('#chapters').innerHTML=story.beats.map((b,i)=>`<button data-stage="${b.id}" aria-current="${i===0}"><span>${String(i+1).padStart(2,'0')}</span>${b.short}</button>`).join('');
 $('#chapters').querySelectorAll('button').forEach((b,i)=>b.onclick=()=>{selected=null;chooseTime(starts[i]+(i===0?2:.4));});
 $('#actors').innerHTML=Object.entries(story.cast).map(([role,id])=>`<button class="actor" data-actor="${role}" aria-pressed="false"><span class="actor-art" aria-hidden="true"></span><span><b>${labels[role]}</b><small>${id}</small></span></button>`).join('');
 $('#actors').querySelectorAll('button').forEach(b=>b.onclick=()=>{selected=story.cast[b.dataset.actor];update();});
 for(const id of ['playStory','restart','storySeek'])$('#'+id).disabled=false;
 $('#sceneLoading').hidden=true;playing=!reduced.matches;update();playUI();last=performance.now();requestAnimationFrame(tick);
}catch(error){$('#sceneLoading').textContent=error.message;$('#playState').textContent='Playback unavailable';}
