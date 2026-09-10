import sys, os, glob
sys.path.insert(0, os.path.dirname(__file__))
import segy, numpy as np
from scipy.signal import hilbert
ROOT = r'D:/code_ws/reference/parsans/report/raw/GPR Raw data_Kuppam'
DT_HF, DT_LF = 0.0610352, 0.1220703

WINS = [(1,5),(4,8),(7,11),(10,14),(13,17),(16,20),(19,23),(22,26),(25,30),(29,34),(33,38)]
acc = {w: [] for w in WINS}
n = 0
for blk in ['A Block','B Block','C Block']:
    for fh in sorted(glob.glob(os.path.join(ROOT, blk, '**', '*_HF.sgy'), recursive=True)):
        fl = fh[:-7] + '_LF.sgy'
        if not os.path.exists(fl): continue
        eh = np.abs(hilbert(segy.read(fh)['data'], axis=1)).mean(axis=0)
        el = np.abs(hilbert(segy.read(fl)['data'], axis=1)).mean(axis=0)
        th = np.arange(len(eh))*DT_HF; tl = np.arange(len(el))*DT_LF
        tg = np.arange(0, 39.0, DT_HF)
        A = np.interp(tg, th, eh); B = np.interp(tg, tl, el)
        n += 1
        for (a0,a1) in WINS:
            m = (tg>=a0)&(tg<a1)
            a = A[m]; b = B[m]
            if a.std()<1e-12 or b.std()<1e-12: continue
            a = (a-a.mean())/a.std(); b = (b-b.mean())/b.std()
            cc = np.correlate(b, a, 'full'); lags = np.arange(-len(a)+1,len(a))*DT_HF
            k = np.abs(lags) < 6.0
            j = int(np.argmax(cc[k])); lag = lags[k][j]; r = cc[k][j]/len(a)
            if r > 0.4: acc[(a0,a1)].append(lag)
import statistics as st
print('Lag of LF behind HF, measured in successive time windows, %d line pairs\n' % n)
print('%-12s %6s %9s %9s   %s' % ('window ns','n','median','sd','depth equiv at v=0.12'))
xs, ys = [], []
for w in WINS:
    v = acc[w]
    if len(v) < 20: print('%-12s %6d  (too few correlated)'%('%g-%g'%w, len(v))); continue
    m = st.median(v)
    print('%-12s %6d %9.3f %9.3f   %6.1f cm' % ('%g-%g'%w, len(v), m, st.pstdev(v), m*0.12/2*100))
    xs.append((w[0]+w[1])/2); ys.append(m)
xs = np.array(xs); ys = np.array(ys)
sl, ic = np.polyfit(xs, ys, 1)
print('\nlinear fit  lag(t) = %.5f * t + %.4f ns' % (sl, ic))
print('  a constant offset (time-zero / wavelet phase) predicts slope 0')
print('  a velocity difference predicts slope = 1 - v_LF/v_HF, intercept 0')
print('  implied v ratio if all slope: v_LF/v_HF = %.4f' % (1-sl))
print('  constant part %.3f ns = %.1f cm at v=0.12' % (ic, ic*0.12/2*100))
