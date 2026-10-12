"""Post-freeze evaluator; never passes outcomes back to replay."""
import numpy as np

def evaluate(run,reference,baseline):
 y=np.asarray(reference)[:,None];q=np.asarray(run['query'],bool);c=np.asarray(run['predictions']['consensus']);lo=run['error_lower'];hi=run['error_upper'];bad=run['contradiction'];rows=[]
 for est,p in run['predictions'].items():
  for scope,cols in [('ALL',slice(None)),('Figaro',slice(0,6)),('FIS',slice(6,12))]+[(f'C{j+1}',slice(j,j+1)) for j in range(12)]:
   for subset,mask in [('all',np.ones(100,bool)),('queried',q),('unqueried',~q)]:
    e=(p-y)[mask,cols];n=e.size;a=abs(e)
    row={'estimator':est,'scope':scope,'subset':subset,'exposures':int(mask.sum()),'outputs':n,'abs_sum':float(a.sum()),'sq_sum':float((e*e).sum()),'signed_sum':float(e.sum()),'mae':float(a.mean()) if n else None,'rmse':float(np.sqrt((e*e).mean())) if n else None,'bias':float(e.mean()) if n else None,'numerical_failures':run['numerical_failures']}
    for base_name,base_p in [('own_B0',baseline['predictions'][est]),('same_subset_consensus',c)]:
     base_error=abs((base_p-y)[mask,cols]);row[base_name+'_mae']=float(base_error.mean()) if n else None
     for tolerance in (.5,1.,2.):row[base_name+f'_exceed_count_{tolerance}']=int((base_error>tolerance).sum())
    for tol in (.5,1.,2.):
     row[f'exceed_count_{tol}']=int((a>tol).sum());row[f'exceed_rate_{tol}']=float((a>tol).mean()) if n else None
     if est in ('consensus','midpoint','projection'):
      rad=np.maximum(abs(lo-(c-p)),abs(hi-(c-p)));flag=((rad<=tol)&~bad)[mask,cols];f=int((flag&(a>tol)).sum());ass=int(flag.sum())
      row.update({f'false_{tol}':f,f'assured_{tol}':ass,f'false_over_assured_{tol}':f/ass if ass else None,f'false_over_all_{tol}':f/n if n else None})
    row['reported_noncontainment']=int((((c-y<lo)|(c-y>hi))[mask,cols]).sum());row['raw_noncontainment']=int((((c-y<run.get('raw_error_lower',lo))|(c-y>run.get('raw_error_upper',hi)))[mask,cols]).sum());row['queries_last10']=int(q[-10:].sum());row['query_at_final']=int(q[-1]);row['contradictions']=int(bad[mask,cols].sum());row['width_mean']=float((hi-lo)[mask,cols].mean()) if n else None
    rows.append(row)
 return rows

def aggregate(rows):
 """Average seeds inside each day, then equal days; counts sum day means.
 Ratios use weighted numerators/denominators and preserve undefined cells.
 """
 grouped={}
 keys=('estimator','scope','subset','policy','budget')
 for r in rows:grouped.setdefault(tuple(r[k] for k in keys),{}).setdefault(r['day'],[]).append(r)
 out=[]
 for key,days in grouped.items():
  if set(days)!={11,12,13}:raise ValueError('missing final session: evaluation invalid')
  result=dict(zip(keys,key));count_fields=[k for k in next(iter(days.values()))[0] if 'count' in k or k.startswith(('false_','assured_')) and 'over' not in k or k in ('outputs','exposures','abs_sum','sq_sum','signed_sum','reported_noncontainment','raw_noncontainment','queries_last10','query_at_final','contradictions','numerical_failures')]
  for k in count_fields:result[k]=float(sum(np.mean([r[k] for r in rr]) for rr in days.values()))
  n=result['outputs'];result.update(mae=result['abs_sum']/n if n else None,rmse=float(np.sqrt(result['sq_sum']/n)) if n else None,bias=result['signed_sum']/n if n else None)
  for tol in (.5,1.,2.):
   result[f'exceed_rate_{tol}']=result[f'exceed_count_{tol}']/n if n else None
   if f'false_{tol}' in result:
    f=result[f'false_{tol}'];ass=result[f'assured_{tol}'];result[f'false_over_assured_{tol}']=f/ass if ass else None;result[f'false_over_all_{tol}']=f/n if n else None
  result['width_mean']=float(np.mean([np.mean([r['width_mean'] for r in rr]) for rr in days.values()])) if n else None
  for name in ('own_B0','same_subset_consensus'):
   result[name+'_mae']=float(np.mean([np.mean([r[name+'_mae'] for r in rr]) for rr in days.values()])) if n else None
  result['day_mae']={str(d):float(np.mean([r['mae'] for r in rr])) if n else None for d,rr in days.items()}
  result['day_p1']={str(d):float(np.mean([r['exceed_rate_1.0'] for r in rr])) if n else None for d,rr in days.items()}
  result['seed_mae_range_by_day']={str(d):[min(r['mae'] for r in rr),max(r['mae'] for r in rr)] if n else None for d,rr in days.items()}
  out.append(result)
 return out

def primary_contrasts(summary):
 out=[]
 for name,policy,budget,base_est in [('historical','none',0,'consensus'),('incremental','envelope',20,'affine')]:
  cells=[]
  for scope in ('ALL','Figaro','FIS'):
   a=next(r for r in summary if r['estimator']=='affine' and r['scope']==scope and r['subset']=='all' and r['policy']==policy and r['budget']==budget)
   b=next(r for r in summary if r['estimator']==base_est and r['scope']==scope and r['subset']=='all' and r['policy']=='none' and r['budget']==0)
   cells.append({'scope':scope,'mae_change':a['mae']-b['mae'],'p1_change':a['exceed_rate_1.0']-b['exceed_rate_1.0'],'day_mae_change':{d:a['day_mae'][d]-b['day_mae'][d] for d in a['day_mae']},'day_p1_change':{d:a['day_p1'][d]-b['day_p1'][d] for d in a['day_p1']}})
  out.append({'comparison':name,'cells':cells,'descriptive_benefit_rule_met':all(c['p1_change']<0 and c['mae_change']<=0 for c in cells),'uniform_improvement_rule_met':all(c['p1_change']<0 and c['mae_change']<=0 and all(x<=0 for x in c['day_mae_change'].values()) and all(x<=0 for x in c['day_p1_change'].values()) for c in cells)})
 return out
