"""Create a deterministic source/evidence ZIP, excluding build output and caches.
The checksum sidecar is outside the ZIP to avoid a self-referential archive hash.
"""
import argparse,hashlib,zipfile
from pathlib import Path
from scan_release import ROOT,public_files,scan_tree

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--output',type=Path,default=ROOT.parent/'CO_Measurement_GitHub_Reproducibility_v1.zip')
 args=parser.parse_args();target=args.output.resolve()
 if target.is_relative_to(ROOT):raise SystemExit('Place the ZIP outside the repository folder.')
 scan=scan_tree(ROOT)
 if scan['findings']:raise SystemExit('Release scan failed; run scripts/scan_release.py for relative-path findings.')
 paths=list(public_files(ROOT))
 hashes=ROOT/'RELEASE_FILES_SHA256.txt'
 expected={}
 for line in hashes.read_text().splitlines():
  digest,name=line.split('  ',1);expected[name]=digest
 actual={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p!=hashes}
 if actual!=expected:raise SystemExit('Release checksum manifest mismatch; do not package an unverified edit.')
 with zipfile.ZipFile(target,'w') as archive:
  for p in paths:
   info=zipfile.ZipInfo('github_release_v1/'+p.relative_to(ROOT).as_posix(),date_time=(2026,10,12,0,0,0))
   info.create_system=3;info.external_attr=(0o100644<<16)
   info.compress_type=zipfile.ZIP_STORED if p.suffix in ('.gz','.npz','.joblib','.pdf','.png') else zipfile.ZIP_DEFLATED
   archive.writestr(info,p.read_bytes())
 with zipfile.ZipFile(target) as archive:
  assert archive.testzip() is None
  assert len(archive.namelist())==len(paths)
 digest=hashlib.sha256(target.read_bytes()).hexdigest()
 target.with_name(target.name+'.sha256').write_text(digest+'  '+target.name+'\n')
 print(target.name, target.stat().st_size, 'bytes; SHA256',digest)
if __name__=='__main__':main()
