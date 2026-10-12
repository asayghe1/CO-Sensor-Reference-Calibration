"""Full-precision evaluation AFTER replay; conditional resampling of fixed losses."""
from pathlib import Path
import numpy as np
import json,gzip,csv,hashlib
import sys
from context import FROZEN, DEV, BUILD, report
sys.path.insert(0,str(FROZEN/'co_revision_execution_v2/work/src'))
from revision_analyses_checked import stratum_metrics
W=FROZEN/'co_revision_execution_v2/work';E=DEV;OUT=BUILD/'development_recomputed';OUT.mkdir(exist_ok=True)
def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def write(path,rows):
 path=OUT/path.name
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def save(path,obj):path.write_text(json.dumps(obj,allow_nan=False,indent=2))
def scalar(x):return x.item() if isinstance(x,np.generic) else x

def session_effects(delta):
 days=['D6','D8','D10']
 if set(delta)!=set(days):raise ValueError('missing named assessment session')
 return days,np.array([delta[s].mean(axis=0) for s in days])
def arm_identity(r):
 return tuple(r[k] for k in ('model','bounds','estimator','schedule','budget','scope','schedule_id','schedule_driver'))

SCOPES={'ALL':np.arange(12),'Figaro':np.arange(6),'FIS':np.arange(6,12)}

def main():
 runs=[]
 for p in sorted(E.glob('runs_*.json.gz')):
  for r in read(p):
   # Keep heavy access/update logs in their archives; evaluator needs only frozen arrays.
   runs.append({k:v for k,v in r.items() if k in ('identity','query','reference','predictions','error_lower','error_upper','contradiction','source')})
 b0={}
 for r in runs:
  if r['identity']['budget']==0:
   for est,p in r['predictions'].items():b0[(r['identity']['model'],r['identity']['bounds'],r['identity']['session'],est)]=np.array(p)
 metricrows=[];configrows=[];timing=[];intervals=[];cross=[];losses={};runarmcounts=0
 for r in runs:
  meta=r['identity'];q=np.array(r['query'],bool);y=np.array(r['reference']);lo=np.array(r['error_lower']);hi=np.array(r['error_upper']);bad=np.array(r['contradiction'],bool);cons=np.array(r['predictions']['consensus'])
  timing.append({**meta,'total':int(q.sum()),'last10':int(q[-10:].sum()),'at_final':int(q[-1]),'horizon':100})
  for est,pp in r['predictions'].items():
   p=np.array(pp);own=b0[(meta['model'],meta['bounds'],meta['session'],est)];runarmcounts+=1
   for scope,cols in SCOPES.items():
    a=np.abs(p[:,cols]-y[:,None]);path=np.column_stack([a.mean(axis=1),*[(a>t).mean(axis=1) for t in (.5,1.,2.)]])
    armkey=arm_identity({**meta,'estimator':est,'scope':scope})
    losses.setdefault(armkey,{}).setdefault(meta['session'],[]).append(path)
    for subset,mask in [('all',np.ones(100,bool)),('queried',q),('unqueried',~q)]:
     for band,bandmask in [('ALL',np.ones(100,bool)),('[0,5]',(y>=0)&(y<=5)),('(5,10]',(y>5)&(y<=10)),('(10,20]',(y>10)&(y<=20))]:
      sel=mask&bandmask;res=stratum_metrics(p[sel][:,cols],y[sel]);base=stratum_metrics(cons[sel][:,cols],y[sel]);historical=stratum_metrics(own[sel][:,cols],y[sel])
      metricrows.append({**meta,'estimator':est,'scope':scope,'subset':subset,'band':band,**res,**{'consensus_'+k:v for k,v in base.items()},**{'own_B0_'+k:v for k,v in historical.items()},'source':r['source']})
   for j,u in enumerate((1,2,3,4,5,6,8,9,10,11,12,13)):
    for subset,sel in [('all',np.ones(100,bool)),('queried',q),('unqueried',~q)]:configrows.append({**meta,'estimator':est,'config':j+1,'unit':u,'subset':subset,**stratum_metrics(p[sel][:,[j]],y[sel]),'source':r['source']})
   if est in ('consensus','midpoint','projection'):
    center=cons-p;rad=np.maximum(np.abs(lo-center),np.abs(hi-center));absr=np.abs(p-y[:,None]);assured=(rad<=1)&~bad
    for scope,cols in SCOPES.items():
     for subset,sel in [('all',np.ones(100,bool)),('queried',q),('unqueried',~q)]:
      rr=rad[sel][:,cols];aa=assured[sel][:,cols];bb=bad[sel][:,cols];error=absr[sel][:,cols];non=(cons-y[:,None]<lo)|(cons-y[:,None]>hi)
      intervals.append({**meta,'estimator':est,'scope':scope,'subset':subset,'outputs':int(rr.size),'width_mean':float((hi-lo)[sel][:,cols].mean()) if rr.size else None,'reported_noncontainment':int(non[sel][:,cols].sum()),'contradiction_count':int(bb.sum()),'assured_count':int(aa.sum()),'false_assured_count':int((aa&(error>1)).sum())})
  if meta['bounds']=='slope95':
   # Raw max/min intersections reconstructed and independently archived in prior correction.
   diagpath=W.parents[1]/f"reference_budget_review_correction_v1/diagnostics/slope95_{meta['model']}_{meta['session']}.json.gz"
   if not hasattr(main,'diag'):main.diag={}
   dk=str(diagpath)
   if dk not in main.diag:main.diag[dk]=read(diagpath)
   match=[d for d in main.diag[dk] if d['metadata']['budget']==meta['budget'] and (meta['budget']==0 or (d['metadata']['policy']==('proposed' if meta['schedule']=='envelope' else meta['schedule']) and d['metadata']['seed']==meta['seed']))]
   d=match[0];rawlo=np.array(d['arrays']['raw_lower']);rawhi=np.array(d['arrays']['raw_upper']);e=cons-y[:,None];rawout=(e<rawlo)|(e>rawhi);hullout=(e<lo)|(e>hi);assured=((hi-lo)/2<=1)&~bad
   assert np.array_equal(rawlo>rawhi,bad)
   for contradiction in (False,True):
    for raw_non in (False,True):
     for hull_non in (False,True):
      for assurance in (False,True):
       mask=(bad==contradiction)&(rawout==raw_non)&(hullout==hull_non)&(assured==assurance);idx=np.argwhere(mask)
       cross.append({**meta,'contradiction':int(contradiction),'raw_noncontainment':int(raw_non),'hull_noncontainment':int(hull_non),'assurance1':int(assurance),'count':len(idx),'identity_list':';'.join(f"{meta['session']}_E{i+1}_C{j+1}" for i,j in idx)})
 write(E/'METRICS_BY_RUN_FAMILY_BAND_SUBSET.csv',metricrows);write(E/'METRICS_BY_CONFIGURATION.csv',configrows);write(E/'QUERY_TIMING_BY_RUN.csv',timing);write(E/'INTERVAL_DIAGNOSTICS.csv',intervals);write(E/'SLOPE95_CROSSTAB.csv',cross)
 print('metrics exported',len(metricrows),len(configrows),flush=True)
 # Exact seed then session weights. Every stratum/session is retained, including NA.
 fields=[k for k in stratum_metrics(np.zeros((1,1)),np.zeros(1)) if k not in ('exposures','outputs')]
 groups={}
 for r in metricrows:
  key=tuple(r[k] for k in ('model','bounds','estimator','schedule','budget','scope','subset','band','schedule_id','schedule_driver'))
  groups.setdefault(key,{}).setdefault(r['session'],[]).append(r)
 aggregate=[];sessionrows=[]
 for key,days in groups.items():
  meta=dict(zip(('model','bounds','estimator','schedule','budget','scope','subset','band','schedule_id','schedule_driver'),key));ds=[]
  for day,rr in sorted(days.items()):
   row={**meta,'session':day,'seed_count':len(rr)}
   for k in ('outputs','exposures',*fields,*['consensus_'+f for f in ('mae','exceed_rate_1.0','exceed_count_1.0')],*['own_B0_'+f for f in ('mae','exceed_rate_1.0','exceed_count_1.0')]):
    vals=[r[k] for r in rr];row[k]=float(np.mean(vals)) if all(v is not None for v in vals) else None
   sessionrows.append(row);ds.append(row)
  out={**meta,'sessions':len(ds)}
  for k in ('outputs','exposures',*fields,*['consensus_'+f for f in ('mae','exceed_rate_1.0','exceed_count_1.0')],*['own_B0_'+f for f in ('mae','exceed_rate_1.0','exceed_count_1.0')]):
   vals=[r[k] for r in ds];out[k]=(float(sum(vals)) if k in ('outputs','exposures') or 'count' in k or k=='abs_sum' else float(np.mean(vals))) if all(v is not None for v in vals) else None
  if all(r['rmse'] is not None for r in ds):out['rmse']=float(np.sqrt(np.mean([r['rmse']**2 for r in ds])))
  aggregate.append(out)
 write(E/'AGGREGATE_METRICS.csv',aggregate);write(E/'SESSION_METRICS.csv',sessionrows)
 # Family exceedance shares use averaged seed numerators/day, never replay counts.
 shares=[]
 for r in aggregate:
  if r['scope']!='ALL' or r['band']!='ALL':continue
  key=tuple(r[k] for k in ('model','bounds','estimator','schedule','budget','subset','schedule_id','schedule_driver'))
  for family in ('Figaro','FIS'):
   f=next(a for a in aggregate if tuple(a[k] for k in ('model','bounds','estimator','schedule','budget','subset','schedule_id','schedule_driver'))==key and a['scope']==family and a['band']=='ALL')
   denom=r['exceed_count_1.0'];shares.append({**dict(zip(('model','bounds','estimator','schedule','budget','subset','schedule_id','schedule_driver'),key)),'family':family,'seed_day_weighted_numerator':f['exceed_count_1.0'],'seed_day_weighted_denominator':denom,'share':f['exceed_count_1.0']/denom if denom else None})
 write(E/'EXCEEDANCE_SHARES.csv',shares)

if __name__=='__main__':main()
