import sys, os, glob, csv
sys.path.insert(0, os.path.dirname(__file__))
import segy, numpy as np
from scipy.signal import hilbert
ROOT = r'D:/code_ws/reference/parsans/report/raw/GPR Raw data_Kuppam'
DX = 0.0249  # m per trace

def env_agc(d, dt, w_ns=4.0):
    e = np.abs(hilbert(d, axis=1))
    w = max(3, int(w_ns / dt)); k = np.ones(w) / w
    sm = np.apply_along_axis(lambda r: np.convolve(r, k, 'same'), 1, e)
    return e / (sm + 1e-12)

def scan(E, dt, i0, j0, vlist, halfw=40):
    """semblance of a diffraction hyperbola apex at trace i0, sample j0."""
    n, ns = E.shape
    lo, hi = max(0, i0 - halfw), min(n, i0 + halfw + 1)
    off = (np.arange(lo, hi) - i0) * DX
    t0 = j0 * dt
    best = (-1, None)
    for v in vlist:
        t = np.sqrt(t0 ** 2 + (2.0 * off / v) ** 2)
        idx = np.round(t / dt).astype(int)
        ok = idx < ns
        if ok.sum() < 0.6 * len(off): continue
        vals = E[np.arange(lo, hi)[ok], idx[ok]]
        s = vals.mean() * np.sqrt(ok.sum())     # coherency x aperture
        if s > best[0]: best = (s, v)
    return best

rows = []
V = np.arange(0.085, 0.175, 0.0015)
for blk in ['A Block', 'B Block', 'C Block']:
    for ch, dt in [('HF', 0.0610352)]:
        for f in sorted(glob.glob(os.path.join(ROOT, blk, '**', '*_%s.sgy' % ch), recursive=True)):
            d = segy.read(f)['data']
            E = env_agc(d, dt)
            n, ns = E.shape
            j0, j1 = int(4.0 / dt), int(22.0 / dt)     # 0.25 - 1.3 m at v=.12
            W = E[:, j0:j1]
            # candidate apices: strong isolated local maxima
            cand = []
            flat = W.copy()
            for _ in range(6):
                k = int(np.argmax(flat)); i, j = np.unravel_index(k, flat.shape)
                if flat[i, j] <= 0: break
                cand.append((i, j + j0, float(flat[i, j])))
                flat[max(0,i-25):i+25, max(0,j-25):j+25] = 0
            for i, j, amp in cand:
                if i < 45 or i > n - 45: continue
                s, v = scan(E, dt, i, j, V)
                if v is None: continue
                # focusing quality: how peaked is the semblance in v
                ss = [scan(E, dt, i, j, [vv])[0] for vv in V]
                ss = np.array(ss); ss = ss / (ss.max() + 1e-12)
                width = float((ss > 0.97).sum()) * (V[1] - V[0])
                rows.append(dict(block=blk[0], line=os.path.basename(os.path.dirname(f))[:34],
                                 trace=i, samp=j, t0_ns=round(j * dt, 3),
                                 v=round(float(v), 4), rdp=round((0.299792458 / v) ** 2, 2),
                                 semb=round(float(s), 4), vwidth=round(width, 4)))
w = csv.DictWriter(open('tables/hyperbola_velocity.csv','w',newline='',encoding='utf-8'),
                   fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

import statistics as st
good = [r for r in rows if r['vwidth'] <= 0.012 and r['t0_ns'] > 10]     # the ONE selection rule; the same rule gives the working velocity (see velocity_summary.json)
print('Diffraction-hyperbola velocity scan, HF channel, apices between 0.25 and 1.3 m')
print('candidates %d, well-focused %d\n' % (len(rows), len(good)))
print('%-6s %5s %10s %10s %10s %10s'%('block','n','v median','v mean','v sd','RDP median'))
for b in 'ABC':
    s = [r['v'] for r in good if r['block'] == b]
    if len(s) < 5: continue
    print('%-6s %5d %10.4f %10.4f %10.4f %10.2f'%(b,len(s),st.median(s),st.mean(s),st.pstdev(s),
                                                  (0.299792458/st.median(s))**2))
allv = [r['v'] for r in good]
m = st.median(allv)
print('%-6s %5d %10.4f %10.4f %10.4f %10.2f'%('ALL',len(allv),m,st.mean(allv),st.pstdev(allv),
                                              (0.299792458/m)**2))
q1,q3 = np.percentile(allv,25), np.percentile(allv,75)
print('\n  interquartile range  %.4f - %.4f m/ns   (RDP %.2f - %.2f)'%(q1,q3,(0.299792458/q3)**2,(0.299792458/q1)**2))
print('  report adopts        0.1200 m/ns (RDP 6.25)')
print('  Proceq plate at 1 m  0.1174 m/ns (RDP 6.52)')
for lab,v in [('report 0.1200',0.12),('measured median %.4f'%m, m)]:
    print('  a 3.00 m pick at %s  ->  %.3f m' % (lab, 3.00*v/0.12))
