"""A failed/new partial run must not present an old full-workflow PASS."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'

class RunStatusTests(unittest.TestCase):
    def fixture(self, directory):
        root=Path(directory)
        (root/'scripts').mkdir()
        for name in ('reproduce.py','context.py','release_io.py'):
            shutil.copy2(SCRIPTS/name,root/'scripts'/name)
        (root/'build/reports').mkdir(parents=True)
        (root/'build/reports/REPRODUCIBILITY.json').write_text('{"status":"PASS"}')
        return root

    def test_failed_run_replaces_stale_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root=self.fixture(directory)
            process=subprocess.run([sys.executable,str(root/'scripts/reproduce.py')],capture_output=True)
            self.assertNotEqual(process.returncode,0)
            status=json.loads((root/'build/reports/REPRODUCIBILITY.json').read_text())
            self.assertEqual(status['status'],'FAIL')

    def test_optimized_python_cannot_disable_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            root=self.fixture(directory)
            (root/'manifests').mkdir()
            (root/'manifests/SOURCE_MANIFEST.json').write_text('{"files":[]}')
            (root/'manuscript').mkdir()
            result=subprocess.run([sys.executable,'-O',str(root/'scripts/reproduce.py'),'--prepare-only'],capture_output=True)
            self.assertNotEqual(result.returncode,0,'optimized Python must be refused before assertions can be disabled')

if __name__=='__main__':unittest.main()
