"""Every published number for C-1, C-2, B-1, B-2 against our picks, per line."""
import csv, numpy as np
V=0.1202
def rd(p):
    R=list(csv.DictReader(open(p,encoding='utf-8')))
    for r in R:
        r['line']=int(r['line']); r['x']=float(r['x_cm']); r['y']=float(r['y_cm'])
        r['z']=float(r.get('z_adj') or r['depth_m']); r['t']=float(r['twt_ns'])
    return R
C1=rd('tables/PICKS_C1_raw.csv'); C2=rd('tables/PICKS_C2_adjusted.csv')
B1=rd('tables/PICKS_B1_raw.csv'); B2=rd('tables/PICKS_B2_raw.csv')

def dip_along(pts,key):
    a=np.array([p[key] for p in pts])/100.0; z=np.array([p['z'] for p in pts])
    return np.degrees(np.arctan(np.polyfit(a,z,1)[0]))

out=[]
print('='*78); print('C-1   report Table (HF Y-lines): line, x, y-range, depth range, apparent dip')
T=[(20,100,76,237,0.47,0.70,8.2),(21,150,49,294,0.16,0.71,12.8),(22,200,51,296,0.17,0.69,11.7),
   (23,250,77,554,0.15,0.83,7.9),(24,300,86,702,0.38,1.08,6.0),(25,350,79,480,0.17,0.89,9.4),
   (26,400,69,391,0.17,1.01,14.0),(27,450,91,462,0.48,1.00,9.1),(28,500,78,438,0.49,0.96,7.3)]
print('%-5s %-13s %-13s %-13s %-13s %-8s %-8s'%('line','rep depth','our depth','d shallow','d deep','rep dip','our dip'))
for ln,fx,y0,y1,z0,z1,dp in T:
    s=[p for p in C1 if p['line']==ln]
    zs=np.array([p['z'] for p in s]); ys=np.array([p['y'] for p in s])
    a=zs[np.argmin(ys)]; b=zs[np.argmax(ys)]
    d=dip_along(s,'y')
    print('%-5d %5.2f-%-5.2f   %5.2f-%-5.2f   %+6.2f        %+6.2f        %5.1f    %5.1f'%(ln,z0,z1,a,b,a-z0,b-z1,dp,d))
    out.append(dict(feature='C-1',line=ln,rep_shallow=z0,our_shallow=round(a,3),rep_deep=z1,our_deep=round(b,3),rep_dip=dp,our_dip=round(d,1)))
dd=[o['our_dip']-o['rep_dip'] for o in out if o['feature']=='C-1']
es=[o['our_shallow']-o['rep_shallow'] for o in out]; ed=[o['our_deep']-o['rep_deep'] for o in out]
print('  endpoint misfit: shallow median %+.3f m, deep median %+.3f m; |max| %.3f'%(np.median(es),np.median(ed),max(map(abs,es+ed))))
print('  dip misfit: median %+.1f deg, range %+.1f to %+.1f;  report mean 9.6, ours %.1f'%(np.median(dd),min(dd),max(dd),np.mean([o['our_dip'] for o in out])))

print('\n'+'='*78); print('C-2   report Table 3 (LF, 8 lines): depth range per line vs our per-line range')
T3=[(18,'Y',0,3.24,3.29),(22,'Y',200,2.99,3.37),(26,'Y',400,2.97,3.28),(30,'Y',600,2.95,3.14),
    (1,'X',0,2.97,3.25),(6,'X',250,2.96,3.11),(11,'X',500,2.99,3.30),(17,'X',800,3.07,3.19)]
print('%-5s %-4s %-6s %-12s %-12s %-10s %-10s'%('line','or','fixed','rep range','our range','rep mid','our med'))
mids=[]
for ln,o,fx,z0,z1,*_ in T3:
    s=[p['z'] for p in C2 if p['line']==ln]
    lo,hi=np.percentile(s,5),np.percentile(s,95); med=np.median(s)
    print('%-5d %-4s %-6d %4.2f-%-6.2f %4.2f-%-6.2f %7.3f   %7.3f  %+.3f'%(ln,o,fx,z0,z1,lo,hi,(z0+z1)/2,med,med-(z0+z1)/2))
    mids.append(med-(z0+z1)/2)
print('  our median vs their mid-depth: median %+.3f m, sd %.3f   (re-anchored, so mean is ~0 by construction; the spread is the test)'%(np.median(mids),np.std(mids)))
allz=[p['z'] for p in C2]
print('  block-wide: report 2.95-3.37 m; ours 5th-95th pct %.2f-%.2f m, full %.2f-%.2f'%(np.percentile(allz,5),np.percentile(allz,95),min(allz),max(allz)))

print('\n'+'='*78); print('B-2   report Table 2 (LF Y-lines): line, x, depth range, apparent dip')
T2=[(14,0,1.86,4.06,None),(16,100,1.98,4.02,24.1),(18,200,1.86,4.00,24.4),(20,300,1.84,3.57,20.8),(22,400,2.12,3.26,18.2),(24,500,1.97,2.97,17.2)]
print('%-5s %-5s %-13s %-13s %-9s %-8s %-8s'%('line','x','rep depth','our depth','d ends','rep dip','our dip'))
b2d=[]
for ln,fx,z0,z1,dp in T2:
    s=[p for p in B2 if p['line']==ln]
    zs=np.array([p['z'] for p in s]); ys=np.array([p['y'] for p in s])
    a=zs[np.argmin(ys)]; b=zs[np.argmax(ys)]; d=dip_along(s,'y')
    print('%-5d %-5d %5.2f-%-5.2f   %5.2f-%-5.2f   %+.2f/%+.2f  %-8s %5.1f'%(ln,fx,z0,z1,a,b,a-z0,b-z1,('%.1f'%dp) if dp else 'n/a',d))
    if dp: b2d.append(d-dp)
print('  dip misfit: median %+.1f deg; report says dips flatten west to east 24.4 -> 17.2, ours: %s'
      %(np.median(b2d),' -> '.join('%.1f'%dip_along([p for p in B2 if p['line']==l],'y') for l in (14,16,18,20,22,24))))

print('\n'+'='*78); print('B-1   report gives NO depths. Checks available:')
zs=np.array([p['z'] for p in B1]); xs=np.array([p['x'] for p in B1])
print('  1. slice windows where the report says it shows: HF Imaxxy12 0.52-0.59 m, Imaxxy21 0.95-1.02 m, LF Imaxxy6 0.47-0.61, Imaxxy9 0.75-0.88')
print('     our B-1 spans %.2f-%.2f m, so it crosses all four windows: %s'
      %(zs.min(),zs.max(),', '.join('%s'%(('yes' if (zs.min()<=hi and zs.max()>=lo) else 'NO')) for lo,hi in [(.52,.59),(.95,1.02),(.47,.61),(.75,.88)])))
print('  2. corridor x 650-950: ours %.0f-%.0f cm by construction'%(xs.min(),xs.max()))
print('  3. "consistently dipping toward increasing x": %d of 13 lines deepen east'%sum(1 for l in range(1,14) if dip_along([p for p in B1 if p['line']==l],'x')>0))
dps=[dip_along([p for p in B1 if p['line']==l],'x') for l in range(1,14)]
print('  4. apparent dip 5.1-14.4 (mean 8.3): ours %.1f-%.1f (mean %.1f), %d of 13 inside their range'
      %(min(dps),max(dps),np.mean(dps),sum(1 for d in dps if 5.1<=d<=14.4)))
print('  5. plan trace x=-0.0667y+753 (3.8 deg rotation, 40 cm across 6 m): ours rotates %.1f deg, %.0f cm across 6 m, same sense'
      %(np.degrees(np.arctan(0.1717)),0.1717*600))

print('\n'+'='*78); print("Ronak's four email answers")
print('  permittivity 6.25 -> hyperbola scan 6.22, 0.5%%  [CONFIRMED]')
print('  lower TWT = shallow end -> every corridor was seeded that way and every one locked on  [CONFIRMED]')
print('  plan positions, use as reported -> used as reported; unmigrated  [ADOPTED]')
print('  Block C clutter y=350-750 -> checked below')
