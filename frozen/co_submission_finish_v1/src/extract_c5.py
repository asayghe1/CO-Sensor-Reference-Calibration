"""Inactive opaque extractor: only exact final members after authorization.
No CSV payload parsing; excluded sensor columns remain unconverted.
"""
from pathlib import Path
import argparse,hashlib,json,zipfile,io,re
O=Path(__file__).resolve().parents[1];R=O.parent

def main():
 a=argparse.ArgumentParser();a.add_argument('--explicit-c5-authorization',action='store_true');a.add_argument('--protocol-sha256',required=True);a.add_argument('--output-directory',type=Path,required=True);args=a.parse_args()
 if not args.explicit_c5_authorization:raise PermissionError('Explicit C5 authorization required')
 protocol=(O/'C5_FROZEN_PROTOCOL.md').read_bytes()
 if hashlib.sha256(protocol).hexdigest()!=args.protocol_sha256:raise ValueError('authorized protocol hash mismatch')
 mb=(O/'C5_CODE_AND_ARTIFACT_HASHES.json').read_bytes();expected=re.search(rb'Artifact-manifest SHA256: `([0-9a-f]{64})`',protocol).group(1).decode()
 if hashlib.sha256(mb).hexdigest()!=expected:raise ValueError('manifest integrity')
 for v in json.loads(mb):
  if hashlib.sha256((R/v['path']).read_bytes()).hexdigest()!=v['sha256']:raise ValueError('frozen artifact integrity')
 m=json.loads((O/'C5_INPUT_MANIFEST.json').read_text());outer=(R/m['archive']).read_bytes()
 if hashlib.sha256(outer).hexdigest()!=m['outer_sha256']:raise ValueError('outer hash')
 with zipfile.ZipFile(io.BytesIO(outer)) as z:nested=z.read(m['nested_member'])
 if hashlib.sha256(nested).hexdigest()!=m['nested_sha256']:raise ValueError('nested hash')
 args.output_directory.mkdir(exist_ok=False)
 with zipfile.ZipFile(io.BytesIO(nested)) as z:
  for s in m['sessions']:
   if s['day'] not in (11,12,13):continue
   name=s['file'];entry=next(v for v in m['raw_inventory'] if v['name']==name);info=z.getinfo(name)
   if info.file_size!=entry['bytes'] or info.CRC!=entry['crc32']:raise ValueError('member inventory integrity')
   data=z.read(name)
   if hashlib.sha256(data).hexdigest()!=entry['sha256']:raise ValueError('member hash')
   (args.output_directory/name).write_bytes(data)
if __name__=='__main__':main()
