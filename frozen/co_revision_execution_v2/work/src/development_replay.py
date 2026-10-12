"""Finite development replay. Estimators see observables, calibration, and purchases only."""
import numpy as np
from revision_analyses_checked import AffineRLS
from reference_budget_study_v1.replay import ReferenceProvider
from reference_budget_study_v1.methods import Envelope
from reference_budget_review_correction_v1.correction import OnlineCorrection,interval_choices
BASE=dict(epsilon=.1,rho=.01,gamma=.5,slope_quantile=1.)

def finite_replay(obs,cal,reference_values,budget,mask=None,trace=None,native=False):
 m=obs['consensus'];cm=cal['consensus'];n,k=m.shape
 if (n,k)!=(100,12) or (not native and (mask is None or np.asarray(mask).shape!=(n,) or np.sum(mask)!=budget)):raise ValueError('development replay support/mask')
 provider=ReferenceProvider(reference_values,budget)
 # Outcome array exists only in provider. No estimator/controller receives it.
 affines={name:[AffineRLS(cm[:,j],cm[:,j]-cal['error'][:,j],lam_new=lam) for j in range(k)] for name,lam in [('affine',1.),('affine_l095',.95),('affine_l090',.90)]}
 offset=OnlineCorrection(cm,cal['error'],False)
 initial={name:[{'theta':a.theta.copy(),'P':a.P.copy(),'mu':a.mu,'s':a.s,'scale_fallback':a.scale_fallback} for a in aa] for name,aa in affines.items()}
 envs=[Envelope(cal['z'][:,j],cal['error'][:,j],**BASE) for j in range(k)] if trace is None else None
 driver=[AffineRLS(cm[:,j],cm[:,j]-cal['error'][:,j],.95) for j in range(k)] if native else None
 history=[max(driver[j].variance_score(cm[i,j]) for j in range(k)) for i in range(len(cm))] if native else []
 hist_initial=history.copy();pred={e:[] for e in ['consensus','midpoint','projection','offset',*affines]};qs=[];logs=[];purchases=[];scores=[];lower=[];upper=[];badlist=[]
 for i in range(n):
  provider.advance(i)
  if trace is not None:
   t=trace[i]
   if t['index']!=i or t['past_query_indices']!=provider.access_log:raise ValueError('saved causal trajectory')
   np.testing.assert_allclose(t['consensus'],m[i],rtol=0,atol=1e-12)
   lo=np.array(t['error_lower']);hi=np.array(t['error_upper']);bad=np.array(t['contradiction'])
  else:
   b=[e.predict(calz,i+1) for e,calz in zip(envs,obs['z'][i])];lo=np.array([v[0] for v in b]);hi=np.array([v[1] for v in b]);bad=np.array([v[2] for v in b])
  choice=interval_choices(m[i],lo,hi,bad)
  for e,old in [('consensus','unchanged'),('midpoint','midpoint'),('projection','projection')]:pred[e].append(choice[old]['prediction'])
  pred['offset'].append(offset.predict(m[i]))
  for e,aa in affines.items():pred[e].append(np.array([a.predict(v) for a,v in zip(aa,m[i])]))
  if native:
   score=max(a.variance_score(v) for a,v in zip(driver,m[i]));remaining=budget-len(provider.access_log);horizon=n-i
   threshold=float(np.quantile(history,1-remaining/horizon,method='higher'));forced=remaining>0 and remaining==horizon
   q=bool(remaining>0 and (forced or score>threshold));history.append(score)
   scores.append({'index':i,'score':score,'threshold':threshold,'remaining_before':remaining,'forced':forced})
  else:q=bool(mask[i])
  qs.append(q);lower.append(lo);upper.append(hi);badlist.append(bad)
  # Persist prediction hash before access. Evaluator sees all labels only after return.
  import hashlib
  frozen_hash=hashlib.sha256(np.array([pred[e][-1] for e in pred]).tobytes()).hexdigest()
  log={'index':i,'stage':'prediction_frozen','past':provider.access_log.copy(),'query':q,'prediction_sha256':frozen_hash,'released_after_freeze':q,'affects_from':i+1 if q and i+1<n else None}
  if q:
   y=provider.purchase(i);changes={}
   for e,aa in affines.items():
    for a,v in zip(aa,m[i]):a.update_purchased(v,y)
    changes[e]=[{'theta':a.theta.copy(),'P':a.P.copy(),'information':np.linalg.inv(a.P),'coefficient_change_norm':a.last_change,'regressor_leverage':a.last_leverage,'failures':a.failures,'failure_events':a.events.copy(),'update_success':a.last_update_success} for a in aa]
   offset.update(m[i],y-m[i],stage='purchase',index=i)
   if driver is not None:
    for a,v in zip(driver,m[i]):a.update_purchased(v,y)
   if envs is not None:
    for j,e in enumerate(envs):e.update(obs['z'][i,j],i+1,float(m[i,j]-y))
   purchases.append({'index':i,'reference':y,'state_after':changes})
  logs.append(log)
 if len(provider.access_log)!=budget:raise ValueError('exact quota')
 return {'predictions':{e:np.array(v) for e,v in pred.items()},'query':np.array(qs),'access_log':logs,'purchases':purchases,'initial':initial,'native_scores':scores,'native_history_initial':hist_initial,'driver':'affine_l095' if native else 'saved_mask','error_lower':np.array(lower),'error_upper':np.array(upper),'contradiction':np.array(badlist),'numerical_failures':sum(a.failures for aa in affines.values() for a in aa)+len(offset.failures)}
