"""Reporting-only saved-output arithmetic audit. No raw access or replay/refit."""
from pathlib import Path
import numpy as np
import csv,json,hashlib,datetime,os
from context import FROZEN as R, C5 as O, REPORTS as W
E=O/'c5_execution_v1';P=E/'replays';PROTOCOL='4de22fff8678773f3fb3ba23198431947efe3c54145b8452ddec2ebf036c40bc'
assert any(json.loads(s)['stage']=='ALL_FINAL_REPLAY_OUTPUTS_COMMITTED' for s in (E/'EXECUTION_LOG.jsonl').read_text().splitlines())
commit=json.loads((E/'FINAL_REPLAY_COMMIT_MANIFEST.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for item in commit['files']:assert sha(E/item['path'])==item['sha256'],item['path']
assert sha(O/'C5_FROZEN_PROTOCOL.md')==PROTOCOL
for row in json.loads((O/'C5_CODE_AND_ARTIFACT_HASHES.json').read_text()):assert sha(R/row['path'])==row['sha256'],row['path']
references={int(k):np.array(v) for k,v in json.loads((E/'REFERENCES_FOR_EVALUATOR_ONLY.json').read_text()).items()}
assert set(references)=={11,12,13} and all(v.shape==(100,) for v in references.values())
expected_runs={(d,'none',0,487) for d in (11,12,13)}|{(d,p,b,s) for d in (11,12,13) for p in ('periodic','random','confidence','envelope','rlsvar') for b in (5,10,20) for s in (range(487,497) if p=='random' else (487,))}
runpaths={}
import re
for path in P.glob('D*.json'):
 m=re.fullmatch(r'D(\d+)_(\w+)_B(\d+)_S(\d+)\.json',path.name);assert m;key=(int(m[1]),m[2],int(m[3]),int(m[4]));assert key not in runpaths;runpaths[key]=path
assert set(runpaths)==expected_runs
baselines={d:json.loads(runpaths[(d,'none',0,487)].read_text()) for d in (11,12,13)}
scopes=[('ALL',slice(None)),('Figaro',slice(0,6)),('FIS',slice(6,12))]+[(f'C{j+1}',slice(j,j+1)) for j in range(12)]
metrics=[];events=0;purchase_states=0;maxmetric=0.;numfail=[]
for (d,policy,budget,seed),path in sorted(runpaths.items()):
 run=json.loads(path.read_text());pred={k:np.array(v) for k,v in run['predictions'].items()};assert set(pred)=={'consensus','midpoint','projection','offset','affine','affine_l095','affine_l090'};assert all(a.shape==(100,12) and np.isfinite(a).all() for a in pred.values())
 q=np.array(run['query'],bool);assert q.shape==(100,) and q.sum()==budget
 if policy=='periodic':assert set(np.flatnonzero(q))==set(np.floor((np.arange(budget)+.5)*100/budget).astype(int))
 if policy=='random':assert set(np.flatnonzero(q))==set(np.random.default_rng(seed).choice(100,budget,replace=False))
 lo=np.array(run['error_lower']);hi=np.array(run['error_upper']);rawlo=np.array(run['raw_error_lower']);rawhi=np.array(run['raw_error_upper']);bad=np.array(run['contradiction'],bool);assert np.array_equal(rawlo>rawhi,bad)
 # Every session and schedule must reset to the identical saved D10-initialized state.
 assert run['initial']==baselines[11]['initial']
 prequery=path.with_name(path.stem+'.prequery.jsonl');record=[json.loads(s) for s in prequery.read_text().splitlines()];assert len(record)==100
 for i,event in enumerate(record):
  log=run['access_log'][i];assert event['event']['stage']=='prediction_frozen' and event['event']['index']==i and event['event']['past']==np.flatnonzero(q[:i]).tolist();assert event['query']==bool(q[i])
  for estimator in pred:np.testing.assert_array_equal(event['predictions'][estimator],pred[estimator][i])
  for field in ('error_lower','error_upper','raw_error_lower','raw_error_upper','contradiction'):np.testing.assert_array_equal(event[field],run[field][i])
  hashpred=hashlib.sha256(np.array([pred[e][i] for e in pred]).tobytes()).hexdigest();assert hashpred==event['event']['prediction_sha256']==log['prediction_sha256']
  encoded=json.dumps(event,sort_keys=True,allow_nan=False).encode();assert hashlib.sha256(encoded).hexdigest()==log['snapshot_sha256'];events+=1
 assert [v['index'] for v in run['purchases']]==np.flatnonzero(q).tolist()
 for purchase in run['purchases']:
  assert purchase['reference']==references[d][purchase['index']]
  for name,states in purchase['state_after'].items():
   for state in states:
    assert np.isfinite(state['theta']).all() and np.isfinite(state['P']).all();purchase_states+=1
    if state['failures'] or not state['update_success']:numfail.append({'run':path.name,'estimator':name,'index':purchase['index'],'events':state['failure_events']})
 if run['numerical_failures']:numfail.append({'run':path.name,'total':run['numerical_failures']})
 y=references[d][:,None];c=pred['consensus'];base=baselines[d]['predictions'];rawnon=(c-y<rawlo)|(c-y>rawhi);non=(c-y<lo)|(c-y>hi)
 for est,p in pred.items():
  for scope,cols in scopes:
   for subset,mask in [('all',np.ones(100,bool)),('queried',q),('unqueried',~q)]:
    residual=(p-y)[mask,cols];a=abs(residual);n=a.size
    row={'day':d,'policy':policy,'budget':budget,'seed':seed,'estimator':est,'scope':scope,'subset':subset,'exposures':int(mask.sum()),'outputs':n,'abs_sum':float(a.sum()),'sq_sum':float((residual**2).sum()),'signed_sum':float(residual.sum()),'mae':float(a.mean()) if n else None,'rmse':float(np.sqrt((residual**2).mean())) if n else None,'bias':float(residual.mean()) if n else None,'numerical_failures':run['numerical_failures']}
    for name,bp in [('own_B0',np.array(base[est])),('same_subset_consensus',c)]:
     ab=abs((bp-y)[mask,cols]);row[name+'_mae']=float(ab.mean()) if n else None
     for tol in (.5,1.,2.):row[name+f'_exceed_count_{tol}']=int((ab>tol).sum())
    for tol in (.5,1.,2.):
     row[f'exceed_count_{tol}']=int((a>tol).sum());row[f'exceed_rate_{tol}']=float((a>tol).mean()) if n else None
     if est in ('consensus','midpoint','projection'):
      center=c-p;radius=np.maximum(abs(lo-center),abs(hi-center));flag=((radius<=tol)&~bad)[mask,cols];f=int((flag&(a>tol)).sum());ass=int(flag.sum());row.update({f'false_{tol}':f,f'assured_{tol}':ass,f'false_over_assured_{tol}':f/ass if ass else None,f'false_over_all_{tol}':f/n if n else None})
    row.update(reported_noncontainment=int(non[mask,cols].sum()),raw_noncontainment=int(rawnon[mask,cols].sum()),queries_last10=int(q[-10:].sum()),query_at_final=int(q[-1]),contradictions=int(bad[mask,cols].sum()),width_mean=float((hi-lo)[mask,cols].mean()) if n else None);metrics.append(row)
keys=('day','policy','budget','seed','estimator','scope','subset');actual={tuple(r[k] for k in keys):r for r in json.loads((P/'METRICS.json').read_text())};assert len(actual)==len(metrics)==40635
for row in metrics:
 source=actual[tuple(row[k] for k in keys)];assert set(source)==set(row)
 for field,v in row.items():
  w=source[field]
  if isinstance(v,float):maxmetric=max(maxmetric,abs(v-w));assert np.isclose(v,w,atol=1e-12,rtol=1e-13),(field,v,w)
  else:assert v==w,(field,v,w)
# Independent equal-day, within-day seed weighting for aggregate fields.
summary=json.loads((P/'AGGREGATE.json').read_text());groups={};aggkeys=('estimator','scope','subset','policy','budget')
for r in metrics:groups.setdefault(tuple(r[k] for k in aggkeys),{}).setdefault(r['day'],[]).append(r)
for original in summary:
 days=groups[tuple(original[k] for k in aggkeys)];assert set(days)=={11,12,13}
 countfields=[k for k in next(iter(days.values()))[0] if 'count' in k or (k.startswith(('false_','assured_')) and 'over' not in k) or k in ('outputs','exposures','abs_sum','sq_sum','signed_sum','reported_noncontainment','raw_noncontainment','queries_last10','query_at_final','contradictions','numerical_failures')]
 vals={k:sum(sum(v[k] for v in rr)/len(rr) for rr in days.values()) for k in countfields}
 for k,v in vals.items():assert np.isclose(original[k],v,atol=1e-11,rtol=1e-13),(k,v,original[k])
 n=vals['outputs']
 for k,v in [('mae',vals['abs_sum']/n if n else None),('rmse',float(np.sqrt(vals['sq_sum']/n)) if n else None),('bias',vals['signed_sum']/n if n else None)]:
  assert original[k] is None if v is None else np.isclose(original[k],v,atol=1e-12,rtol=1e-13)
 for tol in (.5,1.,2.):
  rate=vals[f'exceed_count_{tol}']/n if n else None;assert original[f'exceed_rate_{tol}'] is None if rate is None else np.isclose(original[f'exceed_rate_{tol}'],rate,atol=1e-12,rtol=1e-13)
  if f'false_{tol}' in vals:
   f=vals[f'false_{tol}'];ass=vals[f'assured_{tol}'];v=f/ass if ass else None;w=original[f'false_over_assured_{tol}'];assert w is None if v is None else np.isclose(w,v,atol=1e-12,rtol=1e-13)
result={'status':'PASS','protocol_sha256':PROTOCOL,'replays':129,'prequery_events':events,'metric_rows':len(metrics),'purchase_states_checked':purchase_states,'maximum_run_metric_absolute_difference':maxmetric,'recorded_numerical_failure_events':numfail,'frozen_hashes_and_prior_preservation':'PASS','excluded_sensor_values_parsed':False,'no_refit_or_replay':True,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
result['verification_method']='Automated saved-output arithmetic and causal-log check; no raw access or replay';result['raw_final_payloads_reopened']=False
(W/'SAVED_OUTPUT_VERIFICATION.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
