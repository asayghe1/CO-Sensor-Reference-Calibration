from pathlib import Path
import gzip,json,csv
import numpy as np
from context import DEV as E, BUILD
rows=[]
for path in sorted(E.glob('runs_primary_*.json.gz')):
 for r in json.loads(gzip.decompress(path.read_bytes())):
  if not r.get('purchases'):continue
  meta=r['identity']
  for est in ('affine','affine_l095','affine_l090'):
   if est not in r['predictions']:continue
   changes=[s['coefficient_change_norm'] for p in r['purchases'] for s in p['state_after'][est]];lev=[s['regressor_leverage'] for p in r['purchases'] for s in p['state_after'][est]]
   initial=r['initial'][est];final=r['purchases'][-1]['state_after'][est]
   displacement=[np.linalg.norm(np.array(f['theta'])-a['theta']) for a,f in zip(initial,final)]
   rows.append({**meta,'estimator':est,'purchased_updates':len(r['purchases']),'configuration_updates':len(changes),'mean_update_norm':float(np.mean(changes)),'maximum_update_norm':float(np.max(changes)),'mean_regressor_leverage':float(np.mean(lev)),'maximum_regressor_leverage':float(np.max(lev)),'mean_final_displacement':float(np.mean(displacement)),'maximum_final_displacement':float(np.max(displacement)),'historical_information_discount':(1 if est=='affine' else .95 if est=='affine_l095' else .90)**len(r['purchases'])})
with (BUILD/'development_recomputed/UPDATE_DIAGNOSTICS.csv').open('w',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
print(len(rows),'update diagnostic records')
