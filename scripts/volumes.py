import numpy as np, os
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa

def load(p):
    a=np.loadtxt(p); n=len(np.unique(a[:,0])); m=len(np.unique(a[:,1]))
    return a[:,0].reshape(m,n), a[:,1].reshape(m,n), a[:,2].reshape(m,n)
GX2,GY2,Z2=load('model/C2_grid_10cm.xyz')
GX1,GY1,Z1=load('model/C1_grid_10cm.xyz')
cell=0.10*0.10   # m2 per 10 cm node
RHO=2.95         # t/m3, dolerite

print('BLOCK C, 7.0 x 8.0 m = 56.0 m2\n')
print('C-2, the base cap')
print('  depth  min %.2f  mean %.2f  max %.2f m'%(Z2.min(),Z2.mean(),Z2.max()))
vol2=Z2.sum()*cell
print('  volume above C-2 across the whole block: %.1f m3  = %.0f t'%(vol2,vol2*RHO))
print('  if planned at the report band mid 3.16 m: %.1f m3'%(3.16*56.0))
print('  difference against a flat plan at the mean: %+.1f m3'%(vol2-Z2.mean()*56.0))

# C-1 only covers x 100-500, y 0-760
m1=np.zeros_like(Z2,dtype=bool)
x2=GX2[0]; y2=GY2[:,0]
ix=(x2>=100)&(x2<=500); iy=(y2>=0)&(y2<=760)
m1[np.ix_(iy,ix)]=True
Z1i=np.full_like(Z2,np.nan)
from scipy.interpolate import RegularGridInterpolator
f=RegularGridInterpolator((GY1[:,0],GX1[0]),Z1,bounds_error=False,fill_value=None)
pts=np.c_[GY2.ravel(),GX2.ravel()]
Z1i=f(pts).reshape(Z2.shape)
Z1i[~m1]=np.nan
area1=np.isfinite(Z1i).sum()*cell
print('\nC-1, the shallow fracture, footprint %.1f m2 of the 56'%area1)
print('  depth  min %.2f  mean %.2f  max %.2f m'%(np.nanmin(Z1i),np.nanmean(Z1i),np.nanmax(Z1i)))
print('  clearance C-1 to C-2:  min %.2f  mean %.2f m'%(np.nanmin(Z2-Z1i),np.nanmean(Z2-Z1i)))

vA=np.nansum(np.where(np.isfinite(Z1i),Z1i,0))*cell
vB=np.nansum(np.where(np.isfinite(Z1i),Z2-Z1i,0))*cell
vC=np.nansum(np.where(np.isfinite(Z1i),0,Z2))*cell
print('\nthree extractable volumes, top down')
for nm,v in (('above C-1 (west strip)',vA),('C-1 to C-2 (west strip)',vB),('above C-2 (rest of block)',vC)):
    print('  %-28s %6.1f m3  %5.0f t'%(nm,v,v*RHO))
print('  %-28s %6.1f m3  %5.0f t'%('total',vA+vB+vC,(vA+vB+vC)*RHO))
print('\nthe binding constraint on a single full-height block is C-2 at its shallowest:')
j,i=np.unravel_index(np.argmin(Z2),Z2.shape)
print('  %.2f m, at x = %.0f cm, y = %.0f cm'%(Z2.min(),GX2[j,i],GY2[j,i]))

fig=plt.figure(figsize=(12.5,5.6))
ax=fig.add_subplot(121,projection='3d')
s=3
ax.plot_surface(GX2[::s,::s],GY2[::s,::s],-Z2[::s,::s],cmap='viridis_r',alpha=.92,linewidth=0)
Zp=np.where(np.isfinite(Z1i),-Z1i,np.nan)
ax.plot_surface(GX2[::s,::s],GY2[::s,::s],Zp[::s,::s],color='orangered',alpha=.85,linewidth=0)
ax.set_xlabel('x (cm)'); ax.set_ylabel('y (cm)'); ax.set_zlabel('depth (m)')
ax.set_title('Block C: C-1 (red) over C-2 (green)',fontsize=10)
ax.view_init(elev=24,azim=-58); ax.set_box_aspect((7,8,4))
ax2=fig.add_subplot(122)
im=ax2.pcolormesh(GX2,GY2,Z2,shading='auto',cmap='viridis_r')
cs=ax2.contour(GX2,GY2,Z2,levels=np.arange(2.8,3.65,.1),colors='k',linewidths=.5)
ax2.clabel(cs,fmt='%.1f',fontsize=6)
ax2.contour(GX2,GY2,np.where(np.isfinite(Z1i),Z1i,np.nan),levels=np.arange(.2,1.1,.2),
            colors='orangered',linewidths=1.0)
plt.colorbar(im,ax=ax2,label='C-2 depth (m)')
ax2.plot(GX2[j,i],GY2[j,i],'r*',ms=17,mec='k')
ax2.set_title('C-2 contours, C-1 in red, star = shallowest C-2',fontsize=10)
ax2.set_xlabel('x (cm)'); ax2.set_ylabel('y (cm)'); ax2.set_aspect('equal')
fig.tight_layout(); fig.savefig('figs/BlockC_model.png',dpi=135)
print('\nwrote figs/BlockC_model.png')
