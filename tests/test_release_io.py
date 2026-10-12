"""Release integrity boundary: reject tampering and paths outside the package."""
import gzip
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'release_io.py'

class IntegrityTests(unittest.TestCase):
    def module(self):
        self.assertTrue(SCRIPT.is_file(), 'lossless release reader is not implemented')
        spec = importlib.util.spec_from_file_location('release_io', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def fixture(self, root):
        original = b'pred,ref\n1.0,2.0\n'
        packed = gzip.compress(original, mtime=0)
        (root / 'values.csv.gz').write_bytes(packed)
        return dict(path='values.csv.gz', source_path='evidence/values.csv',
                    sha256=hashlib.sha256(packed).hexdigest(),
                    source_sha256=hashlib.sha256(original).hexdigest(),
                    bytes=len(packed), source_bytes=len(original), encoding='gzip')

    def test_lossless_expansion(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(module.read_verified(root, self.fixture(root)), b'pred,ref\n1.0,2.0\n')

    def test_modified_predictions_are_rejected(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            item = self.fixture(root)
            (root / item['path']).write_bytes(gzip.compress(b'pred,ref\n9.0,2.0\n', mtime=0))
            with self.assertRaises(ValueError):
                module.read_verified(root, item)

    def test_parent_traversal_is_rejected(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                module.safe_path(Path(directory), '../outside.csv')

if __name__ == '__main__':
    unittest.main()
