"""Lossless tabular view of saved predictions, never a prediction generator."""
import csv
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path
from context import ROOT, BUILD, DEV, C5, report

ESTIMATORS = ('consensus', 'midpoint', 'projection', 'offset', 'affine', 'affine_l095', 'affine_l090')
UNITS = (1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13)
FIELDS = ('run_id', 'model', 'bounds', 'session', 'schedule', 'schedule_id', 'schedule_driver',
          'budget', 'seed', 'exposure', 'config', 'unit', 'family', 'queried', 'reference',
          *ESTIMATORS, 'error_lower', 'error_upper', 'contradiction')

def sources():
    for path in sorted(DEV.glob('runs_*.json.gz')):
        yield 'development/' + path.name.replace('runs_', '').replace('.json.gz', '.csv.gz'), [path]
    for day in (11, 12, 13):
        yield f'confirmation/D{day}.csv.gz', sorted((C5/'c5_execution_v1/replays').glob(f'D{day}_*.json'))

def saved_runs(paths):
    for path in paths:
        if path.name.endswith('.gz'):
            yield from json.loads(gzip.decompress(path.read_bytes()))
        else:
            run = json.loads(path.read_text())
            match = re.fullmatch(r'D(\d+)_(\w+)_B(\d+)_S(\d+)\.json', path.name)
            day, schedule, budget, seed = match.groups()
            run['identity'] = dict(run_id=path.stem, model='RF', bounds='primary', session='D'+day,
                                   schedule=schedule, schedule_id=schedule, schedule_driver=run['driver'],
                                   budget=int(budget), seed=int(seed))
            references = json.loads((C5/'c5_execution_v1/REFERENCES_FOR_EVALUATOR_ONLY.json').read_text())
            run['reference'] = references[day]
            yield run

def rows(paths):
    for run in saved_runs(paths):
        meta = run['identity']
        for i in range(100):
            for j, unit in enumerate(UNITS):
                row = {**meta, 'exposure': i+1, 'config': j+1, 'unit': unit,
                       'family': 'Figaro' if j < 6 else 'FIS', 'queried': int(run['query'][i]),
                       'reference': run['reference'][i], 'error_lower': run['error_lower'][i][j],
                       'error_upper': run['error_upper'][i][j], 'contradiction': int(run['contradiction'][i][j])}
                for estimator in ESTIMATORS:
                    row[estimator] = run['predictions'][estimator][i][j] if estimator in run['predictions'] else ''
                yield {key: str(row[key]) for key in FIELDS}

def main(write=False):
    entries = []
    for name, paths in sources():
        if write:
            target = BUILD/'predictions'/name
            target.parent.mkdir(parents=True, exist_ok=True)
            import io
            with target.open('wb') as raw, gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as zipped:
                with io.TextIOWrapper(zipped, encoding='utf-8', newline='') as stream:
                    writer = csv.DictWriter(stream, fieldnames=FIELDS)
                    writer.writeheader()
                    count = 0
                    for row in rows(paths):
                        writer.writerow(row)
                        count += 1
        else:
            target = ROOT/'predictions'/name
            with gzip.open(target, 'rt', newline='') as stream:
                actual = csv.DictReader(stream)
                assert actual.fieldnames == list(FIELDS)
                count = 0
                for expected in rows(paths):
                    assert next(actual, None) == expected, (name, count)
                    count += 1
                assert next(actual, None) is None, name
        entries.append(dict(path='predictions/'+name, rows=count, bytes=target.stat().st_size,
                            sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
    result = {'status':'PASS', 'operation':'lossless saved-value export' if write else 'exact saved-value comparison',
              'prediction_generation':False, 'rows':sum(r['rows'] for r in entries), 'files':entries}
    report('PREDICTION_CSV_EXPORT.json' if write else 'PREDICTION_CSV_CHECK.json', result)
    print('Prediction CSVs:', result['rows'], 'rows, PASS', flush=True)

if __name__ == '__main__':
    if sys.argv[1:] not in ([], ['--write']):
        raise SystemExit('Usage: python scripts/prediction_csv.py [--write]')
    main(write=sys.argv[1:] == ['--write'])
