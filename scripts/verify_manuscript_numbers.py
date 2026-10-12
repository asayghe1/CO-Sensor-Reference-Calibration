"""Explicit frozen manuscript checkpoints; no data-driven choice of a winner."""
import csv,json
import numpy as np
from context import DEV,C5,report

def main():
 A=json.loads((C5/'c5_execution_v1/replays/AGGREGATE.json').read_text())
 def row(est,scope='ALL',policy='none',budget=0):
  out=[r for r in A if (r['estimator'],r['scope'],r['policy'],r['budget'],r['subset'])==(est,scope,policy,budget,'all')]
  assert len(out)==1;return out[0]
 targets={'ALL':([1.456982932606,1.355345024289,1.325676855215],[1791,1550,1517],3600),'Figaro':([2.031983782066,1.763591111706,1.748061598875],[1275,1035,1019],1800),'FIS':([.881982083147,.947098936871,.903292111555],[516,515,498],1800)}
 values={}
 historical=[];incremental=[];uniform=[]
 for scope,(mae,counts,n) in targets.items():
  trio=[row('consensus',scope),row('affine',scope),row('affine',scope,'envelope',20)]
  np.testing.assert_allclose([r['mae'] for r in trio],mae,rtol=0,atol=6e-13)
  assert [r['exceed_count_1.0'] for r in trio]==counts and all(r['outputs']==n for r in trio)
  raw,b0,b20=trio
  historical.append(b0['mae']<=raw['mae'] and b0['exceed_rate_1.0']<raw['exceed_rate_1.0'])
  incremental.append(b20['mae']<=b0['mae'] and b20['exceed_rate_1.0']<b0['exceed_rate_1.0'])
  uniform.extend(b20['day_mae'][d]<=b0['day_mae'][d] and b20['day_p1'][d]<=b0['day_p1'][d] for d in ('11','12','13'))
  values[scope]={'mae':[r['mae'] for r in trio],'strict_1ppm_counts':counts,'outputs':n}
 assert not all(historical) and all(incremental) and not all(uniform)
 assert row('affine','FIS','envelope',20)['mae']>row('consensus','FIS')['mae']
 superior=all(row('affine',scope,'envelope',20)['mae']<=row('affine',scope,p,20)['mae'] and row('affine',scope,'envelope',20)['exceed_rate_1.0']<row('affine',scope,p,20)['exceed_rate_1.0'] for scope in ('ALL','Figaro','FIS') for p in ('periodic','random','confidence'))
 assert not superior
 midpoint=row('midpoint',policy='envelope',budget=20)
 assert [midpoint[k] for k in ('false_1.0','assured_1.0','outputs','raw_noncontainment','reported_noncontainment','contradictions')]==[38,74,3600,284,276,8]
 with (DEV/'CONDITIONAL_RESAMPLING_EFFECTS.csv').open(newline='') as f:
  dev=[r for r in csv.DictReader(f) if r['model']=='RF' and r['estimator'] in ('affine','affine_l095','affine_l090') and r['budget']=='20' and r['scope']=='ALL' and r['effect']=='incremental' and r['block_length']=='10' and r['metric']=='mae']
 assert len(dev)==15 and sum(float(r['estimate'])>0 for r in dev)==15
 conf=[row(e,policy=p,budget=20)['mae']-row(e)['mae'] for e in ('affine','affine_l095','affine_l090') for p in ('periodic','random','confidence','envelope','rlsvar')]
 assert sum(v<0 for v in conf)==14 and sum(v>0 for v in conf)==1
 report('MANUSCRIPT_NUMBERS.json',dict(status='PASS',primary_confirmation=values,historical_full_criterion=False,incremental_aggregate_criterion=True,uniform_session_improvement=False,envelope_schedule_superiority=False,false_assurance={'false':38,'flagged':74,'total_outputs':3600},development_adverse_B20_MAE=15,confirmation_favorable_B20_MAE=14,confirmation_adverse_B20_MAE=1,scientific_winner_reselected=False))
 print('Primary results, unfavorable comparisons and reversal: PASS',flush=True)
if __name__=='__main__':main()
