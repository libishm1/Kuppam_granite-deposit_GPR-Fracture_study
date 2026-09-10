import sys, os, glob, csv
sys.path.insert(0, os.path.dirname(__file__))
import segy, numpy as np
from scipy.signal import hilbert
ROOT = r'D:/code_ws/reference/parsans/report/raw/GPR Raw data_Kuppam'
DX = 2.49  # cm per trace

CFG = {  # block: (Xfam lines, Xfam y0 step, Yfam lines, Yfam x0 step)
 'A Block': dict(fam1=range(1,13), fam2=range(13,25), step=50.0, tag='A'),
 'B Block': dict(fam1=range(1,14), fam2=range(14,34), step=50.0, tag='B'),
 'C Block': dict(fam1=range(1,18), fam2=range(18,33), step=50.0, tag='C'),
}
def load(blk, ln, ch='HF'):
    g = sorted(glob.glob(os.path.join(ROOT, blk, '**', '*new%03d_*_%s.sgy'%(ln,ch)), recursive=True))
    return segy.read(g[0])['data']
def prep(d, dt=0.0610352, t0=1.0, t1=12.0):
    e = np.abs(hilbert(d, axis=1))
    w = np.ones(int(3.0/dt))/int(3.0/dt)
    sm = np.apply_along_axis(lambda r: np.convolve(r, w, 'same'), 1, e)
    a = e/(sm+1e-12)
    i0, i1 = int(t0/dt), int(t1/dt)
    return a[:, i0:i1]

out = []
for blk, cfg in CFG.items():
    F1 = {n: prep(load(blk, n)) for n in cfg['fam1']}
    F2 = {n: prep(load(blk, n)) for n in cfg['fam2']}
    n1, n2 = list(cfg['fam1']), list(cfg['fam2'])
    for p in n1:
        for q in n2:
            # family-1 line p is crossed by family-2 line q at along-line distance (q - n2[0]) * step
            a_idx = (q - n2[0]) * cfg['step'] / DX
            b_idx = (p - n1[0]) * cfg['step'] / DX
            A, B = F1[p], F2[q]
            ia, ib = int(round(a_idx)), int(round(b_idx))
            if not (0 <= ia < len(A) and 0 <= ib < len(B)): continue
            best = (-9, 0)
            W = 8   # +/- 8 traces = +/- 20 cm search
            for s in range(-W, W+1):
                j = ib + s
                if not (0 <= j < len(B)): continue
                x, y = A[ia], B[j]
                if x.std() < 1e-9 or y.std() < 1e-9: continue
                r = float(np.corrcoef(x, y)[0,1])
                if r > best[0]: best = (r, s)
            r0 = float(np.corrcoef(A[ia], B[ib])[0,1]) if A[ia].std()>1e-9 and B[ib].std()>1e-9 else np.nan
            out.append(dict(block=cfg['tag'], l1=p, l2=q, r_nominal=round(r0,4),
                            r_best=round(best[0],4), shift_cm=round(best[1]*DX,2)))
w = csv.DictWriter(open('tables/tie_crossings.csv','w',newline='',encoding='utf-8'),
                   fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
import statistics as st
print('Tie-point check: HF envelope trace at every X-line / Y-line crossing, 1-12 ns window')
print('r_nominal = correlation at the crossing the published grid implies\n')
print('%-6s %6s %10s %10s %10s %12s'%('block','n','r nominal','r best','gain','|shift| median'))
for t in 'ABC':
    s=[o for o in out if o['block']==t]
    rn=[o['r_nominal'] for o in s if o['r_nominal']==o['r_nominal']]
    rb=[o['r_best'] for o in s]
    sh=[abs(o['shift_cm']) for o in s]
    print('%-6s %6d %10.3f %10.3f %10.3f %10.1f cm'%(t,len(s),st.median(rn),st.median(rb),
                                                     st.median(rb)-st.median(rn), st.median(sh)))
print('\nfraction of crossings whose nominal correlation is below 0.3 (no coherent match):')
for t in 'ABC':
    s=[o for o in out if o['block']==t and o['r_nominal']==o['r_nominal']]
    print('  %s  %.0f%%  (%d of %d)'%(t, 100*sum(1 for o in s if o['r_nominal']<0.3)/len(s),
                                      sum(1 for o in s if o['r_nominal']<0.3), len(s)))
