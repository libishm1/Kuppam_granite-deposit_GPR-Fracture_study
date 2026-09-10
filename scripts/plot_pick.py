import sys, os, glob
sys.path.insert(0, os.path.dirname(__file__))
import segy, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import hilbert
ROOT = r'D:/code_ws/reference/parsans/report/raw/GPR Raw data_Kuppam'

def load(blk, ln, ch):
    g = sorted(glob.glob(os.path.join(ROOT, blk, '**', '*new%03d_*_%s.sgy' % (ln, ch)), recursive=True))
    return segy.read(g[0]), g[0]

def agc(d, w=64):
    e = np.abs(hilbert(d, axis=1))
    k = np.ones(w) / w
    sm = np.apply_along_axis(lambda r: np.convolve(r, k, 'same'), 1, e)
    return d / (sm + 1e-9 * sm.max())

def panel(ax, d, dt, dx_cm, vdisp, title, tmax=None):
    a = agc(d)
    n, ns = a.shape
    t = np.arange(ns) * dt
    if tmax: ns = int(tmax / dt); a = a[:, :ns]; t = t[:ns]
    z = t * vdisp / 2.0
    cl = np.percentile(np.abs(a), 98)
    ax.imshow(a.T, aspect='auto', cmap='gray_r', vmin=-cl, vmax=cl,
              extent=[0, n * dx_cm, z[-1], 0])
    ax.set_title(title, fontsize=9)
    ax.set_xlabel('position along line (cm)', fontsize=8)
    ax.set_ylabel('depth (m) at v=%.4f' % vdisp, fontsize=8)
    ax.tick_params(labelsize=7)

# ---- Block C, Line 21 HF: the C-1 pick the report shows in Figure 22 ----
r, f = load('C Block', 21, 'HF')
d = r['data']; dt = 0.0610352
dx = 249.0 / 100.0 * 100 / 100  # cm per trace
dx = 2.49
print('Line 21 HF:', os.path.basename(f), 'ntr', r['ntr'], 'length', round(r['ntr']*2.49,1), 'cm')

fig, axes = plt.subplots(2, 1, figsize=(11, 8.2), constrained_layout=True)
for ax, vd, lab in [(axes[0], 0.12, 'tables (RDP 6.25)'), (axes[1], 0.13416, 'app default (RDP 5.0)')]:
    panel(ax, d, dt, dx, vd, 'Block C Line 21 HF  (Y-line, x=150 cm)  depth axis at %s' % lab, tmax=20)
    # report pick, Table C-1 row for Line 21: y 49->294 cm, TWT 2.68->11.83 ns
    yy = np.array([49, 294]); tt = np.array([2.68, 11.83])
    ax.plot(yy, tt * vd / 2, 'r-o', lw=2, ms=5, label='report pick as printed (y 49->294)')
    L = r['ntr'] * dx
    ax.plot(L - yy, tt * vd / 2, 'c--s', lw=2, ms=5, label='same pick if the scan ran the other way')
    ax.legend(fontsize=7, loc='lower left')
fig.savefig('figs/C_line21_HF_pick.png', dpi=135)
print('wrote figs/C_line21_HF_pick.png')
