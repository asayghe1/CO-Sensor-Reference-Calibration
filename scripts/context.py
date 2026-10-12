"""All generated output stays inside the release's ignored build directory."""
from pathlib import Path
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build'
FROZEN = BUILD / 'frozen'
REPORTS = BUILD / 'reports'
PAPER = BUILD / 'manuscript'
DEV = FROZEN / 'co_revision_execution_v2/work/evidence'
C5 = FROZEN / 'co_submission_finish_v1'

def report(name, value):
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')

if not __debug__:
    report('REPRODUCIBILITY.json', {'status':'FAIL', 'reason':'Optimized Python disables assertion checks and is unsupported.', 'utc':datetime.now(timezone.utc).isoformat()})
    raise SystemExit('Run verification without -O or PYTHONOPTIMIZE.')
