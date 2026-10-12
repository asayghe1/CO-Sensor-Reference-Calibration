import numpy as np
from c5_evaluate import evaluate,aggregate
# Own-center radius differs from midpoint radius; equality is not an exceedance.
n=100;cons=np.zeros((n,12));lo=np.full((n,12),-1.);hi=np.full((n,12),1.);bad=np.zeros((n,12),bool);bad[0,0]=True
r={'predictions':{'consensus':cons,'midpoint':cons,'projection':np.full((n,12),.5),'affine':cons},'query':np.zeros(n,bool),'error_lower':lo,'error_upper':hi,'contradiction':bad,'numerical_failures':0}
y=np.ones(n);rows=evaluate(r,y,r)
x=next(v for v in rows if v['estimator']=='midpoint' and v['scope']=='ALL' and v['subset']=='all');assert x['false_1.0']==0 and x['assured_1.0']==1199
p=next(v for v in rows if v['estimator']=='projection' and v['scope']=='ALL' and v['subset']=='all');assert p['assured_1.0']==0 and p['false_over_assured_1.0'] is None
assert next(v for v in rows if v['subset']=='queried')['mae'] is None
x=evaluate(r,np.full(n,1.1),r);v=next(v for v in x if v['estimator']=='midpoint' and v['scope']=='ALL' and v['subset']=='all');assert v['false_1.0']==1199 and v['reported_noncontainment']==1200
allrows=[dict(v,day=d,policy='none',budget=0,seed=487) for d in (11,12,13) for v in x]
a=next(v for v in aggregate(allrows) if v['estimator']=='midpoint' and v['scope']=='ALL' and v['subset']=='all');assert a['false_1.0']==3597 and a['assured_1.0']==3597 and a['false_over_assured_1.0']==1
print('Boundary, contradiction, own-center assurance, NA and aggregation tests PASS')
