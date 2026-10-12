from pathlib import Path
P=Path(__file__).resolve().parents[1]/'paper'
for name in ('main.tex','supplement.tex'):
 p=P/name;s=p.read_text();s=s.replace(r'\newcommand{\FloatBarrier}{\clearpage}',r'\newcommand{\FloatBarrier}{\par}')
 if name=='supplement.tex':s=s.replace(r'\usepackage{url}',r'\usepackage[numbers,sort&compress]{natbib}\usepackage{url}')
 else:
  s=s.replace('pooled RF MAE from','pooled random forest (RF) mean absolute error (MAE) from').replace('FIS mean error increases','FIS mean absolute error increases').replace('All fifteen pooled RF B20 affine MAE changes are adverse','All fifteen pooled RF affine MAE changes with 20 additional checks per session are adverse, although some lower-budget point changes are favorable').replace('at envelope B20','with 20 additional checks per session under the envelope schedule')
 p.write_text(s)
p=P/'section_5_results.tex';s=p.read_text().replace('All fifteen pooled RF B20 affine MAE changes are positive.','All fifteen pooled RF B20 affine MAE changes are positive (adverse), although some lower-budget pooled point changes are favorable; the complete discrete-budget grid is retained.')
s=s.replace('The sensitivity has substantial false assurance and remains a negative result.','Actual errors, rather than interval noncontainment alone, identify 503 false 1 ppm midpoint assurances among 2,287 assured outputs (21.99\\%), and 503 among all 3,600 outputs (13.97\\%). The 1,188 outside-and-assured entries are not themselves a false-assurance count. Primary midpoint bounds have 0/60 false assurances (0\\%) and 0/3,600 overall, separately from their 16 noncontainments. The sensitivity remains a negative result.')
p.write_text(s)
p=P/'section_6_discussion.tex';s=p.read_text().replace('while endpoint and family patterns vary.','while some lower-budget pooled point changes are favorable and endpoint and family patterns vary.').replace('FIS mean error increases','FIS mean absolute error increases');p.write_text(s)
p=P/'supplement.tex';s=p.read_text().replace(r'\input{table_s_cross.tex}\FloatBarrier',r'''\input{table_s_cross.tex}
False assurance is computed independently as a noncontradictory, own-center radius flag and an actual absolute prediction-minus-reference error strictly above the same tolerance. At 1 ppm, RF slope95 envelope B20 midpoint has 503/2,287 false/assured (21.99\%) and 503/3,600 false/all (13.97\%); primary has 0/60 (0\%) and 0/3,600 (0\%). The 1,188 outside-and-assured entries describe interval noncontainment, not actual errors above 1 ppm. FALSE\_ASSURANCE\_AUDIT.csv retains all saved available interval centers, model/bounds identities, budgets, seeds, days, families and all/queried/unqueried subsets at 0.5/1/2 ppm, with undefined denominators marked NA. Offset and affine assurance remains unavailable. Noncontainment is a separate column.
\FloatBarrier''');p.write_text(s)
p=P/'rebuild_reporting.py';s=p.read_text().replace("'font.size':9","'font.size':11").replace("figsize=(10,3.4)","figsize=(11,4.2)").replace('fontsize=7','fontsize=9').replace('markersize=5','markersize=7').replace('s=12,color=color,alpha=.35','s=32,color=color,alpha=.8,edgecolors=\'white\',linewidths=.35').replace("Faint markers", "Session markers")
p.write_text(s)
