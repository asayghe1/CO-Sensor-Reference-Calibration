"""Portable evidence-only reproduction. Never invokes fitting or replay entry points."""
import argparse,hashlib,json,os,shutil,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
from context import ROOT,BUILD,FROZEN,REPORTS,PAPER,DEV,C5,report
from release_io import materialize

def run(script):
 print('Checking:',script,flush=True)
 env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','MPLCONFIGDIR':str(BUILD/'matplotlib'),'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'}
 subprocess.run([sys.executable,str(ROOT/'scripts'/script)],cwd=ROOT,env=env,check=True)

def prepare():
 BUILD.mkdir(exist_ok=True);REPORTS.mkdir(exist_ok=True)
 n=materialize(FROZEN)
 shutil.copytree(ROOT/'manuscript',PAPER,dirs_exist_ok=True)
 for p in DEV.glob('*.csv'):shutil.copy2(p,PAPER/p.name)
 for p in (C5/'c5_execution_v1').glob('C5_*.csv'):shutil.copy2(p,PAPER/p.name)
 for p in (C5/'paper_with_c5').glob('FALSE_ASSURANCE*.csv'):shutil.copy2(p,PAPER/p.name)
 report('MATERIALIZATION.json',dict(status='PASS',source_files=n,hash_verified_before_expansion=True))
 print('Verified and expanded',n,'frozen files',flush=True)

def workflow(args,started):
 start=time.monotonic();prepare()
 if args.prepare_only:
  report('REPRODUCIBILITY.json',dict(status='PREPARED',started_utc=started,scope='Hash-verified materialization only; numerical and document checks not run.'))
  return
 for script in ('score_saved_development.py','score_saved_updates.py','score_saved_assurance.py','aggregate_saved_assurance.py','verify_development.py','verify_saved_resampling.py','verify_confirmation.py','verify_confirmation_aggregate.py','verify_development_tables.py','verify_confirmation_tables.py','prediction_csv.py','verify_manuscript_numbers.py'):
  run(script)
 env={**os.environ,'MPLCONFIGDIR':str(BUILD/'matplotlib'),'PYTHONDONTWRITEBYTECODE':'1'}
 subprocess.run([sys.executable,str(PAPER/'format_figures.py')],cwd=PAPER,env=env,check=True)
 before=json.loads((ROOT/'manuscript/FIGURE_VALUE_AUDIT.json').read_text());after=json.loads((PAPER/'FIGURE_VALUE_AUDIT.json').read_text());assert before==after
 report('FIGURES.json',dict(status='PASS',figures=4,plotted_cells=len(after['plotted_cells']),saved_cells_exactly_equal=True))
 if args.latex:
  with (BUILD/'latex_build.log').open('w') as log:subprocess.run(['bash','build.sh'],cwd=PAPER,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
  run('verify_latex.py')
 # Expansion must still match its frozen input after all read-only numerical checks.
 entries=json.loads((ROOT/'manifests/SOURCE_MANIFEST.json').read_text())['files']
 for item in entries:assert hashlib.sha256((FROZEN/item['source_path']).read_bytes()).hexdigest()==item['source_sha256'],item['source_path']
 report('REPRODUCIBILITY.json',dict(status='PASS',started_utc=started,completed_utc=datetime.now(timezone.utc).isoformat(),scope='Saved numerical evidence and presentation reproduction',seconds=round(time.monotonic()-start,2),source_files_unchanged=len(entries),models_fitted=0,predictions_generated=0,C5_replays_executed=0,new_resampling_indices=0,confirmation_bootstrap=False,raw_data_access=False,latex_checked=args.latex))
 print('Evidence-only reproduction PASS',flush=True)

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--prepare-only',action='store_true',help='expand and verify evidence without executing any analyses')
 parser.add_argument('--latex',action='store_true',help='also build the completed manuscript with TeX Live')
 args=parser.parse_args()
 REPORTS.mkdir(parents=True,exist_ok=True)
 # Generated reports belong to this workflow; never leave a prior PASS after a failed retry.
 for path in REPORTS.glob('*.json'):path.unlink()
 started=datetime.now(timezone.utc).isoformat()
 report('REPRODUCIBILITY.json',dict(status='RUNNING',started_utc=started))
 try:
  workflow(args,started)
 except BaseException as error:
  report('REPRODUCIBILITY.json',dict(status='FAIL',started_utc=started,completed_utc=datetime.now(timezone.utc).isoformat(),error_type=type(error).__name__,scope='This run did not complete. Inspect its terminal output; no full-reproduction success is claimed.'))
  raise

if __name__=='__main__':main()
