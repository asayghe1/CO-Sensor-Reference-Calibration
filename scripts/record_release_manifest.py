"""Record hashes after all candidate documents/reports have been finalized.
This records identity only. It does not establish scientific or author approval.
"""
import hashlib
from scan_release import ROOT,public_files

def main():
 target=ROOT/'RELEASE_FILES_SHA256.txt'
 rows=[hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix() for p in public_files(ROOT) if p!=target]
 target.write_text('\n'.join(rows)+'\n')
 print('Recorded',len(rows),'release-file hashes; no original scientific manifest replaced.')
if __name__=='__main__':main()
