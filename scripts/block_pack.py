"""Free block packing: an UNCONSTRAINED HEURISTIC ESTIMATE of what fits between the fractures, with no requirement
that a saw can reach any of it. Greedy largest-feasible-box packing on the same absolute-frame domain as the
straight-cut plan (packing_domain.py), pooled from 10 cm to 20 cm voxels (a 20 cm cell is free only if all its
10 cm voxels are rock free of any band), so the footprint is exact and nothing is placed above the surface. It is
NOT a proven upper bound on the straight-cut plan: a different grid, a different search, and classification on
finished size. It says roughly how much rock lies between the surfaces, nothing about how to get it out.
Production route for the same problem: Frahan.StonePack.Core BlockCutOptSolver (C#)."""
import numpy as np, os, json, sys, time
sys.path.insert(0, os.path.dirname(__file__))
import packing_domain as PD
OUT = PD.OUT; VOX = 0.20; RHO = 2.95; KERF = 0.05
CLASSES = [('gangsaw_large', 2.7, 1.5, 1.5), ('gangsaw_standard', 2.1, 1.2, 1.2), ('small_block', 1.5, 0.9, 0.9), ('cutter_block', 0.9, 0.6, 0.6)]
MAXCAP = (2.0, 2.0, 3.3)       # (H, W, L) handling cap in metres
blocks = sys.argv[1:] or ['A', 'B', 'C']


def classify(dx, dy, dz):
    a, b = sorted((dx, dy), reverse=True)
    for nm, L, Wd, Hh in CLASSES:
        if a >= L and b >= Wd and dz >= Hh: return nm
    return None


def largest_box(free, minvox, maxvox):
    """largest axis-aligned all-free box with min <= dims <= max per axis (z, y, x), via a 3D integral image; exclusive bounds"""
    nz, ny, nx = free.shape
    cut = (~free).astype(np.int32)
    S = np.zeros((nz + 1, ny + 1, nx + 1), np.int64); S[1:, 1:, 1:] = cut.cumsum(0).cumsum(1).cumsum(2)
    mz, my, mx = minvox; Mz, My, Mx = maxvox
    best = (0, None); xs = np.arange(nx + 1); dxm = xs[None, :] - xs[:, None]; okx = (dxm >= mx) & (dxm <= Mx)
    for z0 in range(0, nz - mz + 1):
        for z1 in range(z0 + mz, min(nz, z0 + Mz) + 1):
            Sz = S[z1] - S[z0]
            for y0 in range(0, ny - my + 1):
                y1s = np.arange(y0 + my, min(ny, y0 + My) + 1)
                if len(y1s) == 0: continue
                A = Sz[y1s, :] - Sz[y0, :]
                Dm = A[:, None, :] - A[:, :, None]
                feas = (Dm == 0) & okx[None]
                if not feas.any(): continue
                vol = np.where(feas, dxm[None] * (y1s - y0)[:, None, None] * (z1 - z0), 0)
                k = int(np.argmax(vol)); v = int(vol.ravel()[k])
                if v > best[0]:
                    ky, kx0, kx1 = np.unravel_index(k, vol.shape); best = (v, (z0, z1, y0, int(y1s[ky]), int(kx0), int(kx1)))
    return best


def pool(free10):
    """20 cm cells free only if every 10 cm voxel in them is free; partial cells at the edges become forbidden"""
    nz, ny, nx = free10.shape; f = 2
    NZ, NY, NX = -(-nz // f), -(-ny // f), -(-nx // f)
    P = np.zeros((NZ * f, NY * f, NX * f), bool); P[:nz, :ny, :nx] = free10
    return P.reshape(NZ, f, NY, f, NX, f).all(axis=(1, 3, 5))


results = {}
for blk in blocks:
    results[blk] = {}
    for unc in PD.UNC:
        for sname, sdepth in PD.SCEN.items():
            t0 = time.time(); D = PD.build(blk, sdepth, unc); free = pool(D['free']); zbot = D['zbot']
            boxes = []; total_free = int(D['free'].sum()) * PD.VOX ** 3
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
                    boxes.append(dict(cls=cls, x0=round(x0 * VOX, 2), x1=round(x1 * VOX, 2), y0=round(y0 * VOX, 2), y1=round(y1 * VOX, 2), z0=round(zbot + z0 * VOX, 2), z1=round(zbot + z1 * VOX, 2),
                                      L=round(max(dx, dy), 2), Wd=round(min(dx, dy), 2), Hh=round(dz, 2), vol_m3=round(dx * dy * dz, 2), t=round(dx * dy * dz * RHO, 1)))
                    free[z0:z1, y0:y1, x0:x1] = False
                    if len(boxes) >= 400: break
            summ = {nm: dict(n=sum(1 for b in boxes if b['cls'] == nm), m3=round(sum(b['vol_m3'] for b in boxes if b['cls'] == nm), 1), t=round(sum(b['t'] for b in boxes if b['cls'] == nm), 0)) for nm, *_ in CLASSES}
            gross = D['gross_rock_m3']; rec = sum(b['vol_m3'] for b in boxes); key = sname + '__' + unc
            results[blk][key] = dict(surface_trace_depth_m=sdepth, uncertainty=unc, gross_rock_m3=gross, free_after_cuts_m3=round(total_free, 1), packed_m3=round(rec, 1), packed_t=round(rec * RHO, 0),
                                     recovery_ratio=round(rec / gross, 3), classes=summ, boxes=boxes, voxel_m=VOX, kerf_m=KERF, bands=D['bands'], chalk_buffer_m=D['chalk_buffer_m'],
                                     floor=D['floor_desc'], frame='bench-frame absolute elevation, metres; x, y on the painted grid', nature='unconstrained heuristic estimate, not a bound and not a plan')
            print('Block %s %-16s %-9s gross %6.1f m3 free %6.1f packed %6.1f m3 (%4.0f t, %.0f%%)  %s  [%.0f s]' % (
                blk, sname, unc, gross, total_free, rec, rec * RHO, 100 * rec / gross, ' '.join('%s:%d' % (nm.split('_')[0][:5] + ('L' if 'large' in nm else 'S' if 'standard' in nm else ''), summ[nm]['n']) for nm, *_ in CLASSES), time.time() - t0))
json.dump(results, open(os.path.join(OUT, 'tables', 'block_packing.json'), 'w'), indent=1)
print('wrote tables/block_packing.json')
