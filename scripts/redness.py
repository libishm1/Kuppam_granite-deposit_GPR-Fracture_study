"""Continuous redness / whiteness rasters from the saved bench-plane npz, for B and C."""
import numpy as np, os
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
for tag in ('B', 'C', 'A'):
    d = np.load(os.path.join(OUT, 'tables', 'paint_raster_%s.npz' % tag))
    img, cnt, x0, y0, px = d['img'], d['cnt'], float(d['x0']), float(d['y0']), float(d['px'])
    NY, NX = cnt.shape; x1 = x0 + NX * px; y1 = y0 + NY * px
    has = cnt > 0
    R, G, B = img[..., 0], img[..., 1], img[..., 2]
    red = np.where(has, R - 0.5 * (G + B), 0)
    # local contrast: subtract a wide local mean so paint stands out against the rock tone
    m = uniform_filter(np.where(has, red, 0), 41) / np.maximum(uniform_filter(has.astype(float), 41), 1e-6)
    redc = np.where(has, red - m, 0)
    lum = np.where(has, img.mean(2), 0)
    ml = uniform_filter(np.where(has, lum, 0), 41) / np.maximum(uniform_filter(has.astype(float), 41), 1e-6)
    lumc = np.where(has, lum - ml, 0)
    np.savez_compressed(os.path.join(OUT, 'tables', 'redness_%s.npz' % tag), redc=redc, lumc=lumc, x0=x0, y0=y0, px=px)
    v = np.percentile(redc[has], [50, 90, 99, 99.9])
    print('Block %s redness (local-contrast): p50 %.3f p90 %.3f p99 %.3f p99.9 %.3f' % (tag, *v))
    # where are the reddest pixels?
    thr = v[2]; yy, xx = np.nonzero(redc > thr)
    if len(xx):
        X = x0 + xx * px; Y = y0 + yy * px
        print('   top-1%% red pixels: %d, centroid (%.1f, %.1f), 10-90%% x %.1f..%.1f  y %.1f..%.1f'
              % (len(xx), X.mean(), Y.mean(), *np.percentile(X, [10, 90]), *np.percentile(Y, [10, 90])))
    fig, ax = plt.subplots(1, 2, figsize=(16, 8 * NY / NX + 0.8), constrained_layout=True)
    ax[0].imshow(redc, origin='lower', extent=[x0, x1, y0, y1], cmap='Reds', vmin=0, vmax=max(v[2], 0.02))
    ax[0].set_title('Block %s: redness above local mean (paint = red)' % tag, fontsize=10)
    ax[1].imshow(lumc, origin='lower', extent=[x0, x1, y0, y1], cmap='gray', vmin=-0.05, vmax=0.12)
    ax[1].set_title('luminance above local mean (paint = white)', fontsize=10)
    for a in ax: a.set_xlabel('local x'); a.set_ylabel('local y'); a.tick_params(labelsize=7)
    fig.savefig(os.path.join(OUT, 'figs', 'redness_%s.png' % tag), dpi=110); print('   wrote figs/redness_%s.png' % tag)
