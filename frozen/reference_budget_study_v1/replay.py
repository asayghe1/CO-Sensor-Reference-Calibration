"""Observable-only online controller with explicit budget-gated reference access."""
import numpy as np
from reference_budget_study_v1.data import validate_observables
from reference_budget_study_v1.methods import Envelope,historical_risk

class ReferenceProvider:
    def __init__(self,values,budget):
        self.__values=np.asarray(values,float).copy();self.budget=budget;self.current=-1;self.access_log=[]
        if not 0<=budget<=len(values) or not np.all(np.isfinite(self.__values)):raise ValueError('provider input')
    def advance(self,index):
        if index!=self.current+1 or index>=len(self.__values):raise PermissionError('noncausal advance')
        self.current=index
    def purchase(self,index):
        if index!=self.current or index in self.access_log or len(self.access_log)>=self.budget:
            raise PermissionError('reference access not authorized by budget/current step')
        self.access_log.append(index);return float(self.__values[index])

def scheduled_indices(policy,n,budget,seed):
    if budget==0:return set()
    if policy=='periodic':return set(np.floor((np.arange(budget)+.5)*n/budget).astype(int).tolist())
    if policy=='random':return set(np.random.default_rng(seed).choice(n,budget,replace=False).tolist())
    return set()

def replay(observables,calibration,provider,policy,budget,seed,config):
    validate_observables(observables)
    n,k=observables['consensus'].shape
    if policy not in ('periodic','random','confidence','proposed') or not 0<=budget<=n or provider.budget!=budget:
        raise ValueError('policy/budget')
    envs=[Envelope(calibration['z'][:,j],calibration['error'][:,j],**config) for j in range(k)]
    history=(historical_risk(calibration,config) if policy=='proposed' else calibration['confidence']).tolist()
    schedule=scheduled_indices(policy,n,budget,seed);past=[];traces=[]
    for i in range(n):
        provider.advance(i);t=i+1;z=observables['z'][i];m=observables['consensus'][i]
        bounds=[e.predict(z[j],t) for j,e in enumerate(envs)]
        low=np.array([b[0] for b in bounds]);high=np.array([b[1] for b in bounds]);bad=np.array([b[2] for b in bounds])
        radius=(high-low)/2;corrected=m-(low+high)/2
        risk=1e12 if bad.any() else float(np.max(radius/calibration['q']))
        score=risk if policy=='proposed' else float(observables['confidence'][i])
        remaining=budget-len(past);horizon=n-i;forced=remaining>0 and remaining==horizon
        threshold=float(np.quantile(history,1-remaining/horizon,method='higher'))
        query=remaining>0 and (forced or (i in schedule if policy in ('periodic','random') else score>threshold))
        # This record is frozen BEFORE any current reference is requested.
        traces.append({'index':i,'past_query_indices':past.copy(),'remaining_before':remaining,
                       'score':score,'risk':risk,'threshold':threshold,'query':bool(query),'forced':bool(forced),
                       'consensus':m.tolist(),'corrected':corrected.tolist(),'error_lower':low.tolist(),
                       'error_upper':high.tolist(),'radius':radius.tolist(),'contradiction':bad.tolist()})
        history.append(score)
        if query:
            y=provider.purchase(i)
            for j,e in enumerate(envs):e.update(z[j],t,float(m[j]-y))
            past.append(i)
    if len(past)!=budget:raise RuntimeError('quota failure')
    return traces
