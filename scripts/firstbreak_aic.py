import sys, os, glob, csv
sys.path.insert(0, os.path.dirname(__file__))
import segy, numpy as np
ROOT = r'D:/code_ws/reference/parsans/report/raw/GPR Raw data_Kuppam'
C = 0.299792458

def aic_pick(x):
    """Maeda AIC picker. Returns index of the minimum of the AIC function."""
    n = len(x)
    k = np.arange(1, n - 1)
    v1 = np.array([x[:i + 1].var() for i in k])
    v2 = np.array([x[i + 1:].var() for i in k])
    v1[v1 <= 0] = 1e-30; v2[v2 <= 0] = 1e-30
    aic = k * np.log(v1) + (n - k - 1) * np.log(v2)
    return int(k[np.argmin(aic)])

rows = []
for blk in ['A Block', 'B Block', 'C Block']:
    for ch, dt, off in [('HF', 0.0610352, 0.070), ('LF', 0.1220703, 0.244)]:
        for f in sorted(glob.glob(os.path.join(ROOT, blk, '**', '*_%s.sgy' % ch), recursive=True)):
            r = segy.read(f); d = r['data']
            st = d.mean(axis=0)                     # stack the line
            nwin = int(round(10.0 / dt))            # first 10 ns
            i = aic_pick(st[:nwin])
            rows.append(dict(block=blk[0], ch=ch,
                             line=os.path.basename(os.path.dirname(f))[:38],
                             onset_smp=i, onset_ns=round(i * dt, 4),
                             airwave_ns=round(off / C, 4),
                             t0_ns=round(i * dt - off / C, 4)))
w = csv.DictWriter(open('tables/firstbreak_aic.csv','w',newline='',encoding='utf-8'),
                   fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
import statistics as st_
print('AIC first break on the line-stacked trace, first 10 ns\n')
print('%-3s %-3s %4s %10s %10s %10s %10s' % ('blk','ch','n','onset med','onset sd','airwave','t0 = onset-air'))
sm = {}
for b in 'ABC':
    for ch in ['HF','LF']:
        s = [r for r in rows if r['block']==b and r['ch']==ch]
        o = [r['onset_ns'] for r in s]
        print('%-3s %-3s %4d %10.3f %10.3f %10.3f %10.3f' %
              (b, ch, len(s), st_.median(o), st_.pstdev(o), s[0]['airwave_ns'], st_.median(o)-s[0]['airwave_ns']))
        sm.setdefault(ch, []).extend(o)
print()
for ch, off in [('HF',0.070), ('LF',0.244)]:
    o = sm[ch]
    print('ALL %-3s %4d %10.3f %10.3f %10.3f %10.3f' %
          (ch, len(o), st_.median(o), st_.pstdev(o), off/C, st_.median(o)-off/C))
t0h = st_.median(sm['HF']) - 0.070/C
t0l = st_.median(sm['LF']) - 0.244/C
print('\n  system time zero, HF  = %+.3f ns  ->  depth bias %+.1f cm at v=0.12' % (t0h, t0h*0.06*100))
print('  system time zero, LF  = %+.3f ns  ->  depth bias %+.1f cm at v=0.12' % (t0l, t0l*0.06*100))
print('  LF minus HF           = %+.3f ns  ->  %+.1f cm' % (t0l-t0h, (t0l-t0h)*0.06*100))
