"""OBJ export of all four surfaces (metres, z negative down, y up in Rhino terms) and one combined view."""
import numpy as np, os
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa
def load(p):
    a=np.loadtxt(p); n=len(np.unique(a[:,0])); m=len(np.unique(a[:,1]))
    return a[:,0].reshape(m,n),a[:,1].reshape(m,n),a[:,2].reshape(m,n)
S={k:load('model/%s_grid_10cm.xyz'%k) for k in ('C1','C2','B1','B2')}

def obj(path,GX,GY,Z,name):
    ny,nx=Z.shape; L=['# Kuppam GPR fracture surface %s, metres, z negative = depth below block top'%name,'o %s'%name]
    for j in range(ny):
        for i in range(nx): L.append('v %.4f %.4f %.4f'%(GX[j,i]/100.0,GY[j,i]/100.0,-Z[j,i]))
    for j in range(ny-1):
        for i in range(nx-1):
            a=j*nx+i+1; b=a+1; c=a+nx+1; d=a+nx
            L.append('f %d %d %d %d'%(a,b,c,d))
    open(path,'w').write('\n'.join(L)+'\n'); return ny*nx,(ny-1)*(nx-1)
for k,(GX,GY,Z) in S.items():
    nv,nf=obj('model/%s_surface.obj'%k,GX,GY,Z,k); print('%s_surface.obj  %d verts %d quads'%(k,nv,nf))
# one combined OBJ per block, so Rhino gets both surfaces in one import
for blk,keys,dims in (('C',('C1','C2'),(7.0,8.0)),('B',('B1','B2'),(9.5,6.0))):
    L=['# Kuppam Block %s, metres, z negative = depth. Block outline %.1f x %.1f m at z=0'%(blk,*dims)]
    off=0
    for k in keys:
        GX,GY,Z=S[k]; ny,nx=Z.shape; L.append('o %s'%k)
        for j in range(ny):
            for i in range(nx): L.append('v %.4f %.4f %.4f'%(GX[j,i]/100,GY[j,i]/100,-Z[j,i]))
        for j in range(ny-1):
            for i in range(nx-1):
                a=off+j*nx+i+1; L.append('f %d %d %d %d'%(a,a+1,a+nx+1,a+nx))
        off+=ny*nx
    # block top as a quad at z=0
    L+=['o block_top_%s'%blk]+['v 0 0 0','v %.1f 0 0'%dims[0],'v %.1f %.1f 0'%dims,'v 0 %.1f 0'%dims[1],'f %d %d %d %d'%(off+1,off+2,off+3,off+4)]
    open('model/Block%s_all.obj'%blk,'w').write('\n'.join(L)+'\n'); print('Block%s_all.obj'%blk)

fig=plt.figure(figsize=(15,9))
spec=dict(C=dict(pos=(0,0),dims=(700,800),keys=(('C2','viridis_r',.95),('C1','autumn',.9)),az=-55),
          B=dict(pos=(0,1),dims=(950,600),keys=(('B2','Blues_r',.95),('B1','autumn',.9)),az=-62))
for r,(blk,sp) in enumerate(spec.items()):
    ax=fig.add_subplot(2,2,r+1,projection='3d')
    W,H=sp['dims']
    ax.plot([0,W,W,0,0],[0,0,H,H,0],[0,0,0,0,0],'k-',lw=1.5)
    for k,cm,al in sp['keys']:
        GX,GY,Z=S[k]; s=2
        ax.plot_surface(GX[::s,::s],GY[::s,::s],-Z[::s,::s],cmap=cm,alpha=al,linewidth=0)
    ax.set_xlim(0,W); ax.set_ylim(0,H); ax.set_zlim(-4.2,0.2)
    ax.set_xlabel('x (cm)'); ax.set_ylabel('y (cm)'); ax.set_zlabel('depth (m)')
    ax.set_title('Block %s  (%.1f x %.1f m)'%(blk,W/100,H/100),fontsize=11)
    ax.view_init(elev=24,azim=sp['az']); ax.set_box_aspect((W/100,H/100,4.2))
    ax=fig.add_subplot(2,2,r+3)
    for k,cm,al in sp['keys']:
        GX,GY,Z=S[k]
        im=ax.pcolormesh(GX,GY,Z,shading='auto',cmap=cm,alpha=.95)
        cs=ax.contour(GX,GY,Z,levels=8,colors='k',linewidths=.4); ax.clabel(cs,fmt='%.1f',fontsize=6)
        j,i=np.unravel_index(np.argmin(Z),Z.shape)
        ax.plot(GX[j,i],GY[j,i],'r*',ms=14,mec='k'); ax.text(GX[j,i]+12,GY[j,i]+12,'%s min %.2f m'%(k,Z.min()),fontsize=8,color='k',weight='bold')
    ax.set_xlim(0,W); ax.set_ylim(0,H); ax.set_aspect('equal'); ax.set_xlabel('x (cm)'); ax.set_ylabel('y (cm)')
    ax.set_title('Block %s plan, depth contours in m, star = shallowest point of each cap'%blk,fontsize=9)
fig.suptitle('Kuppam GPR, Blocks B and C, fracture surfaces from the raw SEG-Y (09-09-2026)',fontsize=12)
fig.tight_layout(); fig.savefig('figs/MODEL_overview.png',dpi=130); print('wrote figs/MODEL_overview.png')
