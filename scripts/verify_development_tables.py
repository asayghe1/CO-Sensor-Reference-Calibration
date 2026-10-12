"""Rebuild main/supplement from verified full-precision development evaluations."""
from pathlib import Path
import csv,json,gzip,shutil,zipfile
import numpy as np
import os
from context import DEV as E, PAPER as P, report

def read(name):return list(csv.DictReader((E/name).open()))
A=read('AGGREGATE_METRICS.csv');S=read('SESSION_METRICS.csv');F=read('CONDITIONAL_RESAMPLING_EFFECTS.csv')
T=read('QUERY_TIMING_BY_RUN.csv');X=read('SLOPE95_CROSSTAB.csv');I=read('INTERVAL_DIAGNOSTICS.csv')
LABEL={'consensus':'Consensus','midpoint':'Midpoint','projection':'Projection','offset':'Offset','affine':r'Affine $\lambda=1$','affine_l095':r'Affine $\lambda=.95$','affine_l090':r'Affine $\lambda=.90$'}
SCH={'none':'Historical only','periodic':'Periodic','random':'Random','confidence':'Confidence','envelope':'Envelope','rlsvar':'Information'}
def find(rows,**kw):
 vals=[r for r in rows if all(r.get(k)==str(v) for k,v in kw.items())]
 if len(vals)!=1:raise ValueError((kw,len(vals)))
 return vals[0]
def agg(est='affine',sch='none',b=0,scope='ALL',model='RF',subset='all',band='ALL'):
 return find(A,estimator=est,schedule=sch,budget=b,scope=scope,model=model,bounds='primary',subset=subset,band=band)
def eff(est='affine',sch='none',b=0,scope='ALL',metric='mae',length=10,effect=None,model='RF'):
 return find(F,estimator=est,schedule=sch,budget=b,scope=scope,model=model,bounds='primary',metric=metric,block_length=length,effect=effect or ('historical' if b==0 else 'incremental'))
def num(v,d=4,scale=1):return 'NA' if v is None or v=='' else f'{float(v)*scale:.{d}f}'
def ci(r,d=4):return '['+num(r['conditional_low'],d)+', '+num(r['conditional_high'],d)+']'
checked = {}
def table(name,caption,label,headers,rows,align=None,long=False):
 expected=[' & '.join(map(str,row)) for row in rows]
 actual=[]
 for line in (P/name).read_text().splitlines():
  line=line.strip()
  if ' & ' in line and line.endswith(r'\\'):
   actual.append(line[:-2].strip())
 assert actual==expected, (name, len(actual), len(expected))
 checked[name]=len(actual)

# Main historical table, retaining both families prominently.
rows=[]
for scope in ('Figaro','FIS','ALL'):
 c=agg('consensus',scope=scope);a=agg(scope=scope);h=eff(scope=scope);hp=eff(scope=scope,metric='p1.0')
 rows.append([scope,num(c['mae']),num(a['mae']),num(h['estimate']),ci(h),num(c['exceed_rate_1.0'],2,100),num(a['exceed_rate_1.0'],2,100)])
table('table_historical.tex','RF historical-only results. Family emphasis is a declared development extension; pooled results retain the original endpoint. MAE in ppm, $P_1$ in percent; brackets are conditional resampling intervals (length 10).','tab:historical',['Scope','Consensus','Affine','$H$ MAE','Conditional bounds','Raw $P_1$','Affine $P_1$'],rows,'lrrrrrr')
rows=[]
for day in ('D6','D8','D10'):
 for fam in ('Figaro','FIS'):
  c=find(S,model='RF',bounds='primary',estimator='consensus',schedule='none',budget=0,scope=fam,subset='all',band='ALL',session=day)
  a=find(S,model='RF',bounds='primary',estimator='affine',schedule='none',budget=0,scope=fam,subset='all',band='ALL',session=day)
  rows.append([day,fam,num(c['mae']),num(a['mae']),num(float(a['mae'])-float(c['mae'])),num(c['exceed_count_1.0'],0),num(a['exceed_count_1.0'],0)])
table('table_family.tex','Exact historical-only RF family/session values from prediction arrays; each cell has 100 exposures and 600 outputs. Counts are strict 1 ppm exceedances.','tab:family',['Day','Family','Raw MAE','Affine MAE','$H$ MAE','Raw count','Affine count'],rows,'llrrrrr')
rows=[]
for est in ('affine','affine_l095','affine_l090'):
 for sch in ('periodic','random','confidence','envelope','rlsvar'):
  r=eff(est,sch,20);rp=eff(est,sch,20,metric='p1.0')
  rows.append([LABEL[est],SCH[sch],num(r['estimate']),ci(r),num(rp['estimate'],2),ci(rp,2),r['negative_sessions']+'/3'])
table('table_incremental.tex','RF B20 changes from each affine estimator\'s common B0. Positive values worsen the endpoint. Conditional 95\\% resampling bounds use block length 10. Last column counts sessions with a negative MAE change. All budgets, families and lengths are in the supplement.','tab:incremental',['Estimator','Schedule','$I$ MAE','Conditional bounds','$I$ $P_1$ (pp)','Bounds (pp)','MAE $<0$'],rows,'llrrrrr')
# Original bound failures plus native branch; weighted random counts.
rows=[]
for sch,b in [('none',0),('periodic',20),('random',20),('confidence',20),('envelope',20),('rlsvar',20)]:
 rr=[r for r in I if r['model']=='RF' and r['bounds']=='primary' and r['estimator']=='midpoint' and r['scope']=='ALL' and r['subset']=='all' and r['schedule']==sch and r['budget']==str(b)]
 width=np.mean([float(r['width_mean']) for r in rr]);non=np.mean([int(r['reported_noncontainment']) for r in rr]);ass=np.mean([int(r['assured_count']) for r in rr]);rows.append([SCH[sch],b,num(width),num(100*(1-non/1200),2),num(100*ass/1200,2)])
table('table_bounds.tex','RF midpoint interval diagnostics on all exposures. Fractions average seeds within sessions and sessions equally; flags require a noncontradictory radius at most 1 ppm.','tab:bounds',['Schedule','$B$','Width (ppm)','Contained (\\%)','Flagged (\\%)'],rows,'lrrrr')
# Sup complete primary RF family grids, common B0 printed once across lambda names.
rows=[]
for scope in ('ALL','Figaro','FIS'):
 for est in LABEL:
  for b in (0,5,10,20):
   if b==0 and est in ('affine_l095','affine_l090'):continue
   for sch in (('none',) if b==0 else ('periodic','random','confidence','envelope','rlsvar')):
    r=agg(est,sch,b,scope);de=eff(est,sch,b,scope)
    rows.append([scope,LABEL[est],SCH[sch],b,num(r['mae']),num(r['exceed_rate_1.0'],2,100),num(de['estimate']),num(r['relative_rate'],2,100)])
table('table_s_all.tex','Complete primary RF all-exposure family and pooled grid. Rates in percent; changes from consensus at B0 and own B0 at positive budgets, in ppm. The three affine B0 states are identical. Ten random seeds averaged within each day. Full precision and exact counts reside in accompanying CSVs.','tab:s_all',['Scope','Estimator','Schedule','$B$','MAE','$P_1$','$\\Delta$ MAE','Relative'],rows,'llllrrrr',True)
rows=[]
for model in ('OLS','Ridge'):
 for scope in ('ALL','Figaro','FIS'):
  for est in ('consensus','affine','affine_l095'):
   for b in (0,20):
    if b==0 and est=='affine_l095':continue
    for sch in (('none',) if b==0 else ('periodic','random','confidence','envelope','rlsvar')):
     r=agg(est,sch,b,scope,model);de=eff(est,sch,b,scope,model=model)
     rows.append([model,scope,LABEL[est],SCH[sch],b,num(r['mae']),num(r['exceed_rate_1.0'],2,100),num(de['estimate'])])
table('table_s_models.tex','M9: saved OLS/ridge inputs, unchanged consensus and inverse affine factors 1/.95 at B0/B20. Model-specific confidence and envelope masks retained. Common affine B0 shown once.','tab:s_models',['Model','Scope','Estimator','Schedule','$B$','MAE','$P_1$','$\\Delta$ MAE'],rows,'llllrrrr',True)
# Family concentration support including empty bands.
rows=[]
for day in ('D6','D8','D10'):
 for fam in ('Figaro','FIS'):
  for band in ('[0,5]','(5,10]','(10,20]'):
   r=find(S,model='RF',bounds='primary',estimator='affine',schedule='none',budget=0,scope=fam,subset='all',session=day,band=band)
   rows.append([day,fam,band,num(r['exposures'],0),num(r['outputs'],0),num(r['mae']),num(r['exceed_rate_1.0'],2,100),num(r['relative_rate'],2,100)])
table('table_s_support.tex','RF affine B0 concentration support. Boundaries are evaluation-only; the relative research tolerance is 10\\% when reference is positive and 1 ppm at zero. All arms/subsets retain exact support in the CSV.','tab:s_support',['Day','Family','Band','Exposures','Outputs','MAE','$P_1$','Relative (\\%)'],rows,'lllrrrrr',True)
rows=[]
for model in ('RF','OLS','Ridge'):
 for b in ((5,10,20) if model=='RF' else (20,)):
  for sch in ('periodic','random','confidence','envelope','rlsvar'):
   rr=[r for r in T if r['model']==model and r['bounds']=='primary' and r['schedule']==sch and r['budget']==str(b)]
   daymeans=[{f:np.mean([float(r[f]) for r in rr if r['session']==d]) for f in ('last10','at_final')} for d in ('D6','D8','D10')]
   rows.append([model,SCH[sch],b,num(np.mean([d['last10'] for d in daymeans]),2),num(np.mean([d['at_final'] for d in daymeans]),2)])
table('table_s_timing.tex','Paid query timing, mean per session after random-seed averaging. Only the final query has no later scored prediction under day reset; no purchase is refunded. Per-run queries remain in the archive.','tab:s_timing',['Model','Schedule','$B$','Last 10','At final'],rows,'llrrr',True)
rows=[]
for bad in (0,1):
 for raw in (0,1):
  for hull in (0,1):
   for assured in (0,1):
    rr=[r for r in X if r['model']=='RF' and r['schedule']=='envelope' and r['budget']=='20' and r['contradiction']==str(bad) and r['raw_noncontainment']==str(raw) and r['hull_noncontainment']==str(hull) and r['assurance1']==str(assured)]
    rows.append([bad,raw,hull,assured,sum(int(r['count']) for r in rr)])
table('table_s_cross.tex','Complete RF slope95/envelope B20 cross-tab, 3,600 outputs. All zero cells retained. Reported hull is the original numerical fallback on contradictions. Exact identities are saved.','tab:s_cross',['Contradiction','Raw outside','Reported outside','Assured','Count'],rows,'rrrrr')
rows=[]
for scope in ('ALL','Figaro','FIS'):
 for est in ('affine','affine_l095','affine_l090'):
  for sch in ('envelope','rlsvar'):
   for length in (5,10,20):
    r=eff(est,sch,20,scope,length=length)
    rows.append([scope,LABEL[est],SCH[sch],length,num(r['estimate']),ci(r),num(r['D6']),num(r['D8']),num(r['D10'])])
table('table_s_resampling.tex','Conditional resampling sensitivity, B20 envelope/information schedules. All three session changes and block lengths retained; the complete endpoint/comparator grid is in CONDITIONAL\\_RESAMPLING\\_EFFECTS.csv. Bounds condition on original fits, paths and references.','tab:s_resampling',['Scope','Estimator','Schedule','$L$','$I$ MAE','Bounds','D6','D8','D10'],rows,'lllrrrrrr',True)

report('DEVELOPMENT_TABLES.json',{'status':'PASS','rows_by_file':checked,'method':'Original table formatting applied to frozen CSV cells; completed captions and prose retained.'})
print('Development table cells:',sum(checked.values()),'PASS')
