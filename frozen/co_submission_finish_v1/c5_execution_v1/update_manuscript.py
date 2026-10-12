from pathlib import Path
import json,csv,shutil,os
import numpy as np
E=Path(__file__).resolve().parent;O=E.parent;P=O/'paper_with_c5';shutil.copytree(O/'paper',P)
os.environ['MPLCONFIGDIR']=str(E/'mplconfig')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
A=json.loads((E/'replays/AGGREGATE.json').read_text());M=json.loads((E/'replays/METRICS.json').read_text())
def get(est,policy='none',budget=0,scope='ALL',subset='all',day=None):
 rows=M if day is not None else A;kw=dict(estimator=est,policy=policy,budget=budget,scope=scope,subset=subset)
 if day is not None:kw['day']=day
 out=[r for r in rows if all(r[k]==v for k,v in kw.items())];assert len(out)==1;return out[0]
def num(v,d=4):return 'NA' if v is None else f'{v:.{d}f}'
def cnt(v):return str(int(v)) if v==int(v) else f'{v:.2f}'
def table(name,caption,label,headers,rows,align,long=False):
 if long:
  s=r'\small\setlength{\tabcolsep}{4pt}'+'\n'+r'\begin{longtable}{'+align+'}\n'+r'\caption{'+caption+r'}\label{'+label+r'}\\'+'\n'+r'\toprule'+'\n'+' & '.join(headers)+r' \\ \midrule\endfirsthead'+'\n'+r'\toprule'+'\n'+' & '.join(headers)+r' \\ \midrule\endhead'+'\n'+r'\bottomrule\endfoot'+'\n'
 else:s=r'\begin{table}[!htbp]\centering\small'+'\n'+r'\caption{'+caption+r'}\label{'+label+'}\n'+r'\setlength{\tabcolsep}{4pt}\begin{tabular}{'+align+'}\n'+r'\toprule'+'\n'+' & '.join(headers)+r' \\ \midrule'+'\n'
 s+='\n'.join(' & '.join(map(str,row))+r' \\' for row in rows)+'\n'+(r'\end{longtable}\normalsize' if long else r'\bottomrule\end{tabular}\end{table}')+'\n';(P/name).write_text(s)
rows=[]
for scope in ('ALL','Figaro','FIS'):
 c=get('consensus',scope=scope);b=get('affine',scope=scope);a=get('affine','envelope',20,scope)
 rows.append([scope,cnt(c['outputs']),num(c['mae']),num(b['mae']),num(a['mae']),cnt(c['exceed_count_1.0']),cnt(b['exceed_count_1.0']),cnt(a['exceed_count_1.0'])])
table('table_c5_primary.tex','Fixed-D10 temporal confirmation, distinct from development. MAE in ppm; counts are strict 1 ppm exceedances. B0 and envelope B20 use cumulative inverse affine correction. $N$ counts correlated configuration outputs, not independent exposures.','tab:c5primary',['Scope','$N$','Raw MAE','B0 MAE','B20 MAE','Raw count','B0 count','B20 count'],rows,'lrrrrrrr')
rows=[]
for scope in ('ALL','Figaro','FIS'):
 r=get('midpoint','envelope',20,scope);rows.append([scope,cnt(r['outputs']),cnt(r['raw_noncontainment']),cnt(r['reported_noncontainment']),cnt(r['contradictions']),num(r['width_mean']),cnt(r['false_1.0'])+'/'+cnt(r['assured_1.0'])])
table('table_c5_intervals.tex','Primary envelope B20 interval diagnostics in confirmation. Outside counts use raw intersection and reported set separately. False/assured refers to actual midpoint error above 1 ppm among noncontradictory own-radius flags.','tab:c5intervals',['Scope','$N$','Raw out','Report out','Contradictions','Width (ppm)','False/assured'],rows,'lrrrrrr')
rows=[];countrows=[]
for d in (11,12,13):
 for scope in ('ALL','Figaro','FIS'):
  c=get('consensus',scope=scope,day=d);b=get('affine',scope=scope,day=d);a=get('affine','envelope',20,scope,day=d)
  rows.append([f'D{d}',scope,num(c['mae']),num(b['mae']),num(a['mae']),num(b['mae']-c['mae']),num(a['mae']-b['mae'])]);countrows.append([f'D{d}',scope,cnt(c['outputs']),cnt(c['exceed_count_1.0']),cnt(b['exceed_count_1.0']),cnt(a['exceed_count_1.0'])])
table('table_s_c5_sessions_mae.tex','All primary confirmation day/family MAE cells (ppm). $H$ is affine B0 minus raw consensus; $I$ is cumulative affine envelope B20 minus own B0. Positive changes are adverse.','tab:sc5mae',['Day','Scope','Raw','Affine B0','Affine B20','$H$','$I$'],rows,'llrrrrr',True)
table('table_s_c5_sessions_counts.tex','Exact primary confirmation strict 1 ppm exceedance counts. $N$ counts outputs; each day has 100 shared exposures.','tab:sc5counts',['Day','Scope','$N$','Raw','Affine B0','Affine B20'],countrows,'llrrrr',True)
rows=[]
for est in ('affine','affine_l095','affine_l090'):
 for policy in ('periodic','random','confidence','envelope','rlsvar'):
  r=get(est,policy,20);b=get(est);rows.append([{'affine':r'$\lambda=1$','affine_l095':r'$\lambda=.95$','affine_l090':r'$\lambda=.90$'}[est],{'rlsvar':'Information'}.get(policy,policy.title()),num(r['mae']-b['mae']),num(100*(r['exceed_rate_1.0']-b['exceed_rate_1.0'])),*[num(r['day_mae'][str(d)]-b['day_mae'][str(d)]) for d in (11,12,13)]])
table('table_s_c5_b20.tex','All fifteen prespecified pooled affine B20 confirmation contrasts. MAE changes in ppm; exceedance changes in percentage points. Random seeds are averaged within day before equal-day aggregation.','tab:sc5b20',['Factor','Schedule','$I$ MAE','$I$ $P_1$ (pp)','D11','D12','D13'],rows,'llrrrrr',True)
rows=[]
labels={'consensus':'Consensus','midpoint':'Midpoint','projection':'Projection','offset':'Offset','affine':r'Affine $\lambda=1$','affine_l095':r'Affine $\lambda=.95$','affine_l090':r'Affine $\lambda=.90$'}
for scope in ('ALL','Figaro','FIS'):
 for est in labels:
  for b in (0,5,10,20):
   for policy in (('none',) if b==0 else ('periodic','random','confidence','envelope','rlsvar')):
    r=get(est,policy,b,scope);base=get('consensus' if b==0 else est,scope=scope);rows.append([scope,labels[est],{'none':'Historical only','rlsvar':'Information'}.get(policy,policy.title()),b,num(r['mae']),num(100*r['exceed_rate_1.0'],2),num(r['mae']-base['mae'])])
table('table_s_c5_all.tex','Complete prespecified confirmation grid on all exposures. Rates in percent. Changes are from raw consensus at B0 and own B0 at positive budgets; all three affine B0 states are identical. Full-precision session/seed/configuration/subset records are in C5\_METRICS.csv and C5\_AGGREGATE.csv; empty queried B0 cells are NA.','tab:sc5all',['Scope','Estimator','Schedule','$B$','MAE','$P_1$','$\Delta$ MAE'],rows,'lllrrrr',True)
plt.rcParams.update({'font.size':13,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,3,figsize=(11,4.3),layout='constrained',sharey=True)
for ax,scope in zip(axes,('ALL','Figaro','FIS')):
 for d,mark,color in zip((11,12,13),('o','s','^'),('#2678b8','#d47428','#3b9852')):
  vals=[get(e,p,b,scope,day=d)['mae'] for e,p,b in [('consensus','none',0),('affine','none',0),('affine','envelope',20)]];ax.plot(range(3),vals,marker=mark,markersize=7,color=color,lw=1.4,ls='--',label=f'D{d}')
 vals=[get(e,p,b,scope)['mae'] for e,p,b in [('consensus','none',0),('affine','none',0),('affine','envelope',20)]];ax.plot(range(3),vals,color='black',lw=2.7,marker='D',markersize=6,label='Equal-session mean')
 ax.set_xticks(range(3),['Consensus','Affine\nB0','Affine\n20 checks']);ax.set_title('Pooled' if scope=='ALL' else scope);ax.set_ylim(0,2.85)
axes[0].set_ylabel('Mean absolute error (ppm)');axes[-1].legend(fontsize=10,loc='upper right');fig.savefig(P/'fig_4_c5_primary_mae.pdf');fig.savefig(P/'fig_4_c5_primary_mae.png',dpi=170);plt.close(fig)
section=r'''\section{Fixed-D10 temporal confirmation}\label{sec:c5}
\subsection{Frozen roles and complete execution}
A separately authorized temporal confirmation assessed D11, D12 and D13 using R1--R6 and R8--R13. The twelve frozen RF models were fitted only on D1, D2 and D4--D9, with the same seed 487, 100 trees, depth 5, minimum leaf size 5 and fit-only scaling. Initial correction calibration and scheduler normalization used D10 only. Every policy, budget, seed and assessment session reset independently to that same D10 state; no rolling recalibration or final-label carry occurred. R7/R14 and the UCI270 reservations remained excluded.

The complete predeclared comparison retained the two original primary contrasts, all five schedules, budgets 0/5/10/20, all random seeds 487--496, and the declared forgetting and fixed $.95$ information-controller extensions. Each current prediction, raw/reported interval and decision was persisted before purchase; a purchased reference affected later predictions only. All 129 replay paths and 12,900 pre-query records were committed before final performance summaries. An independent arithmetic audit reproduced all 40,635 per-run metric rows exactly, verified the fixed initial states and causal records, and checked unchanged source/model/development hashes. No integrity/access violation or numerical-update failure was found. The 300 exposures and 3,600 correlated outputs are separate from the development sample.

\subsection{Primary historical and incremental findings}
Table~\ref{tab:c5primary} retains the pooled and both-family results. Historical affine correction reduces pooled MAE from 1.4570 to 1.3553 ppm and strict 1 ppm exceedance from 1,791/3,600 to 1,550/3,600 (49.75\% to 43.06\%). Figaro contributes 240 of the 241 net removed exceedances. FIS MAE instead increases from 0.8820 to 0.9471 ppm, worsening on all three sessions. Thus the frozen historical-benefit criterion requiring favorable exceedance and nonpositive MAE change in both families is not met; the finding is heterogeneous.

\input{table_c5_primary.tex}

The original incremental comparison, cumulative affine envelope B20 against its own B0, reduces pooled MAE by 0.0297 ppm to 1.3257 ppm and exceedance by 33 outputs to 1,517/3,600 (42.14\%). Both family-aggregate MAE and exceedance changes are favorable, satisfying the prespecified descriptive incremental-benefit criterion. This does not establish uniform improvement: pooled D12 MAE changes by +0.0049 ppm; Figaro/FIS D12 changes are +0.0071/+0.0027 ppm, and FIS D13 changes by +0.0068 ppm with one additional exceedance. Pooled D11/D13 MAE changes are $-0.0918/-0.0021$ ppm. All session/family numerators and denominators are in Supplement S10 and the full numerical files.

\begin{figure}[!htbp]\centering
\includegraphics[width=\linewidth]{fig_4_c5_primary_mae.pdf}
\caption{Prespecified primary confirmation paths. D11 circles, D12 squares and D13 triangles are individual session MAEs; black diamonds show equal-session means. These three evaluated estimator states share the frozen upstream RF models and D10 initialization. Family/session reversals remain visible.}\label{fig:c5mae}
\end{figure}

Fourteen of the fifteen pooled affine B20 MAE point changes are favorable in confirmation, whereas all fifteen were adverse in development. The confidence $.90$ change is adverse (+0.0047 ppm); confidence $\lambda=1$ improves MAE while worsening strict exceedance. The native $.95$ comparator changes pooled MAE by $-0.0551$ ppm, but remains an extension rather than a replacement primary. No method, factor, budget, family or seed was selected by its final outcome. Secondary envelope-schedule superiority is not established: against confidence at $\lambda=1$ B20, envelope has worse pooled MAE (+0.0078 ppm) and worse FIS MAE and exceedance.

\subsection{Scientific bound failures in a valid evaluation}
Table~\ref{tab:c5intervals} separates raw noncontainment, reported-set noncontainment, contradictions and actual midpoint false assurance. Envelope B20 has 284/3,600 raw noncontainments and 276/3,600 reported noncontainments, with eight contradictory outputs contained only by the descriptive hull. Mean width is 15.7129 ppm. Of 74 midpoint flags at 1 ppm, 38 are false: 38/74=51.35\% conditional and 38/3,600=1.06\% overall. Figaro contributes 1/1 false/assured and FIS 37/73. Queried outputs have 8/14 false/assured and 8/720 false/all; unqueried outputs have 30/60 and 30/2,880. RLS assurance remains unavailable.

\input{table_c5_intervals.tex}

These failures reject an unconditional hard-bound claim and remain scored scientific outcomes. They do not invalidate the otherwise verified evaluation. No bound retuning, model refit, favorable-seed selection or experiment repeat was performed. This is later-session evidence on the same apparatus, not certified physical uncertainty, independent-array validation or a new algorithmic claim.
'''
(P/'section_7_temporal_confirmation.tex').write_text(section)
p=P/'main.tex';s=p.read_text().replace(r'\date{Development study}',r'\date{Development study and temporal confirmation}').replace(r'\input{section_6_discussion.tex}',r'\input{section_7_temporal_confirmation.tex}'+'\n'+r'\input{section_6_discussion.tex}')
s=s.replace('The study is sequential development on one apparatus; reserved temporal confirmation remains outstanding.', 'A separately frozen fixed-D10 confirmation on three later sessions reduces pooled RF MAE from 1.4570 to 1.3553 ppm historically, with adverse FIS MAE. The primary 20-check incremental comparison reduces MAE to 1.3257 ppm and improves both family aggregates, although adverse session cells preclude uniform improvement. Confirmation has 284 raw interval noncontainments and 38/74 false 1 ppm midpoint assurances. Both stages use one apparatus; no independent-array or certified-uncertainty claim follows.')
s=s.replace('Full-precision development predictions,','Full-precision development and separately frozen temporal-confirmation predictions,').replace('Reserved outcomes are excluded.', 'R7/R14 and the UCI270 reserved batches remain excluded.').replace('authentic numerical development outputs','authentic numerical development and temporal-confirmation outputs');p.write_text(s)
p=P/'section_2_setting.tex';s=p.read_text().replace('Channels R7 and R14 and the later sessions D11--D13 were reserved and are not used.', 'Channels R7 and R14 remain excluded. The development analysis excluded reserved sessions D11--D13; their separately frozen temporal confirmation is reported in Section~\\ref{sec:c5}.').replace('Reserved-session confirmation has not been performed.', 'The separately frozen later-session evaluation retains distinct fitting and initialization roles (Section~\\ref{sec:c5}).');p.write_text(s)
p=P/'section_6_discussion.tex';s=p.read_text().replace('A later fixed-initialization temporal confirmation could assess persistence on this apparatus, with no final result inferred from development.', 'The fixed-D10 temporal confirmation provides distinct later-session evidence: family heterogeneity persists historically, while the original incremental aggregate criterion is met despite session reversals (Section~\\ref{sec:c5}).').replace('All results use one chamber and array, with three development assessment sessions and twelve overlapping peer configurations.', 'Both stages use one chamber and array: three development assessment sessions and three separate confirmation sessions, each with twelve overlapping peer configurations.').replace('R7/R14 and D11--D13 remain unused.', 'R7/R14 and the UCI270 reserved batches remain unused; D11--D13 are evaluated only in the separately authorized fixed-D10 confirmation.').replace('These are development findings awaiting temporal confirmation.', 'These development findings remain distinct from the fixed-D10 confirmation. In confirmation, historical pooled and Figaro improvements coexist with adverse FIS MAE, so the full historical-benefit criterion is unsupported. The original incremental affine envelope 20-check comparison improves pooled and both-family aggregates, but adverse D12 and FIS D13 cells preclude uniform improvement. Raw noncontainment and 38/74 false midpoint assurances reject guaranteed assurance. The comparison remains descriptive same-apparatus evidence without certified uncertainty or independent-array validation.');p.write_text(s)
# Preserve all prior supplement sections; append a distinct final section before the bibliography.
extra=r'''\section{Fixed-D10 temporal confirmation}\label{sec:sc5}
These are separately authorized final D11/D12/D13 results, not additional development folds. Upstream RF fitting uses D1,D2,D4--D9 only; correction calibration and controller normalization use D10 only. Every session, policy, budget and seed resets to that same initialized state. R7/R14 and UCI270 batches 7--10 remain excluded. All 129 final paths were committed before summaries, and independent recomputation reproduces all 40,635 run metric rows and 5,040 aggregates. The protocol/source/model hashes and development evidence remain unchanged; no refit, retuning or final-result method selection occurred.

The original pooled primary contrasts are historical affine $\lambda=1$ B0 minus raw consensus and incremental affine $\lambda=1$ envelope B20 minus own B0. Strict 1 ppm exceedance is primary with MAE as guardrail; both families must improve exceedance without adverse MAE for descriptive benefit. Historical benefit is heterogeneous because FIS MAE worsens on all three days. Incremental benefit meets the pooled-and-both-family aggregate criterion, but session reversals preclude uniform improvement. Envelope superiority over all three original schedule comparators is unsupported. The full cell tables retain all unfavorable values.

\input{table_s_c5_sessions_mae.tex}
\input{table_s_c5_sessions_counts.tex}
\input{table_s_c5_b20.tex}

At primary envelope B20, midpoint raw/reported noncontainment counts are 284/276 out of 3,600, with eight contradictions. D11 gives 263/255, eight contradictions and 37/55 false/assured; D12 gives 5/5, zero contradictions and 0/12; D13 gives 16/16, zero contradictions and 1/7. Each session has 1,200 outputs. Family false/assured counts are Figaro 1/1 and FIS 37/73. Overall false assurance is 38/74 (51.35\%) conditional and 38/3,600 (1.06\%) joint. Queried counts are 8/14 and 8/720; unqueried are 30/60 and 30/2,880. Historical B0 midpoint has 242 raw/reported noncontainments and 3/3 false assurances; its Figaro conditional rate is undefined because none are assured. Assurance uses each estimator's own radius and actual error, not interval noncontainment alone; affine/offset assurance remains unavailable.

The all/queried/unqueried numerical records retain 0.5/1/2 ppm endpoints, RMSE, bias, own-B0 and same-subset consensus, exact supports, per-configuration values, timing and fixed-seed ranges. Undefined queried B0 denominators are NA. Seeds are averaged within day, then days equally; counts sum seed-mean day numerators, and RMSE uses squared-error sums. The 300 shared final exposures and 3,600 correlated outputs are distinct from the 300 development exposures. Computational paths/purchases do not add physical replication. No final conditional resampling analysis is part of this frozen executable scope.

\input{table_s_c5_all.tex}

C5\_METRICS.csv and C5\_AGGREGATE.csv retain the complete confirmation records. C5\_PRIMARY\_TABLE.csv, C5\_PRIMARY\_SESSION\_TABLE.csv, C5\_B20\_AFFINE\_CHANGES.csv and C5\_INTERVAL\_TABLE.csv provide full-precision presentation inputs. C5\_RESULTS.md identifies scientific criteria and execution evidence. Raw noncontainment, false assurance and adverse cells remain valid scientific failures; leakage, integrity, quota or missing-group failures would invalidate evaluation, but none was observed. Reference-relative errors and descriptive later-session agreement do not establish certified uncertainty, independent-array validation or algorithmic novelty.
'''
p=P/'supplement.tex';s=p.read_text().replace('Supplementary development results','Supplementary development and temporal-confirmation results').replace(r'\bibliographystyle{unsrtnat}',extra+'\n'+r'\bibliographystyle{unsrtnat}');s=s.replace('S9: code/data access.', 'S9: code/data access. S10: separately frozen fixed-D10 temporal confirmation, complete budget grids, family/session cells, containment and assurance.');p.write_text(s)
for name in ('C5_METRICS.csv','C5_AGGREGATE.csv','C5_PRIMARY_TABLE.csv','C5_PRIMARY_SESSION_TABLE.csv','C5_B20_AFFINE_CHANGES.csv','C5_INTERVAL_TABLE.csv'):shutil.copy2(E/name,P/name)
shutil.copy2(O/'C5_RESULTS.md',P/'C5_RESULTS.md')
(P/'README_C5.md').write_text('''# Development and temporal-confirmation manuscript

Development evidence remains distinct and unchanged. The new temporal-confirmation section reports the authorized fixed-D10 C5 evaluation under SHA256 4de22fff8678773f3fb3ba23198431947efe3c54145b8452ddec2ebf036c40bc. Run bash build.sh to rebuild both PDFs. The complete C5 numerical files retain all prespecified arms and failures. Full PDF-page raster inspection is unavailable locally. No publication or journal-readiness claim is made.

rebuild_reporting.py regenerates the existing development figures/tables only; c5_execution_v1/update_manuscript.py in the project created the additional C5 tables and figure from the saved final metrics without fitting or replaying. The static C5 assets are included for a complete LaTeX build.
''')
