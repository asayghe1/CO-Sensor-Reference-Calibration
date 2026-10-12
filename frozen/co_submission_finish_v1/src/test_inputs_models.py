from pathlib import Path
import json,hashlib,tempfile,sys
import numpy as np
import joblib
sys.path.insert(0,str(Path(__file__).resolve().parent))
import c5_inputs
O=Path(__file__).resolve().parents[1];R=O.parent
manifest=json.loads((O/'MODEL_MANIFEST.json').read_text());records=json.loads((R/manifest['feature_input']).read_text());expected={(d,e,u) for d in (1,2,4,5,6,7,8,9,10) for e in range(1,101) for u in c5_inputs.UNITS}
assert len(records)==len(expected)==len({(v['day'],v['exposure'],v['unit']) for v in records});assert {(v['day'],v['exposure'],v['unit']) for v in records}==expected
assert [v['unit'] for v in manifest['models']]==list(c5_inputs.UNITS)==[v['unit'] for v in manifest['D10_normalization']]
for item in manifest['models']:
 model=joblib.load(O/item['file']);p=model[-1].get_params();assert (p['random_state'],p['n_estimators'],p['max_depth'],p['min_samples_leaf'],p['n_jobs'])==(487,100,5,5,1)
 f=sorted([v for v in records if v['unit']==item['unit'] and v['day'] in (1,2,4,5,6,7,8,9)],key=lambda v:(v['day'],v['exposure']));x=np.array([v['features'] for v in f]);np.testing.assert_allclose(model[0].mean_,x.mean(0),atol=1e-12,rtol=0);np.testing.assert_allclose(model[0].scale_,x.std(0),atol=1e-12,rtol=0);assert item['fit_ids']==[v['id'] for v in f]
with tempfile.TemporaryDirectory(dir=O) as td:
 tmp=Path(td);path=tmp/c5_inputs.FILES[11];header=json.loads((O/'C5_INPUT_MANIFEST.json').read_text())['header']
 with path.open('w') as file:
  file.write(','.join(header)+'\n')
  for tick in range(227276):
   t=tick*.4;heater=1 if t%40<20 else 0
   # Reserved and forbidden columns contain nonnumeric sentinels.
   values=[f'{t:.1f}','5','40','25','FORBIDDEN_FLOW',str(heater)]+[str(u) if u in c5_inputs.UNITS else 'RESERVED_SENTINEL' for u in range(1,15)]
   file.write(','.join(values)+'\n')
 m=json.loads((O/'MODEL_MANIFEST.json').read_text())
 for item in m['models']:item['file']=str(O/item['file'])
 (tmp/'MODEL_MANIFEST.json').write_text(json.dumps(m));(tmp/'C5_INPUT_MANIFEST.json').write_text(json.dumps({'fixture_only':True,'raw_inventory':[{'name':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}],'header':header}))
 c5_inputs.OUT=tmp
 obs,y=c5_inputs.prepare_session(path,11,authorized=True);assert obs['consensus'].shape==(100,12);np.testing.assert_array_equal(y,np.full(100,5.))
 pp=[];ts=[]
 for item in m['models']:
  u=item['unit'];x=np.tile([np.log(u)]*4+[40.,25.],(100,1));model=joblib.load(item['file']);pp.append(model.predict(x));ts.append(np.std([t.predict(model[0].transform(x)) for t in model[-1].estimators_],axis=0))
 pp=np.array(pp).T
 for j,u in enumerate(c5_inputs.UNITS):
  peers=[i for i,v in enumerate(c5_inputs.UNITS) if (v<8)==(u<8) and v!=u];cm=np.median(pp[:,peers],axis=1);np.testing.assert_allclose(obs['consensus'][:,j],cm,rtol=0,atol=1e-12)
  norm=m['D10_normalization'][j];np.testing.assert_allclose(obs['z'][:,j],(np.column_stack([np.full(100,40.),np.full(100,25.),cm])-norm['context_mean'])/norm['context_scale'],rtol=0,atol=1e-12)
 # Outcome perturbation preserves sensor observables/feature extraction.
 path.write_text(path.read_text().replace(',5,40,25,',',6,40,25,'));f=json.loads((tmp/'C5_INPUT_MANIFEST.json').read_text());f['raw_inventory'][0]['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();(tmp/'C5_INPUT_MANIFEST.json').write_text(json.dumps(f));b,yy=c5_inputs.prepare_session(path,11,authorized=True)
 for k in obs:np.testing.assert_array_equal(obs[k],b[k])
 np.testing.assert_array_equal(yy,np.full(100,6.))
(O/'INPUT_MODEL_PREFLIGHT.json').write_text(json.dumps({'status':'PASS','fixture':'synthetic constant-resistance/header fixture, not a final payload','checks':['exact unique development identities','model hyperparameters','fit-only scaler reconstruction','model/normalization unit order','archived phase and late-core feature rules','R7/R14 and forbidden flow not numerically parsed','reference perturbation leaves observables unchanged'],'reserved_payloads_parsed':False},indent=2))
print('Input adapter and model preflight PASS')
