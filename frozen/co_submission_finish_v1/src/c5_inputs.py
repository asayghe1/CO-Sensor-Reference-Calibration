"""Frozen final input adapter. Not invoked by preparation or preflight.
Caller must supply explicit authorization. Only allowed columns converted;
reference values stay in a separate outcome object, never observable packets.
"""
from pathlib import Path
import json,hashlib
import numpy as np
import joblib
UNITS=(1,2,3,4,5,6,8,9,10,11,12,13)
FILES={11:'20161013_143355.csv',12:'20161014_184659.csv',13:'20161016_053656.csv'}
OUT=Path(__file__).resolve().parents[1]
def prepare_session(path,day,authorized=False):
 if not authorized:raise PermissionError('Explicit C5 authorization required before payload opening')
 path=Path(path)
 if day not in FILES or path.name!=FILES[day]:raise ValueError('fixed final filename/day')
 frozen=json.loads((OUT/'C5_INPUT_MANIFEST.json').read_text())
 expected=next(v for v in frozen['raw_inventory'] if v['name']==path.name)
 if hashlib.sha256(path.read_bytes()).hexdigest()!=expected['sha256']:raise ValueError('raw integrity failure')
 a=[];refs=[]
 with path.open() as f:
  if f.readline().strip().split(',')!=frozen['header']:raise ValueError('schema failure')
  for line in f:
   v=line.strip().split(',')
   if len(v)!=20:raise ValueError('row schema')
   # Never convert R7/R14, flow or injected-concentration fields.
   a.append([float(v[i]) for i in (0,2,3,5,*[u+5 for u in UNITS])]);refs.append(float(v[1]))
 a=np.array(a);refs=np.array(refs);t=a[:,0]
 if not np.isfinite(a).all() or not np.isfinite(refs).all() or np.any(np.diff(t)<=0) or np.any(a[:,4:]<=0):raise ValueError('scientific input grouping/quality failure')
 high=a[:,3]>.5;previous=np.maximum.accumulate(np.where(np.r_[True,np.diff(high.astype(int))!=0],t,-np.inf));phase=t-previous
 features=[];y=[]
 for e in range(1,101):
  core=(t>=900*e+600)&(t<900*(e+1)-60);times=t[core]
  if len(times)<=500 or t[0]>900*e or t[-1]<900*(e+1)-10 or np.max(np.diff(times))>=5:raise ValueError('missing/incomplete required exposure: evaluation invalid')
  if len(np.unique(refs[core]))!=1:raise ValueError('reference grouping failure: evaluation invalid')
  masks=[core&high,core&~high&(phase<5),core&~high&(phase>=5)&(phase<15),core&~high&(phase>=15)]
  if min(m.sum() for m in masks)<10:raise ValueError('missing phase: evaluation invalid')
  features.append([[float(np.median(np.log(a[m,j+4]))) for m in masks]+[float(np.median(a[core,1])),float(np.median(a[core,2]))] for j in range(12)]);y.append(float(refs[core][0]))
 x=np.array(features);manifest=json.loads((OUT/'MODEL_MANIFEST.json').read_text());pp=[];ts=[]
 if [v['unit'] for v in manifest['models']]!=list(UNITS) or [v['unit'] for v in manifest['D10_normalization']]!=list(UNITS):raise ValueError('unit order integrity failure')
 for j,item in enumerate(manifest['models']):
  p=OUT/item['file']
  if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('model integrity failure')
  model=joblib.load(p);pp.append(model.predict(x[:,j]));ts.append(np.std([tree.predict(model[0].transform(x[:,j])) for tree in model[-1].estimators_],axis=0))
 pp=np.array(pp).T;ts=np.array(ts).T;cm=[];z=[];confidence=[]
 for j,norm in enumerate(manifest['D10_normalization']):
  peers=[i for i,u in enumerate(UNITS) if (u<8)==(UNITS[j]<8) and i!=j];m=np.median(pp[:,peers],axis=1);cm.append(m)
  raw=np.column_stack([x[:,j,4:6],m]);z.append((raw-norm['context_mean'])/norm['context_scale']);confidence.append(ts[:,peers].mean(1)/norm['confidence_scale'])
 return {'consensus':np.array(cm).T,'z':np.stack(z,axis=1),'confidence':np.max(confidence,axis=0)},np.array(y)
