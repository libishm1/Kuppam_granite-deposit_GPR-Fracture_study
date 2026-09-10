import sys, os, glob
sys.path.insert(0, os.path.dirname(__file__))
import segy, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import hilbert
ROOT = r'D:/code_ws/reference/parsans/report/raw/GPR Raw data_Kuppam'
def load(blk, ln, ch):
    g = sorted(glob.glob(os.path.join(ROOT, blk, '**', '*new%03d_*_%s.sgy'%(ln,ch)), recursive=True))
    return segy.read(g[0])
def agc(d, w=64):
    e = np.abs(hilbert(d, axis=1)); k = np.ones(w)/w
    sm = np.apply_along_axis(lambda r: np.convolve(r, k, 'same'), 1, e)
    return d/(sm+1e-9*sm.max())
def panel(ax, d, dt, dx, v, ttl, tmax):
    a = agc(d); n, ns = a.shape
    t = np.arange(ns)*dt; m = int(tmax/dt); a = a[:,:m]; t = t[:m]
    cl = np.percentile(np.abs(a), 98)
    ax.imshow(a.T, aspect='auto', cmap='gray_r', vmin=-cl, vmax=cl,
              extent=[0, n*dx, t[-1]*v/2, 0])
    ax.set_title(ttl, fontsize=9); ax.tick_params(labelsize=7)
    ax.set_xlabel('along line (cm)', fontsize=8); ax.set_ylabel('depth m @ v=%.3f'%v, fontsize=8)

# C-2 on Line 22 LF (Y-line x=200) and Line 11 LF (X-line y=500), the report's own figures 28/29
fig, ax = plt.subplots(2,1, figsize=(11,8.4), constrained_layout=True)
for a,(ln,ttl,tw) in zip(ax, [(22,'Block C Line 22 LF (Y-line, x=200 cm) - report Fig 28', (49.78,56.12)),
                              (11,'Block C Line 11 LF (X-line, y=500 cm) - report Fig 29', (49.78,55.02))]):
    r = load('C Block', ln, 'LF'); d = r['data']
    panel(a, d, 0.1220703, 2.49, 0.12, ttl, 80)
    L = r['ntr']*2.49
    a.axhspan(tw[0]*0.06, tw[1]*0.06, color='r', alpha=0.18)
    a.axhline(tw[0]*0.06, color='r', lw=1); a.axhline(tw[1]*0.06, color='r', lw=1)
    a.text(10, tw[0]*0.06-0.12, 'report C-2 band %.2f-%.2f m (TWT %.1f-%.1f ns)'%(tw[0]*0.06,tw[1]*0.06,tw[0],tw[1]),
           color='r', fontsize=8)
fig.savefig('figs/C_C2_LF_lines22_11.png', dpi=130)
print('wrote figs/C_C2_LF_lines22_11.png')

# HF vs LF direct wave on the SAME line, zoomed to first 8 ns
fig2, ax2 = plt.subplots(1,2, figsize=(12,4.6), constrained_layout=True)
for a,(ch,dt,off) in zip(ax2, [('HF',0.0610352,7.0), ('LF',0.1220703,24.4)]):
    r = load('C Block', 21, ch); d = r['data']
    rms = d.std(axis=0); t = np.arange(len(rms))*dt
    nf = np.median(rms[-150:])
    a.semilogy(t, rms, 'k-', lw=1)
    a.axhline(nf, color='0.6', ls=':', label='deep noise floor')
    a.axhline(nf*20, color='b', ls='--', label='20x noise floor')
    i = int(np.argmax(rms > nf*20))
    a.axvline(t[i], color='b', lw=1)
    a.axvline(off/100/0.299792458, color='g', lw=1.4, label='air wave over %.1f cm offset'%off)
    a.axvline(t[int(np.argmax(rms))], color='r', lw=1.4, label='peak of direct wave')
    a.set_xlim(0, 8); a.set_title('Block C Line 21  %s  onset %.2f ns, peak %.2f ns'%(ch, t[i], t[int(np.argmax(rms))]), fontsize=9)
    a.set_xlabel('two-way time (ns)', fontsize=8); a.set_ylabel('RMS across traces', fontsize=8)
    a.legend(fontsize=7); a.tick_params(labelsize=7); a.grid(alpha=.3)
fig2.savefig('figs/direct_wave_HF_vs_LF.png', dpi=130)
print('wrote figs/direct_wave_HF_vs_LF.png')
