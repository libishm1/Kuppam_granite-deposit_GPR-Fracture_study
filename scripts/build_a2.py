"""A-2: seed the five stated Y-lines from Figure 7's geometry, fit the plane, hunt it on all 24 lines."""
import sys, os, glob, csv
sys.path.insert(0, os.path.dirname(__file__))
import segy, numpy as np
from scipy.ndimage import uniform_filter1d
exec(open(os.path.join(os.path.dirname(__file__),'build_b.py')).read().split('# ---------------- B-2')[0].replace("'B Block'","'A Block'"))
def geom(ln): return ('X','y',(ln-1)*50.0) if ln<=12 else ('Y','x',(ln-13)*50.0)
def coords(ln,n):
    orient,fixax,fixv=geom(ln); along=np.arange(n)*DX
    return orient,(np.full(n,fixv) if fixax=='x' else along),(np.full(n,fixv) if fixax=='y' else along)
rows=[]; segs=[]
# (a) seed corridors on the five stated lines. Figure 7: z 0.45 m at y 60 cm, dipping ~35 deg toward +y
for ln in (13,15,16,19,22):
    for ch,dt,y0,y1 in (('HF',DTH,60,190),('LF',DTL,150,380)):
        z0=0.45+(y0-60)/100*np.tan(np.radians(35)); z1=0.45+(y1-60)/100*np.tan(np.radians(35))
        r=load(ln,ch); E=agc_env(r['data'],dt); n=r['ntr']; orient,x,y=coords(ln,n)
        idx,jj=corridor(E,int(round(y0/DX)),int(round(y1/DX)),int(round(2*z0/V/dt)),int(round(2*z1/V/dt)),corr=18,jump=2,smooth=0.5)
        z=jj*dt*V/2
        segs.append((ln,orient,geom(ln)[2],ch+'s',y[idx[0]],y[idx[-1]],z[0],z[-1],E[idx,jj].mean()))
        for i,j in zip(idx,jj):
            rows.append(dict(block='A',feature='A-2',line=ln,orientation=orient+'-line',channel=ch,x_cm=round(float(x[i]),1),
                             y_cm=round(float(y[i]),1),twt_ns=round(j*dt,4),depth_m=round(j*dt*V/2,4),envelope=round(float(E[i,j]),3),src='seed'))
P=np.array([[r['x_cm'],r['y_cm'],r['depth_m']] for r in rows]); A=np.c_[P[:,0],P[:,1],np.ones(len(P))]
co,*_=np.linalg.lstsq(A,P[:,2],rcond=None); res=P[:,2]-A@co
print('A-2 plane from the five seeded Y-lines: dip %.1f deg, azimuth %.0f deg from +y toward +x, residual RMS %.3f m'
      %(np.degrees(np.arctan(np.hypot(co[0],co[1])*100)),np.degrees(np.arctan2(co[0],co[1]))%360,res.std()))
print('  report: dips 32-41 (mean 38), "trends approximately E-W", "dipping towards increasing Y"')
print('  per-line seeded apparent dip along y:')
for ln in (13,15,16,19,22):
    s=[r for r in rows if r['line']==ln]; yy=np.array([r['y_cm'] for r in s])/100; zz=np.array([r['depth_m'] for r in s])
    print('    line %2d x=%3.0f  %.1f deg  z %.2f-%.2f'%(ln,geom(ln)[2],np.degrees(np.arctan(np.polyfit(yy,zz,1)[0])),zz.min(),zz.max()))
# (b) hunt on every line along that plane
THR=1.25; MINRUN=40
for ln in range(1,25):
    for ch,dt,zlo,zhi in (('HF',DTH,0.30,1.25),('LF',DTL,0.90,2.60)):
        r=load(ln,ch); E=agc_env(r['data'],dt); n=r['ntr']; orient,x,y=coords(ln,n); along=np.arange(n)*DX
        zp=co[0]*x+co[1]*y+co[2]; ok=(zp>zlo)&(zp<zhi)
        if ok.sum()<16: continue
        i0,i1=int(np.argmax(ok)),int(len(ok)-1-np.argmax(ok[::-1]))
        idx,jj=corridor(E,i0,i1,int(round(2*zp[i0]/V/dt)),int(round(2*zp[i1]/V/dt)),corr=10,jump=1,smooth=0.6)
        en=uniform_filter1d(E[idx,jj],9); hot=en>THR; k=0
        while k<len(hot):
            if hot[k]:
                k2=k
                while k2<len(hot) and hot[k2]: k2+=1
                if (k2-k)*DX>=MINRUN:
                    z=jj[k:k2]*dt*V/2; a=along[idx[k:k2]]
                    segs.append((ln,orient,geom(ln)[2],ch,a[0],a[-1],z[0],z[-1],en[k:k2].mean()))
                    for i,j in zip(idx[k:k2],jj[k:k2]):
                        rows.append(dict(block='A',feature='A-2',line=ln,orientation=orient+'-line',channel=ch,x_cm=round(float(x[i]),1),
                                         y_cm=round(float(y[i]),1),twt_ns=round(j*dt,4),depth_m=round(j*dt*V/2,4),envelope=round(float(E[i,j]),3),src='hunt'))
                k=k2
            else: k+=1
print('\nbright runs along the A-2 plane (s = seeded on a stated line):')
print('%-4s %-3s %-5s %-3s %-13s %-13s %-5s'%('line','or','fixed','ch','along (cm)','depth (m)','env'))
for s in sorted(segs,key=lambda s:(s[0],s[3])): print('%-4d %-3s %-5.0f %-3s %5.0f-%-6.0f %5.2f-%-6.2f %5.2f'%s)
hx=sorted({s[0] for s in segs if s[1]=='X' and not s[3].endswith('s')}); hy=sorted({s[0] for s in segs if s[1]=='Y' and not s[3].endswith('s')})
print('\nhunt found A-2 on X-lines %s and Y-lines %s beyond the five seeded (report: 5 Y-lines only)'%(hx,hy))
w=csv.DictWriter(open('tables/PICKS_A2_raw.csv','w',newline='',encoding='utf-8'),fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
Q=np.array([[r['x_cm'],r['y_cm'],r['depth_m']] for r in rows]); A2=np.c_[Q[:,0],Q[:,1],np.ones(len(Q))]
c2,*_=np.linalg.lstsq(A2,Q[:,2],rcond=None); r2=Q[:,2]-A2@c2
print('refit on all %d picks: dip %.1f deg, azimuth %.0f, residual RMS %.3f m, max %.3f'
      %(len(Q),np.degrees(np.arctan(np.hypot(c2[0],c2[1])*100)),np.degrees(np.arctan2(c2[0],c2[1]))%360,r2.std(),abs(r2).max()))
# X-line cross-check: X-lines run along x at fixed y, so they should see A-2 near-flat at the plane's depth for that y
xs=[r for r in rows if r['orientation']=='X-line']
if xs:
    zx=np.array([r['depth_m'] for r in xs]); zp=np.array([co[0]*r['x_cm']+co[1]*r['y_cm']+co[2] for r in xs])
    print('X-line cross-check: %d picks, depth vs plane-from-Y-lines: median %+.3f m, |misfit| median %.3f, 90th %.3f'
          %(len(xs),np.median(zx-zp),np.median(abs(zx-zp)),np.percentile(abs(zx-zp),90)))
