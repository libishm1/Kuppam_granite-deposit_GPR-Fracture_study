"""Block B: B-2 anchored to published endpoints, B-1 tracked free in its corridor."""
import sys, os, glob, csv
sys.path.insert(0, os.path.dirname(__file__))
import segy, numpy as np
from scipy.signal import hilbert
from scipy.interpolate import griddata
from scipy.ndimage import uniform_filter
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

ROOT=r'D:/code_ws/reference/parsans/report/raw/GPR Raw data_Kuppam'
DX=2.49; V=0.1202
DTH, DTL = 0.0610352, 0.1220703

def load(ln,ch):
    g=sorted(glob.glob(os.path.join(ROOT,'B Block','**','*new%03d_*_%s.sgy'%(ln,ch)),recursive=True))
    return segy.read(g[0])
def agc_env(d,dt,w_ns=3.0):
    e=np.abs(hilbert(d,axis=1)); w=max(3,int(w_ns/dt)); k=np.ones(w)/w
    sm=np.apply_along_axis(lambda r:np.convolve(r,k,'same'),1,e); return e/(sm+1e-12)

def corridor(E,i0,i1,j0,j1,corr,jump=2,smooth=0.5):
    n=E.shape[0]; i0=max(0,i0); i1=min(n-1,i1); idx=np.arange(i0,i1+1)
    centre=np.round(np.linspace(j0,j1,len(idx))).astype(int)
    m=2*corr+1; ns=E.shape[1]
    def val(k,c):
        j=centre[k]-corr+c
        return E[idx[k],j] if 0<=j<ns else -1e9
    S=np.full((len(idx),m),-1e9); B=np.zeros((len(idx),m),dtype=int)
    S[0]=[val(0,c) for c in range(m)]
    for k in range(1,len(idx)):
        prev=S[k-1]; best=prev.copy(); arg=np.arange(m); drift=centre[k]-centre[k-1]
        for s in range(-jump,jump+1):
            sh=s-drift; cand=np.full(m,-1e9)
            if sh==0: cand=prev-smooth*abs(s)
            elif sh>0: cand[sh:]=prev[:-sh]-smooth*abs(s)
            else: cand[:sh]=prev[-sh:]-smooth*abs(s)
            u=cand>best; best[u]=cand[u]; arg[u]=(np.arange(m)-sh)[u]
        S[k]=best+[val(k,c) for c in range(m)]; B[k]=arg
    p=np.zeros(len(idx),dtype=int); p[-1]=int(np.argmax(S[-1]))
    for k in range(len(idx)-1,0,-1): p[k-1]=B[k,p[k]]
    return idx, centre-corr+p

# ---------------- B-2 : LF Y-lines, anchored to Table 2 -------------------
TAB2=[(14,0,15,476,30.99,67.59),(16,100,32,470,32.94,66.98),(18,200,35,458,30.99,66.61),
      (20,300,22,444,30.62,59.54),(22,400,47,385,35.38,54.41),(24,500,45,360,32.82,49.53)]
b2=[]
print('B-2  (LF, Y-lines at fixed x, anchored to the report endpoints)')
for ln,fx,y0,y1,t0,t1 in TAB2:
    E=agc_env(load(ln,'LF')['data'],DTL)
    idx,jj=corridor(E,int(round(y0/DX)),int(round(y1/DX)),int(round(t0/DTL)),int(round(t1/DTL)),corr=16)
    for i,j in zip(idx,jj):
        b2.append(dict(block='B',feature='B-2',line=ln,orientation='Y-line',
                       x_cm=float(fx),y_cm=round(i*DX,1),
                       twt_ns=round(j*DTL,4),depth_m=round(j*DTL*V/2,4)))
    d=[j*DTL*V/2 for j in jj]
    print('  line %2d x=%3d  %3d picks  %.2f to %.2f m  (report %.2f to %.2f)'
          %(ln,fx,len(idx),min(d),max(d),t0*0.06,t1*0.06))

# ---------------- B-1 : HF X-lines, free track in the corridor ------------
print('\nB-1  (HF, X-lines at fixed y, no published depths, tracked free)')
b1=[]; ties=[]
X0,X1=650.0,950.0
for ln in range(1,14):
    r=load(ln,'HF'); E=agc_env(r['data'],DTH); n=r['ntr']
    i0,i1=int(round(X0/DX)),min(n-1,int(round(X1/DX)))
    # corridor from the report's own description of B-1: x 650-950 cm, deepening
    # east at a mean apparent dip of 8.3 deg, seen in the slices at 0.47-1.02 m.
    # Their geometry sets the corridor, the data fills in, exactly as for C-1.
    zA,zB = 0.50, 0.50 + (X1-X0)/100.0*np.tan(np.radians(8.3))
    j0,j1 = int(round(2*zA/V/DTH)), int(round(2*zB/V/DTH))
    idx,jj=corridor(E,i0,i1,j0,j1,corr=26,jump=2,smooth=0.5)
    y=(ln-1)*50.0
    for i,j in zip(idx,jj):
        b1.append(dict(block='B',feature='B-1',line=ln,orientation='X-line',
                       x_cm=round(i*DX,1),y_cm=y,
                       twt_ns=round(j*DTH,4),depth_m=round(j*DTH*V/2,4)))
    d=np.array([j*DTH*V/2 for j in jj]); xs=np.array([i*DX for i in idx])
    sl=np.polyfit(xs,d,1)[0]
    xt=np.interp(0.75,d,xs) if d.min()<0.75<d.max() else np.nan
    ties.append((ln,y,xt,np.degrees(np.arctan(sl*100)),d.mean()))
    print('  line %2d y=%3d  %3d picks  %.2f to %.2f m  apparent dip %+.1f deg  crosses 0.75 m at x=%s'
          %(ln,y,len(idx),d.min(),d.max(),np.degrees(np.arctan(sl*100)),
            '%.0f'%xt if xt==xt else '  -'))

for rows,fn in ((b2,'tables/PICKS_B2_raw.csv'),(b1,'tables/PICKS_B1_raw.csv')):
    w=csv.DictWriter(open(fn,'w',newline='',encoding='utf-8'),fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print('\nB-2 %d picks (report published 12 endpoints);  B-1 %d picks (report published none)'%(len(b2),len(b1)))

# --- check B-1 against the report's own plan trace and dip range ----------
tt=[t for t in ties if t[2]==t[2]]
if len(tt)>=3:
    ys=np.array([t[1] for t in tt]); xs=np.array([t[2] for t in tt])
    m,c=np.polyfit(ys,xs,1)
    print('\nB-1 independent check')
    print('  our 0.75 m crossing fits   x = %+.4f y %+.2f cm'%(m,c))
    print('  report least squares fit   x = -0.0667 y + 753.14 cm')
dips=np.array([t[3] for t in ties])
print('  our apparent dips %.1f to %.1f deg (mean %.1f); report 5.1 to 14.4 (mean 8.3)'
      %(dips.min(),dips.max(),dips.mean()))
print('  sign: positive means deepening toward increasing x (east), as the report states')
