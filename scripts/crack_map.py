"""Surface fracture map from the photographs, on the bench, in the report frame.
Dark-ridge filter (Sato) on every posed photo -> skeleton -> back-project through the Metashape
pose onto the bench plane -> accumulate as persistence across photos. Paint lines are excluded by
colour and by distance to the 0.5 m lattice. Width from the ridge scale x ground sampling distance.
Overlays the predicted GPR daylight traces (v1 flat, v2 on the DEM). usage: crack_map.py [A B C]"""
import numpy as np, json, os, sys, glob, csv, time
from PIL import Image
from skimage.filters import sato, apply_hysteresis_threshold
from skimage.morphology import skeletonize, remove_small_objects
from skimage import measure
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
SITE = r'D:/code_ws/reference/parsans/site'; OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
PH = {'A': 'photogrammetry/block_A', 'B': 'photogrammetry/Block_B', 'C': 'photogrammetry/BLock_C and overall'}
DIMS = {'A': (5.5, 5.5), 'B': (9.5, 6.0), 'C': (7.0, 8.0)}
FEATS = {'A': ('A1', 'A2'), 'B': ('B1', 'B2'), 'C': ('C1', 'C2')}
REG = json.load(open(os.path.join(OUT, 'tables', 'registration.json')))
DS = 2                       # image downscale
SIG = (1.0, 2.0, 3.5)        # ridge scales in downscaled px
CELL = 0.02                  # accumulation raster, metres
blocks = sys.argv[1:] or ['A', 'B', 'C']


def undist(xd_, yd_, cal, it=6):
    x, y = xd_, yd_
    for _ in range(it):
        r2 = x * x + y * y; rad = 1 + cal['k1'] * r2 + cal['k2'] * r2 ** 2 + cal['k3'] * r2 ** 3
        dx = cal['p1'] * (r2 + 2 * x * x) + 2 * cal['p2'] * x * y; dy = cal['p2'] * (r2 + 2 * y * y) + 2 * cal['p1'] * x * y
        x = (xd_ - dx) / rad; y = (yd_ - dy) / rad
    return x, y


for blk in blocks:
    t0 = time.time()
    r = REG[blk]; R = np.array(r['plane_R']); c = np.array(r['plane_c']); sc = r['scale_m_per_unit']; n = R[2]
    corner = np.array(r['origin_local_units']) * sc; xd = np.array(r['xdir_local']); yd = np.array(r['ydir_local'])
    W, H = DIMS[blk]
    cams = json.load(open(os.path.join(OUT, 'tables', 'cameras_%s.json' % blk)))
    NX, NY = int(W / CELL) + 1, int(H / CELL) + 1
    hits = np.zeros((NY, NX)); wsum = np.zeros((NY, NX)); cov = np.zeros((NY, NX))
    photos = sorted(glob.glob(os.path.join(SITE, PH[blk], '*.jp*g'))); used = 0; nhit_total = 0
    for p in photos:
        lab = os.path.splitext(os.path.basename(p))[0]
        if lab not in cams['cameras']: continue
        cam = cams['cameras'][lab]; cal = cams['sensors'][cam['sensor']]; T = np.array(cam['T']); o = T[:3, 3]; Rc = T[:3, :3]
        im = Image.open(p); Wp, Hp = im.size
        if (Wp, Hp) != (cal['w'], cal['h']): continue
        im = im.resize((Wp // DS, Hp // DS), Image.BILINEAR); A = np.asarray(im).astype(np.float32) / 255.0
        g = A.mean(2)
        # ---- coverage: coarse pixel grid onto the plane ----
        vv, uu = np.mgrid[0:g.shape[0]:24, 0:g.shape[1]:24]
        def project(uu, vv):
            u = uu.ravel() * DS; v = vv.ravel() * DS
            x, y = undist((u - cal['w'] / 2 - cal['cx']) / cal['f'], (v - cal['h'] / 2 - cal['cy']) / cal['f'], cal)
            d = (Rc @ np.c_[x, y, np.ones_like(x)].T).T
            dn = d @ n; ok = np.abs(dn) / np.linalg.norm(d, axis=1) > np.sin(np.radians(18))
            t = ((c - o) @ n) / np.where(dn == 0, 1e-9, dn); ok &= t > 0
            P = o + t[:, None] * d
            L = ((P - c) @ R.T) * sc
            rel = L[:, :2] - corner; xg = rel @ xd; yg = rel @ yd
            rng = t * np.linalg.norm(d, axis=1) * sc                    # range camera -> hit, metres
            inb = ok & (xg > -0.3) & (xg < W + 0.3) & (yg > -0.3) & (yg < H + 0.3)
            return xg, yg, rng, inb
        xg, yg, rng, inb = project(uu, vv)
        if inb.sum() < 6: continue
        ix = np.clip((xg[inb] / CELL).astype(int), 0, NX - 1); iy = np.clip((yg[inb] / CELL).astype(int), 0, NY - 1)
        cv = np.zeros((NY, NX)); cv[iy, ix] = 1
        from scipy.ndimage import binary_dilation
        cov += binary_dilation(cv, iterations=int(0.35 / CELL))
        # ---- ridges (dark thin lines) ----
        resp = np.stack([sato(g, sigmas=[s], black_ridges=True) for s in SIG]); best = resp.argmax(0); Rm = resp.max(0)
        thr_hi = np.percentile(Rm, 98.5); thr_lo = np.percentile(Rm, 96.0)
        M = apply_hysteresis_threshold(Rm, thr_lo, thr_hi)
        # exclude paint: red or white pixels
        red = (A[..., 0] - 0.5 * (A[..., 1] + A[..., 2])) > 0.10; white = (A.min(2) > 0.72) & ((A.max(2) - A.min(2)) < 0.14)
        M &= ~red & ~white
        M = remove_small_objects(M, 60); S = skeletonize(M)
        sv, su = np.nonzero(S)
        if len(su) == 0: continue
        keep = np.arange(len(su)) % 2 == 0; su = su[keep]; sv = sv[keep]
        xg, yg, rng, inb = project(su, sv)
        if inb.sum() == 0: continue
        xg, yg, rng = xg[inb], yg[inb], rng[inb]; sig = np.array(SIG)[best[sv[inb], su[inb]]]
        # lattice exclusion: within 4 cm of a 0.5 m line
        dl = np.minimum(np.abs(xg - np.round(xg / 0.5) * 0.5), np.abs(yg - np.round(yg / 0.5) * 0.5))
        m = dl > 0.04
        xg, yg, rng, sig = xg[m], yg[m], rng[m], sig[m]
        gsd = rng / cal['f'] * DS                                          # metres per downscaled pixel
        width = 2.35 * sig * gsd                                            # FWHM of the ridge, metres
        ix = np.clip((xg / CELL).astype(int), 0, NX - 1); iy = np.clip((yg / CELL).astype(int), 0, NY - 1)
        np.add.at(hits, (iy, ix), 1); np.add.at(wsum, (iy, ix), width)
        used += 1; nhit_total += len(xg)
    pers = np.where(cov > 0, hits / np.maximum(cov, 1), 0)
    wmean = np.where(hits > 0, wsum / np.maximum(hits, 1), np.nan)
    np.savez_compressed(os.path.join(OUT, 'tables', 'surface_cracks_%s.npz' % blk), hits=hits, cov=cov, pers=pers, width=wmean, cell=CELL)
    print('Block %s: %d photos used, %d bench hits, coverage max %d photos, %.0f s' % (blk, used, nhit_total, int(cov.max()), time.time() - t0))
    # ---- vectorise persistent cracks ----
    from scipy.ndimage import uniform_filter, binary_closing
    P2 = uniform_filter(pers, 3); C2 = uniform_filter(cov, 3)
    Mk = (P2 > 0.12) & (C2 >= 2) & (uniform_filter(hits, 3) >= 0.6)
    Mk = binary_closing(Mk, iterations=2); Mk = remove_small_objects(Mk, int(0.15 / CELL) * 3)
    Sk = skeletonize(Mk)
    lab = measure.label(Sk, connectivity=2); props = measure.regionprops(lab)
    gx = np.arange(NX) * CELL * 100; gy = np.arange(NY) * CELL * 100
    rows = []
    for pr in props:
        L = pr.area * CELL
        if L < 0.20: continue
        yy, xx = pr.coords.T
        w = np.nanmedian(wmean[yy, xx]); pm = float(pers[yy, xx].mean())
        rows.append(dict(id=pr.label, length_m=round(L, 3), width_mm=round(1000 * w, 1) if np.isfinite(w) else '', persistence=round(pm, 3),
                         x0_cm=round(xx.min() * CELL * 100, 1), x1_cm=round(xx.max() * CELL * 100, 1), y0_cm=round(yy.min() * CELL * 100, 1), y1_cm=round(yy.max() * CELL * 100, 1),
                         orientation_deg=round(float(np.degrees(pr.orientation)) % 180, 1)))
    rows.sort(key=lambda d: -d['length_m'])
    if rows:
        wri = csv.DictWriter(open(os.path.join(OUT, 'tables', 'surface_cracks_%s.csv' % blk), 'w', newline='', encoding='utf-8'), fieldnames=list(rows[0].keys())); wri.writeheader(); wri.writerows(rows)
    print('   %d persistent traces >= 0.2 m; longest %s' % (len(rows), ', '.join('%.1f m (%s mm)' % (d['length_m'], d['width_mm']) for d in rows[:5])))
    # ---- predicted daylight traces of the GPR planes, v1 flat and v2 on the DEM ----
    dem = None; dp = os.path.join(OUT, 'model', 'v2_topo', 'Block%s_DEM_10cm.xyz' % blk)
    if os.path.exists(dp):
        a = np.loadtxt(dp); nn = len(np.unique(a[:, 0])); mm = len(np.unique(a[:, 1])); DX_, DY_, DEM = a[:, 0].reshape(mm, nn), a[:, 1].reshape(mm, nn), a[:, 2].reshape(mm, nn); dem = (DX_, DY_, DEM)
    planes = {}
    for F in FEATS[blk]:
        pf = os.path.join(OUT, 'tables', 'PICKS_%s_final.csv' % F)
        if not os.path.exists(pf): pf = os.path.join(OUT, 'tables', 'PICKS_%s_raw.csv' % F)
        if not os.path.exists(pf): pf = os.path.join(OUT, 'tables', 'PICKS_%s_adjusted.csv' % F)
        if not os.path.exists(pf): continue
        rr = list(csv.DictReader(open(pf, encoding='utf-8')))
        Pp = np.array([[float(q['x_cm']), float(q['y_cm']), float(q.get('z_adj') or q['depth_m'])] for q in rr])
        Am = np.c_[Pp[:, 0], Pp[:, 1], np.ones(len(Pp))]; co, *_ = np.linalg.lstsq(Am, Pp[:, 2], rcond=None); planes[F] = co
    # ---- figure ----
    fig, ax = plt.subplots(1, 2, figsize=(14, 6.4), constrained_layout=True)
    GX, GY = np.meshgrid(gx, gy)
    ax[0].imshow(np.clip(pers, 0, 0.5), origin='lower', extent=[0, W * 100, 0, H * 100], cmap='magma')
    ax[0].set_title('Block %s: surface dark-line persistence across %d photos (paint excluded)' % (blk, used), fontsize=9)
    ax[1].imshow(Sk, origin='lower', extent=[0, W * 100, 0, H * 100], cmap='gray_r')
    for F, co in planes.items():
        dpl = co[0] * GX + co[1] * GY + co[2]                     # fitted depth of the plane (m), positive down
        cs = ax[1].contour(GX, GY, dpl, levels=[0.0], colors='r', linewidths=2)
        if len(cs.allsegs[0]): ax[1].plot([], [], 'r-', lw=2, label='%s daylight, v1 flat bench' % F)
        if dem is not None:
            from scipy.interpolate import RegularGridInterpolator
            fi = RegularGridInterpolator((dem[1][:, 0], dem[0][0]), dem[2], bounds_error=False, fill_value=None)
            hsurf = fi(np.c_[GY.ravel(), GX.ravel()]).reshape(GX.shape)
            cs2 = ax[1].contour(GX, GY, dpl + hsurf, levels=[0.0], colors='c', linewidths=2, linestyles='--')
            if len(cs2.allsegs[0]): ax[1].plot([], [], 'c--', lw=2, label='%s daylight, v2 on DEM' % F)
    ax[1].legend(fontsize=7, loc='upper right'); ax[1].set_title('persistent surface traces (black) vs GPR planes daylighting', fontsize=9)
    for a_ in ax: a_.set_xlabel('x (cm)'); a_.set_ylabel('y (cm)'); a_.set_aspect('equal')
    fig.savefig(os.path.join(OUT, 'figs', 'SURFACE_CRACKS_%s.png' % blk), dpi=120); plt.close(fig)
    # ---- polylines onto the bench frame, on the DEM ----
    od = os.path.join(OUT, 'dataset', 'bench_frame_m', 'Block_' + blk); V = []; PL = []
    for pr in props:
        if pr.area * CELL < 0.20: continue
        yy, xx = pr.coords.T; order = np.argsort(xx + 1e-3 * yy)
        pts = np.c_[xx[order] * CELL, yy[order] * CELL]
        Lm = corner[None, :] + np.outer(pts[:, 0], xd) + np.outer(pts[:, 1], yd)
        z = np.zeros(len(pts))
        if dem is not None:
            fi = RegularGridInterpolator((dem[1][:, 0], dem[0][0]), dem[2], bounds_error=False, fill_value=0.0); z = fi(np.c_[pts[:, 1] * 100, pts[:, 0] * 100])
        i0 = len(V); V += [(Lm[k, 0], Lm[k, 1], z[k]) for k in range(len(pts))]; PL.append(list(range(i0 + 1, i0 + len(pts) + 1)))
    Lo = ['# Block %s surface fracture traces from photos, bench frame metres, on the DEM' % blk, 'o surface_cracks_%s' % blk] + ['v %.4f %.4f %.4f' % v for v in V] + ['l ' + ' '.join(map(str, pl)) for pl in PL]
    open(os.path.join(od, 'Block_%s_surface_cracks_v1.obj' % blk), 'w').write('\n'.join(Lo) + '\n')
    print('   wrote figs/SURFACE_CRACKS_%s.png, tables/surface_cracks_%s.csv, dataset .../Block_%s_surface_cracks_v1.obj' % (blk, blk, blk))
