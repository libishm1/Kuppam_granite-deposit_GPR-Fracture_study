import sys, os, glob, csv
sys.path.insert(0, os.path.dirname(__file__))
import segy, numpy as np
ROOT = r'D:/code_ws/reference/parsans/report/raw/GPR Raw data_Kuppam'
C = 0.299792458  # m/ns

out = []
for blk in ['A Block', 'B Block', 'C Block']:
    for ch, dt_ps, off_cm in [('HF', 61.035, 7.0), ('LF', 122.07, 24.4)]:
        fs = sorted(glob.glob(os.path.join(ROOT, blk, '**', '*_%s.sgy' % ch), recursive=True))
        for f in fs:
            r = segy.read(f)
            d = r['data']
            mn = d.mean(axis=0)                      # mean trace over the line
            n = len(mn)
            t = np.arange(n) * dt_ps / 1000.0        # ns
            a = np.abs(mn)
            pk = int(np.argmax(a))                   # global max = direct wave
            # first sample exceeding 5% of peak (first break)
            thr = 0.05 * a[pk]
            fb = int(np.argmax(a[:pk + 1] >= thr)) if a[:pk+1].max() >= thr else 0
            # first zero crossing before the peak, sub-sample
            zc = None
            for i in range(pk, 0, -1):
                if mn[i] * mn[i - 1] < 0:
                    zc = (i - 1) + mn[i - 1] / (mn[i - 1] - mn[i]); break
            out.append(dict(block=blk[0], ch=ch, line=os.path.basename(os.path.dirname(f))[:40],
                            ntr=r['ntr'], ns=n,
                            pk_smp=pk, pk_ns=round(t[pk], 4),
                            fb_smp=fb, fb_ns=round(t[fb], 4),
                            zc_ns=round(zc * dt_ps / 1000.0, 4) if zc else None,
                            pk_amp=round(float(mn[pk]), 2),
                            t_air_ns=round(off_cm / 100.0 / C, 4)))
w = csv.DictWriter(open('tables/first_break.csv', 'w', newline='', encoding='utf-8'),
                   fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)

import statistics as st
print('%-3s %-3s %5s | %-28s | %-28s | %-28s' % ('blk','ch','n','peak of direct wave (ns)','first break 5%% (ns)','last zero-cross before pk'))
for b in 'ABC':
    for ch in ['HF','LF']:
        s=[o for o in out if o['block']==b and o['ch']==ch]
        f=lambda k: '%6.3f med %6.3f-%6.3f'%(st.median([o[k] for o in s]), min(o[k] for o in s), max(o[k] for o in s))
        print('%-3s %-3s %5d | %-28s | %-28s | %-28s'%(b,ch,len(s),f('pk_ns'),f('fb_ns'),f('zc_ns')))
print()
print('expected air-wave one-way traveltime over antenna offset:')
print('  HF  7.0 cm ->', round(0.070/C,4),'ns')
print('  LF 24.4 cm ->', round(0.244/C,4),'ns')
