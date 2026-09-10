"""Two downstream passes on the surface-fracture evidence.
1. Chain the sketch dashes: join trace endpoints in the report frame when they are close and the join
   continues the direction. The crew draws a fracture as separated dashes; the gaps are real ink gaps.
2. Weed the photo map: a photo trace is CHALK, not crack, when it is both parallel to a lattice axis
   (within 12 deg) and near a lattice line (within 8 cm). Cracks crossing a chalk line pass. Then
   validate every surviving photo trace against the sketch: distance to nearest sketch dash.
Writes tables/sketch_chained_X.csv, tables/surface_cracks_X_weeded.csv, figs/FRACTURES_X.png."""
import numpy as np, csv, os, sys, json
from scipy.spatial import cKDTree
from skimage import measure
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
DIMS = {'A': (550, 550), 'B': (950, 600), 'C': (700, 800)}
FEATS = {'A': ('A1', 'A2'), 'B': ('B1', 'B2'), 'C': ('C1', 'C2')}
blocks = sys.argv[1:] or ['A', 'B', 'C']


def load_sketch(blk):
    rows = list(csv.DictReader(open(os.path.join(OUT, 'tables', 'sketch_traces_%s.csv' % blk), encoding='utf-8')))
    tr = {}
    for r in rows: tr.setdefault(int(r['trace_id']), []).append((float(r['x_cm']), float(r['y_cm'])))
    return [np.array(v) for v in tr.values() if len(v) >= 2]


def chain(traces, join_cm=35.0, ang_deg=40.0):
    """greedy endpoint chaining"""
    traces = [t.copy() for t in traces]
    changed = True
    while changed:
        changed = False
        n = len(traces)
        best = None
        for i in range(n):
            for j in range(n):
                if i == j: continue
                A, B = traces[i], traces[j]
                for ea, eb, flipa, flipb in ((A[-1], B[0], False, False), (A[-1], B[-1], False, True), (A[0], B[0], True, False), (A[0], B[-1], True, True)):
                    d = np.hypot(*(ea - eb))
                    if d > join_cm: continue
                    # direction continuity: tangent at A's end and at B's start, and the bridge
                    ta = (A[-1] - A[max(0, len(A) - 3)]) if not flipa else (A[0] - A[min(len(A) - 1, 2)])
                    tb = (B[min(len(B) - 1, 2)] - B[0]) if not flipb else (B[max(0, len(B) - 3)] - B[-1])
                    br = eb - ea
                    def ang(u, v):
                        nu, nv = np.linalg.norm(u), np.linalg.norm(v)
                        return 0.0 if nu == 0 or nv == 0 else np.degrees(np.arccos(np.clip(u @ v / (nu * nv), -1, 1)))
                    a1 = ang(ta, br) if d > 3 else 0.0; a2 = ang(br, tb) if d > 3 else 0.0; a3 = ang(ta, tb)
                    if max(a1, a2, a3) > ang_deg: continue
                    score = d + 0.3 * max(a1, a2, a3)
                    if best is None or score < best[0]: best = (score, i, j, flipa, flipb)
        if best is not None:
            _, i, j, fa, fb = best
            A = traces[i][::-1] if fa else traces[i]; B = traces[j][::-1] if fb else traces[j]
            new = np.vstack([A, B])
            traces = [t for k, t in enumerate(traces) if k not in (i, j)] + [new]; changed = True
    return traces


def length(t): return float(np.sum(np.hypot(*np.diff(t, axis=0).T)))


def poly_pts(t, step=2.0):
    out = []
    for a, b in zip(t[:-1], t[1:]):
        n = max(2, int(np.hypot(*(b - a)) / step) + 1)
        out.append(np.linspace(a, b, n))
    return np.vstack(out)


for blk in blocks:
    W, H = DIMS[blk]
    # ---------------- 1. sketch chaining ----------------
    raw = load_sketch(blk); ch = chain(raw)
    ch = [t for t in ch if length(t) >= 25]
    ch.sort(key=lambda t: -length(t))
    print('Block %s sketch: %d dashes -> %d chained traces, total %.1f m, longest %s'
          % (blk, len(raw), len(ch), sum(length(t) for t in ch) / 100, ', '.join('%.1f' % (length(t) / 100) for t in ch[:6])))
    with open(os.path.join(OUT, 'tables', 'sketch_chained_%s.csv' % blk), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['trace_id', 'vertex', 'x_cm', 'y_cm', 'length_m'])
        for i, t in enumerate(ch):
            for k, (x, y) in enumerate(t): w.writerow([i + 1, k, '%.1f' % x, '%.1f' % y, '%.2f' % (length(t) / 100)])
    # ---------------- 2. photo map weeding ----------------
    d = np.load(os.path.join(OUT, 'tables', 'surface_cracks_%s.npz' % blk)); pers, cov, hits, wid, cell = d['pers'], d['cov'], d['hits'], d['width'], float(d['cell'])
    from scipy.ndimage import uniform_filter, binary_closing
    from skimage.morphology import skeletonize, remove_small_objects
    P2 = uniform_filter(pers, 3); C2 = uniform_filter(cov, 3)
    Mk = (P2 > 0.12) & (C2 >= 2) & (uniform_filter(hits, 3) >= 0.6)
    Mk = binary_closing(Mk, iterations=2); Mk = remove_small_objects(Mk, int(0.15 / cell) * 3)
    Sk = skeletonize(Mk); lab = measure.label(Sk, connectivity=2)
    sk_pts = np.vstack([poly_pts(t) for t in ch]) if ch else np.zeros((0, 2)); tree = cKDTree(sk_pts) if len(sk_pts) else None
    kept = []; chalk = []; total_len = 0.0
    for p in measure.regionprops(lab):
        L = p.area * cell
        if L < 0.20: continue
        yy, xx = p.coords.T; xg = xx * cell * 100; yg = yy * cell * 100
        ori = np.degrees(p.orientation) % 180                     # 0 = along image rows? skimage: angle between row axis and major axis
        # convert to angle from the x axis in the plane: skimage orientation is measured from the y (row) axis
        ang_x = (90 - ori) % 180
        par_x = min(ang_x, 180 - ang_x) < 12; par_y = abs(ang_x - 90) < 12
        dx = np.abs(xg - np.round(xg / 50) * 50); dy = np.abs(yg - np.round(yg / 50) * 50)
        near_yline = np.median(dx) < 8; near_xline = np.median(dy) < 8     # constant-x lines run along y
        is_chalk = (par_y and near_yline) or (par_x and near_xline)
        wmed = np.nanmedian(wid[yy, xx]); pm = float(pers[yy, xx].mean())
        dsk = float(np.median(tree.query(np.c_[xg, yg])[0])) if tree else np.nan
        rec = dict(id=p.label, length_m=round(L, 2), width_mm=round(1000 * wmed, 1) if np.isfinite(wmed) else '', persistence=round(pm, 3),
                   angle_deg=round(ang_x, 1), x0=round(xg.min(), 0), x1=round(xg.max(), 0), y0=round(yg.min(), 0), y1=round(yg.max(), 0),
                   dist_to_sketch_cm=round(dsk, 1) if np.isfinite(dsk) else '', chalk=int(is_chalk))
        (chalk if is_chalk else kept).append(rec); total_len += 0 if is_chalk else L
    kept.sort(key=lambda r: -r['length_m'])
    with open(os.path.join(OUT, 'tables', 'surface_cracks_%s_weeded.csv' % blk), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list((kept + chalk)[0].keys())); w.writeheader(); w.writerows(kept + chalk)
    conf = [r for r in kept if r['dist_to_sketch_cm'] != '' and r['dist_to_sketch_cm'] <= 30]
    print('   photo map: %d traces, %d weeded as chalk (parallel AND on a lattice line), %d kept (%.1f m); %d of the kept lie within 30 cm of a sketch dash'
          % (len(kept) + len(chalk), len(chalk), len(kept), total_len, len(conf)))
    if kept:
        print('   kept, longest: ' + '; '.join('%.1f m, %s mm, %.0f deg, sketch %s cm' % (r['length_m'], r['width_mm'], r['angle_deg'], r['dist_to_sketch_cm']) for r in kept[:5]))
    # ---------------- 3. GPR daylight and the figure ----------------
    planes = {}
    for F in FEATS[blk]:
        for nm in ('PICKS_%s_final.csv', 'PICKS_%s_raw.csv', 'PICKS_%s_adjusted.csv'):
            pf = os.path.join(OUT, 'tables', nm % F)
            if os.path.exists(pf): break
        rr = list(csv.DictReader(open(pf, encoding='utf-8')))
        Pp = np.array([[float(q['x_cm']), float(q['y_cm']), float(q.get('z_adj') or q['depth_m'])] for q in rr])
        Am = np.c_[Pp[:, 0], Pp[:, 1], np.ones(len(Pp))]; co, *_ = np.linalg.lstsq(Am, Pp[:, 2], rcond=None); planes[F] = co
    dem = None; dp = os.path.join(OUT, 'model', 'v2_topo', 'Block%s_DEM_10cm.xyz' % blk)
    if os.path.exists(dp):
        a = np.loadtxt(dp); nn = len(np.unique(a[:, 0])); mm = len(np.unique(a[:, 1])); dem = (a[:, 0].reshape(mm, nn), a[:, 1].reshape(mm, nn), a[:, 2].reshape(mm, nn))
    fig, ax = plt.subplots(1, 2, figsize=(15, 6.6), constrained_layout=True)
    for a_ in ax:
        for k in range(0, W + 1, 50): a_.axvline(k, color='0.88', lw=.4)
        for k in range(0, H + 1, 50): a_.axhline(k, color='0.88', lw=.4)
    for t in ch: ax[0].plot(t[:, 0], t[:, 1], 'b-', lw=2.2)
    ax[0].plot([], [], 'b-', lw=2.2, label='field sketch, chained (%d, %.1f m)' % (len(ch), sum(length(t) for t in ch) / 100))
    for r in kept:
        c_ = 'g' if (r['dist_to_sketch_cm'] != '' and r['dist_to_sketch_cm'] <= 30) else 'r'
        ax[0].plot([r['x0'], r['x1']], [r['y0'], r['y1']], '-', color=c_, lw=1.0, alpha=.7)
    ax[0].plot([], [], 'g-', label='photo trace confirmed by sketch (<=30 cm)'); ax[0].plot([], [], 'r-', label='photo trace not in sketch')
    for r in chalk: ax[0].plot([r['x0'], r['x1']], [r['y0'], r['y1']], '-', color='0.6', lw=.6, alpha=.6)
    ax[0].plot([], [], '-', color='0.6', lw=.6, label='weeded as chalk line (%d)' % len(chalk))
    ax[0].legend(fontsize=7, loc='upper right'); ax[0].set_title('Block %s surface fractures: sketch vs photo detection' % blk, fontsize=10)
    GX, GY = np.meshgrid(np.arange(0, W + 1, 5.0), np.arange(0, H + 1, 5.0))
    for t in ch: ax[1].plot(t[:, 0], t[:, 1], 'b-', lw=2.0, alpha=.8)
    cols = {'A1': 'red', 'A2': 'darkorange', 'B1': 'red', 'B2': 'darkorange', 'C1': 'red', 'C2': 'darkorange'}
    for F, co in planes.items():
        dpl = co[0] * GX + co[1] * GY + co[2]
        for lev, ls, lab_ in ((0.0, '-', 'daylight'), (0.25, ':', '0.25 m'), (0.5, '--', '0.5 m')):
            cs = ax[1].contour(GX, GY, dpl, levels=[lev], colors=cols[F], linewidths=1.8 if lev == 0 else 1.0, linestyles=ls)
        ax[1].plot([], [], '-', color=cols[F], lw=1.8, label='%s plane daylight (v1); dotted 0.25 m, dashed 0.5 m' % F)
        if dem is not None:
            from scipy.interpolate import RegularGridInterpolator
            fi = RegularGridInterpolator((dem[1][:, 0], dem[0][0]), dem[2], bounds_error=False, fill_value=None)
            hs = fi(np.c_[GY.ravel(), GX.ravel()]).reshape(GX.shape)
            ax[1].contour(GX, GY, dpl + hs, levels=[0.0], colors='c', linewidths=1.6, linestyles='-.'); ax[1].plot([], [], 'c-.', lw=1.6, label='%s daylight on DEM (v2)' % F)
    ax[1].legend(fontsize=7, loc='upper right'); ax[1].set_title('sketch fractures (blue) vs where the GPR planes reach the surface', fontsize=10)
    for a_ in ax: a_.set_xlim(-20, W + 20); a_.set_ylim(-20, H + 20); a_.set_aspect('equal'); a_.set_xlabel('x (cm)'); a_.set_ylabel('y (cm)')
    fig.savefig(os.path.join(OUT, 'figs', 'FRACTURES_%s.png' % blk), dpi=120); plt.close(fig)
    # sketch vs GPR daylight: distance from each chained sketch trace to each plane's daylight line
    for F, co in planes.items():
        dpl = co[0] * GX + co[1] * GY + co[2]
        cs = measure.find_contours(dpl, 0.0)
        if not cs: print('   %s does not daylight inside the grid (plane top at %.2f m)' % (F, dpl.min())); continue
        dl = np.vstack([np.c_[c[:, 1] * 5.0, c[:, 0] * 5.0] for c in cs]); tdl = cKDTree(dl)
        near = [(length(t) / 100, float(np.median(tdl.query(t)[0]))) for t in ch]
        close = [n for n in near if n[1] <= 40]
        print('   %s daylight: %d of %d sketch traces run within 40 cm of it (%s)' % (F, len(close), len(ch), ', '.join('%.1f m at %.0f cm' % n for n in sorted(close, key=lambda n: -n[0])[:4])))
    print('   wrote figs/FRACTURES_%s.png' % blk)
