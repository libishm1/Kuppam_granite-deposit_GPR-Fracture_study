"""For each photogrammetry mesh: find the plane the PAINTED GRID lies on, rotate to it,
and write a top-down colour raster plus a paint mask. The grid is coplanar by
construction, which makes it a far better plane seed than the dominant plane.

Output rasters are in mesh units (arbitrary Metashape scale). Grid spacing in those
rasters is what gives the scale later."""
import numpy as np, sys, os, time
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
SITE = r'D:/code_ws/reference/parsans/site'
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'


def load_vc(path, stride=1):
    xyz = []; rgb = []; k = 0
    with open(path, 'rb') as f:
        for ln in f:
            if ln[:2] != b'v ': continue
            k += 1
            if k % stride: continue
            p = ln.split()
            xyz.append((float(p[1]), float(p[2]), float(p[3])))
            rgb.append((float(p[4]), float(p[5]), float(p[6])) if len(p) >= 7 else (0.5, 0.5, 0.5))
    return np.array(xyz), np.array(rgb)


def paint_mask(rgb):
    r, g, b = rgb.T
    mx = rgb.max(1); mn = rgb.min(1)
    white = (mn > 0.70) & ((mx - mn) < 0.14)
    red = (r > 0.42) & ((r - np.maximum(g, b)) > 0.14)
    return white, red


def ransac_plane(P, thr, n_it=600, rng=np.random.default_rng(1)):
    best = (0, None)
    for _ in range(n_it):
        i = rng.choice(len(P), 3, replace=False); a, b, c = P[i]
        n = np.cross(b - a, c - a); nn = np.linalg.norm(n)
        if nn < 1e-12: continue
        n /= nn; cnt = (np.abs((P - a) @ n) < thr).sum()
        if cnt > best[0]: best = (cnt, (n, a))
    n, a = best[1]; inl = np.abs((P - a) @ n) < thr
    Q = P[inl]; c = Q.mean(0); _, _, vt = np.linalg.svd(Q - c, full_matrices=False)
    return vt[2], c, inl


def frame_from_plane(n, c, P):
    # up = plane normal, signed so that most of the cloud is ABOVE the bench (walls rise)
    d = (P - c) @ n
    if np.median(d[np.abs(d) > np.percentile(np.abs(d), 60)]) < 0: n = -n
    e1 = np.cross(n, [0, 0, 1.0])
    if np.linalg.norm(e1) < 0.1: e1 = np.cross(n, [0, 1.0, 0])
    e1 /= np.linalg.norm(e1); e2 = np.cross(n, e1)
    return np.stack([e1, e2, n])   # rows: local x, local y, up


for tag, fn, stride in (('A', 'block a.obj', 2), ('B', 'block b.obj', 1), ('C', 'block_c_decimated_1M.obj', 1)):
    t = time.time()
    P, C = load_vc(os.path.join(SITE, fn), stride)
    white, red = paint_mask(C)
    diag = np.linalg.norm(P.max(0) - P.min(0))
    print('\n=== Block %s  %s  %d verts (%.0fs)  white %d  red %d  bbox diag %.1f' % (tag, fn, len(P), time.time() - t, white.sum(), red.sum(), diag))
    seed = white | red
    if seed.sum() < 500:
        print('  too little paint found; falling back to the dominant plane'); seed = np.ones(len(P), bool)
    S = P[seed]
    if len(S) > 80000: S = S[np.random.default_rng(0).choice(len(S), 80000, replace=False)]
    n, c, inl = ransac_plane(S, thr=0.004 * diag)
    print('  paint plane: normal %s, %.0f%% of paint points within %.3f units' % (np.round(n, 3), 100 * inl.mean(), 0.004 * diag))
    R = frame_from_plane(n, c, P)
    L = (P - c) @ R.T          # local coords: x, y in plane, z up
    Lp = L[seed]
    band = 0.02 * diag
    near = np.abs(L[:, 2]) < band
    # extent from the paint inliers, padded
    pin = Lp[np.abs(Lp[:, 2]) < 0.004 * diag]
    x0, y0 = pin[:, :2].min(0); x1, y1 = pin[:, :2].max(0)
    pad = 0.15 * max(x1 - x0, y1 - y0)
    x0 -= pad; y0 -= pad; x1 += pad; y1 += pad
    print('  paint in-plane extent %.2f x %.2f units; band +/-%.3f keeps %d of %d points' % (x1 - x0 - 2 * pad, y1 - y0 - 2 * pad, band, near.sum(), len(P)))
    NX = 1600; px = (x1 - x0) / NX; NY = int((y1 - y0) / px) + 1
    sel = near & (L[:, 0] >= x0) & (L[:, 0] < x1) & (L[:, 1] >= y0) & (L[:, 1] < y1)
    ix = ((L[sel, 0] - x0) / px).astype(int); iy = ((L[sel, 1] - y0) / px).astype(int)
    img = np.zeros((NY, NX, 3)); cnt = np.zeros((NY, NX))
    np.add.at(img, (iy, ix), C[sel]); np.add.at(cnt, (iy, ix), 1)
    img = img / np.maximum(cnt, 1)[..., None]; img[cnt == 0] = 0.08
    pm = np.zeros((NY, NX)); np.add.at(pm, (iy, ix), (white | red)[sel].astype(float))
    pm = pm / np.maximum(cnt, 1)
    np.savez_compressed(os.path.join(OUT, 'tables', 'paint_raster_%s.npz' % tag), img=img, paint=pm, cnt=cnt,
                        x0=x0, y0=y0, px=px, R=R, c=c, band=band)
    fig, ax = plt.subplots(1, 2, figsize=(16, 8 * NY / NX + 0.8), constrained_layout=True)
    ax[0].imshow(img, origin='lower', extent=[x0, x1, y0, y1]); ax[0].set_title('Block %s: bench plane, vertex colour (mesh units)' % tag, fontsize=10)
    ax[1].imshow(pm, origin='lower', extent=[x0, x1, y0, y1], cmap='gray', vmin=0, vmax=0.6); ax[1].set_title('paint mask (white | red)', fontsize=10)
    for a in ax: a.set_xlabel('local x'); a.set_ylabel('local y'); a.tick_params(labelsize=7)
    fig.savefig(os.path.join(OUT, 'figs', 'paint_raster_%s.png' % tag), dpi=110)
    print('  wrote figs/paint_raster_%s.png  (%d x %d px, %.4f units/px)' % (tag, NX, NY, px))
