"""Where does each GPR surface reach the bench, and does that line follow a chalked crack better than chance?
Replaces the inline test that produced the earlier sketch_vs_gpr_daylight.json, which contoured
plane_depth + bench_height = 0 (mixing a depth below the local surface with an absolute elevation). Two honest
definitions are used here:
  v1  the plane fitted to depth below the local surface reaches the surface where that depth is zero;
  v2  the plane fitted to ABSOLUTE elevation (bench height minus depth) meets the DEM where e_plane(x,y) = DEM(x,y).
For each daylight line: median distance to the chalked traces, fraction within 30 cm, and a null from random rigid
placements of the same line inside the grid. Also whether the line lies inside or beyond the picks' footprint."""
import numpy as np, csv, os, json
from scipy.interpolate import RegularGridInterpolator
from scipy.spatial import cKDTree
from skimage import measure
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
DIMS = {'A': (5.5, 5.5), 'B': (9.5, 6.0), 'C': (7.0, 8.0)}
FEATS = {'A': ('A1', 'A2'), 'B': ('B1', 'B2'), 'C': ('C1', 'C2')}
NULL_N = 600; TOL = 0.30; rng = np.random.default_rng(7)


def picks(F):
    pf = next(p for p in (os.path.join(OUT, 'tables', n % F) for n in ('PICKS_%s_final.csv', 'PICKS_%s_adjusted.csv', 'PICKS_%s_raw.csv')) if os.path.exists(p))
    rr = list(csv.DictReader(open(pf, encoding='utf-8')))
    return np.array([[float(q['x_cm']) / 100, float(q['y_cm']) / 100, float(q.get('z_adj') or q['depth_m'])] for q in rr]), os.path.basename(pf)


def dem(blk):
    a = np.loadtxt(os.path.join(OUT, 'model', 'v2_topo', 'Block%s_DEM_10cm.xyz' % blk)); gx = np.unique(a[:, 0]) / 100; gy = np.unique(a[:, 1]) / 100
    return RegularGridInterpolator((gy, gx), a[:, 2].reshape(len(gy), len(gx)), bounds_error=False, fill_value=None)


def chalk(blk):
    tr = {}
    for q in csv.DictReader(open(os.path.join(OUT, 'tables', 'sketch_chained_%s.csv' % blk), encoding='utf-8')): tr.setdefault(int(q['trace_id']), []).append((float(q['x_cm']) / 100, float(q['y_cm']) / 100))
    pts = []
    for v in tr.values():
        v = np.array(v)
        for a, b in zip(v[:-1], v[1:]):
            n = max(2, int(np.hypot(*(b - a)) / 0.02) + 1); pts.append(np.linspace(a, b, n))
    return [np.array(v) for v in tr.values()], np.vstack(pts)


def contour_line(Zf, W, H, step=0.05):
    xs = np.arange(0, W + 1e-9, step); ys = np.arange(0, H + 1e-9, step); X, Y = np.meshgrid(xs, ys); Z = Zf(X, Y)
    cs = measure.find_contours(Z, 0.0)
    if not cs: return None
    return [np.c_[c[:, 1] * step, c[:, 0] * step] for c in cs]


def densify(polys, step=0.05):
    out = []
    for c in polys:
        for a, b in zip(c[:-1], c[1:]):
            n = max(2, int(np.hypot(*(b - a)) / step) + 1); out.append(np.linspace(a, b, n))
    return np.vstack(out)


def score(line_pts, tree):
    d = tree.query(line_pts)[0]; return float(np.median(d)), float((d <= TOL).mean())


def null_scores(line_pts, tree, W, H):
    c = line_pts.mean(axis=0); P = line_pts - c; fr = []
    while len(fr) < NULL_N:
        th = rng.uniform(0, 2 * np.pi); R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]]); Q = P @ R.T
        t = np.array([rng.uniform(0, W), rng.uniform(0, H)]); Q = Q + t
        inside = ((Q[:, 0] >= 0) & (Q[:, 0] <= W) & (Q[:, 1] >= 0) & (Q[:, 1] <= H)).mean()
        if inside < 0.8: continue
        fr.append(score(Q[(Q[:, 0] >= 0) & (Q[:, 0] <= W) & (Q[:, 1] >= 0) & (Q[:, 1] <= H)], tree)[1])
    fr = np.array(fr); return float(fr.mean()), float(np.percentile(fr, 95))


res = {}
for blk in 'ABC':
    W, H = DIMS[blk]; fi = dem(blk); traces, cpts = chalk(blk); tree = cKDTree(cpts); res[blk] = {}
    fig, ax = plt.subplots(figsize=(7, 7 * H / W))
    for tr in traces: ax.plot(tr[:, 0], tr[:, 1], 'b-', lw=1.6, alpha=.8)
    for F in FEATS[blk]:
        P, src = picks(F); hs = fi(np.c_[P[:, 1], P[:, 0]]); e = hs - P[:, 2]
        A = np.c_[P[:, 0], P[:, 1], np.ones(len(P))]
        cd, *_ = np.linalg.lstsq(A, P[:, 2], rcond=None)            # depth-below-surface plane (v1)
        ce, *_ = np.linalg.lstsq(A, e, rcond=None)                   # absolute-elevation plane (v2)
        bbox = [float(P[:, 0].min()), float(P[:, 0].max()), float(P[:, 1].min()), float(P[:, 1].max())]
        out = dict(source=src, n_picks=len(P), footprint_x_m=[round(bbox[0], 2), round(bbox[1], 2)], footprint_y_m=[round(bbox[2], 2), round(bbox[3], 2)],
                   plane_depth=[round(float(v), 4) for v in cd], plane_elev=[round(float(v), 4) for v in ce],
                   dip_depth_plane_deg=round(float(np.degrees(np.arctan(np.hypot(cd[0], cd[1])))), 1), dip_elev_plane_deg=round(float(np.degrees(np.arctan(np.hypot(ce[0], ce[1])))), 1))
        for key, Zf, col in (('v1_flat', lambda X, Y: cd[0] * X + cd[1] * Y + cd[2], 'r'),
                             ('v2_dem', lambda X, Y: (ce[0] * X + ce[1] * Y + ce[2]) - fi(np.c_[Y.ravel(), X.ravel()]).reshape(X.shape), 'c')):
            polys = contour_line(Zf, W, H)
            if polys is None:
                out[key] = dict(daylights=False); continue
            L = densify(polys); med, frac = score(L, tree); nm, n95 = null_scores(L, tree, W, H)
            dist_to_fp = float(np.max([0, bbox[0] - L[:, 0].max(), L[:, 0].min() - bbox[1], bbox[2] - L[:, 1].max(), L[:, 1].min() - bbox[3]]))
            inside_fp = float(((L[:, 0] >= bbox[0]) & (L[:, 0] <= bbox[1]) & (L[:, 1] >= bbox[2]) & (L[:, 1] <= bbox[3])).mean())
            out[key] = dict(daylights=True, daylight_len_m=round(float(sum(np.hypot(*np.diff(c, axis=0).T).sum() for c in polys)), 2), median_dist_to_chalk_cm=round(100 * med, 1),
                            frac_within_30cm=round(frac, 3), null_mean_frac=round(nm, 3), null_p95_frac=round(n95, 3), lift=round(frac / nm, 2) if nm > 0 else None,
                            better_than_chance_p05=bool(frac > n95), line_inside_pick_footprint_frac=round(inside_fp, 2), line_beyond_footprint_m=round(dist_to_fp, 2))
            for c in polys: ax.plot(c[:, 0], c[:, 1], color=col, lw=2.2 if key == 'v2_dem' else 1.4, ls='-' if key == 'v2_dem' else '--')
        ax.add_patch(plt.Rectangle((bbox[0], bbox[2]), bbox[1] - bbox[0], bbox[3] - bbox[2], fill=False, ec='k', ls=':', lw=1)); ax.text(bbox[0], bbox[3], F + ' picks', fontsize=8)
        res[blk][F] = out
    ax.plot([], [], 'b-', label='chalked cracks'); ax.plot([], [], 'r--', label='daylight, depth plane (v1)'); ax.plot([], [], 'c-', label='daylight, elevation plane on the DEM (v2)')
    ax.set_xlim(-0.2, W + 0.2); ax.set_ylim(-0.2, H + 0.2); ax.set_aspect('equal'); ax.legend(fontsize=8, loc='upper right'); ax.set_title('Block %s: where the GPR planes reach the bench' % blk)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'figs', 'DAYLIGHT_%s.png' % blk), dpi=110); plt.close(fig)
    for F, o in res[blk].items():
        for key in ('v1_flat', 'v2_dem'):
            k = o[key]
            print('%s %-8s %s' % (F, key, 'no daylight' if not k['daylights'] else 'len %.1f m, within 30 cm %.0f%% (null %.0f%%, p95 %.0f%%) lift %s, %.0f%% of the line inside the pick footprint' % (
                k['daylight_len_m'], 100 * k['frac_within_30cm'], 100 * k['null_mean_frac'], 100 * k['null_p95_frac'], k['lift'], 100 * k['line_inside_pick_footprint_frac'])))
json.dump(res, open(os.path.join(OUT, 'tables', 'sketch_vs_gpr_daylight.json'), 'w'), indent=1)
print('wrote tables/sketch_vs_gpr_daylight.json, figs/DAYLIGHT_{A,B,C}.png')
