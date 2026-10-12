from pathlib import Path
import csv
from collections import defaultdict
from context import BUILD
O=BUILD/'assurance_recomputed';rows=list(csv.DictReader((O/'FALSE_ASSURANCE_AUDIT.csv').open()));groups=defaultdict(lambda:defaultdict(list));keys=('model','bounds','schedule','schedule_id','schedule_driver','budget','estimator','tolerance_ppm','scope','subset')
for row in rows:groups[tuple(row[k] for k in keys)][row['session']].append(row)
output=[]
for key,days in groups.items():
 r=dict(zip(keys,key));r['session']='POOLED_D6_D8_D10';r['aggregation']='seed mean within day; sum day numerators/denominators; ratio after aggregation'
 for field in ('false_count','assured_count','all_count','interval_noncontainment_count'):r[field]=sum(sum(float(x[field]) for x in rr)/len(rr) for rr in days.values())
 r['false_over_assured']=r['false_count']/r['assured_count'] if r['assured_count'] else 'NA';r['false_over_all']=r['false_count']/r['all_count'] if r['all_count'] else 'NA';output.append(r)
with (O/'FALSE_ASSURANCE_POOLED.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(output[0]));w.writeheader();w.writerows(output)
print('Audited run rows',len(rows),'pooled rows',len(output))
