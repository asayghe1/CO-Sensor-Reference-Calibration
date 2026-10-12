"""Authorized finite replay/export only; existing scientific outputs never written."""
from pathlib import Path
import sys,gzip,json,hashlib,csv,time
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from reference_budget_study_v1.data import load_blocks,ALLOWED
from revision_analyses_checked import validate_rows,REQUIRED
from development_replay import finite_replay
W=ROOT/'co_revision_execution_v2/work';E=W/'evidence';E.mkdir(exist_ok=True)
def encode(x):
 if isinstance(x,np.ndarray):return x.tolist()
 if isinstance(x,np.generic):return x.item()
 raise TypeError(type(x))
def save(p,o):
 b=json.dumps(o,default=encode,allow_nan=False,separators=(',',':')).encode()
 p.write_bytes(gzip.compress(b,mtime=0) if p.suffix=='.gz' else b)
def read(p):return json.loads(gzip.decompress(p.read_bytes()))
def prepare(block):
 cm=block['calibration']['z'][:,:,2]*np.array([r['scale'][2] for r in block['normalization']])+np.array([r['center'][2] for r in block['normalization']])
 return {**block['calibration'],'consensus':cm}
def check_inputs():
 for line in (W/'PROTOCOL_SHA256.txt').read_text().splitlines():
  h,p=line.split();assert hashlib.sha256((W/p).read_bytes()).hexdigest()==h
 snapshot=json.loads((W/'PRESERVATION_SNAPSHOT.v2.json').read_text())
 for r in snapshot:
  assert hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256'],r['path']
 return snapshot

def main():
 start=time.monotonic();snapshot=check_inputs();blocks=load_blocks(ROOT)
 mapping=[{'config':j+1,'unit':u,'family':'Figaro' if u<8 else 'FIS','peer_units':[v for v in ALLOWED if (v<8)==(u<8) and v!=u]} for j,u in enumerate(ALLOWED)]
 save(W/'SOURCE_AND_ROLE_MANIFEST.json',{'run_version':'v2','protocol_sha256':hashlib.sha256((W/'PROTOCOL.v2.md').read_bytes()).hexdigest(),'git_tag_created':False,'git_reason':'read-only placeholder, no repository','mapping':mapping,'roles':{'assessment':[6,8,10],'calibration':[5,7,9],'fit':[[1,2,4],[1,2,4,5,6],[1,2,4,5,6,7,8]],'excluded_day':3,'reserved_units':[7,14],'reserved_days':[11,12,13],'UCI270':'not used'},'scientific_inputs':snapshot,'upstream_models':'saved predictions; no model fits; hashes of source archives identify model/fold/configuration inputs','new_code':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((W/'src').glob('*.py'))]})
 # First reproduce original cumulative predictions under each original RF mask.
 maxdiff=0.;scalars=0
 for b in blocks:
  if b['model']!='RF':continue
  day=b['day'];cal=prepare(b);original=read(ROOT/f'reference_budget_review_correction_v1/predictions/RF_D{day}.json.gz')
  for rec in original:
   meta=rec['metadata'];q=np.array(rec['query']);trace=next(r['traces'] for r in read(ROOT/f'reference_budget_study_v1/evidence/traces/primary_RF_D{day}.json.gz') if r['metadata']==meta)
   result=finite_replay(b['observables'],cal,b['outcomes'],meta['budget'],mask=q,trace=trace)
   for new,old in [('consensus','unchanged'),('offset','online_offset'),('affine','online_affine'),('midpoint','midpoint'),('projection','projection')]:
    a=result['predictions'][new];saved=np.array(rec['predictions'][old]);np.testing.assert_allclose(a,saved,rtol=0,atol=1e-11);maxdiff=max(maxdiff,float(np.abs(a-saved).max()));scalars+=a.size
  print('Original cumulative reproduction verified RF D',day,flush=True)
 save(E/'ORIGINAL_REPRODUCTION.json',{'prediction_scalars':scalars,'maximum_absolute_difference_ppm':maxdiff,'tolerance_ppm':1e-11,'all_original_B0_and_positive_masks':True})
 # Export every original bound/model midpoint baseline; add only specified finite corrections.
 canon=[];runmanifest=[];outputs=0;failures=0
 exportdir=E/'exports';exportdir.mkdir(exist_ok=True)
 for b in blocks:
  model=b['model'];day=b['day'];cal=prepare(b);m=b['observables']['consensus'];y=b['outcomes']
  save(E/f'historical_{model}_D{day}.json.gz',{'model':model,'day':day,'mapping':mapping,'consensus':cal['consensus'],'reference':cal['consensus']-cal['error'],'normalization':b['normalization'],'calibration':cal})
  for bounds in ('primary','slope95','rho0','gamma2'):
   source=f'reference_budget_study_v1/evidence/traces/{bounds}_{model}_D{day}.json.gz';recs=read(ROOT/source);b0=[r for r in recs if r['metadata']['budget']==0];base=b0[0]
   for r in b0[1:]:
    for field in ('corrected','consensus','query','error_lower','error_upper','contradiction'):
     assert [t[field] for t in r['traces']]==[t[field] for t in base['traces']],('B0 mismatch',field)
   canon.append({'model':model,'day':day,'bounds':bounds,'canonical_original':base['metadata'],'removed_duplicates':[r['metadata'] for r in b0[1:]],'exact_fields':['predictions','reference from common block','query','bounds','contradiction']})
   selected=[base]+[r for r in recs if r['metadata']['budget']>0]
   if bounds=='primary':
    selected += [{'metadata':{'config':bounds,'model':model,'day':day,'policy':'rlsvar','budget':budget,'seed':487},'traces':None} for budget in ((5,10,20) if model=='RF' else (20,))]
   out=[]
   with gzip.open(exportdir/f'{bounds}_{model}_D{day}.csv.gz','wt',newline='') as f:
    fields=[*REQUIRED,'physical_unit','physical_exposure_id','reference_access','source','interval_lower','interval_upper','contradiction','assurance1']
    writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
    for rec in selected:
     meta=rec['metadata'];budget=meta['budget'];policy=meta['policy'];native=policy=='rlsvar';trace=rec['traces'];q=np.array([t['query'] for t in trace]) if trace else None
     finite=bounds=='primary' and (model=='RF' or budget in (0,20))
     if finite:
      result=finite_replay(b['observables'],cal,y,budget,mask=q,trace=trace,native=native)
      failures+=result['numerical_failures'];pred=result['predictions'];q=result['query'];lo=result['error_lower'];hi=result['error_upper'];bad=result['contradiction']
      if model!='RF':pred={e:v for e,v in pred.items() if e in ('consensus','midpoint','affine','affine_l095')}
     else:
      lo=np.array([t['error_lower'] for t in trace]);hi=np.array([t['error_upper'] for t in trace]);bad=np.array([t['contradiction'] for t in trace]);pred={'consensus':m,'midpoint':np.array([t['corrected'] for t in trace])};result={}
     schedule='none' if budget==0 else {'proposed':'envelope'}.get(policy,policy);seed=-1 if budget==0 else meta['seed'];driver='none' if budget==0 else ('affine_l095' if native else ('envelope_'+bounds if policy=='proposed' else policy+'_'+model));sid='none' if budget==0 else ('native_l095' if native else schedule+'_'+bounds+'_'+model)
     rid=f'v2/{model}/{bounds}/D{day}/{sid}/B{budget}/S{seed}'
     ident={'model':model,'bounds':bounds,'session':f'D{day}','schedule':schedule,'schedule_id':sid,'schedule_driver':driver,'budget':budget,'seed':seed,'run_id':rid}
     rows=[]
     for est,p in pred.items():
      for i in range(100):
       for j,u in enumerate(ALLOWED):
        interval=est in ('consensus','midpoint','projection');center=m[i,j]-p[i,j];radius=max(abs(lo[i,j]-center),abs(hi[i,j]-center))
        rows.append({**ident,'exposure':i+1,'config':j+1,'family':mapping[j]['family'],'estimator':est,'pred':float(p[i,j]),'ref':float(y[i]),'queried':int(q[i]),'physical_unit':u,'physical_exposure_id':f'D{day}_E{i+1}','reference_access':'evaluation_only' if not q[i] else 'purchased_after_prediction','source':source if not native else 'v2 finite native replay','interval_lower':float(m[i,j]-hi[i,j]) if interval else '', 'interval_upper':float(m[i,j]-lo[i,j]) if interval else '', 'contradiction':int(bad[i,j]) if interval else '', 'assurance1':int(not bad[i,j] and radius<=1) if interval else ''})
     validate_rows(rows,require_seeds=False);writer.writerows(rows);outputs+=len(rows)
     out.append({'identity':ident,'query':q,'reference':y,'predictions':pred,'error_lower':lo,'error_upper':hi,'contradiction':bad,'source':source,**{k:v for k,v in result.items() if k not in ('query','predictions','error_lower','error_upper','contradiction')}})
     runmanifest.append({**ident,'estimators':list(pred),'mask_sha256':hashlib.sha256(q.tobytes()).hexdigest(),'queries':np.flatnonzero(q)+1,'outputs':len(rows),'source':source})
   save(E/f'runs_{bounds}_{model}_D{day}.json.gz',out)
   print(bounds,model,day,'exported',len(out),'unique runs',flush=True)
 # Completeness audit of actual seed matrix, without rereading huge CSVs.
 for model in ('RF','OLS','Ridge'):
  for bounds in ('primary','slope95','rho0','gamma2'):
   for day in ('D6','D8','D10'):
    for budget in (5,10,20):
     ss={r['seed'] for r in runmanifest if r['model']==model and r['bounds']==bounds and r['session']==day and r['schedule']=='random' and r['budget']==budget}
     assert ss==set(range(487,497))
 save(E/'B0_NORMALIZATION.json',canon);save(E/'RUN_MANIFEST.json',runmanifest)
 save(E/'EXECUTION.json',{'outputs':outputs,'unique_runs':len(runmanifest),'numerical_failures':failures,'physical_exposures':300,'models_refit':0,'reserved_access':False,'runtime_seconds':time.monotonic()-start,'causal_generation':'provider only; estimators have no outcome-vector interface; per-exposure hash persisted before purchase; full outcomes used after replay for evaluation'})
 print('DONE',outputs,'outputs;',len(runmanifest),'runs;',failures,'numerical failures',flush=True)
if __name__=='__main__':main()
