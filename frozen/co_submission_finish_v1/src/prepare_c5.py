"""Development-only fixed RF fitting and D10 preparation. No raw/final reader."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
import joblib,sklearn
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'co_submission_finish_v1';sys.path.insert(0,str(ROOT))
from phase5.resume.analysis import make_model
UNITS=(1,2,3,4,5,6,8,9,10,11,12,13);FIT=(1,2,4,5,6,7,8,9)
source=ROOT/'phase5/resume/evidence/exposure_features.json'
frozen=json.loads((OUT/'C5_INPUT_MANIFEST.json').read_text())
expected_hash=next(v['sha256'] for v in frozen['records'] if v['path']==str(source.relative_to(ROOT)))
assert hashlib.sha256(source.read_bytes()).hexdigest()==expected_hash
rows=json.loads(source.read_text());assert len(rows)==10800
expected={(d,e,u) for d in (*FIT,10) for e in range(1,101) for u in UNITS}
actual={(v['day'],v['exposure'],v['unit']) for v in rows}
assert actual==expected and len(actual)==len(rows)
assert all(v['id']==f"D{v['day']:02d}_E{v['exposure']:03d}_R{v['unit']:02d}" for v in rows)
assert {v['day'] for v in rows}==set(FIT)|{10};assert {v['unit'] for v in rows}==set(UNITS)
assert all(len(v['features'])==6 and np.isfinite(v['features']).all() for v in rows)
(OUT/'models').mkdir(exist_ok=True);items=[];pred=[];sd=[];normal=[]
for u in UNITS:
 f=sorted([v for v in rows if v['unit']==u and v['day'] in FIT],key=lambda v:(v['day'],v['exposure']))
 c=sorted([v for v in rows if v['unit']==u and v['day']==10],key=lambda v:v['exposure'])
 assert len(f)==800 and len(c)==100
 X=np.array([v['features'] for v in f]);Y=np.array([v['reference_co'] for v in f]);cx=np.array([v['features'] for v in c])
 model=make_model('RF').fit(X,Y);path=OUT/'models'/f'RF_R{u:02d}_fitD1D2D4D5D6D7D8D9.joblib';joblib.dump(model,path)
 pp=model.predict(cx);pred.append(pp);sd.append(np.std([t.predict(model[0].transform(cx)) for t in model[-1].estimators_],axis=0))
 np.testing.assert_array_equal(joblib.load(path).predict(cx),pp)
 items.append({'unit':u,'file':str(path.relative_to(OUT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'fit_ids':[v['id'] for v in f],'scaler_mean':model[0].mean_.tolist(),'scaler_scale':model[0].scale_.tolist(),'settings':model[-1].get_params()})
 print('fitted fixed RF',u,flush=True)
pp=np.array(pred).T;ts=np.array(sd).T;cy=np.array([v['reference_co'] for v in c]);env=np.array([v['features'][4:6] for v in c]);cm=[];cz=[];cc=[];qs=[]
for j,u in enumerate(UNITS):
 peers=[i for i,v in enumerate(UNITS) if (v<8)==(u<8) and v!=u];m=np.median(pp[:,peers],axis=1);z=np.column_stack([env,m]);mu=z.mean(0);scale=z.std(0);scale=np.where(scale==0,1.,scale);confidence=ts[:,peers].mean(1);cs=max(float(np.median(confidence)),.1)
 cm.append(m);cz.append((z-mu)/scale);cc.append(confidence/cs);qs.append(max(float(np.sort(abs(m-cy))[90]),.1));normal.append({'unit':u,'context_mean':mu.tolist(),'context_scale':scale.tolist(),'confidence_scale':cs,'affine_mean':float(m.mean()),'affine_scale':float(m.std()) if m.std()>=1e-8 else 1.,'q':qs[-1]})
cm=np.array(cm).T;cal={'consensus':cm,'error':cm-cy[:,None],'z':np.stack(cz,axis=1),'confidence':np.max(cc,axis=0),'q':np.array(qs)}
np.savez(OUT/'D10_INITIALIZATION.npz',**cal,individual_predictions=pp,individual_tree_sd=ts,reference=cy)
(OUT/'MODEL_MANIFEST.json').write_text(json.dumps({'feature_input':str(source.relative_to(ROOT)),'feature_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'fit_days':FIT,'calibration_day':10,'units':UNITS,'python':sys.version,'numpy':np.__version__,'sklearn':sklearn.__version__,'models':items,'D10_normalization':normal},indent=2))
