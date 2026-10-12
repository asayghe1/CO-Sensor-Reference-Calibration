"""Catch accidental inclusion of local paths, credentials and raw records."""
import gzip
import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1]/'scripts/scan_release.py'

class ScanTests(unittest.TestCase):
    def module(self):
        self.assertTrue(SCRIPT.is_file(), 'release scanner is not implemented')
        spec=importlib.util.spec_from_file_location('scan_release',SCRIPT)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_compressed_private_paths_are_found(self):
        module=self.module()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'records.json.gz').write_bytes(gzip.compress(('/h'+'ome/person/private.csv').encode()))
            findings=module.scan_tree(root)['findings']
            self.assertTrue(any(x['rule']=='private_absolute_path' for x in findings))

    def test_credential_file_is_rejected_without_printing_contents(self):
        module=self.module()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'.env').write_text('EXAMPLE=value')
            findings=module.scan_tree(root)['findings']
            self.assertTrue(any(x['rule']=='credential_filename' for x in findings))
            self.assertNotIn('EXAMPLE',str(findings))

    def test_raw_session_csv_is_rejected(self):
        module=self.module()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'20161013_143355.csv').write_text('header\n')
            self.assertTrue(any(x['rule']=='raw_dataset_payload' for x in module.scan_tree(root)['findings']))

if __name__=='__main__':unittest.main()
