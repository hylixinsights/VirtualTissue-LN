#!/usr/bin/env python3
"""Build an API-free static replay from explicitly reviewed public recordings."""
import gzip,hashlib,json,re,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine import STATES,SCENARIOS

def main():
 reviewed=ROOT/'recordings/examples/reactive-index.json'
 if reviewed.exists() and '--legacy' not in sys.argv:
  from scripts.build_reactive_site import build
  item=json.loads(reviewed.read_text(encoding='utf-8'))
  name=item['file'];assert Path(name).name==name and name.endswith('.ln.json.gz')
  recording=ROOT/'recordings/examples'/name
  assert hashlib.sha256(recording.read_bytes()).hexdigest()==item['sha256']
  build(recording,ROOT/'site');return
 site=ROOT/'site';site.mkdir(exist_ok=True)
 if (site/'site-files.json').exists():(site/'site-files.json').unlink()
 for directory in ('web','vendor','recordings'):(site/directory).mkdir(exist_ok=True)
 catalog=json.loads((ROOT/'recordings/examples/index.json').read_text(encoding='utf-8'))
 for entry in catalog['recordings']:
  name=entry['file'];assert Path(name).name==name and name.endswith('.ln.json.gz')
  raw=(ROOT/'recordings/examples'/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==entry['sha256']
  ep=json.loads(gzip.decompress(raw));assert ep['provider_label']=='jev' and ep['recording_status']=='complete'
  assert ep['final']['metrics']['memory']==3 and ep['final']['metrics']['net_births']==1 and ep['final']['round']==128
  (site/'recordings'/name).write_bytes(raw)
 metadata={'recordings':catalog['recordings'],'registry':ep['contract']['registry'],'states':STATES,'scenarios':SCENARIOS}
 (site/'catalog.json').write_text(json.dumps(metadata,separators=(',',':')))
 for p in (ROOT/'vendor').iterdir():
  if p.is_file() and p.suffix in ('.js','.txt'):shutil.copy2(p,site/'vendor'/p.name)
 for name in ('style.css','icon.svg'):shutil.copy2(ROOT/'web'/name,site/'web'/name)
 for name in ('cell-atlas.mjs','cell-art.mjs','cell-gallery.html','cell-gallery.css','cell-gallery.mjs','vaccine-demo.html','vaccine-demo.css','vaccine-demo.mjs','vaccine-story.json'):
  shutil.copy2(ROOT/'web'/name,site/'web'/name)
 shutil.copytree(ROOT/'web/assets/cells',site/'web/assets/cells',dirs_exist_ok=True)
 js=(ROOT/'web/app.mjs').read_text(encoding='utf-8')
 js='\n'.join(line for line in js.splitlines() if not line.startswith('async function api('))
 start=js.index('function controlsUI()');end=js.index('function showFrame',start)
 js=js[:start]+'''function controlsUI(){
 $('#play').textContent=running?'Ⅱ Pause':'▶ Play recording';$('#play').disabled=!recording;
 for(const id of ['step','pulse','reset','scenario','population','seed','provider'])$('#'+id).disabled=true;
 $('#export').disabled=false;
}
function loop(){if(!running||!recording)return;const i=+$('#seek').value+1;if(i>=recording.frames.length){running=false;controlsUI();return;}showFrame(i);setTimeout(loop,180);}
$('#play').onclick=()=>{if(!recording)return;if(+$('#seek').value>=recording.frames.length-1)showFrame(0);running=!running;controlsUI();if(running)loop();};
$('#clearFilter').onclick=()=>{filter=null;$('#clearFilter').hidden=true;update(data,false);};
$('#about').onclick=()=>$('#notes').showModal();$('#closeNotes').onclick=()=>$('#notes').close();
''' +js[end:]
 start=js.index('async function openSavedRecording');js=js[:start]+'''
let publicCatalog;
async function openSavedRecording(id){
 running=false;controlsUI();
 const entry=publicCatalog.recordings.find(r=>r.id===id);if(!entry)throw Error('This recording is not in the public catalog.');
 if(!/^[-a-z0-9]+\\.ln\\.json\\.gz$/.test(entry.file))throw Error('Invalid catalog filename.');
 notice('Loading the recorded lymph-node response…');
 const response=await fetch(new URL('recordings/'+entry.file,location.href),{credentials:'omit',redirect:'error'});
 if(!response.ok)throw Error('The recording could not be loaded.');
 const bytes=await response.arrayBuffer();
 const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
 if(hash!==entry.sha256)throw Error('Recording integrity check failed.');
 await loadRecording(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip')));
 $('#recordings').value=id;$('#loading').hidden=true;
 $('#setupHint').textContent='Recorded experiment · 100 initial cells · 64 simulated hours. Replay makes no AI calls.';
 $('#export').onclick=()=>{const a=document.createElement('a');a.href='recordings/'+entry.file;a.download=entry.file;a.click();};
}
$('#recordings').onchange=e=>openSavedRecording(e.target.value).catch(e=>notice(e.message,true));
$('#seek').oninput=e=>showFrame(+e.target.value);
try{
 controlsUI();
 const response=await fetch(new URL('catalog.json',location.href),{credentials:'omit',redirect:'error'});
 if(!response.ok)throw Error('The public recording catalog could not be loaded.');
 publicCatalog=await response.json();
 data={registry:publicCatalog.registry,states:publicCatalog.states,scenarios:publicCatalog.scenarios,provider:{provider:'jev',enabled:false,configured:false,server_limit:0,requests:0,input_tokens:0,output_tokens:0,unknown_usage:0}};
 $('#recordings').innerHTML=publicCatalog.recordings.map(r=>`<option value="${esc(r.id)}">${esc(r.title)}</option>`).join('');
 await openSavedRecording(new URLSearchParams(location.search).get('recording')||publicCatalog.recordings[0].id);
}catch(e){$('#loading').textContent=e.message;notice(e.message,true);$('#play').disabled=true;}
new ResizeObserver(()=>{if(tissue)chart();}).observe(document.querySelector('.workspace'));
'''
 assert '/api/' not in js and 'Authorization' not in js and 'api.typesafe' not in js
 (site/'web/app.mjs').write_text(js,encoding='utf-8')
 html=(ROOT/'web/index.html').read_text(encoding='utf-8').replace('"/web/','"./web/').replace('"/vendor/','"./vendor/')
 html=html.replace('class="brand" href="/"','class="brand" href="../"')
 html=html.replace('↓ Export run','↓ Download recording').replace('>LIVE TISSUE<','>RECORDED TISSUE<').replace('>TISSUE STUDIO<','>TISSUE EXPLORER<')
 html=html.replace('Demo recordings are fixtures, not Jev results. A service failure pauses the simulation without substituting a demo policy.','This public recording contains actual Jev choices. A proposed competing-fate rule was introduced at 60 hours and is disclosed in the recording. Playback makes no API calls.')
 html=html.replace('</head>','''<meta name="description" content="Replay a 100-cell lymph-node simulation with real recorded Jev choices, germinal-center formation, division and memory B cells."><meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'"><style>#step,#pulse,#reset,#budgetWrap,#leaveReplay{display:none!important}.header-right a{font-size:11px;margin-left:8px}select:disabled,input:disabled{opacity:.85}#setupHint{line-height:1.6}</style></head>''')
 html=html.replace('<button id="about"','<a href="./model.html">Manual &amp; provenance ↗</a><button id="about"')
 (site/'index.html').write_text(html,encoding='utf-8')
 # A plain escaped manual preserves the supplied wording without an external Markdown runtime.
 import html as h
 manual=(ROOT/'docs/BIOLOGICAL_MANUAL.md').read_text(encoding='utf-8');scope=(ROOT/'docs/IMPLEMENTATION.md').read_text(encoding='utf-8')
 model='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lymph node — model and provenance</title><style>body{background:#101e24;color:#deebe7;font:16px/1.7 system-ui;max-width:960px;margin:40px auto;padding:0 24px}a{color:#9bdcc6}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.7 system-ui}h1{font-family:Georgia}details{margin-top:30px}</style><a href="./">← Replay the lymph node</a> · <a href="../">All tissues</a><h1>Lymph node: recorded demonstration</h1><p>100 initial cells; 64 simulated hours; one physical division and three memory B cells. Memory appears at 63 h in other clones, before the division at 64 h. No plasma cells or antibody output occurred.</p><p>Real Jev responses, with a proposed local-antigen fate rubric introduced at 60 h. This demonstration was selected and stopped upon reaching division and memory. It is not an unbiased estimate of cell-fate frequencies or a calibrated human lymph node.</p><p>The kernel enforces local eligibility, clocks, geometry, finite antigen and lineage. The public player reads saved frames only and never calls Jev.</p><p><a href="https://github.com/hylixinsights/VirtualTissue-LN">Source repository</a> · <a href="recordings/lymph-node-memory.ln.json.gz" download>Full recorded episode</a> · <a href="provenance.json">Recording provenance</a></p>'''
 (site/'model.html').write_text(model+'<details open><summary>Implemented scope</summary><pre>'+h.escape(scope)+'</pre></details><details><summary>Original biological manual</summary><pre>'+h.escape(manual)+'</pre></details></html>',encoding='utf-8')
 (site/'provenance.json').write_text(json.dumps(catalog,indent=2)+'\n')
 (site/'.nojekyll').write_text('')
 print('Built static site: reviewed Jev recording, relative paths, integrity check, no API client.')
if __name__=='__main__':main()
