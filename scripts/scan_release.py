"""Scan distributable files, including compressed text, without printing matches."""
from pathlib import Path
import gzip
import hashlib
import json
import re
import zipfile

ROOT=Path(__file__).resolve().parents[1]
IGNORED={'build','.git','.venv','__pycache__','.pytest_cache'}
PATTERNS={
    'private_absolute_path':re.compile(rb'/(?:home|Users|mnt/[^/]+/Users)/[A-Za-z0-9_.-]+/|[A-Za-z]:\\Users\\'),
    'private_key':re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'github_token':re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})'),
    'aws_access_key':re.compile(rb'(?:AKIA|ASIA)[A-Z0-9]{16}'),
    'slack_token':re.compile(rb'xox[baprs]-[0-9A-Za-z-]{20,}'),
    'credential_assignment':re.compile(rb'(?im)^\s*(?:password|api_key|access_token|secret_key)\s*[:=]\s*[\"\'][A-Za-z0-9+/=_-]{12,}[\"\']'),
}

def public_files(root):
    for p in sorted(root.rglob('*')):
        parts=p.relative_to(root).parts
        if any(part in IGNORED for part in parts) or parts[:2]==('data','external'):
            continue
        if p.suffix in ('.pyc','.aux','.log','.out','.fls','.blg','.bbl') or p.name.endswith(('.fdb_latexmk','.synctex.gz')):
            continue
        if p.is_file() or p.is_symlink():
            yield p

def scan_tree(root):
    findings=[];sizes=[];expanded=0
    def check(data,rel):
        for rule,pattern in PATTERNS.items():
            if pattern.search(data):findings.append({'path':rel,'rule':rule})
    for p in public_files(root):
        rel=p.relative_to(root).as_posix()
        if p.is_symlink():
            findings.append({'path':rel,'rule':'symbolic_link'});continue
        sizes.append({'path':rel,'bytes':p.stat().st_size})
        if p.stat().st_size>=50*1024*1024:findings.append({'path':rel,'rule':'file_at_least_50MiB'})
        if p.name.lower() in ('.env','credentials','credentials.json','id_rsa','id_ed25519') or p.suffix.lower() in ('.pem','.key') or any(x in p.parts for x in ('.aws','.ssh')):
            findings.append({'path':rel,'rule':'credential_filename'})
        if re.fullmatch(r'20\d{6}_\d{6}\.csv(?:\.gz)?',p.name) or re.fullmatch(r'batch\d+\.dat(?:\.gz)?',p.name) or p.name.lower().endswith('.zip'):
            findings.append({'path':rel,'rule':'raw_dataset_payload'})
        data=p.read_bytes()
        if p.suffix=='.gz':
            try:data=gzip.decompress(data);expanded+=1
            except OSError:findings.append({'path':rel,'rule':'invalid_gzip'})
        check(data,rel)
        if p.suffix=='.npz':
            with zipfile.ZipFile(p) as z:
                for name in z.namelist():check(z.read(name),rel+'::'+name)
        if p.suffix=='.pdf':
            from pypdf import PdfReader
            reader=PdfReader(p)
            check(('\n'.join(page.extract_text() or '' for page in reader.pages)+str(reader.metadata)).encode(),rel+'::text')
    return {'status':'PASS' if not findings else 'FAIL','files_scanned':len(sizes),'gzip_payloads_scanned':expanded,
            'total_bytes':sum(s['bytes'] for s in sizes),'largest_files':sorted(sizes,key=lambda r:r['bytes'],reverse=True)[:10],
            'findings':findings,'scope':'Distributable files, expanded gzip/NPZ payloads, raw binary strings and extracted PDF text/metadata. Joblib objects are never loaded. Generated build output, environments, caches, Git metadata and optional external raw downloads are excluded by the packaging rule.',
            'limitation':'Pattern and filename scan, not a guarantee that every possible secret format can be detected.'}

def main():
    result=scan_tree(ROOT)
    checksum=ROOT/'RELEASE_FILES_SHA256.txt'
    if checksum.exists():
        entries={}
        for line in checksum.read_text().splitlines():
            digest,name=line.split('  ',1);entries[name]=digest
        actual={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in public_files(ROOT) if p!=checksum}
        if entries!=actual:
            result['findings'].append({'path':'RELEASE_FILES_SHA256.txt','rule':'release_manifest_mismatch'})
            result['status']='FAIL'
        result['release_hashes_verified']=len(actual)
    else:result['release_hashes_verified']=None
    required=('LICENSE','DATA_LICENSE.md','THIRD_PARTY_NOTICES.md','licenses/LPPL-1.3c.tex','CITATION.cff')
    assert all((ROOT/p).is_file() for p in required)
    result['license_files_present']=True
    result['license_authority_approval']='pending authors; technical scan is not legal approval'
    (ROOT/'build/reports').mkdir(parents=True,exist_ok=True)
    (ROOT/'build/reports/RELEASE_SCAN.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if result['status']!='PASS':raise SystemExit(1)

if __name__=='__main__':main()
