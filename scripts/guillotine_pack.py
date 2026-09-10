"""Guillotine-separable block cutting plan, per block, with a cut order.
A wire saw cuts full-through planes: vertical along x (constant y), vertical along y (constant x), and horizontal
(constant depth). A cutting plan is therefore a recursive bisection of the bench volume by such planes: a
guillotine tree. This solves it exactly by dynamic programming over sub-boxes on a 0.5 m plan grid (the painted
lattice, which is where the crew will mark cuts) and 0.5 m depth steps, maximising a class-weighted tonnage.
Fractures are forbidden voxels (same buffers as block_pack.py); a leaf that contains any is waste.
Cut order: tree order (root cut first), then removal order east to west. East is taken as grid +x, the sense the
report uses on Block B ('dipping toward increasing X (east)'); confirm with a compass."""
import numpy as np, csv, os, json, sys, time
from functools import lru_cache
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import binary_dilation
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
STEP = 0.5; ZSTEP = 0.5; VOX = 0.10                  # plan cut step, depth cut step, feasibility voxel
RHO = 2.95; BUF_GPR = 0.15; BUF_SK = 0.10; KERF = 0.05
DIMS = {'A': (5.5, 5.5), 'B': (9.5, 6.0), 'C': (7.0, 8.0)}
FEATS = {'A': ('A1', 'A2'), 'B': ('B1', 'B2'), 'C': ('C1', 'C2')}
MAXDEPTH = {'A': 3.0, 'B': 3.0, 'C': None}
CLASSES = [('gangsaw_large', 2.7, 1.5, 1.5, 1.00), ('gangsaw_standard', 2.1, 1.2, 1.2, 0.85), ('small_block', 1.5, 0.9, 0.9, 0.55), ('cutter_block', 0.9, 0.6, 0.6, 0.30)]
MAXCAP = (3.3, 2.0, 2.0)   # L, W, H handling cap
SCEN = {'ignore_surface': 0.0, 'surface_0.5m': 0.5, 'surface_1.0m': 1.0, 'surface_full': 99.0}
blocks = sys.argv[1:] or ['A', 'B', 'C']


def classify(dx, dy, dz):
    a, b = sorted((dx, dy), reverse=True)
    if a > MAXCAP[0] or b > MAXCAP[1] or dz > MAXCAP[2]: return None, 0.0
    for nm, L, Wd, Hh, wt in CLASSES:
        if a >= L and b >= Wd and dz >= Hh: return nm, wt
    return None, 0.0


results = {}
for blk in blocks:
    W, H = DIMS[blk]; nx, ny = int(round(W / VOX)), int(round(H / VOX))
    xc = (np.arange(nx) + 0.5) * VOX * 100; yc = (np.arange(ny) + 0.5) * VOX * 100; XC, YC = np.meshgrid(xc, yc)
    surf = {}
    for F in FEATS[blk]:
        a = np.loadtxt(os.path.join(OUT, 'model', '%s_grid_10cm.xyz' % F)); gx = np.unique(a[:, 0]); gy = np.unique(a[:, 1])
        surf[F] = RegularGridInterpolator((gy, gx), a[:, 2].reshape(len(gy), len(gx)), bounds_error=False, fill_value=np.nan)
    if MAXDEPTH[blk] is None:
        cap = surf['C2'](np.c_[YC.ravel(), XC.ravel()]).reshape(ny, nx); cap = np.where(np.isnan(cap), np.nanmedian(cap), cap); zmax = float(np.nanmax(cap)); floor = cap
    else:
        zmax = MAXDEPTH[blk]; floor = np.full((ny, nx), zmax)
    nz = int(np.ceil(zmax / VOX)); zc = (np.arange(nz) + 0.5) * VOX
    sk = {}
    for q in csv.DictReader(open(os.path.join(OUT, 'tables', 'sketch_chained_%s.csv' % blk), encoding='utf-8')):
        sk.setdefault(int(q['trace_id']), []).append((float(q['x_cm']) / 100, float(q['y_cm']) / 100))
    skmask = np.zeros((ny, nx), bool)
    for pts in sk.values():
        pts = np.array(pts)
        for a, b in zip(pts[:-1], pts[1:]):
            for p in np.linspace(a, b, max(2, int(np.hypot(*(b - a)) / (VOX / 2)) + 1)):
                i = int(p[0] / VOX); j = int(p[1] / VOX)
                if 0 <= i < nx and 0 <= j < ny: skmask[j, i] = True
    skmask = binary_dilation(skmask, iterations=max(1, int(round(BUF_SK / VOX))))
    # cut positions
    NX, NY = int(round(W / STEP)), int(round(H / STEP)); NZ = int(np.ceil(zmax / ZSTEP))
    results[blk] = {}
    for sname, sdepth in SCEN.items():
        t0 = time.time()
        free = np.ones((nz, ny, nx), bool)
        for k, z in enumerate(zc): free[k] &= (z < floor - BUF_GPR)
        for F, fz in surf.items():
            if blk == 'C' and F == 'C2': continue
            zs = fz(np.c_[YC.ravel(), XC.ravel()]).reshape(ny, nx)
            for k, z in enumerate(zc): free[k] &= ~(np.abs(z - zs) <= BUF_GPR + VOX / 2)
        for k, z in enumerate(zc):
            if z <= sdepth: free[k] &= ~skmask
        cut = (~free).astype(np.int64); S = np.zeros((nz + 1, ny + 1, nx + 1), np.int64); S[1:, 1:, 1:] = cut.cumsum(0).cumsum(1).cumsum(2)
        r = int(round(STEP / VOX)); rz = int(round(ZSTEP / VOX))
        def ncut(i0, i1, j0, j1, k0, k1):
            """cut voxels inside plan cells [i0,i1) x [j0,j1) and depth steps [k0,k1)"""
            a0, a1, b0, b1, c0, c1 = i0 * r, i1 * r, j0 * r, j1 * r, k0 * rz, min(k1 * rz, nz)
            return int(S[c1, b1, a1] - S[c0, b1, a1] - S[c1, b0, a1] - S[c1, b1, a0] + S[c0, b0, a1] + S[c0, b1, a0] + S[c1, b0, a0] - S[c0, b0, a0])
        @lru_cache(maxsize=None)
        def best(i0, i1, j0, j1, k0, k1):
            """returns (value, tonnes, plan) where plan = ('block', cls) | ('cut', axis, pos, planA, planB) | ('waste',)"""
            nx_, ny_, nz_ = (i1 - i0) * STEP, (j1 - j0) * STEP, (k1 - k0) * ZSTEP        # marked (nominal) size: this is what a quarry classifies on
            dx, dy, dz = nx_ - KERF, ny_ - KERF, nz_ - KERF                                  # finished size after the saw
            whole = None
            if ncut(i0, i1, j0, j1, k0, k1) == 0:
                cls, wt = classify(nx_, ny_, nz_)
                if cls: t = dx * dy * dz * RHO; whole = (t * wt, t, ('block', cls))
            b = whole if whole else (0.0, 0.0, ('waste',))
            for i in range(i0 + 1, i1):
                v1 = best(i, i1, j0, j1, k0, k1); v0 = best(i0, i, j0, j1, k0, k1)
                if v0[0] + v1[0] > b[0] + 1e-9: b = (v0[0] + v1[0], v0[1] + v1[1], ('cut', 'x', i * STEP, (i0, i, j0, j1, k0, k1), (i, i1, j0, j1, k0, k1)))
            for j in range(j0 + 1, j1):
                v1 = best(i0, i1, j, j1, k0, k1); v0 = best(i0, i1, j0, j, k0, k1)
                if v0[0] + v1[0] > b[0] + 1e-9: b = (v0[0] + v1[0], v0[1] + v1[1], ('cut', 'y', j * STEP, (i0, i1, j0, j, k0, k1), (i0, i1, j, j1, k0, k1)))
            for k in range(k0 + 1, k1):
                v1 = best(i0, i1, j0, j1, k, k1); v0 = best(i0, i1, j0, j1, k0, k)
                if v0[0] + v1[0] > b[0] + 1e-9: b = (v0[0] + v1[0], v0[1] + v1[1], ('cut', 'z', k * ZSTEP, (i0, i1, j0, j1, k0, k), (i0, i1, j0, j1, k, k1)))
            return b
        sys.setrecursionlimit(10000)
        val, tons, plan = best(0, NX, 0, NY, 0, NZ)
        # walk the tree: cut list in order (root first, larger sub-box first), leaves as blocks
        cuts = []; leaves = []
        def walk(box, plan, depth):
            if plan[0] == 'block':
                i0, i1, j0, j1, k0, k1 = box; dx, dy, dz = (i1 - i0) * STEP - KERF, (j1 - j0) * STEP - KERF, (k1 - k0) * ZSTEP - KERF
                leaves.append(dict(cls=plan[1], marked=[round((i1 - i0) * STEP, 2), round((j1 - j0) * STEP, 2), round((k1 - k0) * ZSTEP, 2)], x0=i0 * STEP, x1=i1 * STEP, y0=j0 * STEP, y1=j1 * STEP, z0=k0 * ZSTEP, z1=k1 * ZSTEP, L=round(max(dx, dy), 2), Wd=round(min(dx, dy), 2), Hh=round(dz, 2), vol_m3=round(dx * dy * dz, 2), t=round(dx * dy * dz * RHO, 1)))
            elif plan[0] == 'cut':
                i0, i1, j0, j1, k0, k1 = box
                cuts.append(dict(seq=len(cuts) + 1, level=depth, axis=plan[1], pos=plan[2], extent=dict(x=[i0 * STEP, i1 * STEP], y=[j0 * STEP, j1 * STEP], z=[k0 * ZSTEP, k1 * ZSTEP])))
                A, B = plan[3], plan[4]; pa = best(*A)[2]; pb = best(*B)[2]
                # east first: the sub-box with the larger x goes first
                first, second = ((B, pb), (A, pa)) if plan[1] == 'x' else ((A, pa), (B, pb))
                walk(first[0], first[1], depth + 1); walk(second[0], second[1], depth + 1)
        walk((0, NX, 0, NY, 0, NZ), plan, 0)
        # where the floor is a GPR cap (C), a cut need not go past the deepest cap inside its plan extent: say so
        if MAXDEPTH[blk] is None:
            for c in cuts:
                e = c['extent']; i0, i1 = int(e['x'][0] / VOX), int(round(e['x'][1] / VOX)); j0, j1 = int(e['y'][0] / VOX), int(round(e['y'][1] / VOX))
                zcap = float(np.nanmax(floor[j0:j1, i0:i1])); c['capped'] = e['z'][1] > zcap
                if c['capped']: e['z'][1] = round(zcap, 2)
        # removal order: east (large x) to west, top down, then y
        order = sorted(range(len(leaves)), key=lambda i: (-leaves[i]['x1'], leaves[i]['z0'], leaves[i]['y0']))
        for n, i in enumerate(order): leaves[i]['remove_seq'] = n + 1
        summ = {nm: dict(n=sum(1 for b in leaves if b['cls'] == nm), m3=round(sum(b['vol_m3'] for b in leaves if b['cls'] == nm), 1), t=round(sum(b['t'] for b in leaves if b['cls'] == nm), 0)) for nm, *_ in CLASSES}
        gross = float(np.sum(np.minimum(floor, zmax)) * VOX * VOX)
        results[blk][sname] = dict(surface_trace_depth_m=sdepth, gross_rock_m3=round(gross, 1), packed_m3=round(sum(b['vol_m3'] for b in leaves), 1), packed_t=round(tons, 0), recovery_ratio=round(sum(b['vol_m3'] for b in leaves) / gross, 3),
                                   classes=summ, boxes=leaves, cuts=cuts, n_cuts=len(cuts), cut_step_m=STEP, depth_step_m=ZSTEP, class_weights={nm: wt for nm, _, _, _, wt in CLASSES},
                                   depth_limit='C-2 cap' if MAXDEPTH[blk] is None else '%.1f m assumed bench' % zmax, east='grid +x, per the report on Block B; confirm with a compass')
        print('Block %s %-16s guillotine: %d cuts, %d blocks, %.0f t (%.0f%%)  %s  [%.0f s, %d sub-boxes]' % (
            blk, sname, len(cuts), len(leaves), tons, 100 * results[blk][sname]['recovery_ratio'],
            ' '.join('%s:%d' % (nm.split('_')[0][:5] + ('L' if 'large' in nm else 'S' if 'standard' in nm else ''), summ[nm]['n']) for nm, *_ in CLASSES), time.time() - t0, best.cache_info().currsize))
        best.cache_clear()
json.dump(results, open(os.path.join(OUT, 'tables', 'guillotine_packing.json'), 'w'), indent=1)
print('wrote tables/guillotine_packing.json')
