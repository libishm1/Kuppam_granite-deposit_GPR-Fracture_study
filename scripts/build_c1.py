"""C-1: track between PARSAN's own published endpoints on each of the 9 HF Y-lines."""
import sys, os, glob, csv
sys.path.insert(0, os.path.dirname(__file__))
import segy, numpy as np
from scipy.signal import hilbert
from scipy.interpolate import griddata
from scipy.ndimage import uniform_filter
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

ROOT=r'D:/code_ws/reference/parsans/report/raw/GPR Raw data_Kuppam'
DT=0.0610352; DX=2.49; V=0.1202
# report Table, Fracture C-1: line, fixed x, y0, y1, twt0, twt1
TAB=[(20,100,76,237,7.81,11.65),(21,150,49,294,2.68,11.83),(22,200,51,296,2.75,11.53),
     (23,250,77,554,2.56,13.79),(24,300,86,702,6.41,17.93),(25,350,79,480,2.75,14.88),
     (26,400,69,391,2.75,16.77),(27,450,91,462,7.99,16.71),(28,500,78,438,8.23,16.04)]

def agc_env(d,w_ns=3.0):
    e=np.abs(hilbert(d,axis=1)); w=max(3,int(w_ns/DT)); k=np.ones(w)/w
    sm=np.apply_along_axis(lambda r:np.convolve(r,k,'same'),1,e)
    return e/(sm+1e-12)

def track_corridor(E,i0,i1,j0,j1,corr=22,jump=2,smooth=0.5):
    """DP inside a corridor that ramps linearly from (i0,j0) to (i1,j1)."""
    n=E.shape[0]; i0=max(0,i0); i1=min(n-1,i1)
    idx=np.arange(i0,i1+1)
    centre=np.round(np.linspace(j0,j1,len(idx))).astype(int)
    lo=np.maximum(centre-corr,0); hi=np.minimum(centre+corr,E.shape[1]-1)
    m=2*corr+1
    S=np.full((len(idx),m),-1e9); B=np.zeros((len(idx),m),dtype=int)
    def val(k,c):
        j=centre[k]-corr+c
        return E[idx[k],j] if lo[k]<=j<=hi[k] else -1e9
    S[0]=[val(0,c) for c in range(m)]
    for k in range(1,len(idx)):
        prev=S[k-1]; best=prev.copy(); arg=np.arange(m)
        drift=centre[k]-centre[k-1]
        for s in range(-jump,jump+1):
            sh=s-drift
            cand=np.full(m,-1e9)
            if sh==0: cand=prev-smooth*abs(s)
            elif sh>0: cand[sh:]=prev[:-sh]-smooth*abs(s)
            else: cand[:sh]=prev[-sh:]-smooth*abs(s)
            u=cand>best; best[u]=cand[u]; arg[u]=(np.arange(m)-sh)[u]
        S[k]=best+[val(k,c) for c in range(m)]; B[k]=arg
    path=np.zeros(len(idx),dtype=int); path[-1]=int(np.argmax(S[-1]))
    for k in range(len(idx)-1,0,-1): path[k-1]=B[k,path[k]]
    return idx, centre-corr+path

rows=[]
for ln,fx,y0,y1,t0,t1 in TAB:
    g=sorted(glob.glob(os.path.join(ROOT,'C Block','**','*new%03d_*_HF.sgy'%ln),recursive=True))
    r=segy.read(g[0]); E=agc_env(r['data'])
    i0,i1=int(round(y0/DX)),int(round(y1/DX))
    j0,j1=int(round(t0/DT)),int(round(t1/DT))
    idx,jj=track_corridor(E,i0,i1,j0,j1,corr=22)
    for i,j in zip(idx,jj):
        rows.append(dict(block='C',feature='C-1',line=ln,orientation='Y-line',
                         x_cm=float(fx), y_cm=round(i*DX,1),
                         twt_ns=round(j*DT,4), depth_m=round(j*DT*V/2,4)))
    d=[j*DT*V/2 for j in jj]
    print('line %2d x=%3d  %3d picks  depth %.3f to %.3f m   (report %.2f to %.2f)'
          %(ln,fx,len(idx),min(d),max(d),t0*0.06,t1*0.06))
w=csv.DictWriter(open('tables/PICKS_C1_raw.csv','w',newline='',encoding='utf-8'),
                 fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print('\nC-1: %d picks on 9 lines (report published 18 endpoints)'%len(rows))

P=np.array([[r['x_cm'],r['y_cm'],r['depth_m']] for r in rows])
A=np.c_[P[:,0],P[:,1],np.ones(len(P))]; coef,*_=np.linalg.lstsq(A,P[:,2],rcond=None)
res=P[:,2]-A@coef
dip=np.degrees(np.arctan(np.hypot(coef[0],coef[1])*100))
az=(np.degrees(np.arctan2(coef[0],coef[1])))%360
print('best-fit plane  dip %.2f deg, down-dip azimuth %.0f deg from +y toward +x'%(dip,az))
print('  residual RMS %.3f m, max %.3f m'%(res.std(),abs(res).max()))
print('  report: apparent dips 6.0-14.0 deg, mean 9.6, true azimuth stated as south-east')

gx=np.arange(100,500.1,10.); gy=np.arange(0,760.1,10.); GX,GY=np.meshgrid(gx,gy)
Z=griddata(P[:,:2],P[:,2],(GX,GY),'linear')
Gp=np.c_[GX.ravel(),GY.ravel(),np.ones(GX.size)]@coef
Z=np.where(np.isnan(Z.ravel()),Gp,Z.ravel()).reshape(GX.shape)
Z=uniform_filter(Z,size=5,mode='nearest')
os.makedirs('model',exist_ok=True)
np.savetxt('model/C1_grid_10cm.xyz',np.c_[GX.ravel(),GY.ravel(),Z.ravel()],fmt='%.2f %.2f %.4f')
def dxf(path,GX,GY,Z,layer):
    L=['0','SECTION','2','ENTITIES']; ny,nx=Z.shape
    for j in range(ny-1):
        for i in range(nx-1):
            q=[(GX[j,i],GY[j,i],-Z[j,i]*100),(GX[j,i+1],GY[j,i+1],-Z[j,i+1]*100),
               (GX[j+1,i+1],GY[j+1,i+1],-Z[j+1,i+1]*100),(GX[j+1,i],GY[j+1,i],-Z[j+1,i]*100)]
            if any(np.isnan(p[2]) for p in q): continue
            L+=['0','3DFACE','8',layer]
            for k,(x,y,z) in enumerate(q):
                L+=[str(10+k),'%.3f'%x,str(20+k),'%.3f'%y,str(30+k),'%.4f'%z]
    L+=['0','ENDSEC','0','EOF']; open(path,'w').write('\n'.join(L)+'\n')
dxf('model/C1_surface.dxf',GX,GY,Z,'C1')
print('wrote model/C1_surface.dxf and model/C1_grid_10cm.xyz')

fig,ax=plt.subplots(figsize=(6.4,6.6),constrained_layout=True)
im=ax.pcolormesh(GX,GY,Z,shading='auto',cmap='magma_r'); plt.colorbar(im,ax=ax,label='depth (m)')
ax.scatter(P[:,0],P[:,1],c='c',s=.6,alpha=.5)
ax.set_title('C-1 from %d raw picks, 9 HF lines'%len(rows),fontsize=10)
ax.set_xlabel('x (cm)'); ax.set_ylabel('y (cm)'); ax.set_aspect('equal')
ax.set_xlim(0,700); ax.set_ylim(0,800)
fig.savefig('figs/C1_surface.png',dpi=135); print('wrote figs/C1_surface.png')
