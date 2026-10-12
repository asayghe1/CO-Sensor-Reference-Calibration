"""Check saved CSV exports and typeset cells, without inference or raw access."""
from pathlib import Path
import csv, hashlib, json, math, re

W = Path(__file__).resolve().parent
O = W.parent
E = O / 'c5_execution_v1'
P = O / 'paper_with_c5'

def rows(name):
    with (E / name).open(newline='') as f:
        return list(csv.DictReader(f))

def same(value, expected):
    if expected is None:
        assert value in ('', 'NA'), (value, expected)
    elif isinstance(expected, (dict, list)):
        assert json.loads(value) == expected
    elif isinstance(expected, (int, float)):
        assert math.isclose(float(value), expected, rel_tol=1e-13, abs_tol=1e-12), (value, expected)
    else:
        assert value == expected, (value, expected)

M = json.loads((E / 'replays/METRICS.json').read_text())
A = json.loads((E / 'replays/AGGREGATE.json').read_text())
for name, source in [('C5_METRICS.csv', M), ('C5_AGGREGATE.csv', A)]:
    exported = rows(name)
    assert len(exported) == len(source)
    for actual, expected in zip(exported, source):
        assert set(expected) <= set(actual)
        for field, value in actual.items():
            same(value, expected.get(field))

def aggregate(est, policy='none', budget=0, scope='ALL', subset='all'):
    return next(v for v in A if (v['estimator'], v['policy'], v['budget'], v['scope'], v['subset']) == (est, policy, budget, scope, subset))

primary = rows('C5_PRIMARY_TABLE.csv')
sessions = rows('C5_PRIMARY_SESSION_TABLE.csv')
affine = rows('C5_B20_AFFINE_CHANGES.csv')
intervals = rows('C5_INTERVAL_TABLE.csv')
for row in primary:
    scope = row['scope']
    raw = aggregate('consensus', scope=scope)
    b0 = aggregate('affine', scope=scope)
    b20 = aggregate('affine', 'envelope', 20, scope)
    same(row['outputs'], raw['outputs'])
    for label, source in [('consensus', raw), ('affine_B0', b0), ('affine_envelope_B20', b20)]:
        same(row[label + '_mae'], source['mae'])
    for label, source in [('consensus', raw), ('affine_B0', b0), ('affine_B20', b20)]:
        same(row[label + '_p1_count'], source['exceed_count_1.0'])
    for label, high, low in [('historical', b0, raw), ('incremental', b20, b0)]:
        same(row[label + '_mae_change'], high['mae'] - low['mae'])
        same(row[label + '_p1_change_pp'], 100 * (high['exceed_rate_1.0'] - low['exceed_rate_1.0']))
for row in sessions:
    source = []
    for label, est, policy, budget in [('consensus', 'consensus', 'none', 0), ('affine_B0', 'affine', 'none', 0), ('affine_B20', 'affine', 'envelope', 20)]:
        v = next(v for v in M if (v['day'], v['scope'], v['subset'], v['estimator'], v['policy'], v['budget']) == (int(row['day']), row['scope'], 'all', est, policy, budget))
        same(row[label + '_mae'], v['mae'])
        same(row[label + '_p1_count'], v['exceed_count_1.0'])
        same(row['outputs'], v['outputs'])
        source.append(v)
    same(row['historical_mae_change'], source[1]['mae'] - source[0]['mae'])
    same(row['incremental_mae_change'], source[2]['mae'] - source[1]['mae'])
for row in affine:
    v = aggregate(row['estimator'], row['policy'], 20)
    b0 = aggregate(row['estimator'])
    assert int(row['budget']) == 20
    for field in ('mae', 'outputs'):
        same(row[field], v[field])
    same(row['p1_count'], v['exceed_count_1.0'])
    same(row['mae_change'], v['mae'] - b0['mae'])
    same(row['p1_change_pp'], 100 * (v['exceed_rate_1.0'] - b0['exceed_rate_1.0']))
    for day in ('11', '12', '13'):
        same(row[f'D{day}_mae_change'], v['day_mae'][day] - b0['day_mae'][day])
for row in intervals:
    v = aggregate('midpoint', 'envelope', 20, row['scope'], row['subset'])
    mapping = {'width_ppm': 'width_mean', 'assured': 'assured_1.0', 'false': 'false_1.0', 'false_over_assured': 'false_over_assured_1.0', 'false_over_all': 'false_over_all_1.0'}
    for field, value in row.items():
        same(value, v[mapping.get(field, field)])

# Verify typeset values directly against the verified CSV/JSON cells.
checked = {}
def check_table(name, expected_rows):
    lines = [line.strip().removesuffix('\\\\').strip() for line in (P/name).read_text().splitlines() if line.startswith(('ALL &', 'Figaro &', 'FIS &', 'D11 &', 'D12 &', 'D13 &', '$\\lambda='))]
    actual = [[c.strip() for c in line.split('&')] for line in lines]
    assert actual == expected_rows, name
    checked[name] = len(actual)

fmt = lambda v: f'{float(v):.4f}'
check_table('table_c5_primary.tex', [[r['scope'], r['outputs']] + [fmt(r[k]) for k in ('consensus_mae','affine_B0_mae','affine_envelope_B20_mae')] + [r[k] for k in ('consensus_p1_count','affine_B0_p1_count','affine_B20_p1_count')] for r in primary])
check_table('table_c5_intervals.tex', [[r['scope'], r['outputs'], r['raw_noncontainment'], r['reported_noncontainment'], r['contradictions'], fmt(r['width_ppm']), r['false']+'/'+r['assured']] for r in intervals if r['subset']=='all'])
check_table('table_s_c5_sessions_mae.tex', [['D'+r['day'],r['scope']] + [fmt(r[k]) for k in ('consensus_mae','affine_B0_mae','affine_B20_mae','historical_mae_change','incremental_mae_change')] for r in sessions])
check_table('table_s_c5_sessions_counts.tex', [['D'+r['day'],r['scope']] + [r[k] for k in ('outputs','consensus_p1_count','affine_B0_p1_count','affine_B20_p1_count')] for r in sessions])
policy_names = {'none':'Historical only','rlsvar':'Information'}
factor_names = {'affine': r'$\lambda=1$', 'affine_l095': r'$\lambda=.95$', 'affine_l090': r'$\lambda=.90$'}
check_table('table_s_c5_b20.tex', [[factor_names[r['estimator']], policy_names.get(r['policy'],r['policy'].title())] + [fmt(r[k]) for k in ('mae_change','p1_change_pp','D11_mae_change','D12_mae_change','D13_mae_change')] for r in affine])
est_names = {'consensus':'Consensus','midpoint':'Midpoint','projection':'Projection','offset':'Offset', **{k:'Affine '+v for k,v in factor_names.items()}}
expected = []
for scope in ('ALL', 'Figaro', 'FIS'):
    for est,label in est_names.items():
        for budget in (0,5,10,20):
            for policy in (('none',) if budget==0 else ('periodic','random','confidence','envelope','rlsvar')):
                v=aggregate(est,policy,budget,scope)
                b=aggregate('consensus' if budget==0 else est,scope=scope)
                expected.append([scope,label,policy_names.get(policy,policy.title()),str(budget),fmt(v['mae']),f"{100*v['exceed_rate_1.0']:.2f}",fmt(v['mae']-b['mae'])])
check_table('table_s_c5_all.tex', expected)

copies = []
for path in sorted(E.glob('C5_*.csv')):
    assert hashlib.sha256(path.read_bytes()).digest() == hashlib.sha256((P/path.name).read_bytes()).digest(), path.name
    copies.append(path.name)
result = {'status':'PASS','saved_run_export_rows':len(M),'saved_aggregate_export_rows':len(A),'presentation_csv_rows':len(primary)+len(sessions)+len(affine)+len(intervals),'typeset_rows_by_file':checked,'unchanged_csv_copies':copies,'no_prediction_generation_or_raw_access':True}
(W/'REPORTING_EXPORT_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
