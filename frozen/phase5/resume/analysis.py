from pathlib import Path
import json,hashlib,math,time
import numpy as np
from sklearn.linear_model import LinearRegression,Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.neighbors import NearestNeighbors
from phase5.resume.methods import ALLOWED_UNITS,permitted,score_schema
R=Path(__file__).resolve().parents[2];O=R/'phase5/resume/evidence'
def group_quantile(errors,alpha=.9):
 v=np.sort(np.max(errors,axis=1));k=math.ceil(alpha*(len(v)+1))
 if k>len(v):raise ValueError('insufficient calibration groups')
 return float(v[k-1])
def select(scores,ids,rate):
 n=len(ids);k=max(1,math.floor(rate*n));ties=[hashlib.sha256(('487:'+i).encode()).hexdigest() for i in ids]
 ix=sorted(range(n),key=lambda i:(scores[i],ties[i]));m=np.zeros(n,bool);m[ix[:k]]=True;return m
def metrics(y,p,q,mask):
 e=np.abs(y-p);m=mask;score=2*q+20*np.maximum(e-q,0)
 out={'n':int(m.sum()),'retained':float(m.mean()),'mae':float(e[m].mean()),'rmse':float(np.sqrt(((y-p)[m]**2).mean())),'bias':float((p-y)[m].mean()),'coverage':float((e[m]<=q).mean()),'width':float(2*q),'interval_score':float(score[m].mean())}
 for tol in [.5,1.,2.]:
  valid=e<=tol;out['false_rejection_'+str(tol)]=float((valid&~m).sum()/valid.sum()) if valid.sum() else None
 return out
def midcdf(ref,v):
 ref=np.sort(ref);return (np.searchsorted(ref,v,side='left')+np.searchsorted(ref,v,side='right'))/(2*len(ref))
def make_model(kind):
 estimator={'OLS':lambda:LinearRegression(),'Ridge':lambda:Ridge(alpha=10),'RF':lambda:RandomForestRegressor(n_estimators=100,max_depth=5,min_samples_leaf=5,random_state=487,n_jobs=1)}[kind]()
 return make_pipeline(StandardScaler(),estimator)
def raw_scores(model,x,peers,fitnn,calnn,calres,scaler,q):
 score_schema({'features':x,'temperature':x[:,5],'humidity':x[:,4],'predictions':peers})
 p=model.predict(x);z=scaler.transform(x);med=np.median(peers,axis=1)
 dist=fitnn.kneighbors(z,return_distance=True)[0].mean(axis=1)/np.sqrt(6)
 idx=calnn.kneighbors(z,return_distance=False);pr=calres[idx].mean(axis=1)
 scores={'disagreement':np.abs(p-med),'peer_mad':np.median(np.abs(peers-med[:,None]),axis=1),'environment':np.sqrt(np.mean(z[:,4:]**2,axis=1)),'feature_distance':dist,'prior_residual':pr,'width':np.full(len(x),2*q),'hash_only':np.zeros(len(x))}
 if isinstance(model[-1],RandomForestRegressor):scores['confidence']=np.std(np.array([t.predict(model[0].transform(x)) for t in model[-1].estimators_]),axis=0)
 return p,scores

def main():
 import sys
 W=O/'reproduction' if '--reproduce' in sys.argv else O
 W.mkdir(exist_ok=True)
 start=time.monotonic();config=json.loads(O.joinpath('admission.json').read_text());assert config['status']=='PASS_REDUCED_LATE_CORE_ESTIMAND'
 assert hashlib.sha256((R/'phase5/resume/EXPERIMENT_PROTOCOL.v1.0.md').read_bytes()).hexdigest()==config['protocol_sha256']
 records=json.loads(O.joinpath('exposure_features.json').read_text());assert len(records)==10800
 for v in records:permitted(v['day'],v['unit']);assert v['day']!=3 and len(v['features'])==6
 rows=[];calarchive=[];cells=[];shared=[];points=[];fits=[];fit_count=0
 for fold,(last,cd,ad) in enumerate([(4,5,6),(6,7,8),(8,9,10)],1):
  for family,units in [('Figaro',list(range(1,7))),('FIS',list(range(8,14)))]:
   fit=[v for v in records if v['day']<=last and v['unit'] in units];cal=[v for v in records if v['day']==cd and v['unit'] in units];ass=[v for v in records if v['day']==ad and v['unit'] in units]
   assert not ({(v['day'],v['exposure']) for v in fit}&{(v['day'],v['exposure']) for v in cal+ass})
   def byunit(source,u):return sorted([v for v in source if v['unit']==u],key=lambda v:(v['day'],v['exposure']))
   def X(source):return np.array([v['features'] for v in source])
   def Y(source):return np.array([v['reference_co'] for v in source])
   envx=X(fit)[:,4:];envphi=lambda a:np.column_stack([a,a*a,a[:,0]*a[:,1]])
   env=LinearRegression().fit(envphi(envx),Y(fit));fit_count+=1
   indiv={};calpeer={};asspeer={}
   for kind in ['OLS','Ridge','RF']:
    indiv[kind]={};calpeer[kind]={};asspeer[kind]={}
    for u in units:
     f=byunit(fit,u);model=make_model(kind).fit(X(f),Y(f));fit_count+=1;indiv[kind][u]=model
     calpeer[kind][u]=model.predict(X(byunit(cal,u)));asspeer[kind][u]=model.predict(X(byunit(ass,u)))
    block=[]
    for target in units:
     peers=[u for u in units if u!=target];f=[v for v in fit if v['unit']!=target];c=[v for v in cal if v['unit']!=target];a=byunit(ass,target)
     assert target not in {v['unit'] for v in f+c};assert len(c)==500 and len(a)==100
     model=make_model(kind).fit(X(f),Y(f));fit_count+=1;scaler=model[0]
     cp=model.predict(X(c));res=np.abs(Y(c)-cp);q=group_quantile(res.reshape(100,5))
     fn=NearestNeighbors(n_neighbors=5).fit(scaler.transform(X(f)));cn=NearestNeighbors(n_neighbors=5).fit(scaler.transform(X(c)))
     peer_a=np.column_stack([asspeer[kind][u] for u in peers])
     # For calibration each peer is compared against its other four peers.
     peer_c=np.array([[calpeer[kind][u][v['exposure']-1] for u in peers if u!=v['unit']] for v in c])
     _,cref=raw_scores(model,X(c),peer_c,fn,cn,res,scaler,q)
     p,scores=raw_scores(model,X(a),peer_a,fn,cn,res,scaler,q)
     pct={s:midcdf(cref[s],scores[s]) for s in ['disagreement','environment','prior_residual']}
     scores['combined']=(pct['disagreement']+pct['environment']+pct['prior_residual'])/3
     scores['disagreement_residual']=(pct['disagreement']+pct['prior_residual'])/2
     scores['environment_residual']=(pct['environment']+pct['prior_residual'])/2
     ids=[f'D{ad}_E{v["exposure"]}' for v in a];y=Y(a)
     pointpred={'global':p,'individual':indiv[kind][target].predict(X(a)),'environment_only':env.predict(envphi(X(a)[:,4:])),'mean':np.full(len(a),Y(f).mean())}
     for name,pv in pointpred.items():points.append({'fold':fold,'day':ad,'type':family,'unit':target,'model':kind,'baseline':name,'n':len(y),'mae':float(np.mean(np.abs(pv-y))),'rmse':float(np.sqrt(np.mean((pv-y)**2))),'bias':float(np.mean(pv-y))})
     fits.append({'fold':fold,'day':ad,'type':family,'unit':target,'model':kind,'fit_ids':[v['id'] for v in f],'calibration_ids':[v['id'] for v in c],'assessment_ids':[v['id'] for v in a],'q':q,'calibration_score_reference':{k:v.tolist() for k,v in cref.items()}})
     calarchive.extend({'fold':fold,'type':family,'target_unit':target,'model':kind,'id':v['id'],'reference_co':float(v['reference_co']),'prediction':float(cp[j]),'abs_residual':float(res[j])} for j,v in enumerate(c))
     out=[]
     for j,v in enumerate(a):
      record={'id':v['id'],'exposure_id':ids[j],'fold':fold,'day':ad,'type':family,'unit':target,'model':kind,'reference_co':float(y[j]),'prediction':float(p[j]),'q':q,'peer_predictions':peer_a[j].tolist(),'individual_prediction':float(pointpred['individual'][j]),'environment_prediction':float(pointpred['environment_only'][j]),'scores':{k:float(val[j]) for k,val in scores.items()}}
      rows.append(record);out.append(record)
     for policy,val in scores.items():
      for rate in [.5,.75,.9,1.]:
       mask=select(val,ids,rate);cells.append({'fold':fold,'day':ad,'type':family,'unit':target,'model':kind,'policy':policy,'rate':rate,**metrics(y,p,q,mask),'accepted_ids':[a[j]['id'] for j in np.flatnonzero(mask)]})
     block.append(out)
    for policy in block[0][0]['scores']:
     score=np.max(np.array([[v['scores'][policy] for v in unitrows] for unitrows in block]),axis=0)
     for rate in [.5,.75,.9,1.]:
      accept=select(score,[v['exposure_id'] for v in block[0]],rate)
      # Compute each unit's metric with identical whole-exposure acceptance.
      for unitrows in block:
       yy=np.array([v['reference_co'] for v in unitrows]);pp=np.array([v['prediction'] for v in unitrows]);qq=unitrows[0]['q']
       shared.append({'fold':fold,'day':ad,'type':family,'unit':unitrows[0]['unit'],'model':kind,'policy':policy,'rate':rate,**metrics(yy,pp,qq,accept),'accepted_exposures':[v['exposure_id'] for j,v in enumerate(unitrows) if accept[j]]})
    print('completed',fold,family,kind,flush=True)
 W.joinpath('predictions.json').write_text(json.dumps(rows));W.joinpath('calibration_predictions.json').write_text(json.dumps(calarchive));W.joinpath('metrics.json').write_text(json.dumps(cells));W.joinpath('shared_exposure_metrics.json').write_text(json.dumps(shared));W.joinpath('point_baselines.json').write_text(json.dumps(points,indent=2));W.joinpath('assignments.json').write_text(json.dumps(fits))
 # Simulated output-only common-mode control; true reference outcomes unchanged.
 cm=[]
 for v in rows:
  p=v['prediction'];peers=np.array(v['peer_predictions']);med=np.median(peers)
  assert np.isclose(abs(p-med),abs((p+2)-np.median(peers+2)))
  cm.append({'id':v['id'],'fold':v['fold'],'model':v['model'],'baseline_abs_error':abs(p-v['reference_co']),'common_offset_abs_error':abs(p+2-v['reference_co']),'same_disagreement':True})
 W.joinpath('common_mode_control.json').write_text(json.dumps({'control':'SIMULATED_OUTPUT_OFFSET_PLUS_2_PPM_NOT_PHYSICAL_FAILURE','scores_and_acceptance_unchanged':True,'records':cm}))
 import sklearn,sys
 W.joinpath('environment.json').write_text(json.dumps({'python':sys.version,'numpy':np.__version__,'sklearn':sklearn.__version__,'runtime_s':time.monotonic()-start,'model_fit_count':fit_count,'prediction_records':len(rows),'calibration_prediction_records':len(calarchive),'protocol_sha256':config['protocol_sha256']},indent=2))
if __name__=='__main__':main()
