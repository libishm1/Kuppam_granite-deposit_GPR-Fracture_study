import sys, os, glob
sys.path.insert(0, os.path.dirname(__file__))
import segy, numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ROOT = r'D:/code_ws/reference/parsans/report/raw/GPR Raw data_Kuppam'
res = {}
fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), constrained_layout=True)
for ax, (ch, dt) in zip(axes, [('HF', 0.0610352e-9), ('LF', 0.1220703e-9)]):
    acc = None; n = 0
    for blk in ['A Block','B Block','C Block']:
        for f in sorted(glob.glob(os.path.join(ROOT, blk, '**', '*_%s.sgy'%ch), recursive=True)):
            d = segy.read(f)['data']
            w = d[:, :int(round(6e-9/dt))]              # direct-wave window, 6 ns
            w = w * np.hanning(w.shape[1])
            S = np.abs(np.fft.rfft(w, n=4096, axis=1)).mean(axis=0)
            acc = S if acc is None else acc + S; n += 1
    S = acc/n; fr = np.fft.rfftfreq(4096, dt)/1e6        # MHz
    S = S/S.max()
    pk = fr[np.argmax(S)]
    half = S >= 0.5; lo, hi = fr[half][0], fr[half][-1]
    q = S >= 10**(-0.5)  # -10 dB approx (0.316)
    q = S >= 0.1
    res[ch] = dict(peak=pk, f_lo_6dB=lo, f_hi_6dB=hi, bw=hi-lo, n=n,
                   f_lo_20dB=fr[q][0], f_hi_20dB=fr[q][-1])
    ax.plot(fr, 20*np.log10(S+1e-12), 'k-', lw=1.2)
    ax.axvline(pk, color='r', label='peak %.0f MHz'%pk)
    ax.axvspan(lo, hi, color='b', alpha=.15, label='-6 dB %.0f-%.0f MHz'%(lo,hi))
    ax.set_xlim(0, 4000 if ch=='HF' else 2000); ax.set_ylim(-45, 2)
    ax.set_title('%s channel mean amplitude spectrum, %d lines'%(ch,n), fontsize=10)
    ax.set_xlabel('frequency (MHz)'); ax.set_ylabel('dB'); ax.legend(fontsize=8); ax.grid(alpha=.3)
fig.savefig('figs/spectra_HF_LF.png', dpi=130)
import json; json.dump({ch: {k: round(float(v), 1) for k, v in r.items()} for ch, r in res.items()}, open('tables/spectra.json', 'w'), indent=1)
print('wrote figs/spectra_HF_LF.png\n')
for ch in ['HF','LF']:
    r = res[ch]
    print('%s  peak %.0f MHz   -6dB %.0f-%.0f MHz (bw %.0f)   -20dB %.0f-%.0f MHz  [%d lines]'
          % (ch, r['peak'], r['f_lo_6dB'], r['f_hi_6dB'], r['bw'], r['f_lo_20dB'], r['f_hi_20dB'], r['n']))
    for v in [0.1174, 0.12]:
        lam = v/(r['peak']/1000.0)
        print('     at v=%.4f m/ns: lambda %.1f cm, quarter-wavelength resolution %.1f cm, half-period %.3f ns'
              % (v, lam*100, lam/4*100, 0.5/(r['peak']/1000.0)))
