"""Repair only a frozen percentile mismatch in archived outputs, no refitting."""
from pathlib import Path
import gzip,json,statistics as st,hashlib
P=Path(__file__).resolve().parent;E=P/'evidence'
def read(n):return json.loads(gzip.decompress((E/n).read_bytes()))
def save(n,x):(E/n).write_bytes(gzip.compress(json.dumps(x,allow_nan=False,separators=(',',':')).encode(),mtime=0))
a=read('authentic_packets_predictions.json.gz');s=read('synthetic_packets_predictions.json.gz');cal=read('calibration_packets.json.gz');key=lambda c:(c['metadata']['day'],c['metadata']['model'],c['metadata']['unit']);ci={key(c):c for c in cal};changes=[]
for c in a:
 vals=[st.median(abs(x-st.median(pp)) for x in pp) for pp in ci[key(c)]['peer_predictions']];new=sorted(vals)[94];changes.append({'metadata':c['metadata'],'old_96th':c['peer_mad_alert_threshold'],'correct_95th':new});c['peer_mad_alert_threshold']=new
thresholds={key(c):c['peer_mad_alert_threshold'] for c in a}
for c in s:c['peer_mad_alert_threshold']=thresholds[key(c)]
save('authentic_packets_predictions.json.gz',a);save('synthetic_packets_predictions.json.gz',s)
d=json.loads((E/'synthetic_diagnostics.json').read_text())
for r in d:
 base=[c for c in a if c['metadata']['model']=='RF' and c['metadata']['day']==r['day']];stress=[c for c in s if c['metadata']['day']==r['day'] and c['synthetic_metadata']['scenario']==r['scenario']]
 flags=lambda cases:[any(c['scores']['peer_mad'][j]>c['peer_mad_alert_threshold'] for c in cases) for j in range(100)]
 b=flags(base);t=flags(stress)
 r.update(baseline_peer_mad_chamber_alerts=sum(b),stress_peer_mad_chamber_alerts=sum(t),new_peer_mad_chamber_alerts=sum(x and not y for x,y in zip(t,b)),cleared_peer_mad_chamber_alerts=sum(y and not x for x,y in zip(t,b)))
(E/'synthetic_diagnostics.json').write_text(json.dumps(d,allow_nan=False,separators=(',',':')))
# Verify every first-run prediction, score, outcome, q and mask is unchanged.
original=P/'archive/first_run/phase6/evidence'
for n,current in [('authentic_packets_predictions.json.gz',a),('synthetic_packets_predictions.json.gz',s)]:
 old=json.loads(gzip.decompress((original/n).read_bytes()))
 for before,after in zip(old,current):
  before.pop('peer_mad_alert_threshold');clean=dict(after);clean.pop('peer_mad_alert_threshold');assert before==clean
for n in ['authentic_selections.json.gz','authentic_group_metrics.json.gz','authentic_unit_metrics.json.gz','synthetic_selections.json.gz','synthetic_group_metrics.json.gz']:
 assert (E/n).read_bytes()==(original/n).read_bytes()
(E/'alert_correction.json').write_text(json.dumps({'reason':'Interval residual order statistic ceil(.95*(n+1)) was mistakenly reused for ordinary alert percentile ceil(.95*n)','root_cause':'analysis.build peer_mad_alert_threshold helper call','frozen_protocol_changed':False,'models_refitted':0,'point_predictions_scores_outcomes_q_masks_and_error_metrics_unchanged':True,'first_run_preserved':'phase6/archive/first_run','threshold_changes':changes},indent=2)+'\n')
print('Alert threshold correction matches frozen95th order statistic; all predictions/scores/masks/error metrics preserved')
