"""Optional opaque hash verification of a separately downloaded public archive.
Does not extract or parse any raw sensor values. Not used by reproduce.py.
"""
import argparse,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('archive',type=Path)
 args=parser.parse_args()
 expected=json.loads((ROOT/'data/DATASET_MANIFEST.json').read_text())
 def sha(stream):
  h=hashlib.sha256()
  for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
  return h.hexdigest()
 with args.archive.open('rb') as f:observed=sha(f)
 if observed!=expected['outer_sha256']:raise SystemExit('Archive SHA256 differs from the historically verified archive. Stop; do not treat this as the frozen dataset version.')
 with zipfile.ZipFile(args.archive) as archive:
  with archive.open(expected['nested_member']) as f:observed=sha(f)
 if observed!=expected['nested_sha256']:raise SystemExit('Nested archive SHA256 mismatch.')
 print('Outer and nested archive hashes match the historical manifest. No sensor values parsed.')
if __name__=='__main__':main()
