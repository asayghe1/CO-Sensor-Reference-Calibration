from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'co_submission_finish_v1/src'
s=(R/'co_revision_execution_v2/work/src/development_replay.py').read_text()
s=s.replace('from reference_budget_study_v1.replay import ReferenceProvider','from reference_budget_study_v1.replay import ReferenceProvider, scheduled_indices\nfrom reference_budget_study_v1.methods import historical_risk\nfrom reference_budget_study_v1.data import validate_observables\nimport json,hashlib,os')
s=s.replace('def finite_replay(obs,cal,reference_values,budget,mask=None,trace=None,native=False):','def run_session(obs,cal,reference_values,budget,policy,seed,log_path):')
s=s.replace(" m=obs['consensus'];cm=cal['consensus'];n,k=m.shape", " validate_observables(obs)\n native=policy=='rlsvar';trace=None;mask=None\n if policy not in ('none','periodic','random','confidence','envelope','rlsvar'):raise ValueError('policy')\n if policy=='none' and budget!=0:raise ValueError('none budget')\n m=obs['consensus'];cm=cal['consensus'];n,k=m.shape")
s=s.replace(" if (n,k)!=(100,12) or (not native and (mask is None or np.asarray(mask).shape!=(n,) or np.sum(mask)!=budget)):raise ValueError('development replay support/mask')", " if (n,k)!=(100,12) or budget not in (0,5,10,20):raise ValueError('fixed C5 support/budget')\n schedule=scheduled_indices(policy,n,budget,seed)\n policy_history=(historical_risk(cal,BASE) if policy=='envelope' else cal['confidence']).tolist()\n # Exclusive creation prevents silently replacing a frozen run.\n log_file=open(log_path,'x')")
s=s.replace("  else:q=bool(mask[i])", """  else:
   risk=1e12 if bad.any() else float(np.max((hi-lo)/2/cal['q']))
   score=risk if policy=='envelope' else float(obs['confidence'][i])
   remaining=budget-len(provider.access_log);horizon=n-i
   threshold=float(np.quantile(policy_history,1-remaining/horizon,method='higher'))
   forced=remaining>0 and remaining==horizon
   q=bool(remaining>0 and (forced or (i in schedule if policy in ('periodic','random') else score>threshold)))
   policy_history.append(score)
   scores.append({'index':i,'score':score,'threshold':threshold,'remaining_before':remaining,'forced':forced})""")
s=s.replace("  if q:\n   y=provider.purchase(i);changes={}","""  snapshot={'event':log,'predictions':{e:np.asarray(pred[e][-1]).tolist() for e in pred},'error_lower':lo.tolist(),'error_upper':hi.tolist(),'contradiction':bad.tolist(),'query':q}
  frozen_bytes=json.dumps(snapshot,sort_keys=True,allow_nan=False).encode()
  log['snapshot_sha256']=hashlib.sha256(frozen_bytes).hexdigest()
  log_file.write(frozen_bytes.decode()+'\\n');log_file.flush();os.fsync(log_file.fileno())
  if q:
   y=provider.purchase(i);changes={}""")
s=s.replace(" if len(provider.access_log)!=budget:raise ValueError('exact quota')", " log_file.close()\n if len(provider.access_log)!=budget:raise ValueError('exact quota')")
(O/'c5_replay.py').write_text(s)
