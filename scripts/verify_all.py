"""Numeric verification of every stage, written to tables/VERIFY_all.json and printed.
Picks (crossings, report tie), registration (scale self-consistency), DEM (internal), sketch (lattice leak),
photo cracks (against the sketch, with a random null)."""
import numpy as np, csv, os, json
from scipy.spatial import cKDTree
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
T = lambda n: os.path.join(OUT, 'tables', n)
V = {}
DIMS = {'A': (550, 550), 'B': (950, 600), 'C': (700, 800)}

# ---- 1. picks: C-2 crossings, and the report tie (from VERIFICATION.md numbers, recomputed where cheap) ----
mis = [float(r['d']) for r in csv.DictReader(open(T('C2_crossing_misfit.csv'), encoding='utf-8'))]
V['picks'] = dict(C2_crossings=len(mis), C2_before_adjust_median_abs_cm=round(100 * np.median(np.abs(mis)), 1))
adj = list(csv.DictReader(open(T('PICKS_C2_adjusted.csv'), encoding='utf-8')))
X = [r for r in adj if r['orientation'] == 'X-line']; Y = [r for r in adj if r['orientation'] == 'Y-line']
def at(pts, key, val, tol=2.5):
    c = [float(p['z_adj']) for p in pts if abs(float(p[key]) - val) <= tol]; return float(np.median(c)) if c else None
res = []
for lx in range(1, 18):
    px = [p for p in X if int(p['line']) == lx]; ys = (lx - 1) * 50.0
    for ly in range(18, 33):
        py = [p for p in Y if int(p['line']) == ly]; xs = (ly - 18) * 50.0
        a = at(px, 'x_cm', xs); b = at(py, 'y_cm', ys)
        if a is not None and b is not None: res.append(a - b)
res = np.abs(res)
V['picks'].update(C2_after_adjust_median_abs_cm=round(100 * np.median(res), 1), C2_after_adjust_p90_cm=round(100 * np.percentile(res, 90), 1), C2_within_20cm_pct=round(100 * (res < 0.20).mean(), 0))
print('PICKS   C-2 crossings %d: median |misfit| %.1f cm, p90 %.1f, %.0f%% within 20 cm' % (len(res), 100 * np.median(res), 100 * np.percentile(res, 90), 100 * (res < .2).mean()))

# ---- 2. registration: scale self-consistency and frame handedness ----
reg = json.load(open(T('registration.json'))); V['registration'] = {}
for blk, gj in (('A', 'grid_A_paint.json'), ('B', 'grid_B_lum.json'), ('C', 'grid_Cfull_red.json')):
    g = json.load(open(T(gj))); r = reg[blk]
    lattice_spacing_m = g['spacing_units'] * r['scale_m_per_unit']
    xd = np.array(r['xdir_local']); yd = np.array(r['ydir_local'])
    ang = np.degrees(np.arccos(np.clip(xd @ yd, -1, 1))); hand = 'left' if xd[0] * yd[1] - xd[1] * yd[0] < 0 else 'right'
    V['registration'][blk] = dict(scale_m_per_unit=r['scale_m_per_unit'], lattice_spacing_under_this_scale_m=round(lattice_spacing_m, 4),
                                  spacing_error_pct=round(100 * (lattice_spacing_m / 0.5 - 1), 2), axis_angle_deg=round(float(ang), 2), handedness_z_up=hand, source=r['placement'][:60])
    print('REG %s  scale %.4f  painted spacing under it %.4f m (%+.1f%%)  axes %.1f deg  %s-handed' % (blk, r['scale_m_per_unit'], lattice_spacing_m, 100 * (lattice_spacing_m / .5 - 1), ang, hand))

# ---- 3. DEM: internal consistency ----
V['dem'] = {}
for blk in 'ABC':
    a = np.loadtxt(os.path.join(OUT, 'model', 'v2_topo', 'Block%s_DEM_10cm.xyz' % blk)); nn = len(np.unique(a[:, 0])); mm = len(np.unique(a[:, 1])); Z = a[:, 2].reshape(mm, nn)
    A_ = np.c_[a[:, 0], a[:, 1], np.ones(len(a))]; co, *_ = np.linalg.lstsq(A_, a[:, 2], rcond=None); resid = a[:, 2] - A_ @ co
    tilt = np.degrees(np.arctan(np.hypot(co[0], co[1]) * 100))
    # local roughness at 30 cm: std of Z minus its 3x3 mean
    from scipy.ndimage import uniform_filter
    rough = float(np.std(Z - uniform_filter(Z, 3)))
    V['dem'][blk] = dict(relief_m=round(float(Z.max() - Z.min()), 3), plane_tilt_deg=round(float(tilt), 2), residual_from_plane_rms_m=round(float(resid.std()), 3), local_roughness_30cm_m=round(rough, 4))
    print('DEM %s  relief %.2f m, best plane tilt %.1f deg, non-planar residual %.3f m rms, 30 cm roughness %.3f m' % (blk, Z.max() - Z.min(), tilt, resid.std(), rough))

# ---- 4. sketch: lattice leak (trace length parallel to AND on a lattice line) ----
V['sketch'] = {}
for blk in 'ABC':
    tr = {}
    for q in csv.DictReader(open(T('sketch_chained_%s.csv' % blk), encoding='utf-8')): tr.setdefault(int(q['trace_id']), []).append((float(q['x_cm']), float(q['y_cm'])))
    leak = 0.0; tot = 0.0
    for pts in tr.values():
        pts = np.array(pts)
        for a_, b_ in zip(pts[:-1], pts[1:]):
            L = np.hypot(*(b_ - a_)); tot += L
            if L == 0: continue
            d = (b_ - a_) / L; ang = np.degrees(np.arctan2(abs(d[1]), abs(d[0])))
            m = 0.5 * (a_ + b_); dx = abs(m[0] - round(m[0] / 50) * 50); dy = abs(m[1] - round(m[1] / 50) * 50)
            if (ang < 10 and dy < 6) or (ang > 80 and dx < 6): leak += L
    gj = json.load(open(T('sketch_grid_%s.json' % blk)))
    V['sketch'][blk] = dict(traces=len(tr), total_m=round(tot / 100, 1), lattice_leak_pct=round(100 * leak / max(tot, 1), 1), grid_affine_resid_cm=gj['affine_resid_med_cm'])
    print('SKETCH %s  %d traces %.1f m; %.1f%% of length lies parallel-and-on a lattice line (grid leak); hand-drawn grid wobble %.0f cm' % (blk, len(tr), tot / 100, 100 * leak / max(tot, 1), gj['affine_resid_med_cm']))

# ---- 5. photo cracks vs sketch, with a random-segment null ----
V['photo'] = {}
rng = np.random.default_rng(0)
for blk in 'ABC':
    W, H = DIMS[blk]
    tr = {}
    for q in csv.DictReader(open(T('sketch_chained_%s.csv' % blk), encoding='utf-8')): tr.setdefault(int(q['trace_id']), []).append((float(q['x_cm']), float(q['y_cm'])))
    pts = []
    for v in tr.values():
        v = np.array(v)
        for a_, b_ in zip(v[:-1], v[1:]): pts.append(np.linspace(a_, b_, max(2, int(np.hypot(*(b_ - a_)) / 2) + 1)))
    tsk = cKDTree(np.vstack(pts))
    rows = list(csv.DictReader(open(T('surface_cracks_%s_weeded.csv' % blk), encoding='utf-8')))
    kept = [r for r in rows if r['chalk'] == '0']; chalk = [r for r in rows if r['chalk'] == '1']
    def seg_dist(x0, y0, x1, y1):
        s = np.linspace([x0, y0], [x1, y1], 20); return float(np.median(tsk.query(s)[0]))
    dk = np.array([seg_dist(float(r['x0']), float(r['y0']), float(r['x1']), float(r['y1'])) for r in kept])
    # null: same segment lengths and orientations, random positions
    dn = []
    for r in kept:
        L = np.hypot(float(r['x1']) - float(r['x0']), float(r['y1']) - float(r['y0'])); th = rng.uniform(0, np.pi)
        for _ in range(20):
            cx, cy = rng.uniform(0, W), rng.uniform(0, H); dn.append(seg_dist(cx - L / 2 * np.cos(th), cy - L / 2 * np.sin(th), cx + L / 2 * np.cos(th), cy + L / 2 * np.sin(th)))
    dn = np.array(dn)
    V['photo'][blk] = dict(kept=len(kept), chalk_weeded=len(chalk), within30_pct=round(100 * (dk <= 30).mean(), 0), null_within30_pct=round(100 * (dn <= 30).mean(), 0),
                           median_cm=round(float(np.median(dk)), 0), null_median_cm=round(float(np.median(dn)), 0), lift=round(float((dk <= 30).mean() / max((dn <= 30).mean(), 1e-6)), 2))
    print('PHOTO %s  %d kept (%d chalk weeded): %.0f%% within 30 cm of sketch, null %.0f%% -> lift %.2fx; median %.0f vs %.0f cm' % (
        blk, len(kept), len(chalk), 100 * (dk <= 30).mean(), 100 * (dn <= 30).mean(), (dk <= 30).mean() / max((dn <= 30).mean(), 1e-6), np.median(dk), np.median(dn)))
json.dump(V, open(T('VERIFY_all.json'), 'w'), indent=1); print('wrote tables/VERIFY_all.json')
