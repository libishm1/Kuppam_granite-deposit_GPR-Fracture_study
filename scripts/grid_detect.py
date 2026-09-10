"""Detect a painted 0.5 m grid in a bench-plane raster: angle, spacing (=> scale), line positions, corners.
usage: grid_detect.py TAG SOURCE   where SOURCE is 'paint' (mask fraction), 'lum' or 'red' (local-contrast)."""
import numpy as np, os, sys, json
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter, maximum_filter, label
from scipy.signal import find_peaks
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
tag = sys.argv[1]; src = sys.argv[2] if len(sys.argv) > 2 else 'paint'
d = np.load(os.path.join(OUT, 'tables', 'paint_raster_%s.npz' % tag))
x0, y0, px = float(d['x0']), float(d['y0']), float(d['px']); cnt = d['cnt']
if src == 'paint':
    F = d['paint'] * (cnt > 0)
else:
    r = np.load(os.path.join(OUT, 'tables', 'redness_%s.npz' % tag)); F = np.clip(r['redc' if src == 'red' else 'lumc'], 0, None)
NY, NX = F.shape
# --- locate the grid: explicit region (local units) if given, else densest region of signal ---
if len(sys.argv) >= 7:
    rx0, rx1, ry0, ry1 = map(float, sys.argv[3:7])
    cx0, cx1 = max(0, int((rx0 - x0) / px)), min(NX, int((rx1 - x0) / px))
    cy0, cy1 = max(0, int((ry0 - y0) / px)), min(NY, int((ry1 - y0) / px))
else:
    S = uniform_filter(F, 61)
    thr = np.percentile(S[cnt > 0], 97)
    lab, n = label(S > thr); sizes = np.bincount(lab.ravel()); sizes[0] = 0; big = sizes.argmax()
    yy, xx = np.nonzero(lab == big)
    pad = 60
    cy0, cy1 = max(0, yy.min() - pad), min(NY, yy.max() + pad); cx0, cx1 = max(0, xx.min() - pad), min(NX, xx.max() + pad)
W = F[cy0:cy1, cx0:cx1].copy(); W -= W.mean()
h, w = W.shape
print('Block %s [%s]: grid region local x %.2f..%.2f  y %.2f..%.2f  (%d x %d px)'
      % (tag, src, x0 + cx0 * px, x0 + cx1 * px, y0 + cy0 * px, y0 + cy1 * px, w, h))
# --- 2D spectrum -> the two lattice directions and spacing ---
win = np.outer(np.hanning(h), np.hanning(w))
P = np.abs(np.fft.fftshift(np.fft.fft2(W * win))) ** 2
ky = np.fft.fftshift(np.fft.fftfreq(h, px)); kx = np.fft.fftshift(np.fft.fftfreq(w, px))
KX, KY = np.meshgrid(kx, ky); K = np.hypot(KX, KY)
# plausible spacing: 0.5 m must be between 2% and 40% of the region width
kmin, kmax = 1.0 / (0.40 * w * px), 1.0 / (0.02 * w * px)
if len(sys.argv) >= 10:                                  # spacing prior in mesh units, +/-12%
    sp0 = float(sys.argv[9]); kmin, kmax = 1.0 / (1.12 * sp0), 1.0 / (0.88 * sp0)
    print('  spacing prior %.4f units: restricting spectral search to %.4f..%.4f' % (sp0, 0.88 * sp0, 1.12 * sp0))
P[(K < kmin) | (K > kmax)] = 0
P[KY < 0] = 0                                      # half plane
pk = (P == maximum_filter(P, 9)) & (P > 0.02 * P.max())
iy, ix = np.nonzero(pk); order = np.argsort(-P[iy, ix])[:12]
cands = [(np.degrees(np.arctan2(KY[iy[i], ix[i]], KX[iy[i], ix[i]])) % 180, 1.0 / K[iy[i], ix[i]], P[iy[i], ix[i]] / P.max()) for i in order]
print('  spectral peaks (angle deg, spacing units, rel power):')
for a, s, p in cands[:8]: print('    %6.1f  %.4f  %.2f' % (a, s, p))
# choose the strongest peak, then the strongest ~90 deg away
a1, s1, _ = cands[0]
rest = [c for c in cands[1:] if 70 < abs(((c[0] - a1) + 90) % 180 - 90) + 90 - 0 and abs(((c[0] - a1) % 180) - 90) < 20]
a2, s2, _ = rest[0] if rest else (a1 + 90, s1, 0)
# lattice line direction is perpendicular to the wave vector
theta = (a1 + 90) % 180        # direction of one family of lines
spacing = 0.5 * (s1 + s2)
scale = 0.5 / spacing          # metres per mesh unit
print('  wavevectors at %.1f and %.1f deg; spacings %.4f and %.4f units' % (a1, a2, s1, s2))
print('  => lines run at %.1f and %.1f deg; spacing %.4f units = 0.5 m  =>  SCALE %.4f m/unit (%.3f units/m)' % (theta, (theta + 90) % 180, spacing, scale, 1 / scale))
# --- rotate into lattice frame and find every line ---
Y, X = np.mgrid[cy0:cy1, cx0:cx1]; Xl = x0 + X * px; Yl = y0 + Y * px
t = np.radians(theta); c, s = np.cos(t), np.sin(t)
U = Xl * c + Yl * s; Vv = -Xl * s + Yl * c          # U along the line family at theta, V perpendicular
F0 = np.clip(F[cy0:cy1, cx0:cx1], 0, None)
def fold_phase(coord, weights, spacing, nb=48):
    """lattice phase: fold coordinate modulo spacing, the paint piles up at one phase"""
    ph = np.mod(coord, spacing)
    h, e = np.histogram(ph, nb, range=(0, spacing), weights=weights); n, _ = np.histogram(ph, nb, range=(0, spacing))
    prof = uniform_filter(h / np.maximum(n, 1), 3, mode='wrap')
    k = int(np.argmax(prof))
    return 0.5 * (e[k] + e[k + 1]), float(prof.max() / max(np.median(prof), 1e-9)), e, prof
def line_extent(coord, weights, phase, spacing, nexp=None):
    """score every lattice line of this family; the grid is the longest contiguous run of painted lines"""
    halfw = spacing / 10
    k = np.round((coord - phase) / spacing).astype(int)
    off = np.abs(coord - (phase + k * spacing))
    on = off < halfw
    mid = np.abs(off - spacing / 2) < spacing / 6          # the rock between lines
    ks = np.arange(k.min(), k.max() + 1)
    score = np.zeros(len(ks))
    for i, kk in enumerate(ks):
        m = on & (k == kk); r = mid & (k == kk)
        if m.sum() > 50 and r.sum() > 50: score[i] = weights[m].mean() - weights[r].mean()   # contrast, not brightness
    score = np.clip(score, 0, None)
    if nexp and len(ks) >= nexp:
        w = np.array([score[i:i + nexp].sum() for i in range(len(ks) - nexp + 1)])
        i = int(np.argmax(w)); run = ks[i:i + nexp]; q = w[i] / max(score.sum(), 1e-9)
    else:
        good = score > 0.35 * score.max()
        best = (0, 0, 0); i = 0
        while i < len(good):
            if good[i]:
                j = i
                while j < len(good) and good[j]: j += 1
                if j - i > best[0]: best = (j - i, i, j)
                i = j
            else: i += 1
        run = ks[best[1]:best[2]]; q = score[best[1]:best[2]].sum() / max(score.sum(), 1e-9)
    return phase + run * spacing, score, ks, q
Vf = Vv.ravel(); Uf = U.ravel(); Wf = F0.ravel()
phV, cV, eV, pV = fold_phase(Vf, Wf, spacing); phU, cU, eU, pU = fold_phase(Uf, Wf, spacing)
NEXP = (int(sys.argv[7]), int(sys.argv[8])) if len(sys.argv) >= 9 else (None, None)
trials = [(NEXP[0], NEXP[1])] + ([(NEXP[1], NEXP[0])] if NEXP[0] and NEXP[0] != NEXP[1] else [])
best = None
for nu, nv in trials:
    rU_, scU_, ksU_, qU = line_extent(Uf, Wf, phU, spacing, nu); rV_, scV_, ksV_, qV = line_extent(Vf, Wf, phV, spacing, nv)
    print('  trial U=%s V=%s lines: window captures %.0f%% / %.0f%% of line contrast' % (nu, nv, 100 * qU, 100 * qV))
    if best is None or qU + qV > best[0]: best = (qU + qV, rU_, scU_, ksU_, rV_, scV_, ksV_)
_, rU, scU, ksU, rV, scV, ksV = best
nV, nU = len(rV), len(rU)
print('  fold contrast (peak/median): V %.2f  U %.2f' % (cV, cU))
print('  lines at constant V (family @%.1f deg): %d contiguous painted lines -> %.2f m span' % (theta, nV, (nV - 1) * 0.5))
print('     line scores: ' + ' '.join('%.2f' % v for v in scV / max(scV.max(), 1e-9)))
print('  lines at constant U (family @%.1f deg): %d contiguous painted lines -> %.2f m span' % ((theta + 90) % 180, nU, (nU - 1) * 0.5))
print('     line scores: ' + ' '.join('%.2f' % v for v in scU / max(scU.max(), 1e-9)))
# refine spacing from the regular runs
sp = []
for r_ in (rV, rU):
    if len(r_) > 2: sp.append((r_[-1] - r_[0]) / round((r_[-1] - r_[0]) / spacing))
if sp: spacing = float(np.mean(sp)); scale = 0.5 / spacing
print('  refined spacing %.4f units  =>  SCALE %.4f m/unit' % (spacing, scale))
# corners in local plane coords (U,V) -> back to local x,y
corners_uv = [(rU[0], rV[0]), (rU[-1], rV[0]), (rU[-1], rV[-1]), (rU[0], rV[-1])]
corners_xy = [(u * c - v * s, u * s + v * c) for u, v in corners_uv]
print('  grid corners (local x,y): ' + ', '.join('(%.2f, %.2f)' % p for p in corners_xy))
print('  grid size %.2f x %.2f m' % ((rU[-1] - rU[0]) * scale, (rV[-1] - rV[0]) * scale))
json.dump(dict(tag=tag, src=src, theta_deg=float(theta), spacing_units=float(spacing), scale_m_per_unit=float(scale),
               lines_U=[float(v) for v in rU], lines_V=[float(v) for v in rV], corners_xy=[[float(a), float(b)] for a, b in corners_xy],
               R=d['R'].tolist(), c=d['c'].tolist()),
          open(os.path.join(OUT, 'tables', 'grid_%s_%s.json' % (tag, src)), 'w'), indent=1)
fig, ax = plt.subplots(1, 2, figsize=(15, 7), constrained_layout=True)
ax[0].imshow(F0, origin='lower', extent=[x0 + cx0 * px, x0 + cx1 * px, y0 + cy0 * px, y0 + cy1 * px], cmap='gray')
for v in rV:
    uu = np.array([U.min(), U.max()]); ax[0].plot(uu * c - v * s, uu * s + v * c, 'r-', lw=.6)
for u in rU:
    vv = np.array([Vv.min(), Vv.max()]); ax[0].plot(u * c - vv * s, u * s + vv * c, 'c-', lw=.6)
cx = [p[0] for p in corners_xy] + [corners_xy[0][0]]; cy = [p[1] for p in corners_xy] + [corners_xy[0][1]]
ax[0].plot(cx, cy, 'y-', lw=2); ax[0].set_title('Block %s: detected lattice, %d x %d lines, spacing %.4f u = 0.5 m' % (tag, nU, nV, spacing), fontsize=10)
ax[1].plot(eV[:-1], pV, 'r-', lw=.8, label='profile across V'); ax[1].plot(eU[:-1] - eU[0] + eV[0], pU, 'c-', lw=.8, label='profile across U (shifted)')
for v in rV: ax[1].axvline(v, color='r', lw=.4, alpha=.5)
ax[1].legend(fontsize=8); ax[1].set_title('line profiles', fontsize=10)
fig.savefig(os.path.join(OUT, 'figs', 'grid_%s_%s.png' % (tag, src)), dpi=110); print('  wrote figs/grid_%s_%s.png' % (tag, src))
