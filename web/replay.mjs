// Playback uses recorded deltas and receipts only. No biological decisions here.
export const recordedStateLabels={naive:'Naive',activated:'Antigen activated',pre_tfh:'Border helper',tfh:'T follicular helper',founder:'GC founder',dz:'GC · dark zone',lz:'GC · light zone',selected:'GC · selected',memory:'Memory B',plasmablast:'Plasmablast',plasma:'Plasma cell',resting:'Resting',presenting:'Antigen presenting',apoptotic:'Apoptotic',cleared:'Cleared',divided:'Replaced by daughters'};
export async function readRecording(url,sha256){
 const response=await fetch(url,{credentials:'omit',redirect:'error'});
 if(!response.ok)throw Error('The saved recording could not be loaded.');
 const bytes=await response.arrayBuffer();
 if(sha256){
  const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
  if(hash!==sha256)throw Error('Recording integrity check failed.');
 }
 const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
 return new RecordedEpisode(await new Response(stream).json());
}

export class RecordedEpisode{
 constructor(episode){
  if(episode.format!=='lymph-node-reactive-recording-v1'||!episode.timeline?.length)throw Error('This file does not contain a reactive timeline.');
  this.episode=episode;this.frames=episode.timeline;this.checkpoints=new Map();this.cursorIndex=-1;this.cursorCells=null;
  const cells=new Map();
  this.frames.forEach((f,i)=>{
   for(const id of f.removed)cells.delete(id);
   for(const c of f.changes)cells.set(c.id,{...cells.get(c.id),...c});
   if(i%240===0)this.checkpoints.set(i,new Map(cells));
  });
  const events=episode.events;
  const types=[['DC arrival',e=>e.event==='dendritic_cell_arrived'],
   ['T-cell priming',e=>e.event==='program_started'&&e.action==='PRIME'],
   ['Helper differentiation',e=>e.event==='program_completed'&&e.action==='HELPER'],
   ['Linked B–T help',e=>e.event==='program_started'&&e.action==='HELP'],
   ['Help licensed',e=>e.event==='program_completed'&&e.action==='HELP'],
   ['Plasmablast',e=>e.event==='program_completed'&&e.action==='PLASMA'],
   ['First IgM',e=>e.event==='antibody_secreted'],
   ['GC formed',e=>e.event==='germinal_center_formed'],
   ['First division',e=>e.event==='division'],
   ['Plasma cell',e=>e.event==='program_completed'&&e.action==='MATURE'],
   ['Failed selection',e=>e.event==='failed_selection_apoptosis'],
   ['GC resolution',e=>e.event==='germinal_center_resolved']];
  this.chapters=types.flatMap(([label,test])=>{const event=events.find(test);return event?[{label,time:event.time_min,cell:event.daughters?.[0]||event.cell,index:this.frames.findIndex(f=>f.time_min>=event.time_min&&f.event_count>events.indexOf(event))}]:[];}).sort((a,b)=>a.index-b.index);
  this.duration=this.frames.at(-1).time_min;
  this.highlightEnd=Math.min(this.duration,Math.max(48*60,...this.chapters.map(c=>c.time+180)));
 }
 indexAt(time){
  let lo=0,hi=this.frames.length-1;
  while(lo<hi){const mid=Math.ceil((lo+hi)/2);if(this.frames[mid].time_min<=time)lo=mid;else hi=mid-1;}
  return lo;
 }
 tissue(index){
  index=Math.max(0,Math.min(this.frames.length-1,index));
  const forward=this.cursorIndex>=0&&index>=this.cursorIndex&&index-this.cursorIndex<240;
  const start=forward?this.cursorIndex:Math.floor(index/240)*240,cells=new Map(forward?this.cursorCells:this.checkpoints.get(start));
  for(let i=start+1;i<=index;i++){
   for(const id of this.frames[i].removed)cells.delete(id);
   for(const c of this.frames[i].changes)cells.set(c.id,{...cells.get(c.id),...c});
  }
  const frame=this.frames[index],e=this.episode;
  this.cursorIndex=index;this.cursorCells=cells;
  return {...e.initial,mode:'reactive',time_min:frame.time_min,round:frame.round,gc:frame.gc,gc_center:frame.gc_center,
   entries:frame.metrics.entries,metrics:frame.metrics,antigens:frame.antigens,stop_reason:null,
   last_prompt:e.inputs[0]?.prompt,events:e.events.slice(Math.max(0,frame.event_count-35),frame.event_count),
   cells:[...cells.values()].map(c=>{
    const d=e.decisions[c.receipt_index];
    return {...c,last_decision:d?{action:d.proposal.choice,source:d.source,probabilities:d.proposal.probabilities,result:d.result,time_min:d.time_min,observation:d.observation,options:d.options}:null};
   })};
 }
}
