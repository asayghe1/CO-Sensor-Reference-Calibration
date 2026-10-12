"""Re-evaluate existing development contrasts using the frozen index banks.

No new indices, model fits, adaptive paths, or confirmation resamples are created.
"""
import csv,gzip,hashlib,json
import numpy as np
from context import DEV,report

def main():
 fields=('model','bounds','estimator','schedule','budget','scope','schedule_id','schedule_driver')
 loss={}
 for path in sorted(DEV.glob('runs_primary_*.json.gz')):
  for run in json.loads(gzip.decompress(path.read_bytes())):
   meta=run['identity'];y=np.array(run['reference'])[:,None]
   for est,pred in run['predictions'].items():
    pred=np.array(pred)
    # Match the frozen evaluator's advanced-index column order, including its
    # summation layout, so comparisons can be exact at machine precision.
    for scope,cols in [('ALL',np.arange(12)),('Figaro',np.arange(6)),('FIS',np.arange(6,12))]:
     a=abs(pred[:,cols]-y)
     values=np.column_stack([a.mean(axis=1),*[(a>t).mean(axis=1) for t in (.5,1.,2.)]])
     key=tuple({**meta,'estimator':est,'scope':scope}[k] for k in fields)
     loss.setdefault(key,{}).setdefault(meta['session'],[]).append(values)
 paths={key:{day:np.mean(values,axis=0) for day,values in days.items()} for key,days in loss.items()}
 banks={}
 for item in json.loads((DEV/'RESAMPLING_INDEX_MANIFEST.json').read_text()):
  data=(DEV/item['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==item['sha256']
  idx=np.load(DEV/item['file'],allow_pickle=False);assert idx.shape==(2000,100) and idx.min()>=0 and idx.max()<100
  banks.setdefault(item['block_length'],{})[item['session']]=idx
 assert set(banks)=={5,10,20}
 # Apply the original archived indices with the original order of arithmetic.
 sampled={}
 for key,days in paths.items():
  assert set(days)=={'D6','D8','D10'}
  for length,bank in banks.items():
   sampled[key,length]=np.mean([days[d][bank[d]].mean(axis=1) for d in sorted(days)],axis=0)
 effects={}
 with (DEV/'CONDITIONAL_RESAMPLING_EFFECTS.csv').open(newline='') as f:
  for r in csv.DictReader(f):
   key=(r['model'],r['estimator'],r['schedule'],int(r['budget']),r['scope'],r['effect'],r['schedule_id'],r['baseline_schedule_id'],int(r['block_length']),r['metric'])
   assert key not in effects;effects[key]=r
 checked=0;largest=0.;paired=0
 for rec in json.loads(gzip.decompress((DEV/'PAIRED_LOSS_PATHS.json.gz').read_bytes())):
  arm,base=tuple(rec['arm']),tuple(rec['baseline']);delta={d:paths[arm][d]-paths[base][d] for d in ('D6','D8','D10')}
  for d,arr in delta.items():np.testing.assert_array_equal(arr,np.array(rec['exposure_differences'][d]))
  session=np.array([delta[d].mean(axis=0) for d in ('D6','D8','D10')]);point=session.mean(axis=0);paired+=1
  for length in banks:
   low,high=np.percentile(sampled[arm,length]-sampled[base,length],[2.5,97.5],axis=0)
   for j,metric in enumerate(('mae','p0.5','p1.0','p2.0')):
    r=effects[(arm[0],arm[2],arm[3],arm[4],arm[5],rec['effect'],arm[6],base[6],length,metric)]
    scale=1 if j==0 else 100
    values={'estimate':point[j]*scale,'conditional_low':low[j]*scale,'conditional_high':high[j]*scale,**{d:session[k,j]*scale for k,d in enumerate(('D6','D8','D10'))}}
    for key,value in values.items():
     largest=max(largest,abs(value-float(r[key])));assert np.isclose(value,float(r[key]),atol=1e-10,rtol=1e-13),(key,value,r[key])
    assert int(r['sessions_same_sign'])==int((np.sign(session[:,j])==np.sign(point[j])).sum())
    for prefix,condition in [('negative',session[:,j]<0),('positive',session[:,j]>0),('zero',session[:,j]==0)]:assert int(r[prefix+'_sessions'])==int(condition.sum())
    checked+=1
 assert checked==len(effects)
 report('SAVED_DEVELOPMENT_RESAMPLING.json',dict(status='PASS',contrast_rows=checked,paired_loss_paths=paired,archived_index_banks=9,maximum_absolute_difference=largest,new_indices_generated=False,confirmation_bootstrap=False,models_or_paths_replayed=False))
 print('Archived development conditional bounds:',checked,'rows PASS',flush=True)
if __name__=='__main__':main()
