"""Inactive execution entry point. Requires explicit authorization flag.
Preparation/preflight NEVER invokes this entry point on final files.
"""
from pathlib import Path
import argparse,json,hashlib,sys,re
import numpy as np
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R),str(R/'co_revision_execution_v2/work/src')]
from c5_inputs import prepare_session,FILES
from c5_replay import run_session
from c5_evaluate import evaluate,aggregate,primary_contrasts

def serial(v):
 if isinstance(v,np.ndarray):return v.tolist()
 if isinstance(v,np.generic):return v.item()
 raise TypeError(type(v).__name__)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--explicit-c5-authorization',action='store_true');ap.add_argument('--protocol-sha256',required=True);ap.add_argument('--input-directory',type=Path,required=True);ap.add_argument('--output-directory',type=Path,required=True);a=ap.parse_args()
 if not a.explicit_c5_authorization:raise PermissionError('Explicit user C5 authorization required')
 # Verify frozen code/models/normalization before opening any final input.
 protocol=(O/'C5_FROZEN_PROTOCOL.md').read_bytes()
 if hashlib.sha256(protocol).hexdigest()!=a.protocol_sha256:raise ValueError('authorized protocol hash mismatch')
 expected_manifest=re.search(rb'Artifact-manifest SHA256: `([0-9a-f]{64})`',protocol).group(1).decode()
 manifest_bytes=(O/'C5_CODE_AND_ARTIFACT_HASHES.json').read_bytes()
 if hashlib.sha256(manifest_bytes).hexdigest()!=expected_manifest:raise ValueError('artifact manifest integrity failure')
 manifest=json.loads(manifest_bytes)
 for item in manifest:
  if hashlib.sha256((R/item['path']).read_bytes()).hexdigest()!=item['sha256']:raise ValueError('frozen artifact integrity failure')
 a.output_directory.mkdir(exist_ok=False);metrics=[]
 for day in (11,12,13):
  obs,y=prepare_session(a.input_directory/FILES[day],day,authorized=True)
  z=np.load(O/'D10_INITIALIZATION.npz');cal={k:z[k].copy() for k in ('consensus','error','z','confidence','q')}
  arms=[('none',0,487)]+[(policy,b,seed) for b in (5,10,20) for policy in ('periodic','random','confidence','envelope','rlsvar') for seed in (range(487,497) if policy=='random' else (487,))]
  # All prediction paths complete before the evaluator sees this day's outcomes.
  saved=[]
  for policy,budget,seed in arms:
   name=f'D{day}_{policy}_B{budget}_S{seed}';run=run_session(obs,cal,y,budget,policy,seed,a.output_directory/(name+'.prequery.jsonl'))
   (a.output_directory/(name+'.json')).write_text(json.dumps(run,default=serial,allow_nan=False));saved.append((policy,budget,seed,run))
  for policy,budget,seed,run in saved:
   for row in evaluate(run,y,saved[0][3]):metrics.append({'day':day,'policy':policy,'budget':budget,'seed':seed,**row})
  # No reference-bearing replay state survives into the next day.
  del saved,obs,y,cal
 (a.output_directory/'METRICS.json').write_text(json.dumps(metrics,allow_nan=False));summary=aggregate(metrics);(a.output_directory/'AGGREGATE.json').write_text(json.dumps(summary,allow_nan=False));(a.output_directory/'PRIMARY_CONTRASTS.json').write_text(json.dumps(primary_contrasts(summary),allow_nan=False))
if __name__=='__main__':main()
