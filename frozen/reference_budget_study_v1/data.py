"""Strict allowlist adapter for authentic archived development data only."""
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np

ALLOWED=(1,2,3,4,5,6,8,9,10,11,12,13)
INPUTS=('authentic_packets_predictions.json.gz','calibration_packets.json.gz',
        'individual_calibration_predictions.json.gz')

def guard_metadata(m,calday):
    expected={6:(1,5),8:(2,7),10:(3,9)}
    u=m['unit'];peers=m['peer_units'];family='Figaro' if u<8 else 'FIS'
    if (m['day'] not in expected or (m['fold'],calday)!=expected.get(m['day'])
        or u not in ALLOWED or m['type']!=family or m['model'] not in ('RF','OLS','Ridge')
        or sorted(peers)!=[v for v in ALLOWED if (v<8)==(u<8) and v!=u]):
        raise ValueError('invalid or reserved packet role')

def validate_observables(o):
    if set(o)!={'z','consensus','confidence'}:raise ValueError('nonobservable payload')
    if not all(np.all(np.isfinite(v)) for v in o.values()):raise ValueError('nonfinite observable')

def load_blocks(root:Path):
    manifest=json.loads((root/'reference_budget_study_v1/evidence/PRIOR_INPUT_MANIFEST.json').read_text())
    hashes={r['path']:r['sha256'] for r in manifest}
    loaded=[]
    for name in INPUTS:
        rel='phase6/evidence/'+name;b=(root/rel).read_bytes()
        if hashlib.sha256(b).hexdigest()!=hashes[rel]:raise ValueError('input hash mismatch')
        loaded.append(json.loads(gzip.decompress(b)))
    assessment,calibration,individual=loaded
    def key(c):return (c['metadata']['model'],c['metadata']['day'],c['metadata']['unit'])
    calindex={key(c):c for c in calibration}
    if len(calindex)!=108 or len(assessment)!=108:raise ValueError('packet cardinality')
    indiv={}
    for row in individual:
        if row['unit'] not in ALLOWED:raise ValueError('reserved unit')
        fold=row['fold'];day={1:5,2:7,3:9}.get(fold)
        if day is None or not row['id'].startswith(f'D{day:02d}_'):raise ValueError('calibration role')
        indiv[(fold,row['model'],row['unit'],int(row['id'].split('_E')[1].split('_')[0]))]=row
    groups={}
    for a in assessment:
        c=calindex[key(a)];m=a['metadata'];guard_metadata(m,c['calibration_day'])
        expected=[f'D{m["day"]}_E{j}' for j in range(1,101)]
        if a['exposure_ids']!=expected:raise ValueError('exposure identity/order')
        if a['measurement_ids']!=[f'D{m["day"]:02d}_E{j:03d}_R{m["unit"]:02d}' for j in range(1,101)]:raise ValueError('unit identity')
        cid=[[f'D{c["calibration_day"]:02d}_E{j:03d}_R{u:02d}' for u in m['peer_units']] for j in range(1,101)]
        if c['calibration_peer_ids']!=cid:raise ValueError('calibration identities')
        pp=np.asarray(a['observables']['peer_predictions'],float);cp=np.asarray(c['peer_predictions'],float)
        if pp.shape!=(100,5) or cp.shape!=(100,5):raise ValueError('peer shape')
        med=np.median(pp,axis=1);cm=np.median(cp,axis=1)
        cz=np.column_stack([np.asarray(c['context'])[:,:2],cm])
        az=np.column_stack([np.asarray(a['observables']['target_features'])[:,4:6],med])
        mu=cz.mean(axis=0);sd=cz.std(axis=0);sd=np.where(sd==0,1.,sd)
        if m['model']=='RF':
            cc=np.array([[indiv[(m['fold'],'RF',u,j)]['tree_sd'] for u in m['peer_units']] for j in range(1,101)]).mean(axis=1)
            ac=np.asarray(a['observables']['peer_confidence']).mean(axis=1)
        else:
            cc=np.median(np.abs(cp-cm[:,None]),axis=1);ac=np.median(np.abs(pp-med[:,None]),axis=1)
        scale=max(float(np.median(cc)),.1)
        row={'metadata':m,'cz':(cz-mu)/sd,'az':(az-mu)/sd,'cm':cm,'am':med,
             'ce':cm-np.asarray(c['reference_co']),'cy':np.asarray(c['reference_co']),
             'ay':np.asarray(a['outcomes']['reference_co']),'cc':cc/scale,'ac':ac/scale,
             'q':max(float(c['q']['peer_median']),.1),'center':mu.tolist(),'scale':sd.tolist()}
        groups.setdefault((m['model'],m['day']),[]).append(row)
    blocks=[]
    for (model,day),rows in sorted(groups.items()):
        rows.sort(key=lambda r:r['metadata']['unit'])
        if [r['metadata']['unit'] for r in rows]!=list(ALLOWED):raise ValueError('array membership')
        for r in rows:
            if not np.array_equal(r['ay'],rows[0]['ay']) or not np.array_equal(r['cy'],rows[0]['cy']):
                raise ValueError('shared reference mismatch')
        o={'z':np.stack([r['az'] for r in rows],axis=1),
           'consensus':np.column_stack([r['am'] for r in rows]),'confidence':np.max([r['ac'] for r in rows],axis=0)}
        validate_observables(o)
        blocks.append({'model':model,'day':day,'metadata':[r['metadata'] for r in rows],
                       'normalization':[{'center':r['center'],'scale':r['scale']} for r in rows],
                       'observables':o,'calibration':{'z':np.stack([r['cz'] for r in rows],axis=1),
                       'error':np.column_stack([r['ce'] for r in rows]),'confidence':np.max([r['cc'] for r in rows],axis=0),
                       'q':np.array([r['q'] for r in rows])},'outcomes':rows[0]['ay']})
    return blocks
