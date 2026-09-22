import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {CellArt} from './cell-art.mjs';
import {atlasURL, artKind} from './cell-atlas.mjs';
const $=s=>document.querySelector(s), esc=s=>String(s??'—').replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
let data, token, tissue, running=false, busy=false, selected=null, filter=null, recording=null, history=[], showZones=true;
const notice=(s,error=false)=>{$('#notice').textContent=s;$('#notice').classList.toggle('error',error);};
async function api(path,body){const res=await fetch(path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json','X-LN-Token':token}:{},body:body?JSON.stringify(body):undefined});const value=await res.json();if(!res.ok)throw new Error(value.error||'Request failed');return value;}
const canvas=$('#scene'),renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setClearColor(0x101b20,0);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;
const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(39,1,.5,2000);camera.position.set(25,345,340);
const controls=new OrbitControls(camera,canvas);controls.enableDamping=true;controls.dampingFactor=.09;controls.minDistance=220;controls.maxDistance=760;controls.maxPolarAngle=Math.PI*.495;controls.target.set(0,0,0);controls.enablePan=false;
scene.add(new THREE.HemisphereLight(0xd7f9ff,0x22334b,2.1));const light=new THREE.DirectionalLight(0xffecd5,3);light.position.set(-120,230,120);scene.add(light);const fill=new THREE.DirectionalLight(0x9dbeff,1.1);fill.position.set(150,110,-90);scene.add(fill);
const root=new THREE.Group();scene.add(root);const cellLayer=new THREE.Group();root.add(cellLayer);let cells=[],bodies,nuclei,branches,antigenMesh;const temp=new THREE.Object3D();const color=new THREE.Color();
const cellArt=new CellArt(cellLayer), reducedMotion=matchMedia('(prefers-reduced-motion: reduce)');
let artMotion=!reducedMotion.matches, artTime=0, lastArtTick=performance.now();
function motionUI(){$('#artMotion').textContent=artMotion?'Pause illustration':'Animate illustration';$('#artMotion').setAttribute('aria-pressed',String(artMotion));}
motionUI();
reducedMotion.addEventListener('change',e=>{artMotion=!e.matches;motionUI();});
const base=new THREE.Mesh(new THREE.CylinderGeometry(150,150,2.1,128),new THREE.MeshStandardMaterial({color:0x263c40,roughness:.85,transparent:true,opacity:.65}));base.position.y=-5.2;root.add(base);
const ring=new THREE.Mesh(new THREE.TorusGeometry(151,1.5,10,180),new THREE.MeshStandardMaterial({color:0x8bb3a7,roughness:.45,transparent:true,opacity:.75}));ring.rotation.x=Math.PI/2;ring.position.y=-1;root.add(ring);
const inner=new THREE.Mesh(new THREE.TorusGeometry(140,.42,6,160),new THREE.MeshBasicMaterial({color:0x799e91,transparent:true,opacity:.2}));inner.rotation.x=Math.PI/2;inner.position.y=-2;root.add(inner);
const zones=new THREE.Group();root.add(zones);
function region(x,y,rx,ry,col,opacity){const m=new THREE.Mesh(new THREE.CircleGeometry(1,96),new THREE.MeshBasicMaterial({color:col,transparent:true,opacity,depthWrite:false,side:THREE.DoubleSide}));m.rotation.x=-Math.PI/2;m.position.set(x,-3.95,-y);m.scale.set(rx,ry,1);zones.add(m);return m;}
region(-48,25,75,77,0x7b71c5,.13);region(49,0,70,94,0x4f998a,.09);region(3,-97,80,31,0x647d97,.12);
const darkZone=region(-65,9,32,38,0x8571e6,.23),lightZone=region(-32,43,32,34,0xc093d0,.2);darkZone.visible=lightZone.visible=false;
function pathTube(points,col,r=1){const curve=new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p)));const m=new THREE.Mesh(new THREE.TubeGeometry(curve,32,r,8,false),new THREE.MeshStandardMaterial({color:col,transparent:true,opacity:.5}));root.add(m);}
pathTube([[-98,-3,-153],[-83,-3,-137],[-64,-3,-125]],0x76bdb0,2.3);pathTube([[-80,-3,-164],[-69,-3,-143],[-54,-3,-132]],0x76bdb0,2.3);
pathTube([[30,-3,143],[34,-3,162],[38,-3,175]],0x7197ab,2.5);
const selectionRing=new THREE.Mesh(new THREE.TorusGeometry(6.3,.35,6,40),new THREE.MeshBasicMaterial({color:0xf3f4d9}));selectionRing.rotation.x=Math.PI/2;selectionRing.visible=false;cellLayer.add(selectionRing);
const selectedContact=new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(),new THREE.Vector3()]),new THREE.LineDashedMaterial({color:0x9dd7c1,dashSize:1,gapSize:.7,transparent:true,opacity:.9}));selectedContact.visible=false;cellLayer.add(selectedContact);
const antigenMaterial=new THREE.MeshBasicMaterial({color:0xf4ca6b});
const sphere=new THREE.SphereGeometry(1,20,14),bodyMat=new THREE.MeshStandardMaterial({roughness:.46,metalness:.03});
const nucMat=new THREE.MeshStandardMaterial({roughness:.65,metalness:0});
function clearMesh(mesh){if(mesh){cellLayer.remove(mesh);mesh.dispose?.();}return null;}
function updateScene(){
 cellLayer.scale.setScalar(150/(tissue.params?.radius_um||150));
 cells=tissue.cells.filter(c=>!['divided','cleared'].includes(c.state));
 cellArt.update(cells,filter);
 if(!bodies||bodies.count!==cells.length){clearMesh(bodies);clearMesh(nuclei);bodies=new THREE.InstancedMesh(sphere,bodyMat,cells.length);nuclei=new THREE.InstancedMesh(sphere,nucMat,cells.length);cellLayer.add(bodies,nuclei);bodies.frustumCulled=false;nuclei.frustumCulled=false;}
 const branchPositions=[],branchColors=[];
 cells.forEach((c,i)=>{
  const col=data.registry[c.kind].color;let radius=c.radius||4.2;let scaleY=c.kind==='FRC'||c.kind==='LEC'?.55:c.kind==='MAC'?1.12:.94;
  const illustrated=cellArt.has(c);
  temp.position.set(c.x,0,-c.y);temp.rotation.set(0,0,0);temp.scale.set(radius, radius*scaleY,radius*(c.kind==='DC'?1.18:1));if(illustrated)temp.scale.setScalar(0);temp.updateMatrix();bodies.setMatrixAt(i,temp.matrix);
  color.set(c.state==='apoptotic'?'#4e5559':c.state==='plasma'||c.state==='plasmablast'?'#f7be69':c.state==='memory'?'#f7d9ac':['dz','lz','selected','founder'].includes(c.state)?'#b49bf8':col);
  if(filter&&c.kind!==filter)color.multiplyScalar(.18);bodies.setColorAt(i,color);
  temp.position.set(c.x-.5,radius*scaleY*.58,-c.y+.45);temp.scale.set(radius*.58,radius*scaleY*.5,radius*.54);if(illustrated)temp.scale.setScalar(0);temp.updateMatrix();nuclei.setMatrixAt(i,temp.matrix);nuclei.setColorAt(i,color.clone().multiplyScalar(.57));
  if(!illustrated&&['FDC','FRC','DC','MAC'].includes(c.kind))for(let k=0;k<(c.kind==='FDC'?7:4);k++){
   const a=k*Math.PI*2/(c.kind==='FDC'?7:4)+i*.32,l=c.kind==='FDC'?9:c.kind==='FRC'?8:6.3;
   branchPositions.push(c.x,0,-c.y,c.x+Math.cos(a)*l,-.6,-c.y+Math.sin(a)*l);branchColors.push(color.r,color.g,color.b,color.r,color.g,color.b);
  }
 });bodies.instanceMatrix.needsUpdate=true;bodies.instanceColor.needsUpdate=true;bodies.computeBoundingSphere();nuclei.instanceMatrix.needsUpdate=true;nuclei.instanceColor.needsUpdate=true;
 if(branches){cellLayer.remove(branches);branches.geometry.dispose();branches.material.dispose();}
 const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(branchPositions,3));geo.setAttribute('color',new THREE.Float32BufferAttribute(branchColors,3));branches=new THREE.LineSegments(geo,new THREE.LineBasicMaterial({vertexColors:true,transparent:true,opacity:.7}));cellLayer.add(branches);
 const ag=tissue.antigens||[];clearMesh(antigenMesh);if(ag.length){antigenMesh=new THREE.InstancedMesh(sphere,antigenMaterial,ag.length);ag.forEach((a,i)=>{temp.position.set(a.x,5.5,-a.y);temp.scale.setScalar(a.pool==='fdc_retained'?.9:.68);temp.updateMatrix();antigenMesh.setMatrixAt(i,temp.matrix);});cellLayer.add(antigenMesh);}
 darkZone.visible=lightZone.visible=tissue.gc;$('#stageTitle').textContent=tissue.gc?'The germinal-center response':'The primary follicle';
 const c=cells.find(c=>c.id===selected);selectionRing.visible=!!c;if(c)selectionRing.position.set(c.x,4.5,-c.y);
 selectedContact.visible=false;
 const program=c?.program, partner=program?.target?cells.find(cell=>cell.id===program.target):null;
 if(partner&&['CONTACT','PRIME','HELP'].includes(program.action)&&program.due>tissue.time_min&&partner.program?.target===c.id&&partner.program.due===program.due&&Math.hypot(c.x-partner.x,c.y-partner.y)<=tissue.params.contact_um){
  const positions=selectedContact.geometry.getAttribute('position');positions.setXYZ(0,c.x,2,-c.y);positions.setXYZ(1,partner.x,2,-partner.y);positions.needsUpdate=true;selectedContact.geometry.computeBoundingSphere();selectedContact.computeLineDistances();selectedContact.visible=true;
 }
 selectedCellLabel(c);
}
function selectedCellLabel(c){
 const label=$('#cellAction');label.hidden=!c;if(!c)return;
 const decision=c.last_decision, source=decision?.source==='jev'?'Jev':decision?.source||'No choice yet';
 const program=c.program;
 label.innerHTML=`<strong>${esc(c.id)} · ${esc(data.registry[c.kind].label)}</strong>${program?`<b>Active: ${esc(program.action)} · ${Math.max(0,program.due-tissue.time_min)} min remaining</b>`:`<b>${esc(data.states[c.state]||c.state)}</b>`}${decision?`<span>Last choice · ${esc(source)}: ${esc(decision.action)}</span><small>${esc(decision.result)} · ${(decision.time_min/60).toFixed(1)} h${selectedContact.visible?' · dashed line = active contact':''}</small>`:'<span>Awaiting its first individual decision</span>'}`;
}
const labelPositions={follicle:[-66,0,-84],tzone:[63,0,-27],sinus:[-86,0,-170],medulla:[10,0,112],dz:[-67,1,-6],lz:[-30,1,-63]};
function labels(){if(tissue){const p0=new THREE.Vector3(0,0,0).project(camera),p1=new THREE.Vector3(50*150/tissue.params.radius_um,0,0).project(camera);$('.scale i').style.width=Math.abs(p1.x-p0.x)*canvas.clientWidth/2+'px';}const w=canvas.clientWidth,h=canvas.clientHeight;for(const el of document.querySelectorAll('[data-zone]')){const key=el.dataset.zone;el.hidden=!showZones||(key==='dz'||key==='lz')&&!tissue?.gc;const p=new THREE.Vector3(...labelPositions[key]).project(camera);el.style.left=`${(p.x*.5+.5)*w}px`;el.style.top=`${(-p.y*.5+.5)*h}px`;}const c=cells.find(cell=>cell.id===selected);if(c){const scale=150/tissue.params.radius_um,p=new THREE.Vector3(c.x*scale,7*scale,-c.y*scale).project(camera),label=$('#cellAction');label.style.left=Math.max(8,Math.min(w-228,(p.x*.5+.5)*w+16))+'px';label.style.top=Math.max(8,Math.min(h-118,(-p.y*.5+.5)*h-10))+'px';}}
let lastSize='';function render(){requestAnimationFrame(render);const now=performance.now();if(artMotion&&!document.hidden&&cellArt.enabled)artTime+=Math.min((now-lastArtTick)/1000,.05);lastArtTick=now;cellArt.tick(artTime);const w=canvas.clientWidth,h=canvas.clientHeight,key=w+','+h;if(key!==lastSize){renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();lastSize=key;}controls.update();renderer.render(scene,camera);labels();}
render();
let pointerStart;canvas.addEventListener('pointerdown',e=>{pointerStart=[e.clientX,e.clientY];});canvas.addEventListener('pointerup',e=>{if(!pointerStart||Math.hypot(e.clientX-pointerStart[0],e.clientY-pointerStart[1])>5||!bodies)return;pointerStart=null;const rect=canvas.getBoundingClientRect(),ray=new THREE.Raycaster();ray.setFromCamera(new THREE.Vector2((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1),camera);const hits=[...ray.intersectObject(bodies).map(hit=>({...hit,cell:cells[hit.instanceId]})),...cellArt.pick(ray)].sort((a,b)=>a.distance-b.distance);if(hits.length){selected=hits[0].cell.id;inspect();updateScene();}});
$('#top').onclick=()=>{camera.position.set(0,470,.01);controls.update();$('#top').classList.add('active');$('#angle').classList.remove('active');};
$('#angle').onclick=()=>{camera.position.set(25,345,340);controls.update();$('#angle').classList.add('active');$('#top').classList.remove('active');};
$('#zones').onclick=()=>{showZones=!showZones;zones.visible=showZones;$('#zones').classList.toggle('active',showZones);};
function setIllustrated(enabled){cellArt.setEnabled(enabled);$('#illustrated').classList.toggle('active',cellArt.enabled);$('#original3d').classList.toggle('active',!cellArt.enabled);$('#illustrated').setAttribute('aria-pressed',String(cellArt.enabled));$('#original3d').setAttribute('aria-pressed',String(!cellArt.enabled));$('#artMotion').disabled=!cellArt.enabled;$('#artNote').hidden=!cellArt.enabled;controls.minDistance=cellArt.enabled?110:220;if(cellArt.enabled)$('#top').click();else $('#angle').click();if(tissue)update(data,false);}
$('#illustrated').onclick=()=>setIllustrated(true);$('#original3d').onclick=()=>setIllustrated(false);
$('#artMotion').onclick=()=>{artMotion=!artMotion;motionUI();};
function cellSwatch(kind,state){return cellArt.enabled&&artKind({kind,state})?`<span class="atlas-thumb" style="background-image:url('${atlasURL(kind)}')" aria-hidden="true"></span>`:`<span class="dot" style="background:${data.registry[kind].color}" aria-hidden="true"></span>`;}
cellArt.load().then(()=>{$('#illustrated').disabled=false;$('#artStatus').textContent='';setIllustrated(true);}).catch(error=>{$('#artStatus').textContent=error.message;});
function inspect(){
 if(!selected)return;const c=cells.find(x=>x.id===selected);if(!c){$('#inspector').innerHTML='<h2>Cell no longer local.</h2><p>The event log retains its division or clearance history.</p>';return;}
 const info=data.registry[c.kind],d=c.last_decision;const rows=[['Lineage',c.lineage||c.kind],['Clone',c.clone||'—'],['Parent',c.parent||'Founder'],['BCR affinity',c.kind==='B'?Number(c.affinity).toFixed(2)+' · proposed':'—'],['Isotype',c.kind==='B'?c.isotype:'—'],['Antigen display',c.pmhc?`${c.pmhc.peptide} · ${c.pmhc.hla}`:'None'],['Division license',c.division_budget??'Recorded frame'],['Clock',c.program===undefined?'Not sampled in frame':c.program?`${c.program.action} · ${Math.max(0,c.program.due-tissue.time_min)} min`:'No active program']];
 $('#inspector').innerHTML=`<div class="cell-name">${cellSwatch(c.kind,c.state)}<div><h2>${esc(info.label)}</h2><small>${esc(c.id)} · ${esc(info.manual)}</small></div></div><span class="state-pill">${esc(data.states[c.state]||c.state)}</span><div class="inspection-table">${rows.map(([a,b])=>`<div><span>${a}</span><b>${esc(b)}</b></div>`).join('')}</div><span class="eyebrow">LAST INDIVIDUAL DECISION</span><div class="decision-box">${d?`<small>${esc(d.source)} · ${(d.time_min/60).toFixed(1)} h</small><strong>${esc(d.action.replaceAll('_',' '))}</strong>${Object.entries(d.probabilities).sort((a,b)=>b[1]-a[1]).slice(0,6).map(([k,v])=>`<div class="prob"><span>${esc(k)}</span><span>${Math.round(v*100)}%</span></div>`).join('')}<small>${esc(d.result)}</small>`:recording?'Select a saved frame; complete decisions are retained in the exported episode.':'This cell has not received a decision yet.'}</div>`;
}
function chart(){const c=$('#chart'),w=c.clientWidth,h=76;c.width=w*2;c.height=h*2;const ctx=c.getContext('2d');ctx.scale(2,2);ctx.strokeStyle='#2a3940';ctx.beginPath();ctx.moveTo(0,h-17);ctx.lineTo(w,h-17);ctx.stroke();const rows=recording?recording.frames:history;const max=Math.max(4,...rows.map(f=>Math.max(f.metrics.gc_b,f.metrics.plasma,f.metrics.memory||0)));
 for(const [key,col] of [['gc_b','#a3a8ff'],['memory','#f1a6c7'],['plasma','#ffc879']]){ctx.beginPath();ctx.strokeStyle=col;ctx.lineWidth=1.7;rows.forEach((f,i)=>{const x=i/Math.max(1,rows.length-1)*w,y=h-18-f.metrics[key]/max*(h-25);i?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.stroke();}ctx.fillStyle='#7e969f';ctx.font='8px monospace';ctx.fillText('0 h',0,h-3);ctx.textAlign='right';ctx.fillText(`${((rows.at(-1)?.time_min||0)/60).toFixed(1)} h`,w,h-3);}
function update(value,append=true){data=value;token=value.token||token;tissue=value.tissue;if(append&&!recording){const f={time_min:tissue.time_min,metrics:tissue.metrics};if(history.at(-1)?.time_min!==f.time_min)history.push(f);}
 const m=tissue.metrics;$('#diameter').textContent=(tissue.params.radius_um*2).toFixed(1)+' μm';$('#initialPopulation').textContent='initial population: '+m.initial;canvas.setAttribute('aria-label',`Interactive 3D lymph-node patch with ${m.live} living cells`);$('#cellCount').textContent=m.live+' cells';$('#metricLive').textContent=m.live;$('#metricGC').textContent=m.gc_b;$('#metricPresent').textContent=m.presenting;$('#metricAb').textContent=m.antibodies;$('#metricDivisions').textContent=m.net_births;$('#metricMemory').textContent=m.memory;$('#gcStatus').textContent=tissue.gc?'organized GC':'not formed';$('#time').textContent=(tissue.time_min/60).toFixed(1)+' h';
 $('#legend').innerHTML=Object.entries(data.registry).map(([kind,r])=>`<button class="legend-row ${filter&&filter!==kind?'dim':''}" data-kind="${kind}">${cellSwatch(kind)}${r.label}<b>${m.types[kind]||0}</b></button>`).join('');document.querySelectorAll('[data-kind]').forEach(el=>el.onclick=()=>{filter=filter===el.dataset.kind?null:el.dataset.kind;$('#clearFilter').hidden=!filter;update(data,false);});
 $('#providerBadge').textContent=recording?(recording.provider_label==='jev'?'● Jev · recorded':'● Fixture · recorded'):data.provider.provider==='jev'?'● Jev · individual cells':'● Offline demonstration';
 $('#provider option[value=jev]').textContent=recording?'Jev · recorded':'Jev · live';$('#provider option[value=jev]').disabled=!(data.provider.enabled&&data.provider.configured);$('#budget').max=data.provider.server_limit;const vp=recording?.provider||data.provider;$('#usage').textContent=vp.requests?`${vp.requests} requests · ${vp.input_tokens+vp.output_tokens} known tokens${vp.unknown_usage?' · some usage unknown':''}${recording?' · recorded':''}`:recording?'Fixture recording · no paid requests':'No paid requests';
 $('#jevStatus').textContent=recording?(recording.provider_label==='jev'?'These cells follow saved Jev decisions. Playback makes no new requests.':'These cells follow saved fixture decisions.'):
 data.provider.provider==='jev'?`Jev chooses each cell’s action. The LN applies it to the illustrated cell. Session cap: ${data.provider.server_limit} requests.`:
 data.provider.enabled&&data.provider.configured?'Jev is ready. Select Jev and create an experiment to use it.':'Jev is inactive in this session. Open Start Jev.cmd to configure and start the LN with Jev.';
 const events=(tissue.events||[]).filter(e=>!['program_started','program_completed','capture','retain'].includes(e.event)).slice(-7).reverse();const fallback=(tissue.events||[]).slice(-7).reverse();$('#events').innerHTML=(events.length?events:fallback).map(e=>`<div class="event">${esc(e.event.replaceAll('_',' '))}<span>${(e.time_min/60).toFixed(1)} h · ${esc(e.cell||'Tissue')} · ${esc(e.rule)}</span></div>`).join('')||'<p class="small">No completed biological events.</p>';$('#eventCount').textContent=m.decisions+' decisions';
 previewUI();updateScene();inspect();chart();if(tissue.stop_reason){running=false;notice(tissue.stop_reason);}
 controlsUI();
}
function activePreview(){return recording?recording.design_preview:data?.design_preview;}
function previewUI(){
 const p=activePreview();let panel=$('#decisionPreview');
 if(!panel){panel=document.createElement('section');panel.id='decisionPreview';$('.transport').after(panel);}
 panel.hidden=!p;if(!p)return;
 const complete=p.status==='complete',count=complete?p.selected_ids.length:0;
 if(!selected&&complete)selected=p.selected_ids[0];
 $('#providerBadge').textContent=`● Jev · preview ${count}/${p.limit}`;
 $('#jevStatus').textContent=`Visual preview: ${p.limit} individual decisions in one completed call. Further calls are blocked.`;
 $('#budgetWrap').hidden=true;
 $('#setupHint').textContent='Partial sample for design review. The other cells received no decisions.';
 panel.innerHTML=`<div class="preview-heading"><div><span class="eyebrow">DESIGN PREVIEW</span><h3>${complete?`${count} actual Jev decisions`:'Preview '+esc(p.status)}</h3></div>${complete?`<div class="segmented"><button id="previewBefore" aria-pressed="${tissue.time_min===0}">Before</button><button id="previewAfter" aria-pressed="${tissue.time_min!==0}">After Jev</button></div>`:''}</div><p>Select a cell below to inspect its decision in the tissue.</p><div class="preview-cells">${(p.after?.cells||[]).filter(c=>p.selected_ids.includes(c.id)).map(c=>`<button data-preview-cell="${esc(c.id)}" aria-pressed="${c.id===selected}">${cellSwatch(c.kind,c.state)}<span>${esc(data.registry[c.kind].label)} <small>${esc(c.id)}</small></span><b>${esc(c.last_decision?.action)}</b></button>`).join('')}</div><small>Only ${p.limit} of ${tissue.metrics.initial} cells were queried. The model advanced one partial 30-minute step; this preview is not a complete round. Membrane motion is illustrative.</small>`;
 panel.querySelectorAll('[data-preview-cell]').forEach(button=>button.onclick=()=>{selected=button.dataset.previewCell;filter=null;$('#clearFilter').hidden=true;update({...data,tissue:p.after},false);});
 if(complete){$('#previewBefore').onclick=()=>update({...data,tissue:p.before},false);$('#previewAfter').onclick=()=>update({...data,tissue:p.after},false);}
 notice(complete?`${count} decisions completed · 1 successful Jev call · further calls blocked. Explore, zoom and select cells.`:'Preview paused · no further calls will be made.');
}
function syncExperimentSettings(){$('#provider').value=data.provider.provider;$('#population').value=tissue.metrics.initial;$('#budget').value=data.provider.server_limit||100;$('#budgetWrap').hidden=data.provider.provider!=='jev';$('#setupHint').textContent=data.provider.provider==='jev'?'Ready for individual Jev decisions. Run with Jev advances the tissue.':`Starts with ${tissue.metrics.initial} cells and no germinal center.`;if(activePreview())previewUI();}
function controlsUI(){const preview=activePreview(),offline=!!recording||!!preview;$('#play').textContent=preview?`Preview ${preview.status==='complete'?'complete':'paused'} · ${preview.limit} decisions`:running?'Ⅱ Pause':offline?'▶ Play recording':data?.provider.provider==='jev'?'▶ Run with Jev':'▶ Run demonstration';$('#play').disabled=!!preview;$('#step').disabled=busy||running||offline;$('#pulse').disabled=busy||running||offline||tissue?.scenario==='baseline';$('#reset').disabled=busy||running||offline;$('#scenario').disabled=running||busy||offline;$('#population').disabled=running||busy||offline;$('#seed').disabled=running||busy||offline;$('#provider').disabled=running||busy||offline;$('#export').disabled=busy||!!recording;}
async function advance(){if(busy||recording)return;busy=true;controlsUI();try{const value=await api('/api/step',{});update(value);notice(data.provider.provider==='jev'?'Jev decisions applied · probabilities are not biological rates.':'Demo fixture · no AI calls. Numerical parameters are proposed and uncalibrated.');}catch(e){running=false;notice(e.message,true);}finally{busy=false;controlsUI();}}
async function loop(){if(!running)return;if(recording){let i=+$('#seek').value+1;if(i>=recording.frames.length){running=false;controlsUI();return;}showFrame(i);}else await advance();if(running)setTimeout(loop,recording?180:80);}
$('#play').onclick=()=>{running=!running;controlsUI();if(running)loop();};$('#step').onclick=advance;
$('#reset').onclick=async()=>{if(tissue.round&&!confirm('Discard this run and create a new experiment? Export it first to retain its full history.'))return;busy=true;controlsUI();try{history=[];selected=null;update(await api('/api/reset',{scenario:$('#scenario').value,cells:+$('#population').value,seed:+$('#seed').value,provider:$('#provider').value,budget:$('#provider').value==='jev'?+$('#budget').value:0,discard:true}));notice(data.provider.provider==='jev'?'Ready for live Jev. Starting will use your configured request budget.':'New independent fixture run · no paid requests.');}catch(e){notice(e.message,true);}finally{busy=false;controlsUI();}};
$('#provider').onchange=()=>{$('#budgetWrap').hidden=$('#provider').value!=='jev';$('#setupHint').textContent='Choose Create new experiment to apply these settings.';};$('#population').onchange=()=>{$('#setupHint').textContent=`Choose Create new experiment to initialize ${$('#population').value} cells.`;};$('#scenario').onchange=()=>{$('#setupHint').textContent='Choose Create new experiment to apply this context.';};
$('#pulse').onclick=async()=>{busy=true;controlsUI();try{update(await api('/api/inject',{}),false);notice(`${Math.round(80*tissue.metrics.initial/300)} additional antigen packets entered at the afferent boundary.`);}catch(e){notice(e.message,true);}finally{busy=false;controlsUI();}};
$('#export').onclick=()=>{const a=document.createElement('a');a.href='/api/export';a.download='lymph-node.ln.json.gz';a.click();};$('#clearFilter').onclick=()=>{filter=null;$('#clearFilter').hidden=true;update(data,false);};
$('#about').onclick=()=>$('#notes').showModal();$('#closeNotes').onclick=()=>$('#notes').close();
function showFrame(i){const f=recording.frames[i];$('#seek').value=i;const ds=recording.decisions?.slice(0,f.metrics.decisions)||[];const latest=new Map(ds.map(d=>[d.cell,d]));const cs=f.cells.map(c=>{const d=latest.get(c.id);return {...c,last_decision:d?{action:d.proposal.choice,source:d.source,probabilities:d.proposal.probabilities,result:d.result,time_min:d.time_min}:null};});
 update({...data,tissue:{...recording.final,...f,cells:cs,antigens:[],events:(f.event_count!==undefined?recording.events.slice(0,f.event_count):recording.events.filter(e=>e.time_min<f.time_min)).slice(-35),stop_reason:null}},false);notice(`${recording.provider_label==='jev'?'Actual Jev decisions':'Fixture decisions'} · ${recording.recording_status||'complete'} recording · playback makes no API calls.`);}
function replayMilestones(){
 const box=$('#milestones');box.replaceChildren();box.hidden=!recording;
 const policy=$('#policyNote');policy.hidden=!recording?.branch_provenance;
 policy.textContent=recording?.branch_provenance?'Demonstration comparison from 60 h: a proposed local-antigen rule guides Jev’s choice between further cycling and memory. This is a model assumption, not a calibrated biological result.':'';
 if(!recording)return;
 const stages=[['GC formed',f=>f.gc],['First division',f=>f.metrics.net_births>0],['Memory B',f=>f.metrics.memory>0],['Plasmablast',f=>f.cells.some(c=>c.state==='plasmablast')],['Plasma cell',f=>f.cells.some(c=>c.state==='plasma')],['Antibody output',f=>f.metrics.antibodies>0]];
 for(const [label,i] of stages.map(([label,test])=>[label,recording.frames.findIndex(test)]).filter(([,i])=>i>=0).sort((a,b)=>a[1]-b[1])){const b=document.createElement('button');b.className='text-button';b.textContent=`${label} · ${(recording.frames[i].time_min/60).toFixed(1)} h`;b.onclick=()=>{running=false;showFrame(i);controlsUI();};box.append(b);}
}
async function loadRecording(stream){
 running=false;
 const reader=stream.getReader();const chunks=[];let total=0;
 for(;;){const {done,value}=await reader.read();if(done)break;total+=value.length;if(total>256_000_000){await reader.cancel();throw new Error('Recording exceeds 256 MB decompressed limit');}chunks.push(value);}
 const obj=JSON.parse(await new Blob(chunks).text());
 if(obj.format!=='lymph-node-episode-v1'||!Array.isArray(obj.frames)||!obj.frames.length||!obj.final||!Array.isArray(obj.events))throw new Error('Unsupported recording');
 recording=obj;$('#provider').value=obj.provider_label==='jev'?'jev':'fixture';$('#population').value=obj.final.metrics.initial;$('#replay').hidden=false;$('#seek').max=obj.frames.length-1;selected=null;replayMilestones();showFrame(0);
}
$('#import').onchange=async e=>{try{const file=e.target.files[0];if(!file)return;if(file.size>50_000_000)throw new Error('Recording exceeds 50 MB compressed limit');let stream=file.stream();if(file.name.endsWith('.gz'))stream=stream.pipeThrough(new DecompressionStream('gzip'));await loadRecording(stream);}catch(e){recording=null;notice(e.message,true);controlsUI();}};
async function openSavedRecording(id){if(!id)return;try{notice('Loading the saved Jev example…');const res=await fetch('/api/recordings/'+encodeURIComponent(id));if(!res.ok)throw new Error('Recording is not available');await loadRecording(res.body.pipeThrough(new DecompressionStream('gzip')));$('#recordings').value=id;}catch(e){notice(e.message,true);controlsUI();}}
$('#recordings').onchange=e=>openSavedRecording(e.target.value);
async function refreshRecordings(){try{const result=await api('/api/recordings');const current=$('#recordings').value;$('#recordings').innerHTML='<option value="">Saved Jev examples</option>'+result.recordings.map(r=>`<option value="${r.id}">${esc(data?.scenarios?.[r.scenario]?.label||r.scenario)} · ${(r.time_min/60).toFixed(1)} h · ${esc(r.status)}</option>`).join('');$('#recordings').value=current;}catch{}}
$('#seek').oninput=e=>showFrame(+e.target.value);$('#leaveReplay').onclick=async()=>{running=false;recording=null;replayMilestones();$('#replay').hidden=true;update(await api('/api/state'),false);syncExperimentSettings();notice('Returned to the current live tissue.');};
try{update(await api('/api/state'));syncExperimentSettings();$('#loading').hidden=true;await refreshRecordings();const saved=new URLSearchParams(location.search).get('recording');if(saved)await openSavedRecording(saved);}catch(e){$('#loading').textContent=e.message;notice(e.message,true);}

new ResizeObserver(()=>{if(data)chart();}).observe(document.querySelector(".workspace"));

setInterval(refreshRecordings,15000);
