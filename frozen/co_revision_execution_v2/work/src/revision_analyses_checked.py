"""Checked development analysis, derived from supplied revision_analyses_original.py.
NumPy/stdlib backend replaces unavailable pandas; no raw or final-data reader.
Fixture generation is confined to tests; CSV inputs marked fixture/synthetic rejected.
"""
import csv,gzip,json,hashlib,argparse
from pathlib import Path
import numpy as np
TOLS=(.5,1.,2.)
UNITS=(1,2,3,4,5,6,8,9,10,11,12,13)
HORIZONS={'D6':100,'D8':100,'D10':100}
REQUIRED=('session','exposure','config','family','estimator','schedule','budget','seed','pred','ref','queried','model','run_id','schedule_id','schedule_driver','bounds')

def validate_rows(rows,require_seeds=True):
 keys=set();refs={};masks={};supports={};identities={};seeds={}
 for r in rows:
  if not set(REQUIRED)<=set(r):raise ValueError('missing mandatory fields')
  if r.get('fixture',False) or r.get('source_kind')=='synthetic':raise ValueError('fixture cannot be empirical')
  for f in ('exposure','config','budget','seed','queried'):
   v=r[f]
   if not isinstance(v,(int,np.integer)) or isinstance(v,bool):raise ValueError('exact integer required: '+f)
  s=r['session'];h=r['config'];e=r['exposure']
  if s not in HORIZONS or not 1<=h<=12 or not 1<=e<=HORIZONS[s]:raise ValueError('development support')
  if r['family']!=('Figaro' if h<=6 else 'FIS') or r['model'] not in ('RF','OLS','Ridge'):raise ValueError('mapping/model')
  if not np.isfinite([r['pred'],r['ref']]).all() or r['queried'] not in (0,1):raise ValueError('finite/binary contract')
  if r['budget'] not in (0,5,10,20) or not all(str(r[f]) for f in ('run_id','schedule_id','schedule_driver','estimator')):raise ValueError('identity/budget')
  if r['budget']==0 and (r['queried'] or r['schedule']!='none' or r['seed']!=-1):raise ValueError('B0')
  if r['budget']>0 and (r['schedule'] not in ('periodic','random','confidence','envelope','rlsvar') or r['seed'] not in (range(487,497) if r['schedule']=='random' else [487])):raise ValueError('schedule/seed')
  key=(r['run_id'],r['estimator'],e,h)
  if key in keys:raise ValueError('duplicate output key')
  keys.add(key)
  ident=tuple(r[f] for f in ('model','bounds','session','schedule','schedule_id','schedule_driver','budget','seed'))
  if identities.setdefault(r['run_id'],ident)!=ident:raise ValueError('run identity collision')
  refkey=(s,e)
  if refs.setdefault(refkey,r['ref'])!=r['ref']:raise ValueError('shared reference conflict')
  qkey=(r['run_id'],e)
  if masks.setdefault(qkey,r['queried'])!=r['queried']:raise ValueError('within-run shared-mask conflict')
  supports.setdefault((r['run_id'],r['estimator']),set()).add((e,h))
  sk=tuple(r[f] for f in ('model','bounds','session','schedule_id','estimator','budget'))
  seeds.setdefault(sk,set()).add(r['seed'])
 for (run,est),support in supports.items():
  ident=identities[run];s=ident[2];budget=ident[6]
  if support!={(e,h) for e in range(1,HORIZONS[s]+1) for h in range(1,13)}:raise ValueError('incomplete exposure/configuration support')
  if sum(masks[(run,e)] for e in range(1,HORIZONS[s]+1))!=budget:raise ValueError('quota')
 if require_seeds:
  for sk,ss in seeds.items():
   run=next(r for r in rows if tuple(r[f] for f in ('model','bounds','session','schedule_id','estimator','budget'))==sk)
   if run['schedule']=='random' and ss!=set(range(487,497)):raise ValueError('missing declared random seed')
 return len(keys)

def load(path):
 if any(x in str(path).lower() for x in ('synthetic','fixture')):raise ValueError('fixture path excluded')
 opener=gzip.open if str(path).endswith('.gz') else open
 with opener(path,'rt',newline='') as f:rows=list(csv.DictReader(f))
 for r in rows:
  for k in ('exposure','config','budget','seed','queried'):
   v=float(r[k]);
   if not np.isfinite(v) or v!=int(v):raise ValueError('integer parsing')
   r[k]=int(v)
  for k in ('pred','ref'):r[k]=float(r[k])
 validate_rows(rows);return rows

def per_arm(rows,estimator,schedule,budget,family=None,model=None,bounds=None,schedule_id=None):
 sel=[r for r in rows if r['estimator']==estimator and r['schedule']==schedule and r['budget']==budget and (family is None or r['family']==family) and (model is None or r['model']==model) and (bounds is None or r['bounds']==bounds) and (schedule_id is None or r['schedule_id']==schedule_id)]
 if not sel:raise ValueError('missing arm')
 if len({(r['model'],r['bounds'],r['schedule_id'],r['schedule_driver']) for r in sel})!=1:raise ValueError('ambiguous upstream/bounds/schedule identity')
 g={}
 for r in sel:g.setdefault((r['session'],r['exposure'],r['seed']),[]).append(abs(r['pred']-r['ref']))
 out={}
 for (s,e,seed),a in g.items():
  a=np.array(a);v=np.r_[a.mean(),[(a>t).mean() for t in TOLS]];out.setdefault((s,e),[]).append(v)
 return {k:np.mean(v,axis=0) for k,v in sorted(out.items())}

def exact_pair(a,b):
 if set(a)!=set(b) or not a:raise ValueError('unequal or empty exposure keys')
 keys=sorted(a);aa=np.array([a[k] for k in keys]);bb=np.array([b[k] for k in keys])
 if aa.shape!=bb.shape or not np.isfinite(aa).all() or not np.isfinite(bb).all():raise ValueError('unequal metric shapes/nonfinite pair')
 return keys,aa,bb

def block_indices(n,block,rng):
 if not isinstance(n,int) or not isinstance(block,int) or not 1<=block<=n:raise ValueError('block length')
 starts=rng.integers(0,n-block+1,size=int(np.ceil(n/block)))
 return np.concatenate([np.arange(s,s+block) for s in starts])[:n]

def make_bank(reps=2000,length=10,seed=487,horizons=HORIZONS):
 rng=np.random.default_rng(seed)
 return {s:np.stack([block_indices(n,length,rng) for _ in range(reps)]) for s,n in sorted(horizons.items())}

def paired_bootstrap(a,b,reps=2000,block=10,seed=487,bank=None):
 keys,aa,bb=exact_pair(a,b);d=aa-bb;days=sorted({k[0] for k in keys})
 if bank is None:bank=make_bank(reps,block,seed,{s:sum(k[0]==s for k in keys) for s in days})
 samples=[];effects=[]
 for s in days:
  arr=d[[i for i,k in enumerate(keys) if k[0]==s]];idx=bank[s]
  if idx.shape!=(reps,len(arr)) or idx.min()<0 or idx.max()>=len(arr):raise ValueError('index bank support')
  samples.append(arr[idx].mean(axis=1));effects.append(arr.mean(axis=0))
 point=np.mean(effects,axis=0);lo,hi=np.percentile(np.mean(samples,axis=0),[2.5,97.5],axis=0)
 return dict(estimate=point,conditional_low=lo,conditional_high=hi,per_session=np.array(effects),sessions_same_sign=(np.sign(effects)==np.sign(point)).sum(axis=0))

def latechecks(rows):
 masks={};meta={}
 for r in rows:
  run=r['run_id'];key=(run,r['exposure']);q=r['queried']
  ident=tuple(r[f] for f in ('model','bounds','session','schedule_id','schedule_driver','budget','seed'))
  if meta.setdefault(run,ident)!=ident or masks.setdefault(key,q)!=q:raise ValueError('mask/identity conflict')
 out=[]
 for run,v in sorted(meta.items()):
  s=v[2];n=HORIZONS[s];q=[masks.get((run,e)) for e in range(1,n+1)]
  if None in q or sum(q)!=v[5]:raise ValueError('mask support/quota')
  out.append(dict(zip(('model','bounds','session','schedule_id','schedule_driver','budget','seed'),v),run_id=run,total=sum(q),last10=sum(q[max(0,n-10):]),at_final=q[-1]))
 return out

def stratum_metrics(pred,ref):
 pred=np.asarray(pred);ref=np.asarray(ref)
 if pred.ndim!=2 or ref.shape!=(len(pred),):raise ValueError('stratum shape')
 a=np.abs(pred-ref[:,None]);n=a.size
 out={'outputs':n,'exposures':len(ref),'abs_sum':float(a.sum()),'mae':float(a.mean()) if n else None,'rmse':float(np.sqrt((a*a).mean())) if n else None,'bias':float((pred-ref[:,None]).mean()) if n else None}
 for t in TOLS:out.update({f'exceed_count_{t}':int((a>t).sum()),f'exceed_rate_{t}':float((a>t).mean()) if n else None})
 rel=a>np.where(ref>0,.1*ref,1.)[:,None]
 out.update(relative_count=int(rel.sum()),relative_rate=float(rel.mean()) if n else None)
 return out

class AffineRLS:
 """Inverse affine RLS; forgetting clock is purchased references only."""
 def __init__(self,m_hist,y_hist,lam_new=1.,ridge=1.):
  m_hist=np.asarray(m_hist,float);y_hist=np.asarray(y_hist,float)
  if m_hist.ndim!=1 or y_hist.shape!=m_hist.shape or len(m_hist)==0 or not np.isfinite(m_hist).all() or not np.isfinite(y_hist).all():raise ValueError('historical vector length/shape/finite')
  if not np.isfinite([lam_new,ridge]).all() or not 0<lam_new<=1 or ridge<=0:raise ValueError('lambda/ridge')
  self.mu=m_hist.mean();s=m_hist.std();self.scale_fallback=bool(s<1e-8);self.s=1. if self.scale_fallback else s
  self.theta=np.zeros(2);self.P=np.eye(2)/ridge;self.lam_new=lam_new;self.failures=0;self.events=[];self.last_change=0.;self.last_leverage=None;self.last_update_success=False
  for m,y in zip(m_hist,y_hist):self._update(m,y,1.)
 def validate_state(self):
  if self.theta.shape!=(2,) or self.P.shape!=(2,2) or not np.isfinite(self.theta).all() or not np.isfinite(self.P).all() or not np.allclose(self.P,self.P.T,atol=1e-12) or np.linalg.eigvalsh(self.P).min()<=0:raise ValueError('invalid recursive state')
 def phi(self,m):
  if not np.isscalar(m) or not np.isfinite(m):raise ValueError('finite scalar regressor')
  return np.array([(m-self.mu)/self.s,1.])
 def predict(self,m):
  self.validate_state();yh=m+self.phi(m)@self.theta
  if not np.isfinite(yh):self.failures+=1;self.events.append({'kind':'prediction_fallback'});return m
  return yh
 def variance_score(self,m):
  """Unscaled phi'P phi information proxy, not physical covariance."""
  self.validate_state();p=self.phi(m);return float(p@self.P@p)
 def _update(self,m,y,lam):
  self.validate_state()
  if not np.isscalar(y) or not np.isfinite(y) or not 0<lam<=1:raise ValueError('update input')
  self.last_change=0.;self.last_leverage=None;self.last_update_success=False
  p=self.phi(m)
  with np.errstate(over='ignore',invalid='ignore',divide='ignore'):
   leverage=float(p@self.P@p);den=lam+leverage
   if not np.isfinite(den) or den<=0:
    self.failures+=1;self.events.append({'kind':'update_fallback','lambda':lam,'regressor':float(m),'reference':float(y)});return
   v=self.P@p;theta=self.theta+v/den*((y-m)-p@self.theta);P=(self.P-np.outer(v,v)/den)/lam;P=(P+P.T)/2
  if not np.isfinite(theta).all() or not np.isfinite(P).all() or np.linalg.eigvalsh(P).min()<=0:
   self.failures+=1;self.events.append({'kind':'update_fallback','lambda':lam,'regressor':float(m),'reference':float(y)});return
  change=float(np.linalg.norm(theta-self.theta));self.theta,self.P=theta,P
  self.last_change=change;self.last_leverage=leverage;self.last_update_success=True
 def update_purchased(self,m,y):self._update(m,y,self.lam_new)

def cmd_rlstest(args):
 rng=np.random.default_rng(1);m=rng.uniform(0,20,100);y=.9*m+.7+rng.normal(0,.5,100);r=AffineRLS(m,y)
 X=np.column_stack(((m-r.mu)/r.s,np.ones(100)));batch=np.linalg.solve(X.T@X+np.eye(2),X.T@(y-m))
 np.testing.assert_allclose(r.theta,batch,atol=1e-8,rtol=0)
 for lam in (.95,.90):np.testing.assert_array_equal(AffineRLS(m,y,lam).theta,r.theta)
 print('RLS self-test PASS')

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('command',choices=['rlstest','validate']);ap.add_argument('--input');a=ap.parse_args()
 if a.command=='rlstest':cmd_rlstest(a)
 else:print('validated outputs',len(load(a.input)))
