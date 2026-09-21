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
  for name in names:z.write(ROOT/name,'VirtualTissue-LN-0.2.0/'+name)
 with zipfile.ZipFile(site,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted((ROOT/'site').rglob('*')):
   if p.is_file():z.write(p,str(p.relative_to(ROOT/'site')))
 sums={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,site)}
 (dist/'SHA256SUMS.json').write_text(json.dumps(sums,indent=2)+'\n')
 print(json.dumps(sums))
if __name__=='__main__':main()
