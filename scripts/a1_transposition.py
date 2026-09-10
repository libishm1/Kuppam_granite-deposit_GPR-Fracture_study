"""Corridor-track Line 10 LF under both endpoint orderings; the real event has more energy along its path."""
import sys, os, glob
sys.path.insert(0, os.path.dirname(__file__))
import segy, numpy as np
from scipy.signal import hilbert
exec(open(os.path.join(os.path.dirname(__file__),'build_b.py')).read().split('# ---------------- B-2')[0].replace("'B Block'","'A Block'"))
E=agc_env(load(10,'LF')['data'],DTL)
i0,i1=int(round(422/DX)),int(round(542/DX))
res={}
for name,(t0,t1) in (('as printed  422->1.30, 542->1.60',(21.72,26.60)),('reversed    422->1.60, 542->1.30',(26.60,21.72))):
    idx,jj=corridor(E,i0,i1,int(round(t0/DTL)),int(round(t1/DTL)),corr=6,jump=1,smooth=0.8)
    en=E[idx,jj]; z=jj*DTL*V/2
    res[name]=(en.mean(),en.min(),z[0],z[-1])
    print('%s : mean envelope along path %.3f, min %.3f, tracked %.2f -> %.2f m'%(name,en.mean(),en.min(),z[0],z[-1]))
a,b=list(res.values())
print('\nenergy ratio reversed/printed = %.2f'%(b[0]/a[0]))
# also: free track in a broad window at x 380-560, 1.1-1.8 m, no ordering imposed; see which way it goes
j0,j1=int(round(2*1.1/V/DTL)),int(round(2*1.8/V/DTL))
idx,jj=corridor(E,int(round(380/DX)),int(round(560/DX)),(j0+j1)//2,(j0+j1)//2,corr=(j1-j0)//2,jump=1,smooth=0.4)
z=jj*DTL*V/2; x=idx*DX
sl=np.polyfit(x/100,z,1)[0]
print('free track x 380-560, 1.1-1.8 m: depth %.2f at x=%.0f -> %.2f at x=%.0f, slope %+.3f m/m (%s)'
      %(z[0],x[0],z[-1],x[-1],sl,'deepens with x = as printed' if sl>0 else 'SHALLOWS with x = reversed'))
