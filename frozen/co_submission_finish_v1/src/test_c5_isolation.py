"""Preflight: development observables and altered-label fixtures only."""
from pathlib import Path
import sys,json,tempfile,hashlib
import numpy as np
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R),str(R/'co_revision_execution_v2/work/src'),str(Path(__file__).resolve().parent)]
from c5_replay import run_session
from reference_budget_study_v1.data import load_blocks
from reference_budget_study_v1.replay import ReferenceProvider
O=R/'co_submission_finish_v1';block=next(b for b in load_blocks(R) if b['model']=='RF' and b['day']==10)
obs=block['observables']
# C5 uses actual frozen D10 initialization, not rolling development calibration.
z=np.load(O/'D10_INITIALIZATION.npz');cal={k:z[k] for k in ('consensus','error','z','confidence','q')};y=block['outcomes']
checks=[];events=0
with tempfile.TemporaryDirectory(dir=O) as td:
 counter=0
 def run(policy,budget,seed,yy):
  global counter
  p=Path(td)/f'{counter}.jsonl';counter+=1
  out=run_session(obs,cal,yy,budget,policy,seed,p)
  events=[json.loads(s) for s in p.read_text().splitlines()];assert len(events)==100
  for i,e in enumerate(events):
   assert e['event']['index']==i and all(j<i for j in e['event']['past']);assert e['query']==bool(out['query'][i])
   for est in out['predictions']:np.testing.assert_array_equal(e['predictions'][est],out['predictions'][est][i])
  assert out['query'].sum()==budget
  return out
 for policy in ('periodic','random','confidence','envelope','rlsvar'):
  for budget in (0,5,10,20):
   seeds=range(487,497) if policy=='random' else (487,)
   for seed in seeds:
    a=run(policy,budget,seed,y);changed=y.copy();changed[~a['query']]+=10000;b=run(policy,budget,seed,changed)
    np.testing.assert_array_equal(a['query'],b['query'])
    for e in a['predictions']:np.testing.assert_array_equal(a['predictions'][e],b['predictions'][e])
    # First purchased reference cannot alter its own prediction or decision.
    if budget:
     at=int(np.flatnonzero(a['query'])[0]);alter=y.copy();alter[at]+=100;c=run(policy,budget,seed,alter)
     np.testing.assert_array_equal(a['query'][:at+1],c['query'][:at+1])
     for e in a['predictions']:np.testing.assert_array_equal(a['predictions'][e][:at+1],c['predictions'][e][:at+1])
    # Independent rerun after altered-label run tests no state/label carry.
    d=run(policy,budget,seed,y)
    np.testing.assert_array_equal(a['query'],d['query'])
    for e in a['predictions']:np.testing.assert_array_equal(a['predictions'][e],d['predictions'][e])
    checks.append({'policy':policy,'budget':budget,'seed':seed,'status':'PASS'})
    print(policy,budget,seed,'PASS',flush=True)
 provider=ReferenceProvider(y,5)
 for index in (0,99):
  try:provider.purchase(index)
  except PermissionError:pass
  else:raise AssertionError('unadvanced access')
 provider.advance(0);provider.purchase(0)
 try:provider.purchase(0)
 except PermissionError:pass
 else:raise AssertionError('duplicate purchase')
 try:run_session({**obs,'reference':y},cal,y,0,'none',487,Path(td)/'bad.jsonl')
 except ValueError:pass
 else:raise AssertionError('reference in observable schema')
(O/'ISOLATION_RESULTS.json').write_text(json.dumps({'status':'PASS','cases':checks,'checks':['immutable on-disk predictions, intervals and decisions before purchase','unpurchased-label invariance','purchased-current-label prefix invariance','fresh replay after perturbation: policy/budget/seed/session isolation','provider current-step and duplicate-purchase guards','observable reference-field rejection'],'source':'development D10 observables; frozen D10 initialization; altered-label fixtures','reserved_payloads_parsed':False},indent=2))
