"""Block packing against the fracture model. Voxel volume per block in the report frame (x, y, depth
below the surface), fractures rasterised with a safety buffer, greedy largest-feasible-box packing into
size classes. Scenarios over what the surface-only sketch fractures do at depth, because their depth is
the one thing nobody measured.
Production route for the same problem: Frahan.StonePack.Core BlockCutOptSolver (C#), same family of
greedy maximal-box packing over a fracture-cut volume. This is the transparent Python equivalent."""
import numpy as np, csv, os, json, sys, time
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import binary_dilation
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
VOX = 0.20                     # m
RHO = 2.95                     # t/m3
BUF_GPR = 0.15                 # m, safety around a GPR surface: its own accuracy
BUF_SK = 0.10                  # m, around a sketched surface fracture
KERF = 0.05                    # m, saw allowance on each block face, taken off the reported size
DIMS = {'A': (5.5, 5.5), 'B': (9.5, 6.0), 'C': (7.0, 8.0)}
FEATS = {'A': ('A1', 'A2'), 'B': ('B1', 'B2'), 'C': ('C1', 'C2')}
MAXDEPTH = {'A': 3.0, 'B': 3.0, 'C': None}          # C: the C-2 cap; A, B: assumed bench height, no floor was surveyed
# size classes, metres, sorted largest first. Plan dims are interchangeable (L, W), H is vertical.
CLASSES = [('gangsaw_large', 2.7, 1.5, 1.5), ('gangsaw_standard', 2.1, 1.2, 1.2), ('small_block', 1.5, 0.9, 0.9), ('cutter_block', 0.9, 0.6, 0.6)]
SCEN = {'ignore_surface': 0.0, 'surface_0.5m': 0.5, 'surface_1.0m': 1.0, 'surface_full': 99.0}
blocks = sys.argv[1:] or ['A', 'B', 'C']


def classify(dx, dy, dz):
    a, b = sorted((dx, dy), reverse=True)
    for nm, L, Wd, Hh in CLASSES:
        if a >= L and b >= Wd and dz >= Hh: return nm
    return None


def surface_depth(F):
    a = np.loadtxt(os.path.join(OUT, 'model', '%s_grid_10cm.xyz' % F)); n = len(np.unique(a[:, 0])); m = len(np.unique(a[:, 1]))
    gx = np.unique(a[:, 0]); gy = np.unique(a[:, 1]); Z = a[:, 2].reshape(m, n)
    return RegularGridInterpolator((gy, gx), Z, bounds_error=False, fill_value=np.nan), (gx.min(), gx.max(), gy.min(), gy.max())


MAXCAP = (2.0, 2.0, 3.3)       # (H, W, L) handling cap in metres: what a loader and a gangsaw take


def largest_box(free, minvox, maxvox):
    """largest axis-aligned all-free box with min <= dims <= max per axis (z, y, x), via 3D integral image.
    returns (volume_vox, (z0,z1,y0,y1,x0,x1)) exclusive bounds"""
    nz, ny, nx = free.shape
    cut = (~free).astype(np.int32)
    S = np.zeros((nz + 1, ny + 1, nx + 1), np.int64); S[1:, 1:, 1:] = cut.cumsum(0).cumsum(1).cumsum(2)
    mz, my, mx = minvox; Mz, My, Mx = maxvox
    best = (0, None)
    xs = np.arange(nx + 1)
    dxm = xs[None, :] - xs[:, None]                                   # (x0, x1)
    okx = (dxm >= mx) & (dxm <= Mx)
    for z0 in range(0, nz - mz + 1):
        for z1 in range(z0 + mz, min(nz, z0 + Mz) + 1):
            Sz = S[z1] - S[z0]
            for y0 in range(0, ny - my + 1):
                y1s = np.arange(y0 + my, min(ny, y0 + My) + 1)
                if len(y1s) == 0: continue
                A = Sz[y1s, :] - Sz[y0, :]                           # (ky, nx+1)
                D = A[:, None, :] - A[:, :, None]                     # (ky, x0, x1)
                feas = (D == 0) & okx[None]
                if not feas.any(): continue
                vol = np.where(feas, dxm[None] * (y1s - y0)[:, None, None] * (z1 - z0), 0)
                k = int(np.argmax(vol)); v = int(vol.ravel()[k])
                if v > best[0]:
                    ky, kx0, kx1 = np.unravel_index(k, vol.shape); best = (v, (z0, z1, y0, int(y1s[ky]), int(kx0), int(kx1)))
    return best


results = {}
for blk in blocks:
    W, H = DIMS[blk]; nx, ny = int(round(W / VOX)), int(round(H / VOX))
    dem = np.loadtxt(os.path.join(OUT, 'model', 'v2_topo', 'Block%s_DEM_10cm.xyz' % blk)); nn = len(np.unique(dem[:, 0])); mm = len(np.unique(dem[:, 1]))
    surf = {}
    for F in FEATS[blk]: surf[F] = surface_depth(F)
    # depth limit
    xc = (np.arange(nx) + 0.5) * VOX * 100; yc = (np.arange(ny) + 0.5) * VOX * 100; XC, YC = np.meshgrid(xc, yc)
    if MAXDEPTH[blk] is None:
        f2, _ = surf['C2']; cap = f2(np.c_[YC.ravel(), XC.ravel()]).reshape(ny, nx); cap = np.where(np.isnan(cap), np.nanmedian(cap), cap)
        zmax = float(np.nanmax(cap)); floor = cap
    else:
        zmax = MAXDEPTH[blk]; floor = np.full((ny, nx), zmax)
    nz = int(np.ceil(zmax / VOX)); zc = (np.arange(nz) + 0.5) * VOX
    # sketch traces
    sk = {}
    for q in csv.DictReader(open(os.path.join(OUT, 'tables', 'sketch_chained_%s.csv' % blk), encoding='utf-8')):
        sk.setdefault(int(q['trace_id']), []).append((float(q['x_cm']) / 100, float(q['y_cm']) / 100))
    # 2D mask of sketch traces (with buffer)
    skmask = np.zeros((ny, nx), bool)
    for pts in sk.values():
        pts = np.array(pts)
        for a, b in zip(pts[:-1], pts[1:]):
            n = max(2, int(np.hypot(*(b - a)) / (VOX / 2)) + 1)
            for p in np.linspace(a, b, n):
                i = int(p[0] / VOX); j = int(p[1] / VOX)
                if 0 <= i < nx and 0 <= j < ny: skmask[j, i] = True
    skmask = binary_dilation(skmask, iterations=max(1, int(round(BUF_SK / VOX))))
    results[blk] = {}
    for sname, sdepth in SCEN.items():
        t0 = time.time()
        free = np.ones((nz, ny, nx), bool)
        # below the floor / cap -> not extractable
        for k, z in enumerate(zc): free[k] &= (z < floor - BUF_GPR)
        # GPR surfaces: cut voxels within BUF_GPR of the surface (in depth)
        for F, (fz, _) in surf.items():
            if blk == 'C' and F == 'C2': continue           # already the floor
            zs = fz(np.c_[YC.ravel(), XC.ravel()]).reshape(ny, nx)
            for k, z in enumerate(zc):
                free[k] &= ~(np.abs(z - zs) <= BUF_GPR + VOX / 2)
        # sketch surface fractures, vertical to sdepth
        for k, z in enumerate(zc):
            if z <= sdepth: free[k] &= ~skmask
        boxes = []; total_free = int(free.sum())
        vx = lambda m: int(np.ceil(m / VOX)); vX = lambda m: int(np.floor(m / VOX))
        for nm, Lc, Wc, Hc in CLASSES:
            while True:
                cands = []
                for (lx, ly) in ((Lc, Wc), (Wc, Lc)):
                    minvox = (vx(Hc + KERF), vx(ly + KERF), vx(lx + KERF)); maxvox = (vX(MAXCAP[0]), vX(MAXCAP[1] if ly == Wc else MAXCAP[2]), vX(MAXCAP[2] if lx == Lc else MAXCAP[1]))
                    v, box = largest_box(free, minvox, maxvox)
                    if box is not None: cands.append((v, box))
                if not cands: break
                v, (z0, z1, y0, y1, x0, x1) = max(cands, key=lambda c: c[0])
                dx, dy, dz = (x1 - x0) * VOX - KERF, (y1 - y0) * VOX - KERF, (z1 - z0) * VOX - KERF
                cls = classify(dx, dy, dz) or nm
                boxes.append(dict(cls=cls, x0=round(x0 * VOX, 2), x1=round(x1 * VOX, 2), y0=round(y0 * VOX, 2), y1=round(y1 * VOX, 2), z0=round(z0 * VOX, 2), z1=round(z1 * VOX, 2),
                                  L=round(max(dx, dy), 2), Wd=round(min(dx, dy), 2), Hh=round(dz, 2), vol_m3=round(dx * dy * dz, 2), t=round(dx * dy * dz * RHO, 1)))
                free[z0:z1, y0:y1, x0:x1] = False
                if len(boxes) >= 400: break
        summ = {}
        for nm, *_ in CLASSES:
            bb = [b for b in boxes if b['cls'] == nm]; summ[nm] = dict(n=len(bb), m3=round(sum(b['vol_m3'] for b in bb), 1), t=round(sum(b['t'] for b in bb), 0))
        gross = float(np.sum(np.minimum(floor, zmax)) * VOX * VOX)
        rec = sum(b['vol_m3'] for b in boxes)
        results[blk][sname] = dict(surface_trace_depth_m=sdepth, gross_rock_m3=round(gross, 1), free_after_cuts_m3=round(total_free * VOX ** 3, 1),
                                   packed_m3=round(rec, 1), packed_t=round(rec * RHO, 0), recovery_ratio=round(rec / gross, 3), classes=summ, boxes=boxes,
                                   voxel_m=VOX, buffers_m=dict(gpr=BUF_GPR, sketch=BUF_SK, kerf=KERF), depth_limit='C-2 cap' if MAXDEPTH[blk] is None else '%.1f m assumed bench' % zmax)
        print('Block %s  %-16s gross %6.1f m3  free %6.1f  packed %6.1f m3 (%4.0f t, %.0f%%)  %s   [%.0f s]' % (
            blk, sname, gross, total_free * VOX ** 3, rec, rec * RHO, 100 * rec / gross,
            ' '.join('%s:%d' % (nm.split('_')[0][:5] + ('L' if 'large' in nm else 'S' if 'standard' in nm else ''), summ[nm]['n']) for nm, *_ in CLASSES), time.time() - t0))
json.dump(results, open(os.path.join(OUT, 'tables', 'block_packing.json'), 'w'), indent=1)
print('wrote tables/block_packing.json')
