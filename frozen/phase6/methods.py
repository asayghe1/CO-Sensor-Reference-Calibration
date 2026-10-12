"""Fixed fusion and observable-only scoring; no current reference inputs."""
import hashlib,math
import numpy as np
ALLOWED=(1,2,3,4,5,6,8,9,10,11,12,13)
POINTS=('target_transfer','peer_single','peer_mean','peer_median','peer_trimmed','peer_huber','target_peer_huber')
def guard_role(day,target,peers):
 if day not in (6,8,10) or target not in ALLOWED or len(peers)!=5 or target in peers or any(u not in ALLOWED for u in peers):raise ValueError('reserved/invalid physical role')
 if len(set(peers))!=5 or any((u<8)!=(target<8) for u in peers):raise ValueError('invalid peer identity')
def validate_packet(p):
 allowed={'target_prediction','peer_predictions','target_features','peer_confidence','target_scores'}
 if set(p)-allowed or set(p.get('target_scores',{}))-{'confidence','environment','prior_residual','feature_distance'}:raise ValueError('nonobservable packet field')
def huber(p):
 p=np.asarray(p,float);center=np.median(p,axis=-1);s=1.4826*np.median(np.abs(p-center[...,None]),axis=-1)
 lo=np.min(p,axis=-1);hi=np.max(p,axis=-1);c=1.345*s
 for _ in range(80):
  z=(lo+hi)/2;der=np.clip(p-z[...,None],-c[...,None],c[...,None]).sum(axis=-1)
  lo=np.where(der>0,z,lo);hi=np.where(der<=0,z,hi)
 return np.where(s==0,center,(lo+hi)/2)
def fuse(target,peers):
 p=np.asarray(peers,float);t=np.asarray(target,float);q=np.sort(p,axis=-1)
 return {'target_transfer':t,'peer_single':p[...,0],'peer_mean':p.mean(axis=-1),'peer_median':np.median(p,axis=-1),'peer_trimmed':q[...,1:-1].mean(axis=-1),'peer_huber':huber(p),'target_peer_huber':huber(np.concatenate([t[...,None],p],axis=-1))}
def quantile(errors,level=.9):
 v=np.sort(np.asarray(errors));k=math.ceil(level*(len(v)+1))
 if k>len(v) or k<1:raise ValueError('insufficient calibration exposure groups')
 return float(v[k-1])
def alert_quantile(values,level=.95):
 v=np.sort(np.asarray(values));k=math.ceil(level*len(v))
 if k<1 or k>len(v):raise ValueError('invalid alert percentile')
 return float(v[k-1])
def context(features,peers):return np.column_stack([np.asarray(features)[:,4:6],np.sort(peers,axis=1)])
def compute_scores(packet,cal_context,cal_median_residual):
 validate_packet(packet);p=np.asarray(packet['peer_predictions']);target=np.asarray(packet['target_prediction']);med=np.median(p,axis=1)
 mad=np.median(np.abs(p-med[:,None]),axis=1);d=np.abs(target-med);scale=1.4826*mad
 ratio=np.divide(d,scale,out=np.where(d==0,0.,1e12),where=scale>0)
 cx=context(packet['target_features'],p);mean=cal_context.mean(axis=0);sd=cal_context.std(axis=0);sd=np.where(sd==0,1,sd)
 distance=np.sum(((cx[:,None,:]-cal_context[None,:,:])/sd)**2,axis=2)
 neighbors=np.argsort(distance,axis=1,kind='stable')[:,:5]
 out={'disagreement':d,'peer_mad':mad,'peer_range':np.ptp(p,axis=1),'normalized_disagreement':ratio,'environment':np.asarray(packet['target_scores']['environment']),'transfer_prior_residual':np.asarray(packet['target_scores']['prior_residual']),'consensus_prior_residual':np.asarray(cal_median_residual)[neighbors].mean(axis=1),'width':np.zeros(len(p)),'hash_only':np.zeros(len(p))}
 if packet['peer_confidence'] is not None:
  out['target_confidence']=np.asarray(packet['target_scores']['confidence']);out['peer_confidence']=np.asarray(packet['peer_confidence']).mean(axis=1)
 return out

def select_group(channel_scores,ids,rate):
 scores=np.max(np.asarray(channel_scores),axis=0);k=max(1,math.floor(rate*len(ids)))
 order=sorted(range(len(ids)),key=lambda i:(float(scores[i]),hashlib.sha256(('487:'+ids[i]).encode()).hexdigest()))
 m=np.zeros(len(ids),bool);m[order[:k]]=True;return m

def metrics(y,p,q,mask):
 y=np.asarray(y);p=np.asarray(p);m=np.asarray(mask,bool);e=p-y;a=np.abs(e)
 r={'n':int(m.sum()),'retained':float(m.mean()),'mae':float(a[m].mean()),'rmse':float(np.sqrt((e[m]**2).mean())),'bias':float(e[m].mean()),'coverage':None,'width':None,'interval_score':None}
 if q is not None:
  qq=np.broadcast_to(q,y.shape);r.update(coverage=float((a[m]<=qq[m]).mean()),width=float((2*qq[m]).mean()),interval_score=float((2*qq[m]+20*np.maximum(a[m]-qq[m],0)).mean()))
 for tol in [.5,1.,2.]:
  valid=a<=tol;r['false_rejection_'+str(tol)]=float((valid&~m).sum()/valid.sum()) if valid.any() else None
 return r
