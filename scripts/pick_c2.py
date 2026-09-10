"""Track the C-2 reflector on every Block C LF line, straight from the raw SEG-Y."""
import sys, os, glob, csv
sys.path.insert(0, os.path.dirname(__file__))
import segy, numpy as np
from scipy.signal import hilbert

ROOT = r'D:/code_ws/reference/parsans/report/raw/GPR Raw data_Kuppam'
DT = 0.1220703          # ns per sample, LF
DX = 2.49               # cm per trace
V  = 0.1202             # m/ns, measured by hyperbola scan (report adopts 0.1200)
WIN = (44.0, 62.0)      # ns; report brackets C-2 at 49.17-56.12

# Block C: lines 1-17 are X-lines at fixed y; 18-32 are Y-lines at fixed x. Step 50 cm.
def geom(ln):
    if ln <= 17: return ('X', 'y', (ln - 1) * 50.0)      # runs along x
    return ('Y', 'x', (ln - 18) * 50.0)                  # runs along y

def agc_env(d, w_ns=6.0):
    e = np.abs(hilbert(d, axis=1))
    w = max(3, int(w_ns / DT)); k = np.ones(w) / w
    sm = np.apply_along_axis(lambda r: np.convolve(r, k, 'same'), 1, e)
    return e / (sm + 1e-12)

def track(E, j0, j1, jump=2, smooth=0.35):
    """Dynamic programming: maximise summed envelope, penalise sample-to-sample jumps."""
    W = E[:, j0:j1]
    n, m = W.shape
    sc = W.copy(); bk = np.zeros((n, m), dtype=int)
    for i in range(1, n):
        prev = sc[i - 1]
        best = prev.copy(); arg = np.arange(m)
        for s in range(1, jump + 1):
            cand = np.full(m, -1e18); cand[s:] = prev[:-s] - smooth * s
            upd = cand > best; best[upd] = cand[upd]; arg[upd] = (np.arange(m) - s)[upd]
            cand = np.full(m, -1e18); cand[:-s] = prev[s:] - smooth * s
            upd = cand > best; best[upd] = cand[upd]; arg[upd] = (np.arange(m) + s)[upd]
        sc[i] += best; bk[i] = arg
    path = np.zeros(n, dtype=int); path[-1] = int(np.argmax(sc[-1]))
    for i in range(n - 1, 0, -1): path[i - 1] = bk[i, path[i]]
    return path + j0

rows = []
j0, j1 = int(WIN[0] / DT), int(WIN[1] / DT)
for ln in range(1, 33):
    g = sorted(glob.glob(os.path.join(ROOT, 'C Block', '**', '*new%03d_*_LF.sgy' % ln), recursive=True))
    if not g: print('missing line', ln); continue
    r = segy.read(g[0]); d = r['data']; E = agc_env(d)
    p = track(E, j0, j1)
    twt = p * DT
    orient, fixax, fixv = geom(ln)
    amp = E[np.arange(len(p)), p]
    for i, (t, a) in enumerate(zip(twt, amp)):
        along = i * DX
        x = fixv if fixax == 'x' else along
        y = fixv if fixax == 'y' else along
        rows.append(dict(block='C', line=ln, orientation=orient + '-line',
                         trace=i, x_cm=round(x, 1), y_cm=round(y, 1),
                         twt_ns=round(float(t), 4), depth_m=round(float(t) * V / 2, 4),
                         envelope=round(float(a), 3)))
w = csv.DictWriter(open('tables/PICKS_C2_raw.csv','w',newline='',encoding='utf-8'),
                   fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
import statistics as st
tw = [r['twt_ns'] for r in rows]; dp = [r['depth_m'] for r in rows]
print('C-2 tracked on 32 lines, %d picks (report published 8 lines as depth ranges)' % len(rows))
print('  TWT   %.2f to %.2f ns, median %.2f' % (min(tw), max(tw), st.median(tw)))
print('  depth %.3f to %.3f m, median %.3f  (v = %.4f m/ns)' % (min(dp), max(dp), st.median(dp), V))
print('\n  report Table 3 says 49.17-56.12 ns, 2.95-3.37 m')
print('  per-line median depth:')
for ln in range(1, 33):
    s = [r['depth_m'] for r in rows if r['line'] == ln]
    if s: print('    line %2d %-7s  n=%3d  median %.3f m  spread %.3f' %
                (ln, geom(ln)[0]+'-line', len(s), st.median(s), max(s)-min(s)))
