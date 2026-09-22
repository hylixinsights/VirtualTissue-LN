// Capture the actual static replay canvas as a captioned MP4. No inference.
// Developer dependency: Playwright and Chrome. Run with the static site served.
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {dirname,resolve} from 'node:path';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';

const args=process.argv.slice(2),arg=(name,fallback)=>args.includes(name)?args[args.indexOf(name)+1]:fallback;
const base=arg('--url',process.env.REPLAY_URL||'http://127.0.0.1:8024/');
const output=resolve(arg('--output','dist/lymph-node-jev-highlights.mp4'));
const seconds=Number(arg('--seconds','150'));
if(!Number.isFinite(seconds)||seconds<20||seconds>600)throw Error('Choose a duration from 20 to 600 seconds.');

// Chrome writes fragmented MP4 with a provisional movie duration. Fill the three
// existing duration fields from actual fragment sample clocks, without re-encoding.
function finalizeMp4(bytes){
 const boxes=(start,end)=>{const out=[];for(let p=start;p<end;){const size=bytes.readUInt32BE(p),type=bytes.toString('ascii',p+4,p+8);if(size<8||p+size>end)throw Error('Unexpected MP4 box size.');out.push({p,size,type});p+=size;}return out;};
 const children=box=>boxes(box.p+8,box.p+box.size),find=(box,type)=>children(box).find(b=>b.type===type);
 const roots=boxes(0,bytes.length),movie=roots.find(b=>b.type==='moov'),tracks=children(movie).filter(b=>b.type==='trak');
 if(tracks.length!==1)throw Error('The export expects exactly one video track.');
 const mvhd=find(movie,'mvhd'),tkhd=find(tracks[0],'tkhd'),mdhd=find(find(tracks[0],'mdia'),'mdhd');
 const scale=box=>bytes.readUInt32BE(box.p+(bytes[box.p+8]===1?28:20));
 let duration=0;
 for(const moof of roots.filter(b=>b.type==='moof'))for(const traf of children(moof).filter(b=>b.type==='traf')){
  const tfdt=find(traf,'tfdt');let time=bytes[tfdt.p+8]===1?Number(bytes.readBigUInt64BE(tfdt.p+12)):bytes.readUInt32BE(tfdt.p+12);
  for(const trun of children(traf).filter(b=>b.type==='trun')){
   const flags=bytes.readUIntBE(trun.p+9,3),count=bytes.readUInt32BE(trun.p+12);
   if(!(flags&0x100))throw Error('Expected explicit MP4 sample durations.');
   let offset=trun.p+16+(flags&1?4:0)+(flags&4?4:0);
   const stride=[0x100,0x200,0x400,0x800].filter(flag=>flags&flag).length*4;
   for(let i=0;i<count;i++){time+=bytes.readUInt32BE(offset);offset+=stride;}
  }
  duration=Math.max(duration,time);
 }
 const seconds=duration/scale(mdhd),set=(box,value,track=false)=>{const wide=bytes[box.p+8]===1,offset=box.p+(track?(wide?36:28):(wide?32:24));if(wide)bytes.writeBigUInt64BE(BigInt(Math.ceil(value)),offset);else bytes.writeUInt32BE(Math.ceil(value),offset);};
 set(mdhd,duration);set(mvhd,seconds*scale(mvhd));set(tkhd,seconds*scale(mvhd),true);
 return seconds;
}
const manifest=await (await fetch(new URL('recording.json',base))).json();
if(manifest.preview&&!args.includes('--preview'))throw Error('A final video requires a completed recording.');
if(!/^[A-Za-z0-9_.-]+$/.test(manifest.file))throw Error('Invalid recording filename.');
const bytes=Buffer.from(await (await fetch(new URL('recordings/'+manifest.file,base))).arrayBuffer());
if(createHash('sha256').update(bytes).digest('hex')!==manifest.sha256)throw Error('Recording integrity check failed.');
const episode=JSON.parse(gunzipSync(bytes)),events=episode.events;
const specs=[
 ['DC entry',e=>e.event==='dendritic_cell_arrived','One dendritic cell brings nine finite antigen packets into a quiet tissue.'],
 ['T-cell priming',e=>e.event==='program_started'&&e.action==='PRIME','A compatible local DC–CD4 contact starts a timed priming program.'],
 ['Border helper',e=>e.event==='program_completed'&&e.action==='HELPER','The primed CD4 cell acquires a border-helper program.'],
 ['Linked B–T help',e=>e.event==='program_started'&&e.action==='HELP','A local cognate B–helper contact can license B-cell output.'],
 ['Help completed',e=>e.event==='program_completed'&&e.action==='HELP','Linked help completes; the helper becomes Tfh. B-cell fates remain individual choices.'],
 ['Germinal center',e=>e.event==='germinal_center_formed','Qualified founders and timed organization create a local GC.'],
 ['Plasmablast',e=>e.event==='program_completed'&&e.action==='PLASMA','One helped B cell completes plasmablast differentiation.'],
 ['First IgM output',e=>e.event==='antibody_secreted','After differentiation, the antibody-producing cell starts releasing its clone’s IgM output.'],
 ['Cell division',e=>e.event==='division','Two daughters replace one parent. Their recorded lineage and clone are preserved.'],
 ['Plasma cell',e=>e.event==='program_completed'&&e.action==='MATURE','The plasmablast matures into a plasma cell and continues secreting IgM.'],
 ['Failed GC selection',e=>e.event==='failed_selection_apoptosis','Unsuccessful GC cells undergo apoptosis. These outcomes remain in the recording.'],
 ['GC resolution',e=>e.event==='germinal_center_resolved','The local GC resolves after failed selection; the plasma cell continues output.'],
];
const chapters=specs.flatMap(([title,test,description])=>{const e=events.find(test);return e?[{title,description,time:e.time_min,cell:e.daughters?.[0]||e.cell}]:[];}).sort((a,b)=>a.time-b.time);
const end=Math.min(manifest.time_min,Math.max(48*60,...chapters.map(c=>c.time+180)));
const marks=[0,...new Set(chapters.map(c=>c.time).filter(t=>t>0)),end].sort((a,b)=>a-b);
const weights=marks.slice(1).map((t,i)=>Math.max(5,Math.min(18,Math.sqrt((t-marks[i])/60)*6)));
const sum=weights.reduce((a,b)=>a+b,0),segments=[];let elapsed=3;
for(let i=1;i<marks.length;i++){const duration=weights[i-1]/sum*(seconds-11);segments.push({start:elapsed,duration,from:marks[i-1],to:marks[i]});elapsed+=duration;}
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const browser=await chromium.launch({channel:process.env.CI?undefined:'chrome',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1600,height:1100},deviceScaleFactor:1}),errors=[],forbidden=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('request',r=>{if(r.method()!=='GET'||new URL(r.url()).origin!==new URL(base).origin||/\/api\//.test(r.url()))forbidden.push(r.url());});
 await page.goto(base);await page.locator('#loading').waitFor({state:'hidden',timeout:60000});
 await page.evaluate(()=>{
  if(document.querySelector('#play').getAttribute('aria-pressed')==='true')document.querySelector('#play').click();
  const range=document.querySelector('#replayWindow');range.value='full';range.dispatchEvent(new Event('change'));
 });
 const download=page.waitForEvent('download',{timeout:(seconds+90)*1000});
 const capture=page.evaluate(async({seconds,segments,chapters,manifest,end})=>{
  const $=id=>document.getElementById(id),canvas=document.createElement('canvas');canvas.width=1920;canvas.height=1080;
  const ctx=canvas.getContext('2d'),mime='video/mp4;codecs=avc1.42E01E';
  if(!MediaRecorder.isTypeSupported(mime))throw Error('This browser does not support MP4 recording. Use current Chrome.');
  const recorder=new MediaRecorder(canvas.captureStream(30),{mimeType:mime,videoBitsPerSecond:3200000}),chunks=[];
  recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};
  const completed=new Promise(resolve=>recorder.onstop=resolve);
  let tick=-1,selected=null,focused=false,started=performance.now();
  const text=(value,x,y,size=24,color='#214947',weight='400')=>{ctx.fillStyle=color;ctx.font=`${weight} ${size}px Segoe UI, sans-serif`;ctx.fillText(String(value),x,y);};
  function wrap(value,x,y,width,size=24,color='#315854'){
   ctx.font=`${size}px Segoe UI, sans-serif`;let line='';
   for(const word of String(value).split(' ')){const next=line?line+' '+word:word;if(ctx.measureText(next).width>width&&line){text(line,x,y,size,color);y+=size*1.45;line=word;}else line=next;}
   if(line){text(line,x,y,size,color);y+=size*1.45;}return y;
  }
  function seek(time){const range=$('seek');range.value=String(time);range.dispatchEvent(new Event('input'));}
  function paint(now){
   const elapsed=Math.min(seconds,(now-started)/1000),late=elapsed>=seconds-8;
   const segment=segments.find(s=>elapsed>=s.start&&elapsed<s.start+s.duration);
   let time=elapsed<3?0:segment?segment.from+(segment.to-segment.from)*(elapsed-segment.start)/segment.duration:end;
   if(late)time=manifest.time_min;
   const nextTick=Math.floor(time/10);
   if(nextTick!==tick){seek(time);tick=nextTick;}
   const chapter=late?{title:manifest.preview?'Current saved state':'Full run saved',description:manifest.preview?'This review snapshot is from a run still in progress.':`The run ended (${manifest.status.replaceAll('_',' ')}). The full replay preserves every saved tick, decision and lineage.`,cell:chapters.find(c=>c.title==='Plasma cell')?.cell}:chapters.filter(c=>c.time<=time).at(-1)||chapters[0];
   if(chapter.cell!==selected&&[...$('cellSelect').options].some(o=>o.value===chapter.cell)){$('cellSelect').value=chapter.cell;$('cellSelect').dispatchEvent(new Event('change'));selected=chapter.cell;}
   const focus=elapsed>=3&&!late;if(focus!==focused){$('view').click();focused=focus;}
   ctx.fillStyle='#f4f3eb';ctx.fillRect(0,0,1920,1080);
   text('VirtualTissue / LN',54,65,38,'#173f3e','600');
   text('ONE CELL. ONE LOCAL VIEW.',56,109,18,'#66877d','600');
   text(`${manifest.usage.requests.toLocaleString('en-US')} actual Jev calls · saved experiment`,1140,67,24);
   ctx.fillStyle='#1e4241';ctx.fillRect(40,145,1280,760);
   const source=$('tissue'),ratio=Math.min(1280/source.width,760/source.height),w=source.width*ratio,h=source.height*ratio;
   ctx.drawImage(source,40+(1280-w)/2,145+(760-h)/2,w,h);
   text('RECORDED BIOLOGICAL TIME',1360,181,18,'#6b847a','600');
   text($('clock').textContent,1360,237,46,'#173f3e','600');
   let y=wrap(chapter.title,1360,305,490,31,'#173f3e')+12;
   y=wrap(chapter.description,1360,y,490,24)+28;
   text('INDIVIDUAL CELL',1360,y,18,'#6b847a','600');y+=37;
   y=wrap($('cellName').textContent,1360,y,490,28)+10;
   y=wrap($('cellIdentity').textContent,1360,y,490,20)+18;
   wrap($('choice').textContent,1360,y,490,22);
   const fields=[['population','living cells'],['never','never queried'],['divisions','cell divisions'],['antibodies','IgM units']];
   fields.forEach(([id,label],i)=>{const x=55+i*315;text($(id).textContent,x,965,40,'#173f3e','600');text(label,x,1002,21,'#5f7c73');});
   wrap(late?'Late output: plasma-cell lifespan and antibody decay are not modeled.':'Uncalibrated demonstration policy. Timed biological processes and local eligibility are enforced.',1360,858,495,20,'#84683b');
   text('Accelerated saved timeline · artwork motion is illustrative · playback uses zero API calls',55,1052,19,'#6b847a');
   if(manifest.preview)text('IN-PROGRESS PREVIEW',1360,1032,22,'#98692b','600');
   if(elapsed<seconds)requestAnimationFrame(paint);else recorder.stop();
  }
  seek(0);recorder.start(1000);requestAnimationFrame(paint);await completed;
  const blob=new Blob(chunks,{type:'video/mp4'}),link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download='lymph-node-jev-highlights.mp4';link.click();
  return {bytes:blob.size,seconds,width:canvas.width,height:canvas.height,mime:recorder.mimeType};
 },{seconds,segments,chapters,manifest,end});
 await mkdir(dirname(output),{recursive:true});await (await download).saveAs(output);
 const result=await capture;if(errors.length||forbidden.length)throw Error(JSON.stringify({errors,forbidden}));
 const movie=await readFile(output);result.encodedDuration=finalizeMp4(movie);result.videoSha256=createHash('sha256').update(movie).digest('hex');await writeFile(output,movie);
 const review={...result,recordingSha256:manifest.sha256,requests:manifest.usage.requests,status:manifest.status,preview:manifest.preview,chapters,errors,forbidden};
 await writeFile(output.replace(/\.mp4$/i,'.json'),JSON.stringify(review,null,2)+'\n');
 console.log(JSON.stringify({output,...result,requests:manifest.usage.requests,status:manifest.status}));
}finally{await browser.close();}
