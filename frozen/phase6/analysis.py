"""Frozen information-equivalent development evaluation. No raw/final data access."""
from pathlib import Path
import json,gzip,hashlib,time,sys,collections
import numpy as np
from phase5.resume.analysis import make_model
from phase6.methods import POINTS,ALLOWED,guard_role,fuse,compute_scores,context,quantile,alert_quantile,select_group,metrics
R=Path(__file__).resolve().parents[1];P=R/'phase6';E=P/'evidence';OLD=R/'phase5/resume/evidence'
def read(p):return json.loads(p.read_text())
def save(name,obj):
 b=json.dumps(obj,allow_nan=False,separators=(',',':')).encode()
 if name.endswith('.gz'):b=gzip.compress(b,mtime=0)
 (E/name).write_bytes(b)
def array_packet(p):
 return {k:({s:np.array(v) for s,v in x.items()} if k=='target_scores' else None if x is None else np.array(x)) for k,x in p.items()}
def list_packet(p):return {k:({s:v.tolist() for s,v in x.items()} if k=='target_scores' else None if x is None else x.tolist()) for k,x in p.items()}
def build():
 records=read(OLD/'exposure_features.json');pred=read(OLD/'predictions.json');oldby=collections.defaultdict(list)
 for v in records:assert v['unit'] in ALLOWED and v['day']<=10 and v['day']!=3
 for v in pred:oldby[(v['fold'],v['type'],v['model'],v['unit'])].append(v)
 cells=[];calarchive=[];assignments=[];individual=[];fitcount=0;largest=0.
 for fold,(last,cd,ad) in enumerate([(4,5,6),(6,7,8),(8,9,10)],1):
  for family,units in [('Figaro',list(range(1,7))),('FIS',list(range(8,14)))]:
   for kind in ['OLS','Ridge','RF']:
    cp={};ap={};csd={};asd={};fitids={}
    for u in units:
     f=sorted([r for r in records if r['day']<=last and r['unit']==u],key=lambda r:(r['day'],r['exposure']))
     c=sorted([r for r in records if r['day']==cd and r['unit']==u],key=lambda r:r['exposure']);a=sorted([r for r in records if r['day']==ad and r['unit']==u],key=lambda r:r['exposure'])
     fitids[u]=[r['id'] for r in f];model=make_model(kind).fit(np.array([r['features'] for r in f]),np.array([r['reference_co'] for r in f]));fitcount+=1
     cx=np.array([r['features'] for r in c]);ax=np.array([r['features'] for r in a]);cp[u]=model.predict(cx);ap[u]=model.predict(ax)
     if kind=='RF':
      csd[u]=np.std(np.array([t.predict(model[0].transform(cx)) for t in model[-1].estimators_]),axis=0)
      asd[u]=np.std(np.array([t.predict(model[0].transform(ax)) for t in model[-1].estimators_]),axis=0)
     for j,r in enumerate(c):individual.append({'fold':fold,'model':kind,'type':family,'unit':u,'id':r['id'],'prediction':float(cp[u][j]),'tree_sd':float(csd[u][j]) if kind=='RF' else None})
    for target in units:
     peers=[u for u in units if u!=target];guard_role(ad,target,peers)
     old=sorted(oldby[(fold,family,kind,target)],key=lambda v:int(v['exposure_id'].split('E')[1]));assert len(old)==100
     peer_a=np.column_stack([ap[u] for u in peers]);peer_c=np.column_stack([cp[u] for u in peers]);oldpa=np.array([v['peer_predictions'] for v in old]);difference=float(np.max(np.abs(peer_a-oldpa)));largest=max(largest,difference)
     assert np.allclose(peer_a,oldpa,atol=1e-12,rtol=1e-12);assert np.allclose(ap[target],[v['individual_prediction'] for v in old],atol=1e-12,rtol=1e-12)
     aa=sorted([r for r in records if r['day']==ad and r['unit']==target],key=lambda r:r['exposure']);cc=sorted([r for r in records if r['day']==cd and r['unit']==peers[0]],key=lambda r:r['exposure'])
     ycal=np.array([r['reference_co'] for r in cc]);cfeatures=np.array([r['features'] for r in cc]);calctx=context(cfeatures,peer_c);calres=np.abs(np.median(peer_c,axis=1)-ycal)
     calpoints=fuse(np.zeros(100),peer_c);q={m:(old[0]['q'] if m=='target_transfer' else None if m=='target_peer_huber' else quantile(np.abs(calpoints[m]-ycal))) for m in POINTS}
     packet={'target_prediction':np.array([v['prediction'] for v in old]),'peer_predictions':peer_a,'target_features':np.array([r['features'] for r in aa]),'peer_confidence':np.column_stack([asd[u] for u in peers]) if kind=='RF' else None,'target_scores':{s:np.array([v['scores'][s] for v in old]) for s in ['environment','prior_residual','feature_distance']+(['confidence'] if kind=='RF' else [])}}
     scores=compute_scores(packet,calctx,calres);points=fuse(packet['target_prediction'],peer_a)
     meta={'fold':fold,'day':ad,'type':family,'unit':target,'model':kind,'peer_units':peers};ids=[v['exposure_id'] for v in old]
     cell={'metadata':meta,'exposure_ids':ids,'measurement_ids':[v['id'] for v in old],'observables':list_packet(packet),'outcomes':{'reference_co':[v['reference_co'] for v in old]},'predictions':{k:v.tolist() for k,v in points.items()},'q':q,'scores':{k:v.tolist() for k,v in scores.items()},'peer_mad_alert_threshold':alert_quantile(np.median(np.abs(peer_c-np.median(peer_c,axis=1)[:,None]),axis=1),.95)}
     cells.append(cell);calarchive.append({'metadata':meta,'calibration_day':cd,'calibration_peer_ids':[[f'D{cd:02d}_E{j:03d}_R{u:02d}' for u in peers] for j in range(1,101)],'peer_predictions':peer_c.tolist(),'context':calctx.tolist(),'reference_co':ycal.tolist(),'median_abs_residual':calres.tolist(),'q':q})
     assignments.append({'metadata':meta,'fit_ids':[i for u in peers for i in fitids[u]],'calibration_peer_ids':[f'D{cd:02d}_E{j:03d}_R{u:02d}' for j in range(1,101) for u in peers],'assessment_ids':[v['id'] for v in old]})
    print('reconstructed',fold,family,kind,flush=True)
 save('individual_calibration_predictions.json.gz',individual);save('calibration_packets.json.gz',calarchive);save('authentic_packets_predictions.json.gz',cells);save('assignments.json.gz',assignments)
 save('reconstruction.json',{'existing_individual_model_fits':fitcount,'global_model_fits':0,'largest_archived_peer_prediction_difference':largest,'assessment_own_and_peer_predictions':'MATCH_1E-12','reserved_fields_accessed':False})
 return cells,calarchive

def evaluate(cells,modes=('whole_chamber','family'),tag='authentic',fixed=None,unit_results=True):
 groups=collections.defaultdict(list)
 for c in cells:
  meta=c['metadata'];groups[(meta['model'],meta['day'])].append(c)
 selections={};groupmetrics=[];unitmetrics=[]
 for (model,day),allcells in groups.items():
  for mode in modes:
   families=['ALL'] if mode=='whole_chamber' else ['Figaro','FIS']
   for fam in families:
    block=[c for c in allcells if fam=='ALL' or c['metadata']['type']==fam];assert len(block)==(12 if mode=='whole_chamber' else 6)
    ids=block[0]['exposure_ids'];assert all(c['exposure_ids']==ids for c in block)
    for policy in block[0]['scores']:
     for rate in [.5,.75,.9,1.]:
      key=f'{model}/D{day}/{mode}/{fam}/{policy}/{rate}'
      mask=select_group(np.array([c['scores'][policy] for c in block]),ids,rate) if fixed is None else np.array([x in fixed[key] for x in ids])
      selections[key]=[ids[j] for j in np.flatnonzero(mask)]
      for point in POINTS:
       for typ in (['ALL','Figaro','FIS'] if mode=='whole_chamber' else [fam]):
        bb=[c for c in block if typ=='ALL' or c['metadata']['type']==typ];yy=np.array([c['outcomes']['reference_co'] for c in bb]);pp=np.array([c['predictions'][point] for c in bb]);qq=None if point=='target_peer_huber' else np.repeat(np.array([c['q'][point] for c in bb])[:,None],100,axis=1)
        mm=np.broadcast_to(mask,yy.shape);qflat=None if qq is None else qq.ravel();r=metrics(yy.ravel(),pp.ravel(),qflat,mm.ravel())
        groupmetrics.append({'scenario':tag,'mode':mode,'model':model,'day':day,'type':typ,'point':point,'policy':policy,'rate':rate,'selection_key':key,'unique_exposures':int(mask.sum()),'target_hypotheses':len(bb),**r})
       if unit_results:
        for c in block:
         unitmetrics.append({'scenario':tag,'mode':mode,**{k:c['metadata'][k] for k in ['model','day','type','unit']},'point':point,'policy':policy,'rate':rate,'selection_key':key,**metrics(np.array(c['outcomes']['reference_co']),np.array(c['predictions'][point]),c['q'][point],mask)})
 return selections,groupmetrics,unitmetrics

def stresses(cells,cal,base_selections):
 rf=[c for c in cells if c['metadata']['model']=='RF'];calix={(c['metadata']['day'],c['metadata']['unit']):c for c in cal if c['metadata']['model']=='RF'}
 stressed=[];allmetrics=[];allselections={};diagnostics=[]
 for name,gain,offset,local in [('offset_plus2',1.,2.,False),('offset_minus2',1.,-2.,False),('gain_0.8',.8,0.,False),('gain_1.2',1.2,0.,False),('gain1.2_offset2',1.2,2.,False),('one_peer_plus5',1.,0.,True)]:
  out=[]
  for c in rf:
   meta=c['metadata'];packet=array_packet(c['observables']);origpeer=packet['peer_predictions'].copy();origp=packet['target_prediction'].copy()
   if local:packet['peer_predictions'][:,0]+=5.
   else:
    packet['target_prediction']=gain*origp+offset;packet['peer_predictions']=gain*origpeer+offset
    packet['peer_confidence']*=abs(gain);packet['target_scores']['confidence']*=abs(gain)
   calcell=calix[(meta['day'],meta['unit'])];score=compute_scores(packet,np.array(calcell['context']),np.array(calcell['median_abs_residual']));point=fuse(packet['target_prediction'],packet['peer_predictions'])
   obj={**c,'observables':list_packet(packet),'scores':{k:v.tolist() for k,v in score.items()},'predictions':{k:v.tolist() for k,v in point.items()},'synthetic_metadata':{'scenario':name,'gain':gain,'offset_ppm':offset,'localized_peer_only':local,'not_physical_failure':True}}
   out.append(obj)
   if not local:
    for m in POINTS:assert np.allclose(point[m],gain*np.array(c['predictions'][m])+offset,atol=1e-10,rtol=1e-10)
    assert np.allclose(score['disagreement'],abs(gain)*np.array(c['scores']['disagreement']),atol=1e-10,rtol=1e-10)
    assert np.allclose(score['peer_mad'],abs(gain)*np.array(c['scores']['peer_mad']),atol=1e-10,rtol=1e-10)
  ss,gm,_=evaluate(out,modes=('whole_chamber',),tag=name,unit_results=False)
  _,fixedgm,_=evaluate(out,modes=('whole_chamber',),tag=name+'_baseline_masks',fixed=base_selections,unit_results=False)
  allmetrics.extend(gm+fixedgm);allselections[name]=ss;stressed.extend(out)
  for day in [6,8,10]:
   bc=[c for c in rf if c['metadata']['day']==day];sc=[c for c in out if c['metadata']['day']==day]
   alert=lambda cc:np.any(np.array([np.array(c['scores']['peer_mad'])>c['peer_mad_alert_threshold'] for c in cc]),axis=0)
   ba=alert(bc);sa=alert(sc)
   for policy in bc[0]['scores']:
    key=f'RF/D{day}/whole_chamber/ALL/{policy}/0.75';oldset=set(base_selections[key]);newset=set(ss[key])
    diagnostics.append({'scenario':name,'day':day,'policy':policy,'accepted_set_changed_exposures':len(oldset^newset),'baseline_peer_mad_chamber_alerts':int(ba.sum()),'stress_peer_mad_chamber_alerts':int(sa.sum()),'new_peer_mad_chamber_alerts':int((sa&~ba).sum()),'cleared_peer_mad_chamber_alerts':int((ba&~sa).sum()),'all_exposures':100,'synthetic_not_physical':True})
  print('stress completed',name,flush=True)
 save('synthetic_packets_predictions.json.gz',stressed);save('synthetic_group_metrics.json.gz',allmetrics);save('synthetic_selections.json.gz',allselections);save('synthetic_diagnostics.json',diagnostics)

def main():
 start=time.monotonic();sha=hashlib.sha256((P/'FROZEN_PROTOCOL.v1.0.md').read_bytes()).hexdigest();assert sha==(P/'PROTOCOL_SHA256.txt').read_text().split()[0]
 cells,cal=build();selections,group,unit=evaluate(cells);save('authentic_selections.json.gz',selections);save('authentic_group_metrics.json.gz',group);save('authentic_unit_metrics.json.gz',unit)
 stresses(cells,cal,selections)
 import sklearn
 save('execution.json',{'protocol_sha256':sha,'python':sys.version,'numpy':np.__version__,'sklearn':sklearn.__version__,'runtime_seconds':time.monotonic()-start,'authenticated_cell_packets':len(cells),'point_prediction_values':len(cells)*100*len(POINTS),'unique_assessment_chamber_exposures':300,'assessment_sessions':3,'physical_development_units':12,'shared_apparatus':1,'model_fits':108,'global_model_fits':0,'reserved_outcomes_accessed':False})
 print('finished',flush=True)
if __name__=='__main__':main()
