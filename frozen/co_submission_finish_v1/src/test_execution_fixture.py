"""Entry-point orchestration fixture; no raw/final file is opened."""
from pathlib import Path
import tempfile,json,hashlib,sys,shutil
import numpy as np
import execute_c5 as executor
O=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(dir=O) as td:
 root=Path(td);shutil.copy2(O/'D10_INITIALIZATION.npz',root/'D10_INITIALIZATION.npz');mb=b'[]';(root/'C5_CODE_AND_ARTIFACT_HASHES.json').write_bytes(mb);protocol=('SOFTWARE FIXTURE ONLY\nArtifact-manifest SHA256: `'+hashlib.sha256(mb).hexdigest()+'`\n').encode();(root/'C5_FROZEN_PROTOCOL.md').write_bytes(protocol)
 executor.O=root;opened=[];calls=[]
 def prepare(path,day,authorized):
  assert authorized and path.name==executor.FILES[day];opened.append(day)
  y=np.linspace(0,20,100);return {'consensus':np.tile(y[:,None],(1,12))},y
 executor.prepare_session=prepare
 def fake_run(obs,cal,y,budget,policy,seed,log_path):
  calls.append((budget,policy,seed));pred={e:obs['consensus'].copy() for e in ('consensus','midpoint','projection','offset','affine','affine_l095','affine_l090')};q=np.zeros(100,bool);q[:budget]=True;log_path.write_text('FIXTURE ONLY\n')
  return {'predictions':pred,'query':q,'error_lower':np.full((100,12),-1.),'error_upper':np.full((100,12),1.),'contradiction':np.zeros((100,12),bool),'numerical_failures':0}
 executor.run_session=fake_run
 sys.argv=['execute_c5.py','--explicit-c5-authorization','--protocol-sha256',hashlib.sha256(protocol).hexdigest(),'--input-directory',str(root/'NONEXISTENT_FIXTURE_INPUT'),'--output-directory',str(root/'output')]
 executor.main();assert opened==[11,12,13] and len(calls)==129
 primary=json.loads((root/'output/PRIMARY_CONTRASTS.json').read_text());assert len(primary)==2 and all(not p['descriptive_benefit_rule_met'] for p in primary)
 summary=json.loads((root/'output/AGGREGATE.json').read_text());assert next(r for r in summary if r['budget']==0 and r['subset']=='queried')['mae'] is None
print('Entry-point orchestration/aggregation fixture PASS; no final file opened')
