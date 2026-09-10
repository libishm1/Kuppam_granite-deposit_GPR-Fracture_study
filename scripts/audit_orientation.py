"""Orientation audit of what the interface shows. Independent of three.js.
1. Baked texture vs lattice: the paint must sit on the image's own 0.5 m lines (score, and shift search).
2. Plan figure per block in the report frame: texture + lattice + chalked cracks + GPR daylight/contours + block outlines.
3. Oblique matplotlib render of texture on the DEM with the v2 surfaces and packed blocks."""
import numpy as np, json, os, csv
from PIL import Image
from scipy.ndimage import uniform_filter
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
DIMS = {'A': (5.5, 5.5), 'B': (9.5, 6.0), 'C': (7.0, 8.0)}
FEATS = {'A': ('A1', 'A2'), 'B': ('B1', 'B2'), 'C': ('C1', 'C2')}
PAINT = {'A': 'white', 'B': 'red', 'C': 'red'}
meta = json.load(open(os.path.join(OUT, 'web', 'tex', 'meta.json'))); PX = meta['px_m']; PAD = meta['pad_m']
PACK = json.load(open(os.path.join(OUT, 'tables', 'block_packing.json')))
CLSCOL = {'gangsaw_large': '#1b7f3b', 'gangsaw_standard': '#57a639', 'small_block': '#e0a400', 'cutter_block': '#c96a1b'}
res = {}
for blk in 'ABC':
    W, H = DIMS[blk]
    im = np.asarray(Image.open(os.path.join(OUT, 'web', 'tex', 'bench_%s.jpg' % blk))).astype(float) / 255
    ny, nx = im.shape[:2]
    X = (np.arange(nx) + 0.5) * PX - PAD; Y = (np.arange(ny) + 0.5) * PX - PAD          # report metres at pixel centres
    # paint signal
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    sig = (r - 0.5 * (g + b)) if PAINT[blk] == 'red' else (im.min(2) - 0.55)
    sig = sig - uniform_filter(sig, 61)                                                     # local contrast
    inside = (X[None, :] > 0.1) & (X[None, :] < W - 0.1) & (Y[:, None] > 0.1) & (Y[:, None] < H - 0.1)
    # distance to nearest lattice line, for a range of trial shifts (the truth test: best shift should be ~0)
    def score(dx, dy):
        Dx = np.abs(((X + dx) % 0.5) - 0.25); Dy = np.abs(((Y + dy) % 0.5) - 0.25)        # 0.25 on a line, 0 mid-cell
        on = (Dx[None, :] > 0.21) | (Dy[:, None] > 0.21)                                     # within 4 cm of a line
        off = (Dx[None, :] < 0.12) & (Dy[:, None] < 0.12)
        return float(sig[on & inside].mean() - sig[off & inside].mean())
    shifts = np.arange(-0.25, 0.2501, 0.05); S = np.array([[score(dx, dy) for dx in shifts] for dy in shifts])
    j, i = np.unravel_index(int(np.argmax(S)), S.shape); s0 = score(0, 0)
    res[blk] = dict(paint_contrast_at_zero=round(s0, 4), best_shift_m=[round(float(shifts[i]), 2), round(float(shifts[j]), 2)], best_contrast=round(float(S[j, i]), 4),
                    ratio_zero_to_best=round(s0 / max(float(S[j, i]), 1e-9), 3))
    print('Block %s texture vs its own lattice: paint contrast on-line minus mid-cell = %+.4f at zero shift; best over +/-25 cm is %+.4f at shift (%.2f, %.2f) m  -> %s'
          % (blk, s0, S[j, i], shifts[i], shifts[j], 'ALIGNED' if abs(shifts[i]) <= 0.05 and abs(shifts[j]) <= 0.05 else 'MISALIGNED'))
    # ---- plan figure ----
    fig, ax = plt.subplots(figsize=(9, 9 * (H + 2 * PAD) / (W + 2 * PAD)))
    ax.imshow(im, extent=[-PAD, W + PAD, -PAD, H + PAD], origin='lower')
    for k in np.arange(0, W + 0.01, 0.5): ax.axvline(k, color='#00e5ff', lw=0.5, alpha=0.7)
    for k in np.arange(0, H + 0.01, 0.5): ax.axhline(k, color='#00e5ff', lw=0.5, alpha=0.7)
    ax.plot([0, W, W, 0, 0], [0, 0, H, H, 0], 'y-', lw=2)
    ax.plot([0, 1], [0, 0], 'r-', lw=4); ax.plot([0, 0], [0, 1], 'g-', lw=4); ax.plot(0, 0, 'o', mfc='none', mec='yellow', mew=2, ms=14)
    ax.text(0.05, -0.35, '%s0 ⊕  x→ red  y→ green' % blk, color='yellow', fontsize=9, weight='bold')
    tr = {}
    for q in csv.DictReader(open(os.path.join(OUT, 'tables', 'sketch_chained_%s.csv' % blk), encoding='utf-8')): tr.setdefault(int(q['trace_id']), []).append((float(q['x_cm']) / 100, float(q['y_cm']) / 100))
    for v in tr.values(): v = np.array(v); ax.plot(v[:, 0], v[:, 1], '-', color='#2457E6', lw=1.8)
    dem = np.loadtxt(os.path.join(OUT, 'model', 'v2_topo', 'Block%s_DEM_10cm.xyz' % blk)); gx = np.unique(dem[:, 0]) / 100; gy = np.unique(dem[:, 1]) / 100; DEM = dem[:, 2].reshape(len(gy), len(gx))
    from scipy.interpolate import RegularGridInterpolator
    fi = RegularGridInterpolator((gy, gx), DEM, bounds_error=False, fill_value=None)
    GX, GY = np.meshgrid(np.arange(0, W + 0.001, 0.05), np.arange(0, H + 0.001, 0.05)); hs = fi(np.c_[GY.ravel(), GX.ravel()]).reshape(GX.shape)
    surf = {}
    for F, col in zip(FEATS[blk], ('#D98E1E', '#1F8A80')):
        a = np.loadtxt(os.path.join(OUT, 'model', '%s_grid_10cm.xyz' % F)); fx = np.unique(a[:, 0]) / 100; fy = np.unique(a[:, 1]) / 100; Z = a[:, 2].reshape(len(fy), len(fx))
        surf[F] = (fx, fy, Z)
        rr = list(csv.DictReader(open(next(p for p in (os.path.join(OUT, 'tables', n % F) for n in ('PICKS_%s_final.csv', 'PICKS_%s_raw.csv', 'PICKS_%s_adjusted.csv')) if os.path.exists(p)), encoding='utf-8')))
        Pp = np.array([[float(q['x_cm']) / 100, float(q['y_cm']) / 100, float(q.get('z_adj') or q['depth_m'])] for q in rr])
        co, *_ = np.linalg.lstsq(np.c_[Pp[:, 0], Pp[:, 1], np.ones(len(Pp))], Pp[:, 2], rcond=None)
        dpl = co[0] * GX + co[1] * GY + co[2]
        cs = ax.contour(GX, GY, dpl + hs, levels=[0.0], colors=col, linewidths=2.5); ax.contour(GX, GY, dpl, levels=[0.5, 1.0, 1.5, 2.0, 2.5, 3.0], colors=col, linewidths=0.8, linestyles='--')
        ax.plot([], [], '-', color=col, lw=2.5, label='%s daylight on DEM; dashed = 0.5 m depth steps' % F)
        ax.scatter(Pp[:, 0], Pp[:, 1], s=1.5, c=col, alpha=0.5)
    for b in PACK[blk]['surface_1.0m']['boxes']:
        if b['cls'].startswith('gangsaw'): ax.add_patch(plt.Rectangle((b['x0'], b['y0']), b['x1'] - b['x0'], b['y1'] - b['y0'], fill=False, ec=CLSCOL[b['cls']], lw=1.6))
    ax.plot([], [], '-', color='#2457E6', lw=1.8, label='chalked cracks (sketch)'); ax.plot([], [], '-', color=CLSCOL['gangsaw_large'], lw=1.6, label='gangsaw blocks, cracks to 1 m')
    ax.legend(fontsize=7, loc='upper right', framealpha=0.85); ax.set_xlabel('report x (m)'); ax.set_ylabel('report y (m)')
    ax.set_title('Block %s in its own frame: baked texture, lattice, cracks, GPR picks and planes, blocks  [paint on lattice: %s]' % (blk, 'aligned' if res[blk]['ratio_zero_to_best'] > 0.85 else 'CHECK'), fontsize=9)
    ax.set_xlim(-PAD, W + PAD); ax.set_ylim(-PAD, H + PAD)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'figs', 'ORIENT_plan_%s.png' % blk), dpi=120); plt.close(fig)
    # ---- oblique 3D render ----
    fig = plt.figure(figsize=(12, 8)); ax = fig.add_subplot(111, projection='3d')
    step = 0.1; GX2, GY2 = np.meshgrid(np.arange(0, W + 0.001, step), np.arange(0, H + 0.001, step)); Z2 = fi(np.c_[GY2.ravel(), GX2.ravel()]).reshape(GX2.shape)
    # texture sampled at the DEM nodes
    ii = np.clip(((GX2 + PAD) / PX).astype(int), 0, nx - 1); jj = np.clip(((GY2 + PAD) / PX).astype(int), 0, ny - 1); fc = im[jj, ii]
    ax.plot_surface(GX2, GY2, Z2, facecolors=fc, rstride=1, cstride=1, linewidth=0, antialiased=False, shade=False)
    for F, col in zip(FEATS[blk], ('#D98E1E', '#1F8A80')):
        fx, fy, Z = surf[F]; FX, FY = np.meshgrid(fx, fy); hsf = fi(np.c_[FY.ravel(), FX.ravel()]).reshape(FX.shape)
        Zv2 = np.where(np.isfinite(Z), hsf - Z, np.nan)
        ax.plot_surface(FX, FY, Zv2, color=col, alpha=0.75, linewidth=0, shade=True)
    for v in tr.values(): v = np.array(v); ax.plot(v[:, 0], v[:, 1], fi(np.c_[v[:, 1], v[:, 0]]) + 0.03, '-', color='#2457E6', lw=1.5)
    for b in PACK[blk]['surface_1.0m']['boxes']:
        if not b['cls'].startswith('gangsaw'): continue
        x0, x1, y0, y1 = b['x0'], b['x1'], b['y0'], b['y1']; hs0 = float(fi([[0.5 * (y0 + y1), 0.5 * (x0 + x1)]])[0]); zt, zb = hs0 - b['z0'], hs0 - b['z1']
        P = [(x0, y0, zb), (x1, y0, zb), (x1, y1, zb), (x0, y1, zb), (x0, y0, zt), (x1, y0, zt), (x1, y1, zt), (x0, y1, zt)]
        faces = [[P[0], P[1], P[2], P[3]], [P[4], P[5], P[6], P[7]], [P[0], P[1], P[5], P[4]], [P[2], P[3], P[7], P[6]], [P[1], P[2], P[6], P[5]], [P[0], P[3], P[7], P[4]]]
        ax.add_collection3d(Poly3DCollection(faces, facecolors=CLSCOL[b['cls']], edgecolors='k', linewidths=0.4, alpha=0.45))
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_zlim(-3.6, 0.4); ax.set_box_aspect((W, H, 4.0)); ax.view_init(elev=32, azim=-55)
    ax.set_xlabel('x (m)'); ax.set_ylabel('y (m)'); ax.set_zlabel('m, bench = 0'); ax.set_title('Block %s: bench texture on the DEM, v2 surfaces, chalked cracks, gangsaw blocks (matplotlib, independent of the web renderer)' % blk, fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'figs', 'ORIENT_3d_%s.png' % blk), dpi=110); plt.close(fig)
    print('   wrote figs/ORIENT_plan_%s.png, figs/ORIENT_3d_%s.png' % (blk, blk))
json.dump(res, open(os.path.join(OUT, 'tables', 'texture_orientation.json'), 'w'), indent=1)
