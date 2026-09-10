"""Network adjustment: one depth shift per line, least squares over all crossings.
Same idea as levelling a survey net. Fixes tracker cycle skips between lines."""
import csv, numpy as np, os
from scipy.interpolate import griddata
from scipy.ndimage import uniform_filter
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

R=list(csv.DictReader(open('tables/PICKS_C2_raw.csv',encoding='utf-8')))
for r in R:
    r['line']=int(r['line']); r['x']=float(r['x_cm']); r['y']=float(r['y_cm'])
    r['z']=float(r['depth_m']); r['t']=float(r['twt_ns'])
X=[r for r in R if r['orientation']=='X-line']; Y=[r for r in R if r['orientation']=='Y-line']
LINES=sorted({r['line'] for r in R}); idx={l:i for i,l in enumerate(LINES)}

def at(pts,key,val,tol=2.5):
    c=[p['z'] for p in pts if abs(p[key]-val)<=tol]
    return float(np.median(c)) if c else None

obs=[]
for lx in range(1,18):
    px=[p for p in X if p['line']==lx]; ys=(lx-1)*50.0
    for ly in range(18,33):
        py=[p for p in Y if p['line']==ly]; xs=(ly-18)*50.0
        a=at(px,'x',xs); b=at(py,'y',ys)
        if a is not None and b is not None: obs.append((lx,ly,a,b,xs,ys))
print('crossings used: %d'%len(obs))

# robust IRLS: z_X + s_lx  =  z_Y + s_ly
n=len(LINES); A=np.zeros((len(obs)+1,n)); L=np.zeros(len(obs)+1)
for k,(lx,ly,a,b,_,_) in enumerate(obs):
    A[k,idx[lx]]=1.0; A[k,idx[ly]]=-1.0; L[k]=b-a
A[-1,:]=1.0; L[-1]=0.0                       # datum: mean shift zero
w=np.ones(len(L))
for it in range(12):
    W=np.diag(w)
    s,*_=np.linalg.lstsq(W@A,W@L,rcond=None)
    r=A@s-L
    sig=1.4826*np.median(np.abs(r[:-1]-np.median(r[:-1])))+1e-6
    w=np.minimum(1.0,(1.5*sig)/np.maximum(np.abs(r),1e-9)); w[-1]=50.0
print('per-line shift: median %+.3f m, range %+.3f to %+.3f'%(np.median(s),s.min(),s.max()))
big=[(LINES[i],s[i]) for i in np.argsort(-np.abs(s))[:6]]
print('largest: '+', '.join('L%d %+.2f m'%t for t in big))

before=np.array([b-a for _,_,a,b,_,_ in obs])
after =np.array([(b+s[idx[ly]])-(a+s[idx[lx]]) for lx,ly,a,b,_,_ in obs])
for nm,d in (('before',before),('after ',after)):
    print('  %s  median|d| %.3f m   90th %.3f   within 10 cm %.0f%%   within 20 cm %.0f%%'
          %(nm,np.median(abs(d)),np.percentile(abs(d),90),100*(abs(d)<.10).mean(),100*(abs(d)<.20).mean()))

for r in R: r['z_adj']=r['z']+s[idx[r['line']]]
# re-anchor to the report's own C-2 band so the surface stays comparable
REP=[('18',3.265),('22',3.180),('26',3.125),('30',3.045),('1',3.110),('6',3.035),('11',3.145),('17',3.130)]
mine=[np.median([r['z_adj'] for r in R if r['line']==int(l)]) for l,_ in REP]
off=np.mean([v for _,v in REP])-np.mean(mine)
for r in R: r['z_adj']=round(r['z_adj']+off,4)
print('re-anchored to the report mid-depths on its 8 published lines, offset %+.3f m'%off)

w2=csv.DictWriter(open('tables/PICKS_C2_adjusted.csv','w',newline='',encoding='utf-8'),
    fieldnames=['block','line','orientation','trace','x_cm','y_cm','twt_ns','depth_m','z_adj','envelope'])
w2.writeheader()
for r in R: w2.writerow({k:r[k] for k in w2.fieldnames})

P=np.array([[r['x'],r['y'],r['z_adj']] for r in R])
gx=np.arange(0,700.1,10.); gy=np.arange(0,800.1,10.); GX,GY=np.meshgrid(gx,gy)
Z=griddata(P[:,:2],P[:,2],(GX,GY),'linear')
Z=np.where(np.isnan(Z),griddata(P[:,:2],P[:,2],(GX,GY),'nearest'),Z)
Z=uniform_filter(Z,size=7,mode='nearest')
print('\nadjusted surface: depth %.3f to %.3f m, mean %.3f'%(Z.min(),Z.max(),Z.mean()))
print('report Table 3 band: 2.95 to 3.37 m')
print('SHALLOWEST point, the binding constraint on block height: %.3f m at x=%.0f y=%.0f'
      %(Z.min(),GX.ravel()[Z.argmin()],GY.ravel()[Z.argmin()]))

os.makedirs('model',exist_ok=True)
np.savetxt('model/C2_grid_10cm.xyz',np.c_[GX.ravel(),GY.ravel(),Z.ravel()],fmt='%.2f %.2f %.4f')
def dxf(path,GX,GY,Z,layer):
    L=['0','SECTION','2','ENTITIES']; ny,nx=Z.shape
    for j in range(ny-1):
        for i in range(nx-1):
            q=[(GX[j,i],GY[j,i],-Z[j,i]),(GX[j,i+1],GY[j,i+1],-Z[j,i+1]),
               (GX[j+1,i+1],GY[j+1,i+1],-Z[j+1,i+1]),(GX[j+1,i],GY[j+1,i],-Z[j+1,i])]
            if any(np.isnan(p[2]) for p in q): continue
            L+=['0','3DFACE','8',layer]
            for k,(x,y,z) in enumerate(q):
                L+=[str(10+k),'%.3f'%x,str(20+k),'%.3f'%y,str(30+k),'%.4f'%(z*100)]
    L+=['0','ENDSEC','0','EOF']; open(path,'w').write('\n'.join(L)+'\n')
dxf('model/C2_surface.dxf',GX,GY,Z,'C2')
print('wrote model/C2_surface.dxf (cm, z negative down) and model/C2_grid_10cm.xyz')

fig,ax=plt.subplots(1,2,figsize=(13,5.4),constrained_layout=True)
im=ax[0].pcolormesh(GX,GY,Z,shading='auto',cmap='viridis_r'); plt.colorbar(im,ax=ax[0],label='depth (m)')
ax[0].set_title('C-2 after network adjustment, %d picks'%len(R),fontsize=10)
sc=ax[1].scatter([o[4] for o in obs],[o[5] for o in obs],c=after,cmap='coolwarm',vmin=-.4,vmax=.4,
                 s=46,edgecolor='k',linewidth=.3)
plt.colorbar(sc,ax=ax[1],label='residual misfit (m)')
ax[1].set_title('crossing residual, median |%.0f| cm'%(100*np.median(abs(after))),fontsize=10)
for a in ax: a.set_xlabel('x (cm)'); a.set_ylabel('y (cm)'); a.set_aspect('equal')
fig.savefig('figs/C2_surface_adjusted.png',dpi=135); print('wrote figs/C2_surface_adjusted.png')
