import sys, os, glob
sys.path.insert(0, os.path.dirname(__file__))
import segy, numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy.signal import hilbert
ROOT=r'D:/code_ws/reference/parsans/report/raw/GPR Raw data_Kuppam'
V=0.1202
def load(ln,ch):
    g=sorted(glob.glob(os.path.join(ROOT,'B Block','**','*new%03d_*_%s.sgy'%(ln,ch)),recursive=True))
    return segy.read(g[0])
def agc(d,dt,w=3.0):
    e=np.abs(hilbert(d,axis=1)); k=np.ones(max(3,int(w/dt)))/max(3,int(w/dt))
    sm=np.apply_along_axis(lambda r:np.convolve(r,k,'same'),1,e); return d/(sm+1e-12)
def panel(ax,d,dt,ttl,tmax):
    a=agc(d,dt); n,ns=a.shape; m=int(tmax/dt); a=a[:,:m]
    cl=np.percentile(np.abs(a),98)
    ax.imshow(a.T,aspect='auto',cmap='gray_r',vmin=-cl,vmax=cl,
              extent=[0,n*2.49,m*dt*V/2,0])
    ax.set_title(ttl,fontsize=9); ax.tick_params(labelsize=7)
    ax.set_xlabel('along line (cm)',fontsize=8); ax.set_ylabel('depth m',fontsize=8)

fig,ax=plt.subplots(3,1,figsize=(12,11),constrained_layout=True)
# B-1 lives on HF X-lines, corridor x 650-950
for a,ln in zip(ax[:2],[1,13]):
    r=load(ln,'HF'); y=(ln-1)*50
    panel(a,r['data'],0.0610352,'Block B Line %d HF  (X-line, y=%d cm) - B-1 corridor shaded'%(ln,y),22)
    a.axvspan(650,950,color='orange',alpha=.16)
    xt=-0.0667*y+753.14
    a.axvline(xt,color='r',ls='--',lw=1.2,label='B-1 plan trace x=%.0f cm'%xt)
    a.legend(fontsize=7,loc='lower left')
# B-2 on LF Y-lines, published endpoints
r=load(18,'LF')
panel(ax[2],r['data'],0.1220703,'Block B Line 18 LF  (Y-line, x=200 cm) - B-2 published pick',80)
ax[2].plot([35,458],[30.99*0.06,66.61*0.06],'r-o',lw=2,ms=5,label='Table 2: y 35-458, 1.86-4.00 m')
ax[2].legend(fontsize=7,loc='lower left')
fig.savefig('figs/B_look.png',dpi=125); print('wrote figs/B_look.png')
