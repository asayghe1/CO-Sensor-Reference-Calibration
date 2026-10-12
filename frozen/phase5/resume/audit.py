from pathlib import Path,PurePosixPath
import json,hashlib,zipfile,io,stat,datetime
import numpy as np
from phase5.resume.methods import COLS,ALLOWED_UNITS,scheduled_core
R=Path(__file__).resolve().parents[2]; O=R/'phase5/resume/evidence'
def sha(b):return hashlib.sha256(b).hexdigest()
def inventory(z):
 seen=set();out=[]
 assert sum(i.file_size for i in z.infolist())<2_000_000_000
 for i in z.infolist():
  p=PurePosixPath(i.filename)
  assert not p.is_absolute() and '..' not in p.parts and i.filename not in seen
  assert not stat.S_ISLNK(i.external_attr>>16)
  assert i.file_size/max(1,i.compress_size)<1000
  seen.add(i.filename)
  b=z.read(i.filename) # Opaque CRC/hash validation only for reserved members.
  out.append({'name':i.filename,'bytes':len(b),'compressed_bytes':i.compress_size,'crc32':i.CRC,'sha256':sha(b)})
 return out
raw=(R/'data/co_chamber/uci487.zip').read_bytes()
with zipfile.ZipFile(io.BytesIO(raw)) as z:
 outer=inventory(z);nested=z.read('gas-sensor-array-temperature-modulation.zip')
 with zipfile.ZipFile(io.BytesIO(nested)) as n:
  inv=inventory(n);names=sorted(x for x in n.namelist() if x.endswith('.csv'));assert len(names)==13
  assert n.read('README.txt')==z.read('README.txt')
  sessions=[{'day':d+1,'file':name,'role':'development' if d<10 else 'reserved_final','start':datetime.datetime.strptime(name[:-4],'%Y%m%d_%H%M%S').isoformat()} for d,name in enumerate(names)]
  all_aud=[];features=[];failed=[]
  for d,name in enumerate(names[:10],1):
   with n.open(name) as f:
    header=f.readline().decode().strip().split(',');assert len(header)==20
    a=np.loadtxt(f,delimiter=',',usecols=COLS)
   t=a[:,0];dt=np.diff(t);clock_bad=bool(np.any(dt<=0))
   row={'day':d,'file':name,'rows':len(a),'header':header,'nonfinite_allowed_values':int((~np.isfinite(a)).sum()),'nonpositive_time_steps':int((dt<=0).sum()),'dt_quantiles':np.quantile(dt,[0,.5,1]).tolist(),'time_end_s':float(t[-1]),'nonpositive_allowed_resistance':{str(u):int((a[:,j+6]<=0).sum()) for j,u in enumerate(ALLOWED_UNITS)},'exact_duplicate_allowed_full_rows':int(len(a)-len(np.unique(a,axis=0))),'exposures':[]}
   starts=np.flatnonzero(np.diff(a[:,1])!=0)+1;burst=starts[np.r_[True,np.diff(t[starts])>10]]
   row['reference_transition_bursts']=len(burst);row['transition_offset_to_nearest_900_s_quantiles']=np.quantile(t[burst]-np.round(t[burst]/900)*900,[0,.5,1]).tolist()
   eligible=not clock_bad and row['nonfinite_allowed_values']==0
   if clock_bad:row['session_exclusion']='nonmonotonic_clock';failed.append({'day':d,'reason':'nonmonotonic_clock','indices':np.flatnonzero(dt<=0).tolist()})
   high=a[:,5]>.5;edges=np.flatnonzero(np.diff(high.astype(int))!=0)+1
   previous=np.maximum.accumulate(np.where(np.r_[True,np.diff(high.astype(int))!=0],t,-np.inf));phase=t-previous
   counts={}
   for e in range(1,101):
    m=scheduled_core(t,e);b=a[m];co=np.unique(b[:,1]);core={'exposure':e,'n_core_rows':len(b),'co_values':co.tolist(),'complete_nominal_block':bool(t[0]<=900*e and t[-1]>=900*(e+1)-10),'max_core_gap_s':float(np.max(np.diff(b[:,0]))) if len(b)>1 else None}
    valid=eligible and core['complete_nominal_block'] and len(co)==1 and len(b)>500 and np.all(np.isfinite(b)) and np.all(b[:,6:]>0) and core['max_core_gap_s']<5
    core['eligible']=bool(valid);row['exposures'].append(core)
    if len(co)==1:counts[str(co[0])]=counts.get(str(co[0]),0)+1
    if valid:
     masks=[m&high,m&(~high)&(phase<5),m&(~high)&(phase>=5)&(phase<15),m&(~high)&(phase>=15)]
     if min(int(q.sum()) for q in masks)<10:core['eligible']=False;core['reason']='incomplete_heater_phase';continue
     for j,u in enumerate(ALLOWED_UNITS):
      x=[float(np.median(np.log(a[q,j+6]))) for q in masks]+[float(np.median(b[:,2])),float(np.median(b[:,3]))]
      features.append({'id':f'D{d:02}_E{e:03}_R{u:02}','day':d,'exposure':e,'unit':u,'type':'Figaro' if u<8 else 'FIS','features':x,'reference_co':float(co[0]),'core_rows':len(b)})
   row['nominal_level_counts']=counts;row['eligible_exposures']=sum(q['eligible'] for q in row['exposures']);all_aud.append(row)
   print(name,'rows',len(a),'eligible',row['eligible_exposures'],'excluded',row.get('session_exclusion'),flush=True)
assert sum(x['eligible_exposures'] for x in all_aud)==len(features)//12
result={'archive_sha256':sha(raw),'archive_bytes':len(raw),'nested_sha256':sha(nested),'outer_inventory':outer,'nested_inventory':inv,'provenance':'user_reports_manually_downloaded_official_archive; structure/README consistent with official record; no publisher checksum available','official_checksum_comparison':None,'reserved_units':[7,14],'sessions':sessions,'development_audit':all_aud,'structural_failures':failed,'development_rows_checked':sum(x['rows'] for x in all_aud),'eligible_exposures':len(features)//12,'documented_physical_units':14,'development_units':12,'reference_covariance':'unknown','exact_switch_timestamps':'not recorded; nominal schedule cores only'}
O.joinpath('data_audit.json').write_text(json.dumps(result,indent=2));O.joinpath('exposure_features.json').write_text(json.dumps(features))
print('eligible exposures',len(features)//12)
