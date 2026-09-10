"""Block C: re-raster the grid region from the FULL 21.5M-vertex mesh, using the plane frame
already found on the decimated one. Writes paint_raster_Cfull.npz and redness_Cfull.npz so
grid_detect.py works on tag 'Cfull' unchanged."""
import numpy as np, os, time
from scipy.ndimage import uniform_filter
SITE = r'D:/code_ws/reference/parsans/site'; OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
d = np.load(os.path.join(OUT, 'tables', 'paint_raster_C.npz'))
R, c = d['R'], d['c']
X0, X1, Y0, Y1 = -4.0, 15.0, -11.0, 8.0          # local plane region holding the C grid, with margin
BAND = 0.6                                       # +/- units about the bench plane
PX = 0.012                                       # units per pixel, ~4x finer than the decimated raster
NX = int((X1 - X0) / PX) + 1; NY = int((Y1 - Y0) / PX) + 1
img = np.zeros((NY, NX, 3)); cnt = np.zeros((NY, NX)); kept = 0; total = 0; t = time.time()
with open(os.path.join(SITE, 'block c.obj'), 'rb') as f:
    buf = []
    def flush(buf):
        global kept, total
        if not buf: return
        a = np.array(b' '.join(buf).split(), dtype=float).reshape(-1, 6)
        total += len(a)
        L = (a[:, :3] - c) @ R.T
        m = (np.abs(L[:, 2]) < BAND) & (L[:, 0] >= X0) & (L[:, 0] < X1) & (L[:, 1] >= Y0) & (L[:, 1] < Y1)
        if not m.any(): return
        ix = ((L[m, 0] - X0) / PX).astype(int); iy = ((L[m, 1] - Y0) / PX).astype(int)
        np.add.at(img, (iy, ix), a[m, 3:6]); np.add.at(cnt, (iy, ix), 1); kept += int(m.sum())
    for ln in f:
        if ln[:2] == b'v ':
            buf.append(ln[2:].strip())
            if len(buf) >= 1_500_000: flush(buf); buf = []
    flush(buf)
print('streamed %d vertices, kept %d in the grid region, %.0f s' % (total, kept, time.time() - t))
img = img / np.maximum(cnt, 1)[..., None]; img[cnt == 0] = 0.08
has = cnt > 0
Rc, G, B = img[..., 0], img[..., 1], img[..., 2]
red = np.where(has, Rc - 0.5 * (G + B), 0)
m = uniform_filter(np.where(has, red, 0), 61) / np.maximum(uniform_filter(has.astype(float), 61), 1e-6)
redc = np.where(has, red - m, 0)
lum = np.where(has, img.mean(2), 0)
ml = uniform_filter(np.where(has, lum, 0), 61) / np.maximum(uniform_filter(has.astype(float), 61), 1e-6)
lumc = np.where(has, lum - ml, 0)
mx = img.max(2); mn = img.min(2)
paint = (((mn > 0.70) & ((mx - mn) < 0.14)) | ((Rc > 0.42) & ((Rc - np.maximum(G, B)) > 0.14))).astype(float) * has
np.savez_compressed(os.path.join(OUT, 'tables', 'paint_raster_Cfull.npz'), img=img, paint=paint, cnt=cnt, x0=X0, y0=Y0, px=PX, R=R, c=c, band=BAND)
np.savez_compressed(os.path.join(OUT, 'tables', 'redness_Cfull.npz'), redc=redc, lumc=lumc, x0=X0, y0=Y0, px=PX)
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 2, figsize=(16, 8.4), constrained_layout=True)
ax[0].imshow(img, origin='lower', extent=[X0, X1, Y0, Y1]); ax[0].set_title('Block C grid region, full mesh, %.3f u/px' % PX, fontsize=10)
v = np.percentile(redc[has], 99)
ax[1].imshow(redc, origin='lower', extent=[X0, X1, Y0, Y1], cmap='Reds', vmin=0, vmax=max(v, 0.02)); ax[1].set_title('redness above local mean', fontsize=10)
fig.savefig(os.path.join(OUT, 'figs', 'paint_raster_Cfull.png'), dpi=110); print('wrote figs/paint_raster_Cfull.png  (%d x %d px)' % (NX, NY))
