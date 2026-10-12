from pathlib import Path
import gzip,json,csv
import numpy as np
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'co_submission_finish_v1'
rows=[]
for path in sorted((ROOT/'co_revision_execution_v2/work/evidence').glob('runs_*.json.gz')):
 for run in json.loads(gzip.decompress(path.read_bytes())):
  meta=run['identity']; y=np.array(run['reference'])[:,None]; cons=np.array(run['predictions']['consensus']);lo=np.array(run['error_lower']);hi=np.array(run['error_upper']);bad=np.array(run['contradiction'],bool);q=np.array(run['query'],bool)
  non=(cons-y<lo)|(cons-y>hi)
  for est in (e for e in ('consensus','midpoint','projection') if e in run['predictions']):
   p=np.array(run['predictions'][est]);center=cons-p;radius=np.maximum(abs(lo-center),abs(hi-center));error=abs(p-y)
   for tol in (.5,1.,2.):
    flag=(radius<=tol)&~bad; false=flag&(error>tol)
    for family,cols in [('ALL',slice(None)),('Figaro',slice(0,6)),('FIS',slice(6,12))]:
     for subset,mask in [('all',np.ones(100,bool)),('queried',q),('unqueried',~q)]:
      assured=int(flag[mask,cols].sum());f=int(false[mask,cols].sum());n=int(flag[mask,cols].size)
      rows.append({**meta,'estimator':est,'tolerance_ppm':tol,'scope':family,'subset':subset,'false_count':f,'assured_count':assured,'all_count':n,'false_over_assured':'NA' if not assured else f/assured,'false_over_all':'NA' if not n else f/n,'interval_noncontainment_count':int(non[mask,cols].sum()),'source':str(path.relative_to(ROOT))})
with (OUT/'FALSE_ASSURANCE_AUDIT.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
for bounds in ('primary','slope95'):
 r=[x for x in rows if x['model']=='RF' and x['bounds']==bounds and x['schedule']=='envelope' and x['budget']==20 and x['estimator']=='midpoint' and x['tolerance_ppm']==1 and x['scope']=='ALL' and x['subset']=='all']
 counts={k:sum(x[k] for x in r) for k in ('false_count','assured_count','all_count','interval_noncontainment_count')};print(bounds,counts)
(OUT/'ASSURANCE_SUMMARY.json').write_text(json.dumps([{ 'bounds':b,**{k:sum(x[k] for x in rows if x['model']=='RF' and x['bounds']==b and x['schedule']=='envelope' and x['budget']==20 and x['estimator']=='midpoint' and x['tolerance_ppm']==1 and x['scope']=='ALL' and x['subset']=='all') for k in ('false_count','assured_count','all_count','interval_noncontainment_count')}} for b in ('primary','slope95')],indent=2))
