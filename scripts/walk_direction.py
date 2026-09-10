"""Which end was each line family walked from? Not a mirror, so the crossings can tell."""
import sys, os, glob
sys.path.insert(0, os.path.dirname(__file__))
import segy, numpy as np
from scipy.signal import hilbert
ROOT=r'D:/code_ws/reference/parsans/report/raw/GPR Raw data_Kuppam'; DX=2.49
def load(blk,ln):
    g=sorted(glob.glob(os.path.join(ROOT,blk,'**','*new%03d_*_HF.sgy'%ln),recursive=True)); return segy.read(g[0])['data']
def prep(d,dt=0.0610352):
    e=np.abs(hilbert(d,axis=1)); w=int(3.0/dt); k=np.ones(w)/w
    sm=np.apply_along_axis(lambda r:np.convolve(r,k,'same'),1,e); a=e/(sm+1e-12)
    return a[:,int(1.0/dt):int(12.0/dt)]
CFG={'A Block':(range(1,13),range(13,25),550),'B Block':(range(1,14),range(14,34),None),'C Block':(range(1,18),range(18,33),None)}
for blk,(F1,F2,_) in CFG.items():
    E1={n:prep(load(blk,n)) for n in F1}; E2={n:prep(load(blk,n)) for n in F2}
    F1=list(F1); F2=list(F2)
    L1=(len(F2)-1)*50.0; L2=(len(F1)-1)*50.0   # span each family covers on the other
    res={}
    for f1_from_first in (True,False):
        for f2_from_first in (True,False):
            rs=[]
            for p in F1:
                for q in F2:
                    d1=(q-F2[0])*50.0 if f1_from_first else L1-(q-F2[0])*50.0
                    d2=(p-F1[0])*50.0 if f2_from_first else L2-(p-F1[0])*50.0
                    i=int(round(d1/DX)); j=int(round(d2/DX))
                    A=E1[p]; B=E2[q]
                    if not (0<=i<len(A) and 0<=j<len(B)): continue
                    best=-9
                    for s in range(-4,5):   # +/- 10 cm slop for odometer
                        jj=j+s
                        if 0<=jj<len(B) and A[i].std()>1e-9 and B[jj].std()>1e-9:
                            best=max(best,float(np.corrcoef(A[i],B[jj])[0,1]))
                    rs.append(best)
            rs=np.array(rs); res[(f1_from_first,f2_from_first)]=(np.median(rs),(rs<0.3).mean(),len(rs))
    print('\n%s   family1 = lines %d-%d, family2 = lines %d-%d'%(blk,F1[0],F1[-1],F2[0],F2[-1]))
    print('  %-34s %-34s %8s %8s'%('family1 walked from','family2 walked from','median r','no-match'))
    for (a,b),(m,nm,n) in sorted(res.items(),key=lambda kv:-kv[1][0]):
        print('  %-34s %-34s %8.3f %7.0f%%'%('line %d end'%(F2[0] if a else F2[-1]),'line %d end'%(F1[0] if b else F1[-1]),m,100*nm))
    top=sorted(res.values(),key=lambda v:-v[0])
    print('  margin between best and second: %.3f'%(top[0][0]-top[1][0]))
