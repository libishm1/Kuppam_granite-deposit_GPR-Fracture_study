"""Grid B-1 and B-2, and cross-check B-1 against the LF Y-lines it also appears on."""
import sys, os, glob, csv
sys.path.insert(0, os.path.dirname(__file__))
import segy, numpy as np
from scipy.signal import hilbert
from scipy.interpolate import griddata
from scipy.ndimage import uniform_filter
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
exec(open(os.path.join(os.path.dirname(__file__),'build_b.py')).read().split('# ---------------- B-2')[0])

b1=[dict(line=int(r['line']),x=float(r['x_cm']),y=float(r['y_cm']),z=float(r['depth_m']))
    for r in csv.DictReader(open('tables/PICKS_B1_raw.csv',encoding='utf-8'))]
b2=[dict(line=int(r['line']),x=float(r['x_cm']),y=float(r['y_cm']),z=float(r['depth_m']))
    for r in csv.DictReader(open('tables/PICKS_B2_raw.csv',encoding='utf-8'))]

# ---- independent check: track B-1 on the LF Y-lines that cross the corridor ----
print('B-1 cross-check on the LF Y-lines (report: "also visible at shallower depth on multiple Y-lines in the LF channel")')
P1=np.array([[d['x'],d['y'],d['z']] for d in b1])
mis=[]
for ln in range(27,34):                       # x = 650 .. 950 cm
    x=(ln-14)*50.0
    if not (650<=x<=950): continue
    E=agc_env(load(ln,'LF')['data'],DTL); n=E.shape[0]
    i0,i1=0,min(n-1,int(round(600/DX)))
    zc=np.interp(x,[650,950],[0.50,0.94])
    j=int(round(2*zc/V/DTL))
    idx,jj=corridor(E,i0,i1,j,j,corr=20,jump=1,smooth=0.6)
    for i,k in zip(idx,jj):
        y=i*DX; z=k*DTL*V/2
        sel=[d for d in b1 if abs(d['x']-x)<=3 and abs(d['y']-y)<=25]
        if sel: mis.append(z-float(np.median([s['z'] for s in sel])))
mis=np.array(mis)
if len(mis):
    print('  %d comparisons.  LF minus HF depth: median %+.3f m, |misfit| median %.3f, 90th %.3f'
          %(len(mis),np.median(mis),np.median(abs(mis)),np.percentile(abs(mis),90)))
    print('  within 20 cm: %.0f%%'%(100*(abs(mis)<0.20).mean()))

# ---- grids and exports ----
def dxf(path,GX,GY,Z,layer):
    L=['0','SECTION','2','ENTITIES']; ny,nx=Z.shape
    for j in range(ny-1):
        for i in range(nx-1):
            q=[(GX[j,i],GY[j,i],-Z[j,i]*100),(GX[j,i+1],GY[j,i+1],-Z[j,i+1]*100),
               (GX[j+1,i+1],GY[j+1,i+1],-Z[j+1,i+1]*100),(GX[j+1,i],GY[j+1,i],-Z[j+1,i]*100)]
            if any(np.isnan(p[2]) for p in q): continue
            L+=['0','3DFACE','8',layer]
            for k,(x,y,z) in enumerate(q): L+=[str(10+k),'%.3f'%x,str(20+k),'%.3f'%y,str(30+k),'%.4f'%z]
    L+=['0','ENDSEC','0','EOF']; open(path,'w').write('\n'.join(L)+'\n')

os.makedirs('model',exist_ok=True)
out={}
for nm,pts,xr,yr in (('B1',b1,(650,950),(0,600)),('B2',b2,(0,500),(0,480))):
    P=np.array([[d['x'],d['y'],d['z']] for d in pts])
    gx=np.arange(xr[0],xr[1]+.1,10.); gy=np.arange(yr[0],yr[1]+.1,10.)
    GX,GY=np.meshgrid(gx,gy)
    Z=griddata(P[:,:2],P[:,2],(GX,GY),'linear')
    A=np.c_[P[:,0],P[:,1],np.ones(len(P))]; co,*_=np.linalg.lstsq(A,P[:,2],rcond=None)
    Gp=np.c_[GX.ravel(),GY.ravel(),np.ones(GX.size)]@co
    Z=np.where(np.isnan(Z.ravel()),Gp,Z.ravel()).reshape(GX.shape)
    Z=uniform_filter(Z,size=5,mode='nearest')
    res=P[:,2]-A@co
    dip=np.degrees(np.arctan(np.hypot(co[0],co[1])*100)); az=np.degrees(np.arctan2(co[0],co[1]))%360
    print('\n%s  %d picks, %.2f to %.2f m'%(nm,len(P),Z.min(),Z.max()))
    print('  best-fit plane dip %.2f deg, down-dip azimuth %.0f deg from +y toward +x'%(dip,az))
    print('  residual RMS %.3f m, max %.3f m'%(res.std(),abs(res).max()))
    np.savetxt('model/%s_grid_10cm.xyz'%nm,np.c_[GX.ravel(),GY.ravel(),Z.ravel()],fmt='%.2f %.2f %.4f')
    dxf('model/%s_surface.dxf'%nm,GX,GY,Z,nm)
    out[nm]=(GX,GY,Z)
print('\nwrote model/B1_surface.dxf, model/B2_surface.dxf and both .xyz grids')

fig=plt.figure(figsize=(12.6,5.6))
ax=fig.add_subplot(121,projection='3d')
for nm,c in (('B1','orangered'),('B2','steelblue')):
    GX,GY,Z=out[nm]; s=3
    ax.plot_surface(GX[::s,::s],GY[::s,::s],-Z[::s,::s],color=c,alpha=.85,linewidth=0)
ax.set_xlim(0,950); ax.set_ylim(0,600); ax.set_xlabel('x (cm)'); ax.set_ylabel('y (cm)')
ax.set_zlabel('depth (m)'); ax.set_title('Block B: B-1 (red, east) and B-2 (blue, west)',fontsize=10)
ax.view_init(elev=22,azim=-62); ax.set_box_aspect((9.5,6,4))
ax2=fig.add_subplot(122)
for nm,cm_ in (('B2','Blues'),('B1','Oranges')):
    GX,GY,Z=out[nm]; ax2.pcolormesh(GX,GY,Z,shading='auto',cmap=cm_)
    cs=ax2.contour(GX,GY,Z,levels=8,colors='k',linewidths=.4); ax2.clabel(cs,fmt='%.1f',fontsize=6)
yy=np.linspace(0,600,20)
ax2.plot(-0.0667*yy+753.14,yy,'g--',lw=2,label='report B-1 plan trace')
ax2.plot(-0.1717*yy+883.22,yy,'r-',lw=2,label='our 0.75 m crossing')
ax2.legend(fontsize=7); ax2.set_aspect('equal'); ax2.set_xlim(0,950); ax2.set_ylim(0,600)
ax2.set_xlabel('x (cm)'); ax2.set_ylabel('y (cm)'); ax2.set_title('Block B plan, depths in m',fontsize=10)
fig.tight_layout(); fig.savefig('figs/BlockB_model.png',dpi=135); print('wrote figs/BlockB_model.png')
