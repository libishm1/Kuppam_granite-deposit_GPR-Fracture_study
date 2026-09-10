"""A-1: both published picks on their raw lines, as printed and with Line 10's depths reversed."""
import sys, os, glob
sys.path.insert(0, os.path.dirname(__file__))
import segy, numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy.signal import hilbert
ROOT=r'D:/code_ws/reference/parsans/report/raw/GPR Raw data_Kuppam'; V=0.1202
def load(ln,ch):
    g=sorted(glob.glob(os.path.join(ROOT,'A Block','**','*new%03d_*_%s.sgy'%(ln,ch)),recursive=True)); return segy.read(g[0])
def agc(d,dt,w=3.0):
    e=np.abs(hilbert(d,axis=1)); k=np.ones(max(3,int(w/dt)))/max(3,int(w/dt))
    sm=np.apply_along_axis(lambda r:np.convolve(r,k,'same'),1,e); return d/(sm+1e-12)
def panel(ax,d,dt,ttl,tmax):
    a=agc(d,dt); n,ns=a.shape; m=int(tmax/dt); a=a[:,:m]; cl=np.percentile(np.abs(a),98)
    ax.imshow(a.T,aspect='auto',cmap='gray_r',vmin=-cl,vmax=cl,extent=[0,n*2.49,m*dt*V/2,0])
    ax.set_title(ttl,fontsize=9); ax.tick_params(labelsize=7); ax.set_xlabel('along line (cm)',fontsize=8); ax.set_ylabel('depth m',fontsize=8)
fig,ax=plt.subplots(2,1,figsize=(12,8.4),constrained_layout=True)
r=load(19,'HF'); panel(ax[0],r['data'],0.0610352,'Block A Line 19 HF (report: fixed x=300, pick along y 266-342 cm, TWT 18.91-24.52 ns)',32)
ax[0].plot([266,342],[18.91*0.0601,24.52*0.0601],'r-o',lw=2.2,ms=6,label='as printed: deepens with distance')
ax[0].legend(fontsize=8,loc='lower left')
r=load(10,'LF'); panel(ax[1],r['data'],0.1220703,'Block A Line 10 LF (report: fixed y=450, pick along x 422-542 cm, TWT 21.72-26.60 ns)',40)
ax[1].plot([422,542],[21.72*0.0601,26.60*0.0601],'r-o',lw=2.2,ms=6,label='as printed: 422 shallow, 542 deep')
ax[1].plot([422,542],[26.60*0.0601,21.72*0.0601],'c--s',lw=2.2,ms=6,label='reversed: 422 deep, 542 shallow')
ax[1].legend(fontsize=8,loc='lower left')
fig.savefig('figs/A1_line19_line10.png',dpi=125); print('wrote figs/A1_line19_line10.png')
