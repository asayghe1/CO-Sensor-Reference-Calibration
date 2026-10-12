"""Read and expand hash-verified frozen evidence without importing experiment code."""
from pathlib import Path, PurePosixPath
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]

def safe_path(root, relative):
    p = PurePosixPath(relative)
    if p.is_absolute() or '..' in p.parts or '\\' in relative:
        raise ValueError('unsafe manifest path')
    target = (root / p).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError('path escapes package')
    return target

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read_verified(root, item):
    data = safe_path(root, item['path']).read_bytes()
    if len(data) != item['bytes'] or digest(data) != item['sha256']:
        raise ValueError('packaged artifact changed: ' + item['path'])
    if item['encoding'] == 'gzip':
        data = gzip.decompress(data)
    elif item['encoding'] != 'identity':
        raise ValueError('unknown packaging encoding')
    if len(data) != item['source_bytes'] or digest(data) != item['source_sha256']:
        raise ValueError('expanded artifact changed: ' + item['path'])
    return data

def materialize(destination):
    items = json.loads((ROOT / 'manifests/SOURCE_MANIFEST.json').read_text())['files']
    for item in items:
        data = read_verified(ROOT, item)
        target = safe_path(destination, item['source_path'])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return len(items)
