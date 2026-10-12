from pathlib import Path
import json,numpy as np
W=Path(__file__).resolve().parent;E=W.parent/'c5_execution_v1';M=json.loads((E/'INDEPENDENT_METRICS.json').read_text());A=json.loads((E/'replays/AGGREGATE.json').read_text());C=json.loads((E/'replays/PRIMARY_CONTRASTS.json').read_text());groups={};keys=('estimator','scope','subset','policy','budget')
for row in M:groups.setdefault(tuple(row[k] for k in keys),{}).setdefault(row['day'],[]).append(row)
def same(v,w):
 if v is None or w is None:assert v is None and w is None
 else:assert np.isclose(v,w,atol=1e-12,rtol=1e-13),(v,w)
for r in A:
 days=groups[tuple(r[k] for k in keys)];n=r['outputs']
 for name in ('own_B0','same_subset_consensus'):same(r[name+'_mae'],float(np.mean([np.mean([v[name+'_mae'] for v in rr]) for rr in days.values()])) if n else None)
 same(r['width_mean'],float(np.mean([np.mean([v['width_mean'] for v in rr]) for rr in days.values()])) if n else None)
 for day,rr in days.items():
  same(r['day_mae'][str(day)],float(np.mean([v['mae'] for v in rr])) if n else None);same(r['day_p1'][str(day)],float(np.mean([v['exceed_rate_1.0'] for v in rr])) if n else None)
  ranges=[min(v['mae'] for v in rr),max(v['mae'] for v in rr)] if n else None
  if ranges is None:assert r['seed_mae_range_by_day'][str(day)] is None
  else:
   for x,y in zip(ranges,r['seed_mae_range_by_day'][str(day)]):same(x,y)
 for tol in (.5,1.,2.):
  if f'false_{tol}' in r:same(r[f'false_over_all_{tol}'],r[f'false_{tol}']/n if n else None)
for contrast in C:
 historical=contrast['comparison']=='historical';policy='none' if historical else 'envelope';budget=0 if historical else 20;base_est='consensus' if historical else 'affine';criteria=[];uniform=[]
 for cell in contrast['cells']:
  scope=cell['scope'];a=next(r for r in A if r['estimator']=='affine' and r['scope']==scope and r['subset']=='all' and r['policy']==policy and r['budget']==budget);b=next(r for r in A if r['estimator']==base_est and r['scope']==scope and r['subset']=='all' and r['budget']==0)
  same(cell['mae_change'],a['mae']-b['mae']);same(cell['p1_change'],a['exceed_rate_1.0']-b['exceed_rate_1.0'])
  for d in ('11','12','13'):same(cell['day_mae_change'][d],a['day_mae'][d]-b['day_mae'][d]);same(cell['day_p1_change'][d],a['day_p1'][d]-b['day_p1'][d])
  criterion=cell['mae_change']<=0 and cell['p1_change']<0;criteria.append(criterion);uniform.append(criterion and all(v<=0 for v in cell['day_mae_change'].values()) and all(v<=0 for v in cell['day_p1_change'].values()))
 assert contrast['descriptive_benefit_rule_met']==all(criteria);assert contrast['uniform_improvement_rule_met']==all(uniform)
(W/'AGGREGATE_AND_CONTRAST_RECHECK.json').write_text(json.dumps({'status':'PASS','aggregate_rows':len(A),'primary_contrasts':len(C),'all_aggregate_fields_verified':True,'no_replay_or_refit':True},indent=2));print('Aggregate fields and primary contrasts: PASS')
