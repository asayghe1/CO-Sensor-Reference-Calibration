"""Frozen fixed-schedule correction estimators. No scheduler and no final-data reader."""
import numpy as np
from reference_budget_study_v1.replay import ReferenceProvider

ESTIMATORS=('unchanged','midpoint','projection','online_offset','online_affine')

def interval_choices(m,lo,hi,bad):
    m,lo,hi,bad=map(np.asarray,(m,lo,hi,bad))
    centers={'unchanged':np.zeros_like(m),'midpoint':(lo+hi)/2,
             'projection':np.where(bad,0,np.clip(np.zeros_like(m),lo,hi))}
    return {k:{'prediction':m-c,'radius':np.maximum(np.abs(lo-c),np.abs(hi-c)),
               'consistent':~bad} for k,c in centers.items()}

class OnlineCorrection:
    def __init__(self,cal_m,cal_error,affine):
        self.affine=affine; self.mu=np.mean(cal_m,axis=0); self.sd=np.std(cal_m,axis=0)
        self.scale_fallback=self.sd<1e-8; self.sd=np.where(self.scale_fallback,1,self.sd)
        self.k=len(self.mu); self.d=2 if affine else 1
        self.theta=np.zeros((self.k,self.d)); self.P=np.tile(np.eye(self.d),(self.k,1,1))
        self.gram=np.zeros_like(self.P); self.failures=[]; self.updates=0
        for i in range(len(cal_m)): self.update(cal_m[i],-cal_error[i],stage='historical',index=i)
    def features(self,m):
        return np.column_stack(((m-self.mu)/self.sd,np.ones(self.k))) if self.affine else np.ones((self.k,1))
    def predict(self,m):
        pred=m+np.einsum('ij,ij->i',self.features(m),self.theta)
        bad=~np.isfinite(pred)
        if bad.any(): self.failures.append({'kind':'prediction_fallback','units':np.flatnonzero(bad).tolist()})
        return np.where(bad,m,pred)
    def update(self,m,target,stage,index):
        # target is y-m, not y. It is available only historically or after purchase.
        x=self.features(m)
        for h in range(self.k):
            v=self.P[h]@x[h]; den=1+x[h]@v
            if not np.isfinite(den) or den<=0:
                self.failures.append({'kind':'singular_update','stage':stage,'index':index,'h':h}); continue
            th=self.theta[h]+v/den*(target[h]-x[h]@self.theta[h])
            p=self.P[h]-np.outer(v,v)/den; p=(p+p.T)/2
            if not np.all(np.isfinite(th)) or not np.all(np.isfinite(p)) or np.linalg.eigvalsh(p).min()<=0:
                self.failures.append({'kind':'invalid_update','stage':stage,'index':index,'h':h}); continue
            self.theta[h]=th; self.P[h]=p; self.gram[h]+=np.outer(x[h],x[h])
        self.updates+=1
    def status(self):
        return {'rank':[int(np.linalg.matrix_rank(g)) for g in self.gram],
                'condition':[float(np.linalg.cond(g)) if np.linalg.matrix_rank(g)==self.d else None for g in self.gram],
                'insufficient_excitation':[bool(np.linalg.matrix_rank(g)<self.d) for g in self.gram],
                'scale_fallback':self.scale_fallback.tolist(),'failures':self.failures.copy(),
                'theta':self.theta.tolist(),'updates':self.updates}

def fixed_replay(obs,cal,provider,trace):
    m=obs['consensus']; n,k=m.shape
    if n!=100 or k!=12 or provider.budget!=sum(t['query'] for t in trace): raise ValueError('frozen scope')
    # Calibration consensus can be recovered from standardized context coordinate3.
    cm=cal['consensus']; offset=OnlineCorrection(cm,cal['error'],False); affine=OnlineCorrection(cm,cal['error'],True)
    initial={'offset':offset.status(),'affine':affine.status()}; predictions={e:[] for e in ESTIMATORS}; radii={e:[] for e in ESTIMATORS[:3]}; log=[]
    for i,t in enumerate(trace):
        provider.advance(i)
        if t['index']!=i or t['past_query_indices']!=provider.access_log: raise ValueError('causal saved schedule')
        if not np.allclose(m[i],t['consensus'],rtol=0,atol=1e-12): raise ValueError('observable mismatch')
        choices=interval_choices(m[i],t['error_lower'],t['error_upper'],t['contradiction'])
        for e,v in choices.items(): predictions[e].append(v['prediction']); radii[e].append(v['radius'])
        predictions['online_offset'].append(offset.predict(m[i])); predictions['online_affine'].append(affine.predict(m[i]))
        log.append({'index':i,'stage':'prediction_frozen','past':provider.access_log.copy(),'query':t['query']})
        if t['query']:
            y=provider.purchase(i)
            log.append({'index':i,'stage':'purchase_after_prediction','reference':y,'affects_from':i+1 if i+1<n else None})
            offset.update(m[i],y-m[i],stage='purchase',index=i); affine.update(m[i],y-m[i],stage='purchase',index=i)
    if len(provider.access_log)!=provider.budget: raise ValueError('quota')
    return {'predictions':{e:np.array(v) for e,v in predictions.items()},'radii':{e:np.array(v) for e,v in radii.items()},
            'initial_status':initial,'final_status':{'offset':offset.status(),'affine':affine.status()},'access_log':log}
