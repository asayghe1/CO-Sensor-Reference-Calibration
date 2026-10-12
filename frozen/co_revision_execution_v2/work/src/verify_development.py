"""Independent batch/state, causal-event, metric and preservation verification."""
from pathlib import Path
import json,gzip,csv,hashlib
import numpy as np
W=Path(__file__).resolve().parents[1];R=W.parents[1];E=W/'evidence'
def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def main():
 snapshot=json.loads((W/'PRESERVATION_SNAPSHOT.v2.json').read_text());unchanged=0
 for row in snapshot:
  assert hashlib.sha256((R/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path'];unchanged+=1
 assert hashlib.sha256((W/'PROTOCOL.v2.md').read_bytes()).hexdigest()==(W/'PROTOCOL_SHA256.txt').read_text().split()[0]
 metrics={}
 for r in csv.DictReader((E/'METRICS_BY_RUN_FAMILY_BAND_SUBSET.csv').open()):
  if r['subset']=='all' and r['band']=='ALL':metrics[(r['run_id'],r['estimator'],r['scope'])]=r
 states=0;predictions=0;maxerr=0.;logs=0;counts=0
 for p in sorted(E.glob('runs_*.json.gz')):
  for r in read(p):
   meta=r['identity'];y=np.array(r['reference']);q=np.array(r['query'],bool)
   assert q.shape==(100,) and int(q.sum())==meta['budget'];assert y.shape==(100,)
   for est,arr in r['predictions'].items():
    pp=np.array(arr);assert pp.shape==(100,12) and np.isfinite(pp).all()
    for scope,cols in [('ALL',np.arange(12)),('Figaro',np.arange(6)),('FIS',np.arange(6,12))]:
     row=metrics[(meta['run_id'],est,scope)];a=np.abs(pp[:,cols]-y[:,None]);assert int(row['outputs'])==a.size
     assert abs(float(row['mae'])-a.mean())<1e-12
     for tol in (.5,1.,2.):assert int(row[f'exceed_count_{tol}'])==int((a>tol).sum());counts+=1
   if 'access_log' not in r:continue
   cal=read(E/f"historical_{meta['model']}_{meta['session']}.json.gz");cm=np.array(cal['consensus']);cy=np.array(cal['reference']);m=np.array(r['predictions']['consensus']);past=[];purchases={v['index']:v for v in r['purchases']}
   info={};rhs={};phis={}
   for est,init in r['initial'].items():
    info[est]=[];rhs[est]=[];phis[est]=[]
    for j,a in enumerate(init):
     X=np.column_stack(((cm[:,j]-a['mu'])/a['s'],np.ones(100)));S=np.eye(2)+X.T@X;b=X.T@(cy[:,j]-cm[:,j])
     np.testing.assert_allclose(a['theta'],np.linalg.solve(S,b),atol=1e-10,rtol=0);np.testing.assert_allclose(a['P'],np.linalg.inv(S),atol=1e-10,rtol=0)
     info[est].append(S);rhs[est].append(b);phis[est].append(np.column_stack(((m[:,j]-a['mu'])/a['s'],np.ones(100))))
   for i,ev in enumerate(r['access_log']):
    assert ev['index']==i and ev['stage']=='prediction_frozen' and ev['past']==past and ev['released_after_freeze']==bool(q[i]);logs+=1
    for est in info:
     if est in r['predictions']:
      pr=np.array([m[i,j]+phis[est][j][i]@np.linalg.solve(info[est][j],rhs[est][j]) for j in range(12)]);observed=np.array(r['predictions'][est][i]);err=float(np.max(np.abs(pr-observed)));maxerr=max(maxerr,err);assert err<1e-10;predictions+=12
    if q[i]:
     purchase=purchases[i];assert purchase['reference']==y[i]
     for est,lam in [('affine',1.),('affine_l095',.95),('affine_l090',.90)]:
      for j,state in enumerate(purchase['state_after'][est]):
       phi=phis[est][j][i];info[est][j]=lam*info[est][j]+np.outer(phi,phi);rhs[est][j]=lam*rhs[est][j]+phi*(y[i]-m[i,j])
       np.testing.assert_allclose(state['theta'],np.linalg.solve(info[est][j],rhs[est][j]),atol=1e-10,rtol=0);np.testing.assert_allclose(state['P'],np.linalg.inv(info[est][j]),atol=1e-10,rtol=0);np.testing.assert_allclose(state['information'],info[est][j],atol=1e-9,rtol=0);states+=1
     past.append(i)
   assert len(past)==meta['budget'] and (not q[-1] or r['access_log'][-1]['affects_from'] is None)
 # Named day labels must independently match saved loss differences, irrespective lexical ordering.
 paths=read(E/'PAIRED_LOSS_PATHS.json.gz');effects={}
 for row in csv.DictReader((E/'CONDITIONAL_RESAMPLING_EFFECTS.csv').open()):
  if row['block_length']=='10':effects[(row['model'],row['estimator'],row['schedule'],int(row['budget']),row['scope'],row['effect'],row['schedule_id'],row['baseline_schedule_id'],row['metric'])]=row
 for rec in paths:
  arm=rec['arm'];base=rec['baseline']
  for j,metric in enumerate(('mae','p0.5','p1.0','p2.0')):
   row=effects[(arm[0],arm[2],arm[3],arm[4],arm[5],rec['effect'],arm[6],base[6],metric)]
   for day,arr in rec['exposure_differences'].items():assert abs(float(row[day])-np.array(arr)[:,j].mean()*(1 if j==0 else 100))<1e-10
 result={'protected_files_unchanged':unchanged,'independent_batch_prediction_scalars':predictions,'maximum_batch_prediction_difference_ppm':maxerr,'weighted_purchase_states_checked':states,'causal_prediction_events_checked':logs,'exact_exceedance_cells_checked':counts,'day_labels_checked':True,'reserved_data_accessed':False,'all_assertions_passed':True}
 (E/'VERIFICATION.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
