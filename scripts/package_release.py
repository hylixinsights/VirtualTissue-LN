#!/usr/bin/env python3
"""Package only explicitly allowlisted source and verified public static assets."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 dist=ROOT/'dist';dist.mkdir(exist_ok=True)
 names=json.loads((ROOT/'scripts/release_files.json').read_text())
 assert all(not x.startswith(('recordings/private/','.git/','.env')) or x=='.env.example' for x in names)
 source=dist/'VirtualTissue-LN-0.2.0-source.zip';site=dist/'VirtualTissue-LN-0.2.0-site.zip'
 with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
  for name in names:
   entry='VirtualTissue-LN-0.2.0/'+name
   z.write(ROOT/name,entry)
   if name.endswith('.command'):
    info=z.getinfo(entry);info.create_system=3;info.external_attr=0o100755<<16
 with zipfile.ZipFile(site,'w',zipfile.ZIP_DEFLATED) as z:
  allowlist=ROOT/'site/site-files.json'
  if allowlist.exists():
   for name in json.loads(allowlist.read_text(encoding='utf-8')):
    p=(ROOT/'site'/name).resolve()
    assert (ROOT/'site').resolve() in p.parents and p.is_file()
    z.write(p,name)
  else:
   for p in sorted((ROOT/'site').rglob('*')):
    if p.is_file():z.write(p,str(p.relative_to(ROOT/'site')))
 artifacts=[source,site]
 video=dist/'lymph-node-jev-highlights.mp4'
 if video.is_file():artifacts.append(video)
 sums={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts}
 (dist/'SHA256SUMS.json').write_text(json.dumps(sums,indent=2)+'\n')
 print(json.dumps(sums))
if __name__=='__main__':main()
