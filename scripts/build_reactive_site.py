#!/usr/bin/env python3
"""Package one explicitly selected recording as a portable static website."""
import argparse
import gzip
import hashlib
import html
import json
from pathlib import Path
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import ROOT


def build(recording,output,preview_running=False):
    raw=Path(recording).read_bytes();episode=json.loads(gzip.decompress(raw))
    if episode.get('format')!='lymph-node-reactive-recording-v1' or episode.get('provider_label')!='jev':
        raise ValueError('Select an actual reactive Jev recording.')
    if episode['recording_status'] in ('prepared','running') and not preview_running:
        raise ValueError('The run is still active. Use --preview-running only for a clearly labeled local review.')
    if b'apikey_' in raw or any('apikey_' in json.dumps(v) for v in (episode,)):
        raise ValueError('Credential-like text detected; recording was not packaged.')
    if not all(d['source']=='jev' for d in episode['decisions']):raise ValueError('Mixed decision sources cannot be labeled Jev.')
    out=Path(output);(out/'web').mkdir(parents=True,exist_ok=True);(out/'recordings').mkdir(exist_ok=True)
    name='lymph-node-development.ln.json.gz';(out/'recordings'/name).write_bytes(raw)
    web_files=('reactive.css','reactive.mjs','replay.mjs','cell-atlas.mjs','cell-gallery.html','cell-gallery.css','cell-gallery.mjs')
    for f in web_files:
        shutil.copy2(ROOT/'web'/f,out/'web'/f)
    shutil.copytree(ROOT/'web/assets/cells',out/'web/assets/cells',dirs_exist_ok=True)
    page=(ROOT/'web/reactive.html').read_text(encoding='utf-8').replace('<body>','<body data-mode="replay">').replace('"/web/','"./web/').replace('href="/"','href="./"')
    page=page.replace('<title>Lymph node · Local responses</title>','<title>Lymph node · Recorded Jev response</title>')
    page=page.replace('A lymph node, coming to life.','A lymph node, frame by frame.')
    page=page.replace('Cell atlas ↗','Model &amp; provenance ↗').replace('href="./web/cell-gallery.html"','href="./model.html"')
    page=page.replace('</head>','<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; script-src \'self\'; style-src \'self\' \'unsafe-inline\'; img-src \'self\' data:; connect-src \'self\'; object-src \'none\'; base-uri \'self\'">\n</head>')
    (out/'index.html').write_text(page,encoding='utf-8')
    e=episode;m=e['final']['metrics'];usage=e['provider']
    manifest=dict(format='lymph-node-static-replay-v1',file=name,sha256=hashlib.sha256(raw).hexdigest(),status=e['recording_status'],
        model=usage['resolved_model'],usage=usage,policy=e['run_control']['policy_description'],
        time_min=e['final']['time_min'],metrics=m,frames=len(e['timeline']),decisions=len(e['decisions']),preview=preview_running)
    (out/'recording.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    warning='This is an in-progress review snapshot.' if preview_running else 'This is a saved, bounded Jev run.'
    details=f'''# Recorded LN response

{warning} Playback makes no inference calls and requires no API key.

Model: {usage['resolved_model']}. Recorded API attempts: {usage['requests']:,}.
Individual decisions: {len(e['decisions']):,}. Simulated duration: {e['final']['time_min']/60:,.1f} h.
Divisions: {m['net_births']}. Antibody-producing cells: {m['plasma']}. IgM output: {m['antibodies']} arbitrary units.

Policy: {e['run_control']['policy_description']}

This qualitative policy uses a proposed affinity-annotation threshold of 0.79 to
illustrate competing early-output and GC paths. The annotation and threshold are
not measured biological fate probabilities. All responses are actual Jev choices;
the kernel enforces local eligibility, physical contacts, process clocks, finite
antigen and parent–daughter accounting. Failed selection and deaths remain visible.

The full call-budget run can extend far beyond the initial response. The current
toy model does not implement a calibrated plasma-cell lifespan or antibody decay.
Late sustained secretion is therefore a model behavior, not a prediction of vaccine
duration. Highlights show the initial response; Full recording exposes every saved tick.

Run your own experiment with Python 3.10 or newer: open Start Jev.cmd (Windows)
or Start Jev.command (macOS), enter your own key through hidden input, and set
your maximum calls per run. The key stays on your computer's local server.
The public static website only replays the saved experiment.

Original manual: docs/BIOLOGICAL_MANUAL.md in the source repository.
Recorded actions and assumptions are included in the downloadable episode.
'''
    (out/'README.txt').write_text(details,encoding='utf-8')
    model='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Recorded LN — provenance</title><style>body{background:#f3f2e9;color:#173f3e;font:16px/1.7 system-ui;max-width:850px;margin:40px auto;padding:0 22px}pre{white-space:pre-wrap;font:inherit}a{color:inherit}</style><a href="./">← Play recording</a><pre>'+html.escape(details)+'</pre><a href="recording.json">Provenance &amp; integrity hash</a> · <a href="recordings/'+name+'" download>Download recording</a></html>'
    (out/'model.html').write_text(model,encoding='utf-8');(out/'.nojekyll').write_text('')
    files=['index.html','model.html','recording.json','README.txt','.nojekyll','site-files.json','recordings/'+name]
    files+=['web/'+f for f in web_files]
    files+=['web/assets/cells/'+str(p.relative_to(ROOT/'web/assets/cells')).replace('\\','/') for p in (ROOT/'web/assets/cells').rglob('*') if p.is_file()]
    (out/'site-files.json').write_text(json.dumps(sorted(files),indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(output=str(out),status=manifest['status'],requests=usage['requests'],frames=manifest['frames'],bytes=len(raw))))
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--recording',type=Path,required=True)
    p.add_argument('--output',type=Path,default=ROOT/'site');p.add_argument('--preview-running',action='store_true')
    a=p.parse_args();build(a.recording,a.output,a.preview_running)

if __name__=='__main__':main()
