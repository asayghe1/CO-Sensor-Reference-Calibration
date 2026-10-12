"""Compare frozen development metrics and saved causal records; no learning/replay."""
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from context import BUILD, DEV, C5, FROZEN, report

def compare_csv(expected, actual):
    count = 0
    largest = 0.
    with expected.open(newline='') as left, actual.open(newline='') as right:
        a, b = csv.DictReader(left), csv.DictReader(right)
        assert a.fieldnames == b.fieldnames, expected.name
        for row in a:
            other = next(b, None)
            assert other is not None, expected.name
            for key, value in row.items():
                if value == other[key]:
                    continue
                try:
                    x, y = float(value), float(other[key])
                except ValueError:
                    raise AssertionError((expected.name, count, key, value, other[key])) from None
                assert math.isfinite(x) and math.isfinite(y)
                largest = max(largest, abs(x-y))
                assert math.isclose(x, y, abs_tol=1e-10, rel_tol=1e-13), (expected.name, count, key, x, y)
            count += 1
        assert next(b, None) is None, expected.name
    return dict(rows=count, maximum_absolute_difference=largest)

def main():
    checked = {}
    for path in sorted((BUILD/'development_recomputed').glob('*.csv')):
        checked[path.name] = compare_csv(DEV/path.name, path)
    for path in sorted((BUILD/'assurance_recomputed').glob('*.csv')):
        checked[path.name] = compare_csv(C5/'paper_with_c5'/path.name, path)
    run_manifest = {row['run_id']: row for row in json.loads((DEV/'RUN_MANIFEST.json').read_text())}
    seen = set()
    events = 0
    predictions = 0
    saved_states = 0
    missing_success_flags = 0
    for path in sorted(DEV.glob('runs_*.json.gz')):
        for run in json.loads(gzip.decompress(path.read_bytes())):
            meta = run['identity']
            key = meta['run_id']
            assert key not in seen
            seen.add(key)
            record = run_manifest[key]
            q = np.array(run['query'], bool)
            assert q.shape == (100,) and q.sum() == meta['budget']
            assert np.flatnonzero(q).tolist() == [n-1 for n in record['queries']]
            assert hashlib.sha256(q.tobytes()).hexdigest() == record['mask_sha256']
            for estimator, values in run['predictions'].items():
                values = np.array(values)
                assert values.shape == (100, 12) and np.isfinite(values).all()
                predictions += values.size
            if 'access_log' in run:
                assert len(run['access_log']) == 100
                for i, event in enumerate(run['access_log']):
                    assert event['index'] == i and event['stage'] == 'prediction_frozen'
                    assert event['past'] == np.flatnonzero(q[:i]).tolist()
                    assert event['query'] == event['released_after_freeze'] == bool(q[i])
                    # Historical OLS/ridge exports retain four of the seven internal
                    # estimators covered by this digest; their full digest cannot
                    # be reconstructed from that reduced export. Never infer them.
                    if meta['model'] == 'RF':
                        value = np.array([run['predictions'][e][i] for e in run['predictions']])
                        assert hashlib.sha256(value.tobytes()).hexdigest() == event['prediction_sha256']
                    if i == 99:
                        assert event['affects_from'] is None
                    events += 1
                assert [p['index'] for p in run['purchases']] == np.flatnonzero(q).tolist()
                for purchase in run['purchases']:
                    assert purchase['reference'] == run['reference'][purchase['index']]
                    for states in purchase['state_after'].values():
                        for state in states:
                            assert np.isfinite(state['theta']).all() and np.isfinite(state['P']).all()
                            assert not state['failures']
                            if 'update_success' in state:
                                assert state['update_success']
                            else:
                                missing_success_flags += 1
                            saved_states += 1
    assert seen == set(run_manifest)
    result = dict(status='PASS', csv_checks=checked, runs=len(seen), saved_prediction_scalars=predictions,
                  causal_events=events, saved_purchase_states=saved_states, prediction_generation=False,
                  state_records_without_explicit_update_success_flag=missing_success_flags,
                  raw_data_access=False, note='Legacy bound-sensitivity records have masks and arrays; detailed causal events exist for the revised primary branch. Full prequery prediction digests are reproduced for RF. OLS/ridge retained four of seven internally hashed estimators, so their original full prediction digests are preserved but not independently reconstructed.')
    report('DEVELOPMENT_VERIFICATION.json', result)
    print('Development:',len(seen),'runs;',events,'causal events; metric CSVs PASS', flush=True)

if __name__ == '__main__':
    main()
