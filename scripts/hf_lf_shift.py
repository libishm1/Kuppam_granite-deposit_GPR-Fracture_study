import sys, os, glob, csv
sys.path.insert(0, os.path.dirname(__file__))
import segy, numpy as np
from scipy.signal import hilbert

ROOT = r'D:/code_ws/reference/parsans/report/raw/GPR Raw data_Kuppam'
DT_HF, DT_LF = 0.0610352, 0.1220703   # ns
C = 0.299792458

def env_mean(f, dt):
    r = segy.read(f); d = r['data']
    e = np.abs(hilbert(d, axis=1))
    return e.mean(axis=0), r['ntr'], dt

rows = []
for blk in ['A Block', 'B Block', 'C Block']:
    hfs = sorted(glob.glob(os.path.join(ROOT, blk, '**', '*_HF.sgy'), recursive=True))
    for fh in hfs:
        fl = fh[:-7] + '_LF.sgy'
        if not os.path.exists(fl): continue
        eh, nh, _ = env_mean(fh, DT_HF)
        el, nl, _ = env_mean(fl, DT_LF)
        th = np.arange(len(eh)) * DT_HF
        tl = np.arange(len(el)) * DT_LF
        # common grid on the HF sample rate, over 0 - 39 ns
        tg = np.arange(0, 39.0, DT_HF)
        a = np.interp(tg, th, eh); b = np.interp(tg, tl, el)
        # normalise, restrict to the window that both channels usefully cover
        w = (tg > 1.0) & (tg < 25.0)
        a = a[w]; b = b[w]
        a = (a - a.mean()) / (a.std() + 1e-12)
        b = (b - b.mean()) / (b.std() + 1e-12)
        cc = np.correlate(b, a, mode='full')
        lags = np.arange(-len(a) + 1, len(a)) * DT_HF
        m = np.abs(lags) < 8.0
        k = int(np.argmax(cc[m]))
        lag = lags[m][k]
        # parabolic refine
        idx = np.where(m)[0][k]
        if 0 < idx < len(cc) - 1:
            y0, y1, y2 = cc[idx - 1], cc[idx], cc[idx + 1]
            den = (y0 - 2 * y1 + y2)
            if den != 0: lag += DT_HF * 0.5 * (y0 - y2) / den
        rows.append(dict(block=blk[0], line=os.path.basename(os.path.dirname(fh))[:38],
                         ntr=nh, lag_ns=round(float(lag), 4),
                         r=round(float(cc[m][k] / len(a)), 4)))
w = csv.DictWriter(open('tables/hf_lf_lag.csv', 'w', newline='', encoding='utf-8'),
                   fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

import statistics as st
print('LF minus HF arrival-time lag, from envelope cross-correlation over 1-25 ns')
print('positive lag = LF records the same reflector LATER than HF\n')
print('%-6s %5s %9s %9s %9s %9s %9s' % ('block','n','median','mean','sd','min','max'))
for b in 'ABC':
    s = [r['lag_ns'] for r in rows if r['block'] == b]
    print('%-6s %5d %9.3f %9.3f %9.3f %9.3f %9.3f' % (b, len(s), st.median(s), st.mean(s), st.pstdev(s), min(s), max(s)))
allv = [r['lag_ns'] for r in rows]
print('%-6s %5d %9.3f %9.3f %9.3f %9.3f %9.3f' % ('ALL', len(allv), st.median(allv), st.mean(allv), st.pstdev(allv), min(allv), max(allv)))
med = st.median(allv)
print('\nmedian lag %.3f ns' % med)
for v in [0.12, 0.1252, 0.1095, 0.13416]:
    print('  at v = %.4f m/ns  ->  depth bias %6.1f cm' % (v, med * v / 2 * 100))
print('\ngeometric expectation from antenna offsets alone (air wave):')
print('  LF 24.4 cm - HF 7.0 cm = %.3f ns' % ((0.244 - 0.070) / C))
print('  residual unexplained by offset: %.3f ns' % (med - (0.244 - 0.070) / C))
print('  quality: mean corr %.3f, %d of %d lines with r>0.5' %
      (st.mean([r['r'] for r in rows]), sum(1 for r in rows if r['r'] > 0.5), len(rows)))
