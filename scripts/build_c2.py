"""Validate the C-2 pick at every X/Y crossing, then grid and export."""
import csv, numpy as np, os
from scipy.interpolate import griddata
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

R = list(csv.DictReader(open('tables/PICKS_C2_raw.csv', encoding='utf-8')))
for r in R:
    r['line']=int(r['line']); r['x']=float(r['x_cm']); r['y']=float(r['y_cm'])
    r['z']=float(r['depth_m']); r['t']=float(r['twt_ns'])
X = [r for r in R if r['orientation']=='X-line']   # fixed y, runs along x
Y = [r for r in R if r['orientation']=='Y-line']   # fixed x, runs along y

# --- crossing misfit -------------------------------------------------------
def at(pts, key, val, tol=1.5):
    c=[p for p in pts if abs(p[key]-val)<=tol]
    return np.median([p['z'] for p in c]) if c else None
mis=[]
for lx in range(1,18):
    ys=(lx-1)*50.0
    px=[p for p in X if p['line']==lx]
    for ly in range(18,33):
        xs=(ly-18)*50.0
        py=[p for p in Y if p['line']==ly]
        a=at(px,'x',xs); b=at(py,'y',ys)
        if a is None or b is None: continue
        mis.append(dict(lx=lx,ly=ly,x=xs,y=ys,zX=a,zY=b,d=a-b))
d=np.array([m['d'] for m in mis])
print('C-2 crossing check: %d of 255 crossings resolved'%len(mis))
print('  X-line minus Y-line depth:  median %+.3f m   mean %+.3f   sd %.3f'%(np.median(d),d.mean(),d.std()))
print('  |misfit|: median %.3f m, 90th pct %.3f, max %.3f'%(np.median(abs(d)),np.percentile(abs(d),90),abs(d).max()))
print('  within 0.10 m: %.0f%%   within 0.20 m: %.0f%%'%(100*(abs(d)<0.10).mean(),100*(abs(d)<0.20).mean()))
w=csv.DictWriter(open('tables/C2_crossing_misfit.csv','w',newline='',encoding='utf-8'),
                 fieldnames=list(mis[0].keys())); w.writeheader(); w.writerows(mis)

# --- grid ------------------------------------------------------------------
P=np.array([[r['x'],r['y'],r['z']] for r in R])
gx=np.arange(0,700.1,10.0); gy=np.arange(0,800.1,10.0)
GX,GY=np.meshgrid(gx,gy)
Z=griddata(P[:,:2],P[:,2],(GX,GY),method='linear')
Zn=griddata(P[:,:2],P[:,2],(GX,GY),method='nearest')
Z=np.where(np.isnan(Z),Zn,Z)
from scipy.ndimage import uniform_filter
Z=uniform_filter(Z,size=5,mode='nearest')
print('\nGridded surface %dx%d at 10 cm, depth %.3f to %.3f m, mean %.3f'%(Z.shape[1],Z.shape[0],Z.min(),Z.max(),Z.mean()))

# plane fit for reference
A=np.c_[P[:,0],P[:,1],np.ones(len(P))]
coef,*_=np.linalg.lstsq(A,P[:,2],rcond=None)
res=P[:,2]-A@coef
print('best-fit plane  z = %+.6f x %+.6f y %+.4f  (cm, m)'%tuple(coef))
print('  dip %.2f deg toward azimuth %.0f deg from +y'%(
    np.degrees(np.arctan(np.hypot(coef[0],coef[1])*100)),
    (np.degrees(np.arctan2(coef[0],coef[1])))%360))
print('  residual RMS %.3f m, max |res| %.3f m  -> C-2 is NOT a plane at tolerance'%(res.std(),abs(res).max()))

# --- exports ---------------------------------------------------------------
os.makedirs('model',exist_ok=True)
np.savetxt('model/C2_grid_10cm.xyz',np.c_[GX.ravel(),GY.ravel(),Z.ravel()],fmt='%.2f %.2f %.4f')

def dxf_mesh(path,GX,GY,Z,layer='C2'):
    L=['0','SECTION','2','ENTITIES']
    ny,nx=Z.shape
    for j in range(ny-1):
        for i in range(nx-1):
            q=[(GX[j,i],GY[j,i],-Z[j,i]),(GX[j,i+1],GY[j,i+1],-Z[j,i+1]),
               (GX[j+1,i+1],GY[j+1,i+1],-Z[j+1,i+1]),(GX[j+1,i],GY[j+1,i],-Z[j+1,i])]
            if any(np.isnan(p[2]) for p in q): continue
            L+= ['0','3DFACE','8',layer]
            for k,(x,y,z) in enumerate(q):
                L+= [str(10+k),'%.3f'%x, str(20+k),'%.3f'%y, str(30+k),'%.4f'%z]
    L+=['0','ENDSEC','0','EOF']
    open(path,'w').write('\n'.join(L)+'\n')
dxf_mesh('model/C2_surface.dxf',GX,GY,Z)
print('\nwrote model/C2_grid_10cm.xyz  and  model/C2_surface.dxf  (%.1f MB)'
      %(os.path.getsize('model/C2_surface.dxf')/1e6))
print('  DXF is in cm, z NEGATIVE downward, so it drops into Rhino at survey scale.')

# --- figure ----------------------------------------------------------------
fig,ax=plt.subplots(1,2,figsize=(13,5.4),constrained_layout=True)
im=ax[0].pcolormesh(GX,GY,Z,shading='auto',cmap='viridis_r')
ax[0].set_title('C-2 depth surface from 9,481 raw picks (m below surface)',fontsize=10)
plt.colorbar(im,ax=ax[0],label='depth (m)')
for l in range(1,18): ax[0].axhline((l-1)*50,color='w',lw=.3,alpha=.35)
for l in range(18,33): ax[0].axvline((l-18)*50,color='w',lw=.3,alpha=.35)
ax[0].set_xlabel('x (cm)'); ax[0].set_ylabel('y (cm)'); ax[0].set_aspect('equal')
sc=ax[1].scatter([m['x'] for m in mis],[m['y'] for m in mis],c=[m['d'] for m in mis],
                 cmap='coolwarm',vmin=-.4,vmax=.4,s=46,edgecolor='k',linewidth=.3)
plt.colorbar(sc,ax=ax[1],label='X-line minus Y-line (m)')
ax[1].set_title('crossing misfit, median |%.0f| cm'%(100*np.median(abs(d))),fontsize=10)
ax[1].set_xlabel('x (cm)'); ax[1].set_ylabel('y (cm)'); ax[1].set_aspect('equal')
fig.savefig('figs/C2_surface.png',dpi=135)
print('wrote figs/C2_surface.png')
