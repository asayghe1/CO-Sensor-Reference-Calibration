"""Rebuild main/supplement from verified full-precision development evaluations."""
from pathlib import Path
import csv,json,gzip,shutil,zipfile
import numpy as np
import os
W=Path(__file__).resolve().parents[1];E=W/'evidence';P=W/'paper'
os.environ.setdefault('MPLCONFIGDIR',str(W/'mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

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
def put(name,text):(P/name).write_text(text)
def template(name):
 with zipfile.ZipFile(W.parents[0]/'inputs/Measurement_CO_Revised_LaTeX.zip') as z:return z.read(name).decode()
def table(name,caption,label,headers,rows,align=None,long=False):
 if long:
  text=r'\small\setlength{\tabcolsep}{4pt}'+'\n'+r'\begin{longtable}{'+(align or 'l'*len(headers))+'}\n'+r'\caption{'+caption+r'}\label{'+label+r'}\\'+'\n'+r'\toprule'+'\n'+' & '.join(headers)+r' \\ \midrule\endfirsthead'+'\n'+r'\toprule'+'\n'+' & '.join(headers)+r' \\ \midrule\endhead'+'\n'+r'\bottomrule\endfoot'+'\n'
 else:
  text=r'\begin{table}[!htbp]\centering\small'+'\n'+r'\caption{'+caption+r'}\label{'+label+'}\n'+r'\setlength{\tabcolsep}{4pt}\begin{tabular}{'+(align or 'l'*len(headers))+'}\n'+r'\toprule'+'\n'+' & '.join(headers)+r' \\ \midrule'+'\n'
 text+='\n'.join(' & '.join(map(str,row))+r' \\' for row in rows)
 text+='\n'+(r'\end{longtable}\normalsize' if long else r'\bottomrule\end{tabular}\end{table}')+'\n';put(name,text)
 # Inspectable table rendering from identical text/numerical rows, chunked to readable pages.
 rd=W/'rendered_tables';rd.mkdir(exist_ok=True)
 for part in range(0,len(rows),35):
  fig,ax=plt.subplots(figsize=(max(8,len(headers)*1.5),max(2,(min(35,len(rows)-part)+2)*.27)));ax.axis('off')
  clean=lambda s:str(s).replace('\\lambda', 'λ').replace('\\%','%').replace('$','').replace('\\Delta','Δ').replace('\\','')
  cells=[[clean(c) for c in row] for row in rows[part:part+35]]
  tab=ax.table(cellText=cells,colLabels=[clean(h) for h in headers],loc='center',cellLoc='left');tab.auto_set_font_size(False);tab.set_fontsize(8);tab.auto_set_column_width(list(range(len(headers))));fig.tight_layout();fig.savefig(rd/f'{name[:-4]}_{part//35+1}.png',dpi=110);plt.close(fig)

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
# Figures replace duplication with exact family B0 and per-day effect markers.
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,2,figsize=(8,3.4),layout='constrained')
for ax,scope in zip(axes,('Figaro','FIS')):
 vals=[float(agg(e,scope=scope)['mae']) for e in ('consensus','affine')];ax.bar([0,1],vals,color=['#687d8c','#236f9e'],width=.55)
 for d,marker in zip(('D6','D8','D10'),('o','s','^')):
  vv=[float(find(S,model='RF',bounds='primary',estimator=e,schedule='none',budget=0,scope=scope,subset='all',band='ALL',session=d)['mae']) for e in ('consensus','affine')];ax.plot([0,1],vv,marker=marker,ls='',color='#c95d3a',label=d,markersize=5)
 ax.set_xticks([0,1],['Consensus','Affine B0']);ax.set_title(scope);ax.set_ylabel('MAE (ppm)');ax.legend(fontsize=7)
fig.savefig(P/'fig_1_historical_mae.pdf');fig.savefig(P/'fig_1_historical_mae.png',dpi=170);plt.close(fig)
for metric,file,ylabel in [('mae','fig_2_affine_increment_mae','Incremental MAE (ppm)'),('p1.0','fig_3_affine_increment_exceedance','Incremental >1 ppm (percentage points)')]:
 fig,axes=plt.subplots(1,3,figsize=(10,3.4),layout='constrained',sharey=True)
 for ax,est in zip(axes,('affine','affine_l095','affine_l090')):
  for j,sch in enumerate(('periodic','random','confidence','envelope','rlsvar')):
   rs=[eff(est,sch,b,metric=metric) for b in (5,10,20)];color=plt.cm.tab10(j);vals=[0]+[float(r['estimate']) for r in rs]
   ax.plot([0,5,10,20],vals,marker='o',markersize=3,label=SCH[sch],color=color,lw=1.2)
   for day,mark in zip(('D6','D8','D10'),('o','s','^')):ax.scatter([5,10,20],[float(r[day]) for r in rs],marker=mark,s=12,color=color,alpha=.35)
  ax.axhline(0,color='black',lw=.5);ax.set_title({'affine':'λ = 1','affine_l095':'λ = .95','affine_l090':'λ = .90'}[est]);ax.set_xticks([0,5,10,20]);ax.set_xlabel('Additional shared references')
 axes[0].set_ylabel(ylabel);axes[-1].legend(fontsize=7,loc='upper left');fig.savefig(P/(file+'.pdf'));fig.savefig(P/(file+'.png'),dpi=170);plt.close(fig)
# Persist table-level full precision provenance alongside presentation assets.
for name in ('AGGREGATE_METRICS.csv','SESSION_METRICS.csv','CONDITIONAL_RESAMPLING_EFFECTS.csv','LOSS_TIME_STRUCTURE.csv','EXCEEDANCE_SHARES.csv','RESAMPLING_INDEX_MANIFEST.json','QUERY_TIMING_BY_RUN.csv','INTERVAL_DIAGNOSTICS.csv','SLOPE95_CROSSTAB.csv','METRICS_BY_RUN_FAMILY_BAND_SUBSET.csv','METRICS_BY_CONFIGURATION.csv'):
 shutil.copy2(E/name,P/name)
# Retain manuscript setting and definitions; move conditional proofs to supplement.
methods=template('section_3_methods.tex')
start=methods.index('The forgetting factor is 1.');end=methods.index('\\subsection{Contextual residual envelopes}',start)
methods=methods[:start]+r'''The original cumulative estimator ($\lambda=1$) remains primary. A declared development extension uses $\lambda=.95$ as comparator and $.90$ as sensitivity, fixed before these new scores. Historical assimilation always uses $\lambda=1$, giving an identical B0 state. At a purchased reference only, replace the gain denominator by $\lambda+\phi^\top P\phi$ and set $P^+=(P-k\phi^\top P)/\lambda$. After $k$ purchases, old information and the original ridge term are discounted by $\lambda^k$: $.95^{20}\simeq.36$ and $.90^{20}\simeq.12$. This is information weighting, not a fraction of prediction influence. Nonzero gains also occur for $\lambda=1$; the actual update depends on leverage and innovation. Coefficient changes, information matrices and purchased-regressor leverage are archived. Recursive identification is established methodology \cite{ljung1983}. This inverse correction is not a forward physical gain/offset model.

'''+methods[end:]
start=methods.index('If $\\ell>u$');end=methods.index('\\subsection{Reference schedules',start)
proof=methods[start:end]
methods=methods[:start]+r'''A contradictory raw intersection ($\ell>u$) uses a descriptive hull for the midpoint and unchanged consensus for projection; neither receives assurance. An assurance flag requires a noncontradictory intersection and its own radius $R(c)\leq\tau$. Conditional properties and fallback definitions are in Supplement S2. These sets are conditional residual bounds, without a calibrated physical coverage probability.

'''+methods[end:]
start=methods.index('The envelope algorithm is a');end=methods.index('\\begin{table}',start)
methods=methods[:start]+r'''The envelope algorithm generates the original shared masks; all correction estimators consume those saved masks. One additional information-driven controller uses the fixed $\lambda=.95$ driver and score $\max_h\phi_{h,t}^\top P_{h,t}\phi_{h,t}$. This is an unscaled leverage/information proxy, not a physical prediction variance. Its history starts with the 100 historical regressors scored using the initialized driver matrix, then appends pre-query current scores. It uses the same quantile and forcing rule. Each model/day/budget has one distinct saved native mask, shared by every evaluated estimator. The $.95$ estimator on its own mask is a coupled comparator; other lambdas on that mask are fixed-schedule ablations. No scheduling variant was chosen by its outcome.

'''+methods[end:]
put('section_3_methods.tex',methods)
put('supplement_properties.tex',proof)
# Replace evaluation with compact transparent definitions.
put('section_4_evaluation.tex',r'''\section{Evaluation endpoints}\label{sec:evaluation}
Let $r_{h,d,t}=\widehat y_{h,d,t}-y_{d,t}$. MAE averages $|r|$ and $P_\tau$ averages $\mathbf1\{|r|>\tau\}$ over configurations within exposure, exposures within session, fixed random seeds within session, and then the three sessions equally. The original pooled primary endpoint is strict 1 ppm exceedance, with MAE and 0.5/2 ppm sensitivities. Family-stratified reporting is a declared extension informed by earlier development results, not a retroactive claim of original preregistration. Both families and every fixed seed remain included. Positive-budget effects use the same estimator's own B0 on identical exposure keys. RMSE, bias, interval containment, width, and numerator/denominator counts are retained separately.

All predictions are scored before their own reference is purchased. Queried and unqueried subsets retain their exact counts, unchanged-consensus comparison and own-B0 comparison on that same subset. Different policies' unqueried subsets have different membership; comparing their means alone cannot identify predictive improvement. Reference concentration bands $[0,5]$, $(5,10]$, $(10,20]$ ppm are used only during evaluation, with support and undefined strata retained. A relative research-tolerance sensitivity uses 10\% of positive reference and 1 ppm at zero; it is not an instrument specification or an inference-time input.

\paragraph{Conditional resampling sensitivity.}
Each deterministic pooled evaluation comprises 300 shared exposures and 3,600 correlated configuration outputs. One indicator flip changes $P_1$ by $100/3600=0.02778$ percentage points; seed-averaged arithmetic can have smaller increments without extra physical replication. We retain the three session effects and their direction counts. Paired overlapping moving blocks of length 10 are resampled within each session, with 2,000 replicates and seed 487. Lengths 5 and 20 are declared sensitivities. A single saved index bank per length/session serves all arms, families and endpoints. Exact exposure and metric support is checked before pairing; configurations are never independently resampled.

Percentile 2.5/97.5 bounds are called conditional resampling intervals. They hold fits, historical calibration, query trajectories, labels and apparatus fixed; adaptive learning is not rerun, and reference uncertainty is not propagated. Ordinary moving-block resampling needs dependence and regularity assumptions. Adaptive and chronological losses can be nonstationary, so these bounds are not validated coverage for arbitrary drift or an array population. Loss differences by quarter, lag-one association and linear time trend are recorded. An interval crossing zero establishes neither no effect nor equivalence, and no physical cause or multiple-testing superiority follows from these diagnostics.

False assurance means a noncontradictory flag at radius at most $\tau$ with actual reference-relative error above $\tau$. Joint and conditional rates use all outputs and assured outputs, respectively. Empty denominators are undefined. Historical initialization, model-specific masks, original failed bound settings and all charged final queries are retained. Numerical and causal checks verify the software contracts without establishing physical identifiability or certified uncertainty.
''')
# Scientific prose generated from actual numbers, no pending RUN results.
c=agg('consensus');a=agg();f95=agg('affine_l095','rlsvar',20);ef=eff('affine_l095','rlsvar',20)
intro=template('section_1_introduction.tex');start=intro.index('The study contributes');end=intro.index('\\section{Related work',start)
intro=intro[:start]+r'''Historical inverse affine correction improves pooled reference-relative accuracy before any additional query, with larger Figaro gains and adverse FIS mean changes. Three contributions follow: an information-matched chronological protocol, a reporting identity separating historical correction from incremental reference access, and a diagnostic distinction between containment and useful assurance. Established correction rules are compared, with forgetting and one native schedule added as a declared development extension. The evidence is sequential development on one apparatus.

'''+intro[end:]
intro+=r'''
\paragraph{Drift compensation, field calibration and recursive identification.}
Classifier ensembles have been studied for long-term MOX gas discrimination \cite{vergara2012}; that classification task differs from reference-relative CO estimation. Spinelle et al. examined field calibration for ozone/NO$_2$ and later NO/CO/CO$_2$, including reference collocation and temporal sensor behavior \cite{spinelle2015,spinelle2017}. Those field conditions and costs are not reproduced by a chamber replay. Recursive identification with forgetting is a standard framework \cite{ljung1983}, rather than a new correction algorithm here.

\paragraph{Conformal prediction.}
Split conformal methods offer marginal coverage under exchangeability of calibration and test data \cite{angelopoulos2021}. Extensions for distribution shift or sequential data need their own conditions. Ordinary split conformal guarantees do not apply unconditionally to arbitrary chronological drift. A properly specified conformal comparator is future work; descriptive envelope containment is not a substitute for its assumptions.
'''
put('section_1_introduction.tex',intro)
put('section_2_setting.tex',template('section_2_setting.tex'))
# Terminology consistently peer configuration.
for name in ('section_1_introduction.tex','section_2_setting.tex','section_3_methods.tex'):
 t=(P/name).read_text().replace('hypotheses','peer configurations').replace('hypothesis','peer configuration').replace('bookkeeping, not a new statistical theorem or a decomposition of physical causes','a reporting identity, not a novel theorem or physical causal decomposition')
 put(name,t)
# Results section with compact interpretive prose.
put('section_5_results.tex',r'''\section{Development results}\label{sec:results}
\subsection{Historical benefit is family dependent}
Historical inverse affine correction reduces pooled RF MAE from '''+num(c['mae'])+' to '+num(a['mae'])+r''' ppm and $P_1$ from '''+num(c['exceed_rate_1.0'],2,100)+r'''\% to '''+num(a['exceed_rate_1.0'],2,100)+r'''\%. Table~\ref{tab:historical} retains both family effects and their conditional resampling sensitivity. Figaro supplies 1,056 of 1,230 consensus exceedances (85.85\%) and 871 of 1,039 affine exceedances (83.83\%). Of the 191 net exceedances removed by historical affine correction, 185 are Figaro and six are FIS; the improvement is predominantly, not exclusively, Figaro.
\input{table_historical.tex}
\begin{figure}[!htbp]\centering\includegraphics[width=.92\linewidth]{fig_1_historical_mae.pdf}
\caption{Exact RF historical-only family means (bars), with D6 circles, D8 squares and D10 triangles. Both families retain all six correlated peer configurations.}\label{fig:historical}\end{figure}
Table~\ref{tab:family} reports exact array-based family/session values. Figaro MAE improves on all three days. FIS MAE improves on D6 and worsens on D8/D10, although its strict exceedance count falls by two on each day. Endpoint directions therefore differ. The three affine lambdas have identical B0 predictions by construction and exact verification.
\input{table_family.tex}
\FloatBarrier
\subsection{Additional references and forgetting}
Table~\ref{tab:incremental} compares B20 with each estimator's own B0, rather than attributing its historical advantage to new queries. All fifteen pooled RF B20 affine MAE changes are positive. Under the envelope mask, changes are 0.0029, 0.0056 and 0.0115 ppm for $\lambda=1,.95,.90$. The native $.95$ comparator has MAE '''+num(f95['mae'])+r''' ppm and an incremental change '''+num(ef['estimate'])+r''' ppm, with length-10 conditional bounds '''+ci(ef)+r''' ppm. This tested coupled comparator does not improve pooled RF MAE. Exceedance directions, family effects and individual sessions differ; no universal statement about reference value follows.
\input{table_incremental.tex}
\begin{figure}[!htbp]\centering\includegraphics[width=\linewidth]{fig_2_affine_increment_mae.pdf}
\caption{RF pooled incremental MAE by update factor and schedule. Faint markers are the three session effects (circle D6, square D8, triangle D10); opaque lines are equal-session means. Lines join evaluated discrete budgets only. Conditional intervals and family values are in the numerical supplement.}\label{fig:incrementalmae}\end{figure}
\begin{figure}[!htbp]\centering\includegraphics[width=\linewidth]{fig_3_affine_increment_exceedance.pdf}
\caption{Incremental strict 1 ppm exceedance, in percentage points, with the same session markers and discrete-budget convention. MAE and exceedance can move in different directions.}\label{fig:incrementalp}\end{figure}
The original cumulative envelope B20 estimate remains 0.7872 ppm and 29.11\% exceedance, compared with its own B0 at 0.7843 ppm and 28.86\%. Resampling intervals crossing zero are retained as conditional sensitivity bounds, not reworded as no effect or equivalence. Other schedules and block lengths, including unfavorable changes, remain visible.
\FloatBarrier
\subsection{Subset, support and upstream-model checks}
A concrete selection example is confidence B20 cumulative affine: unqueried MAE is 0.7403 ppm, but unchanged consensus on that same subset is 0.8580 ppm versus 0.8993 ppm on all exposures. The affine B0 MAE on those same unqueried exposures is 0.7243 ppm, so the positive-budget 0.7403 ppm is adverse against its own matched baseline. Selecting difficult exposures for purchase changes the unqueried population. Every subset now also has the estimator's own same-subset B0 and exact count, so subset selection and incremental prediction changes are distinguishable.

Concentration support and the 10\% relative tolerance are tabulated in Supplement S5 and full numerical files. Both families have the same chamber-concentration support, while their errors differ. Reference-defined bands are evaluation diagnostics only.

The limited saved-input M9 sensitivity retains RF as primary. OLS historical affine MAE is 0.7678 ppm versus consensus 0.8652 ppm; ridge gives 0.9046 versus 1.0873 ppm. Under envelope B20, cumulative affine changes are $-0.0021$ and $-0.0025$ ppm for OLS and ridge. Native $.95$ changes are $-0.0037$ ppm for OLS and $+0.0039$ ppm for ridge. Thus the incremental pattern is model dependent. No model was refitted or promoted; OLS/ridge confidence uses peer MAD, unlike RF tree spread, and each model retains its own mask.

Paid queries in the last ten exposures and at exposure 100 are counted per run, then averaged over seeds and days (Supplement S6). Only exposure-100 purchases lack a subsequent scored prediction under reset; the other last-ten purchases can affect later outputs. All budgets remain charged.
\subsection{Containment is not assurance}\label{sec:boundresults}
Primary envelope-driven B20 midpoint width is 16.8528 ppm and containment 99.56\%, yet only 60 of 3,600 outputs (1.67\%) meet the conditional 1 ppm criterion. All 60 are unqueried: 60/2,880=2.08\%; queried outputs have none. No complete twelve-configuration unqueried exposure is assured under the original primary RF schedules. Sixteen primary B20 raw noncontainments occur without contradictions. Numerical consistency alone therefore does not establish containment.
\input{table_bounds.tex}
The exact slope95/envelope B20 cross-tab reconciles 2,072 raw noncontainments: 749 contradictory outputs are contained by their descriptive hull, and 1,323 noncontradictory outputs remain outside their reported interval. This partition was checked by output identities. The complete 16-cell cross-tab, including zero cells and assurance, is in Supplement S7. The sensitivity has substantial false assurance and remains a negative result. Broad primary bounds and failed narrower bounds are both retained.

The old 52 raw schedule replays per model/day/bounds contain thirteen identical B0 runs. Exact equality permits 40 unique original runs: one B0 and 39 positive-budget masks. The three RF native positive budgets and two models' native B20 masks add 15 runs across days, giving 1,455 unique run identities versus 1,872 original raw replays. These computational counts do not increase the 300 physical exposures. Original logs and their duplicate mapping remain archived.
''')
put('section_6_discussion.tex',r'''\section{Discussion}\label{sec:discussion}
\subsection{Control initialization before assigning reference value}
Historical correction accounts for the pooled RF advantage before a new reference is bought. The reporting identity in Eq.~\eqref{eq:decomp} exposes this distinction separately for MAE and exceedance. Retaining family results prevents a pooled improvement from concealing adverse FIS MAE. Additional-reference and schedule comparisons must use identical exposure keys and an effective same-estimator B0.

\subsection{Update information and conditional sensitivity}
Cumulative RLS can absorb new references: its gain is nonzero for informative regressors. The response depends on leverage, innovation and historical information, not merely 100 versus 20 rows. Forgetting at purchases discounts old information and ridge; it does not forget during unqueried exposures. The fixed $.95$ comparator and $.90$ sensitivity, including one native schedule, increase the scope of this development comparison without supporting a claim that any tested method is optimal. Actual state changes and leverage are archived.

For RF, every pooled B20 affine MAE point change is adverse, while endpoint and family patterns vary. OLS/ridge provide some small favorable incremental changes, showing dependence on upstream prediction and mask. Conditional resampling bounds help describe the frozen paths; crossing zero does not prove absence or equivalence, and excluding zero does not confer population significance after sequential development. Quarter-path, lag-one and trend diagnostics expose temporal structure rather than assume away nonstationarity. The stated relative reference-uncertainty percentage is not an independent Gaussian noise floor for a paired contrast using common labels.

\subsection{Prediction sets and measurement assurance}
Conditional minimax midpoint behavior is distinct from empirical MAE. Projection's non-worsening property requires the actual residual to lie within the assumed interval. Hull containment cannot rescue a contradictory intersection. Frequent containment, a narrow radius and complete-array service assurance are separate properties. Standard conformal methods provide a useful future comparison only under their own exchangeability or sequential assumptions \cite{angelopoulos2021}; neither descriptive envelopes nor ordinary split conformal offer unconditional protection against arbitrary drift.

Traceable co-calibration requires characterized references and uncertainty propagation \cite{gruber2023,jcgm100,jcgm200}. Multiple accesses to one generated-concentration system cannot identify a shared reference bias. The current analysis is a reference-relative algorithm comparison. A later fixed-initialization temporal confirmation could assess persistence on this apparatus, with no final result inferred from development.

\section{Limitations}\label{sec:limitations}
All results use one chamber and array, with three development assessment sessions and twelve overlapping peer configurations. Sequential extensions were informed by earlier development results; family emphasis, forgetting, native scheduling and conditional resampling are declared extensions rather than independent preregistration. Error is relative to released nominal CO with stated relative uncertainty below 5.5\%, without exposure-level reference-error covariance or hard bounds. Certified physical uncertainty, independent-array coverage and a causal drift diagnosis are not established. Acquisition latency and cost are simulated, and resets limit the horizon of late purchases. R7/R14 and D11--D13 remain unused.

The calibrated hardware union includes units omitted from individual peer configurations; strict unseen-unit or single-sensor deployment is a different estimand. Late-core summaries omit transient and washout behavior, and anonymous positions do not establish serial/lot provenance. Inverse regression and numerical rank do not identify forward physical parameters. Empirical slopes and fixed temporal/session allowances are unvalidated future bounds. Ordinary block resampling requires regularity that these adaptive chronological paths may not satisfy; the saved conditional intervals neither rerun adaptive trajectories nor propagate fitting or reference uncertainty. The finite comparison does not rank all possible online methods. Complete local per-output provenance is retained; a public reproducibility deposit is not yet available.

\section{Conclusion}
Historical inverse affine correction reduces pooled RF MAE from 0.8993 to 0.7843 ppm and strict 1 ppm exceedance from 34.17\% to 28.86\% before any additional check. Most benefit is Figaro, while FIS mean error increases. All tested RF affine B20 MAE point changes are adverse, including fixed forgetting and native information scheduling; the limited OLS/ridge sensitivities give model-dependent small changes. Conditional resampling preserves family and session variation without establishing equivalence, arbitrary-drift coverage or a physical cause. Broad primary residual intervals and failed slope95 bounds show why containment alone is insufficient for useful assurance. Reference-budget evaluations should retain each estimator's B0, its incremental contrast, family support, exact pairing and query costs. These are development findings awaiting temporal confirmation.
''')
# Main wrapper from bundled package, preserving legitimate author fields.
main=template('main.tex');main=main.replace('Separating Historical Recalibration from Additional Reference Checks in CO Sensor Arrays: A Chronological Evaluation','Historical recalibration versus additional reference checks in CO sensor arrays: a chronological evaluation')
start=main.index('\\begin{abstract}');end=main.index('\\end{abstract}',start)
main=main[:start]+r'''\begin{abstract}
Reference-assisted methods can be credited with gains already delivered by historical calibration. A chronological CO sensor-array replay separates historical correction from additional shared references across three development sessions, twelve correlated peer configurations and two sensor families. Predictions precede reference purchase, with budgets 0, 5, 10 and 20 per 100 exposures. Historical inverse affine correction reduces pooled RF MAE from 0.8993 to 0.7843 ppm and strict 1 ppm exceedance from 34.17\% to 28.86\%; 185 of 191 net exceedances removed are Figaro, whereas FIS mean error increases. Fixed forgetting factors .95/.90 and one shared information-driven schedule extend the original cumulative comparison. All fifteen pooled RF B20 affine MAE changes are adverse; the coupled native .95 comparator changes MAE by +0.0070 ppm. Saved OLS/ridge sensitivities yield model-dependent small changes. Paired moving-block resampling is reported as conditional sensitivity of frozen loss paths, retaining all session/family effects without population coverage or equivalence claims. Primary envelope intervals average 16.85 ppm at envelope B20 and flag only 1.67\% of outputs at a conditional 1 ppm criterion; narrower slope95 bounds fail. An estimator's zero-check baseline, incremental contrast, family support and query costs must be reported separately. The study is sequential development on one apparatus; reserved temporal confirmation remains outstanding.
'''+main[end:]
main=main.replace('Gas sensor calibration \\sep Reference measurements \\sep Calibration drift','Metal-oxide gas sensors \\sep Reference-assisted calibration \\sep Calibration drift')
start=main.index('\\section*{Data and reporting-code availability}');end=main.index('\\input{author_declarations.tex}',start)
main=main[:start]+r'''\section*{Data and code availability}
The original measurements are public from UCI under DOI \href{https://doi.org/10.24432/C5S302}{10.24432/C5S302} \cite{uci487}. Full-precision development predictions, query masks, causal access logs, protocols, numerical endpoints and their source hashes are retained in a portable local reproducibility archive with original training/replay code and permitted development feature inputs. The accompanying numerical files rebuild all tables and figures. A public code/prediction deposit and release identifier are not yet available. Reserved outcomes are excluded.
'''+main[end:]
start=main.index('OpenAI ChatGPT and Codex');end=main.index('\\bibliographystyle',start)
main=main[:start]+r'''OpenAI ChatGPT and Codex assisted software drafting and checking, analysis/reporting code, manuscript organization, exposition and literature checks. Figures were plotted from authentic numerical development outputs. No experimental results were generated by an image model. The authors must verify the complete tool inventory and retain responsibility for the scientific content.
'''+main[end:];put('main.tex',main)
put('supplement.tex',r'''\documentclass[11pt,a4paper]{article}
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}
\usepackage{lmodern,amsmath,amssymb,booktabs,longtable,graphicx,microtype,placeins}
\usepackage[margin=23mm]{geometry}\usepackage{xurl}\usepackage[hidelinks]{hyperref}
\setlength{\emergencystretch}{3em}
\newcommand{\clip}{\operatorname{clip}}
\renewcommand{\thetable}{S\arabic{table}}\renewcommand{\thefigure}{S\arabic{figure}}
\title{Supplementary development results\\\large Historical recalibration versus additional reference checks in CO sensor arrays}
\author{}\date{}
\begin{document}\maketitle
\section*{Contents and numerical-file guide}
S1: full-precision provenance and denominator definitions. S2: envelope conditions and contradiction handling. S3: complete RF family/pooled budget grid (Table S1; AGGREGATE\_METRICS.csv). S4: limited OLS/ridge affine robustness (Table S2). S5: concentration support and relative tolerance (Table S3; METRICS\_BY\_RUN\_FAMILY\_BAND\_SUBSET.csv). S6: timing (Table S4; QUERY\_TIMING\_BY\_RUN.csv). S7: exact negative slope95 diagnostic (Table S5; SLOPE95\_CROSSTAB.csv). S8: conditional length sensitivity and all three day effects (Table S6; CONDITIONAL\_RESAMPLING\_EFFECTS.csv, LOSS\_TIME\_STRUCTURE.csv). S9: code/data access. Every configuration/subset/count is in METRICS\_BY\_CONFIGURATION.csv. Figures 1--3 rebuild from SESSION\_METRICS.csv and conditional effects. RESAMPLING\_INDEX\_MANIFEST.json identifies saved paired banks; EXCEEDANCE\_SHARES.csv records weighted family numerators and denominators.
\section{Numerical provenance and denominators}
Values derive from authentic saved development prediction arrays and causal replays. The local archive records a versioned SHA256 protocol/source manifest; no Git tag is claimed. Historical calibration is D5/D7/D9, assessment D6/D8/D10, and all original fit/exclusion/reservation roles remain fixed. Each assessment has 100 shared exposures and 1,200 correlated configuration outputs, with six configurations per family. No reserved measurements enter these results.

Original B0 copies are collapsed only after exact equality of predictions, references, query flags and intervals is checked. The original logs and removed-duplicate mapping remain intact. Three affine lambdas retain named identities but share one B0 numerical state. Every original bound/upstream sensitivity is retained in the CSV, even where only primary results are typeset. Each numerical row has complete model/bounds/schedule/budget/seed/day identity and source provenance; tables show four-decimal MAE and percent rates, while CSVs retain stored precision.

Random seeds 487--496 are averaged within each day before equal-day means. Seeds and overlapping peer configurations do not add physical replication. All/queried/unqueried supports and their own-subset consensus/B0 are retained. Empty queried B0 cells and unsupported bands have undefined rates, not zero. The 10\% relative sensitivity uses a strict exceedance and absolute 1 ppm at reference zero.
\section{Conditional envelope properties and contradiction fallback}
The following properties assume every anchor inequality in the main text holds. They do not establish empirical future validity. All failed settings remain retained.
\input{supplement_properties.tex}
\section{Complete primary RF results}
\input{table_s_all.tex}\FloatBarrier
\section{Limited upstream-model sensitivity}
RF remains primary. No sensor model is refitted. OLS/ridge reuse their own saved observables and masks; confidence is peer MAD rather than RF tree spread. Only consensus and affine factors 1/.95 at B0/B20 are added to the previous midpoint sensitivity. This is not an outcome-selected model competition.
\input{table_s_models.tex}\FloatBarrier
\section{Family and concentration support}
\input{table_s_support.tex}\FloatBarrier
\section{Paid query timing}
\input{table_s_timing.tex}\FloatBarrier
\section{Contradiction, containment and assurance}
\input{table_s_cross.tex}\FloatBarrier
\section{Conditional resampling and temporal structure}
Paired overlapping blocks use 2,000 replicates, seed 487 and fixed lengths 5/10/20. One index bank per length/day is shared across all arms/families/endpoints. Configurations are not resampled independently. Fixed fits, trajectories, initialization and shared reference labels are conditioned upon; learning and reference uncertainty are not resimulated. Percentile intervals are conditional sensitivity bounds, requiring regularity assumptions for an inferential interpretation. Adaptive chronological loss paths may be nonstationary. Neither a zero crossing nor an excluded zero establishes equivalence, causal drift explanation or independent-array coverage. The complete CSV retains every comparator/metric, all three session effects and direction counts. Quarter means, lag-one correlations and linear trends inspect temporal structure without validating arbitrary nonstationarity.
\input{table_s_resampling.tex}\FloatBarrier
\section{Code and data access}
The original UCI measurements are public under DOI 10.24432/C5S302. The complete permitted local development archive contains pre-query exports, source hashes, model/mask identities, causal logs, original training/replay code and derived development feature inputs. The accompanying rebuild\_reporting.py regenerates this article's tables and figures from these numerical CSVs. A public code/prediction deposit is not yet available; no URL, DOI or independent temporal confirmation is implied. No reserved inputs are distributed.
\end{document}
''')
# Portable reporting wrapper invokes exact generator from included evaluated CSVs.
source=Path(__file__).read_text().replace("W=Path(__file__).resolve().parents[1];E=W/'evidence';P=W/'paper'", "W=Path(__file__).resolve().parent;E=W;P=W")
# Rendering/prose transformations are not idempotent; existing prepared sections remain authoritative.
source=source[:source.index('# Retain manuscript setting and definitions;')]
# Avoid copying files onto themselves when reporting from flat LaTeX bundle.
source=source.replace(" shutil.copy2(E/name,P/name)","\n if (E/name).resolve()!=(P/name).resolve():shutil.copy2(E/name,P/name)")
put('rebuild_reporting.py',source)
put('README.md','Build with bash build.sh (pdfLaTeX, BibTeX). Rebuild numerical tables/figures with python rebuild_reporting.py using NumPy/Matplotlib. Full precision comes from authentic evaluated prediction arrays, not reconstructed printed rows. No training, raw parsing, final access or publication occurs in reporting. Source data CSVs are explained in the supplement. Author fields require actual confirmation.\n')
put('requirements-reporting.txt','numpy\nmatplotlib\n')
print('Manuscript sources, tables and figures rebuilt from exact exports')

import subprocess,sys
subprocess.run([sys.executable,str(W/'src/prepare_latex.py')],check=True)
