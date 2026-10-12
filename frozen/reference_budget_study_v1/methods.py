"""Conditional bounded-error envelopes; empirical constants are not guarantees."""
import numpy as np

class Envelope:
    def __init__(self,z,errors,epsilon=.1,rho=.01,gamma=.5,slope_quantile=1.):
        z=np.asarray(z,float);errors=np.asarray(errors,float)
        if z.ndim!=2 or errors.shape!=(len(z),) or len(z)<2:raise ValueError('anchor shape')
        if min(epsilon,rho,gamma)<0 or not 0<slope_quantile<=1:raise ValueError('invalid bounds')
        if not np.all(np.isfinite(z)) or not np.all(np.isfinite(errors)):raise ValueError('nonfinite anchor')
        d=np.linalg.norm(z[:,None]-z[None,:],axis=2)
        excess=np.maximum(np.abs(errors[:,None]-errors[None,:])-2*epsilon,0)
        if np.any((d==0)&(excess>0)):raise ValueError('zero-distance error incompatibility')
        i,j=np.triu_indices(len(z),1);mask=d[i,j]>0
        slopes=excess[i[mask],j[mask]]/d[i[mask],j[mask]]
        self.L=float(np.quantile(slopes,slope_quantile,method='higher')) if len(slopes) else 0.
        self.z=z.copy();self.errors=errors.copy();self.times=np.zeros(len(z),int)
        self.historical=np.ones(len(z),bool);self.epsilon=epsilon;self.rho=rho;self.gamma=gamma
        self.last_update=0

    def predict(self,z,t):
        if t<=self.last_update:raise ValueError('current reference cannot affect own prediction')
        w=self.epsilon+self.L*np.linalg.norm(self.z-np.asarray(z),axis=1)+self.rho*(t-self.times)+self.gamma*self.historical
        low=self.errors-w;high=self.errors+w
        lo=float(low.max());hi=float(high.min());bad=lo>hi
        if bad:lo=float(low.min());hi=float(high.max())
        return lo,hi,bool(bad)

    def update(self,z,t,error):
        if t<=self.last_update or not np.isfinite(error):raise ValueError('invalid purchase update')
        self.z=np.vstack([self.z,z]);self.errors=np.append(self.errors,error)
        self.times=np.append(self.times,t);self.historical=np.append(self.historical,False);self.last_update=t

def historical_risk(cal,config):
    n,k=cal['error'].shape;radius=np.zeros((n,k))
    # Calibration leave-one-out scores are computed before assessment replay.
    for j in range(k):
        z=cal['z'][:,j];err=cal['error'][:,j];env=Envelope(z,err,**config)
        d=np.linalg.norm(z[:,None]-z[None,:],axis=2)
        w=config['epsilon']+env.L*d+config['gamma'];low=err[None,:]-w;high=err[None,:]+w
        np.fill_diagonal(low,-np.inf);np.fill_diagonal(high,np.inf)
        lo=low.max(axis=1);hi=high.min(axis=1);bad=lo>hi
        radius[:,j]=np.where(bad,1e12,(hi-lo)/2/cal['q'][j])
    return radius.max(axis=1)
