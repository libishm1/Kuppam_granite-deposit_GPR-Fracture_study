"""A-1: corrected plane from the published picks (Line 10 reversed); hunt bright RUNS along it on HF and LF."""
import sys, os, glob, csv
sys.path.insert(0, os.path.dirname(__file__))
import segy, numpy as np
from scipy.signal import hilbert
from scipy.ndimage import uniform_filter1d
exec(open(os.path.join(os.path.dirname(__file__),'build_b.py')).read().split('# ---------------- B-2')[0].replace("'B Block'","'A Block'"))
def geom(ln): return ('X','y',(ln-1)*50.0) if ln<=12 else ('Y','x',(ln-13)*50.0)
P=np.array([[300,266,1.13],[300,342,1.47],[422,450,1.60],[542,450,1.30]],float)
A=np.c_[P[:,0],P[:,1],np.ones(4)]; co,*_=np.linalg.lstsq(A,P[:,2],rcond=None)
print('A-1 plane, Line 10 reversed: dip %.1f, azimuth %.0f, strike %.0f from +y (NE-SW), residual %.1f cm'
      %(np.degrees(np.arctan(np.hypot(co[0],co[1])*100)),np.degrees(np.arctan2(co[0],co[1]))%360,
        (np.degrees(np.arctan2(co[0],co[1]))+90)%180,100*abs(P[:,2]-A@co).max()))
THR=1.25; MINRUN=40   # envelope threshold and minimum run length in cm
rows=[]; segs=[]
for ln in range(1,25):
    orient,fixax,fixv=geom(ln)
    for ch,dt,zlo,zhi in (('HF',DTH,0.30,1.25),('LF',DTL,0.90,2.40)):
        r=load(ln,ch); E=agc_env(r['data'],dt); n=r['ntr']; along=np.arange(n)*DX
        x=np.full(n,fixv) if fixax=='x' else along; y=np.full(n,fixv) if fixax=='y' else along
        zp=co[0]*x+co[1]*y+co[2]; ok=(zp>zlo)&(zp<zhi)
        if ok.sum()<16: continue
        i0,i1=int(np.argmax(ok)),int(len(ok)-1-np.argmax(ok[::-1]))
        idx,jj=corridor(E,i0,i1,int(round(2*zp[i0]/V/dt)),int(round(2*zp[i1]/V/dt)),corr=10,jump=1,smooth=0.6)
        en=uniform_filter1d(E[idx,jj],9)
        hot=en>THR
        # runs
        k=0
        while k<len(hot):
            if hot[k]:
                k2=k
                while k2<len(hot) and hot[k2]: k2+=1
                L=(k2-k)*DX
                if L>=MINRUN:
                    z=jj[k:k2]*dt*V/2; a=along[idx[k:k2]]
                    segs.append((ln,orient,fixv,ch,a[0],a[-1],z[0],z[-1],en[k:k2].mean()))
                    for i,j in zip(idx[k:k2],jj[k:k2]):
                        rows.append(dict(block='A',feature='A-1',line=ln,orientation=orient+'-line',channel=ch,
                                         x_cm=round(float(x[i]),1),y_cm=round(float(y[i]),1),
                                         twt_ns=round(j*dt,4),depth_m=round(j*dt*V/2,4),envelope=round(float(E[i,j]),3)))
                k=k2
            else: k+=1
# the two published segments, tracked between their endpoints (Line 10 with depths reversed)
for ln,ch,dt,fx,a0,a1,t0,t1 in ((19,'HF',DTH,300,266,342,18.91,24.52),(10,'LF',DTL,450,422,542,26.60,21.72)):
    orient,fixax,fixv=geom(ln); r=load(ln,ch); E=agc_env(r['data'],dt); n=r['ntr']; along=np.arange(n)*DX
    x=np.full(n,fixv) if fixax=='x' else along; y=np.full(n,fixv) if fixax=='y' else along
    idx,jj=corridor(E,int(round(a0/DX)),int(round(a1/DX)),int(round(t0/dt)),int(round(t1/dt)),corr=8,jump=1,smooth=0.6)
    z=jj*dt*V/2; segs.append((ln,orient,fixv,ch+'*',along[idx[0]],along[idx[-1]],z[0],z[-1],E[idx,jj].mean()))
    for i,j in zip(idx,jj):
        rows.append(dict(block='A',feature='A-1',line=ln,orientation=orient+'-line',channel=ch,
                         x_cm=round(float(x[i]),1),y_cm=round(float(y[i]),1),
                         twt_ns=round(j*dt,4),depth_m=round(j*dt*V/2,4),envelope=round(float(E[i,j]),3)))
print('\nbright runs (>= %d cm with smoothed envelope > %.2f) along the plane corridor, plus the published segments (*):'%(MINRUN,THR))
print('%-4s %-3s %-5s %-3s %-13s %-13s %-6s'%('line','or','fixed','ch','along (cm)','depth (m)','env'))
for s in segs: print('%-4d %-3s %-5.0f %-3s %5.0f-%-6.0f %5.2f-%-6.2f %5.2f%s'%(s[0],s[1],s[2],s[3],s[4],s[5],s[6],s[7],s[8],'  <- published' if s[0] in(10,19) else ''))
lines=sorted({s[0] for s in segs})
print('\nA-1 found on %d lines (%s), %d picks. Report: 2 lines, 4 endpoints.'%(len(lines),','.join(map(str,lines)),len(rows)))
w=csv.DictWriter(open('tables/PICKS_A1_raw.csv','w',newline='',encoding='utf-8'),fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
Q=np.array([[r['x_cm'],r['y_cm'],r['depth_m']] for r in rows]); A2=np.c_[Q[:,0],Q[:,1],np.ones(len(Q))]
c2,*_=np.linalg.lstsq(A2,Q[:,2],rcond=None); r2=Q[:,2]-A2@c2
print('refit on all picks: dip %.1f deg, azimuth %.0f, residual RMS %.3f m, max %.3f  (seeded from the 4-point plane, so corroboration not independence)'
      %(np.degrees(np.arctan(np.hypot(c2[0],c2[1])*100)),np.degrees(np.arctan2(c2[0],c2[1]))%360,r2.std(),abs(r2).max()))
