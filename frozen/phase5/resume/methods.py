"""UCI487 development guards. No reserved-field numeric conversion."""
import numpy as np
ALLOWED_UNITS=(1,2,3,4,5,6,8,9,10,11,12,13)
COLS=tuple(range(6))+tuple(u+5 for u in ALLOWED_UNITS)
def permitted(day,unit):
 if not isinstance(day,int) or day<1 or day>10 or unit not in ALLOWED_UNITS:raise ValueError('reserved or invalid role')
def selected_row(line):
 fields=line.strip().split(',')
 if len(fields)!=20:raise ValueError('invalid schema')
 return np.array([float(fields[c]) for c in COLS])
def scheduled_core(t,exposure):
 if not 1<=exposure<=100:raise ValueError('purge/invalid exposure')
 return (t>=900*exposure+600)&(t<900*(exposure+1)-60)
def score_schema(record):
 if set(record)-{'features','temperature','humidity','predictions'}:raise ValueError('nonobservable score field')
