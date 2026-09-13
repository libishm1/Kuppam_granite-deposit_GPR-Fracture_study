"""Straight-cut (guillotine) block plan in ONE physical frame: bench-frame absolute elevation (packing_domain.py).
A wire saw makes through-planes: vertical along the painted 0.5 m lattice, horizontal at absolute elevations on a
0.5 m step. The plan is a recursive bisection of the bench volume by such planes (a guillotine tree), solved exactly
by dynamic programming over every sub-box, maximising class-weighted tonnage. A leaf is a block when it holds no
forbidden voxel (fracture bands, chalked prisms, below the floor); its usable height runs from the cut below it up to
the LOWEST surface point over its footprint (relief is real: the top of the first lift is the rough bench). Every
other leaf holding rock is waste that still has to be lifted. The removal order respects dependencies: nothing is
lifted before every piece above it (block or waste); the priority among ready pieces is east first (EAST, per block), then
top down. A piece's free faces at its own removal time are recorded. Two uncertainty cases per chalk scenario: 'modelled'
(15 cm from the surfaces as drawn) and 'uncertain' (2 sigma of the surface's positional uncertainty, joined with its
migrated position, 20 cm from chalked cracks)."""
import numpy as np, os, json, sys, time
from functools import lru_cache
sys.path.insert(0, os.path.dirname(__file__))
import packing_domain as PD
OUT = PD.OUT; VOX = PD.VOX; STEP = 0.5; RHO = 2.95; KERF = 0.05
CLASSES = [('gangsaw_large', 2.7, 1.5, 1.5, 1.00), ('gangsaw_standard', 2.1, 1.2, 1.2, 0.85), ('small_block', 1.5, 0.9, 0.9, 0.55), ('cutter_block', 0.9, 0.6, 0.6, 0.30)]
MAXCAP = (3.3, 2.0, 2.0)   # L, W, H handling cap
MINH = 0.30                # a leaf with less usable height than this is waste
# East on the painted grid. The client, who laid the grids, reads east along the short side of Block B from B0 toward B1,
# i.e. grid +y, and the same painting convention and orientation on A and C. PARSAN's report reads increasing x as east.
# Carried as the client's reading; a compass on site settles it. Changing this flips the order, not the cuts.
EAST = {'A': '+x', 'B': '+y', 'C': '+y'}   # 12 Sep. Origin is the north-west corner on every bench and both axes run into the bench, but which axis runs east differs: on A the X-line numerals run down the WEST edge from A0 (client, from the site: '9, 12...' from the NW to the SW corner), so X-lines are stacked north-south and run east, +x east, +y south, left-handed. On B and C +y is east (6 m and 8 m sides, verified). See ORIENTATION.md.
EAST_NOTE = "from the site photographs, the surveyors' sketch correlated to the photogrammetry mesh, and the satellite view (ORIENTATION.md): origin at the north-western corner, bench looking east to the ramp; A has +x east, B and C +y east; corner 0 to 1 runs east on all three benches; PARSAN's report reads +x on B; not compass-checked"
blocks = sys.argv[1:] or ['A', 'B', 'C']


def classify(dx, dy, dz):
    a, b = sorted((dx, dy), reverse=True)
    if a > MAXCAP[0] or b > MAXCAP[1] or dz > MAXCAP[2]: return None, 0.0
    for nm, L, Wd, Hh, wt in CLASSES:
        if a >= L and b >= Wd and dz >= Hh: return nm, wt
    return None, 0.0


def solve(blk, D, sdepth=1.0, unc='modelled', quiet=False):
    if True:
        if True:
            t0 = time.time()
            nx, ny, nz = D['nx'], D['ny'], D['nz']; zc = D['zc']; dem = D['dem']; zbot = D['zbot']
            NX, NY = int(round(nx * VOX / STEP)), int(round(ny * VOX / STEP)); NZ = int(round(nz * VOX / STEP)); r = int(round(STEP / VOX))
            bad = (D['cut'] | ~D['rock']) & (zc[:, None, None] < dem[None])          # forbidden or below-floor voxels under the surface; air above the surface is not 'bad'
            S = np.zeros((nz + 1, ny + 1, nx + 1), np.int64); S[1:, 1:, 1:] = bad.astype(np.int64).cumsum(0).cumsum(1).cumsum(2)
            R = np.zeros((nz + 1, ny + 1, nx + 1), np.int64); R[1:, 1:, 1:] = D['rock'].astype(np.int64).cumsum(0).cumsum(1).cumsum(2)
            hsmin = dem.reshape(NY, r, NX, r).min(axis=(1, 3))                          # lowest surface point per lattice cell
            def box_sum(T, i0, i1, j0, j1, k0, k1):
                a0, a1, b0, b1, c0, c1 = i0 * r, i1 * r, j0 * r, j1 * r, k0 * r, k1 * r
                return int(T[c1, b1, a1] - T[c0, b1, a1] - T[c1, b0, a1] - T[c1, b1, a0] + T[c0, b0, a1] + T[c0, b1, a0] + T[c1, b0, a0] - T[c0, b0, a0])
            def usable(i0, i1, j0, j1, k0, k1):
                """usable height of a leaf: from its bottom cut up to the lowest surface point over its footprint, capped by its top"""
                z0 = zbot + k0 * STEP; z1 = zbot + k1 * STEP; top = min(z1, float(hsmin[j0:j1, i0:i1].min()))
                return z0, top
            @lru_cache(maxsize=None)
            def best(i0, i1, j0, j1, k0, k1):
                whole = None
                if box_sum(S, i0, i1, j0, j1, k0, k1) == 0:
                    z0, top = usable(i0, i1, j0, j1, k0, k1); h = top - z0
                    if h >= MINH:
                        nx_, ny_ = (i1 - i0) * STEP, (j1 - j0) * STEP; cls, wt = classify(nx_, ny_, h)
                        if cls: t = (nx_ - KERF) * (ny_ - KERF) * (h - KERF) * RHO; whole = (t * wt, t, ('block', cls))
                b = whole if whole else (0.0, 0.0, ('waste',))
                for i in range(i0 + 1, i1):
                    v0 = best(i0, i, j0, j1, k0, k1); v1 = best(i, i1, j0, j1, k0, k1)
                    if v0[0] + v1[0] > b[0] + 1e-9: b = (v0[0] + v1[0], v0[1] + v1[1], ('cut', 'x', i * STEP, (i0, i, j0, j1, k0, k1), (i, i1, j0, j1, k0, k1)))
                for j in range(j0 + 1, j1):
                    v0 = best(i0, i1, j0, j, k0, k1); v1 = best(i0, i1, j, j1, k0, k1)
                    if v0[0] + v1[0] > b[0] + 1e-9: b = (v0[0] + v1[0], v0[1] + v1[1], ('cut', 'y', j * STEP, (i0, i1, j0, j, k0, k1), (i0, i1, j, j1, k0, k1)))
                for k in range(k0 + 1, k1):
                    v0 = best(i0, i1, j0, j1, k0, k); v1 = best(i0, i1, j0, j1, k, k1)
                    if v0[0] + v1[0] > b[0] + 1e-9: b = (v0[0] + v1[0], v0[1] + v1[1], ('cut', 'z', zbot + k * STEP, (i0, i1, j0, j1, k0, k), (i0, i1, j0, j1, k, k1)))
                return b
            sys.setrecursionlimit(20000)
            val, tons, plan = best(0, NX, 0, NY, 0, NZ)
            # walk the tree: cuts in order (root first, east sub-box first); every leaf with rock is a piece (block or waste)
            cuts = []; pieces = []
            def walk(box, plan, depth):
                i0, i1, j0, j1, k0, k1 = box
                if plan[0] == 'cut':
                    e = dict(x=[i0 * STEP, i1 * STEP], y=[j0 * STEP, j1 * STEP], z=[zbot + k0 * STEP, zbot + k1 * STEP])
                    cuts.append(dict(seq=len(cuts) + 1, level=depth, axis=plan[1], pos=round(plan[2], 3), extent=e))
                    A, B = plan[3], plan[4]; pa, pb = best(*A)[2], best(*B)[2]
                    first, second = ((B, pb), (A, pa)) if plan[1] == EAST[blk][1] else ((A, pa), (B, pb))      # the east sub-box first
                    walk(first[0], first[1], depth + 1); walk(second[0], second[1], depth + 1)
                else:
                    rk = box_sum(R, i0, i1, j0, j1, k0, k1)
                    if rk == 0: return
                    z0, top = usable(i0, i1, j0, j1, k0, k1)
                    piece = dict(kind='block' if plan[0] == 'block' else 'waste', x0=i0 * STEP, x1=i1 * STEP, y0=j0 * STEP, y1=j1 * STEP, z0=round(z0, 3), z1=round(zbot + k1 * STEP, 3),
                                 z_top_usable=round(top, 3), rock_m3=round(rk * VOX ** 3, 2), box=box)
                    if plan[0] == 'block':
                        nx_, ny_, h = (i1 - i0) * STEP, (j1 - j0) * STEP, top - z0; dx, dy, dz = nx_ - KERF, ny_ - KERF, h - KERF
                        piece.update(cls=plan[1], marked=[round(nx_, 2), round(ny_, 2), round(h, 2)], L=round(max(dx, dy), 2), Wd=round(min(dx, dy), 2), Hh=round(dz, 2), vol_m3=round(dx * dy * dz, 2), t=round(dx * dy * dz * RHO, 1),
                                     surface_top=bool(zbot + k1 * STEP > top - 1e-9), depth_top_m=round(float(dem[j0 * r:j1 * r, i0 * r:i1 * r].mean()) - top, 2), depth_bottom_m=round(float(dem[j0 * r:j1 * r, i0 * r:i1 * r].mean()) - z0, 2))
                    pieces.append(piece)
            walk((0, NX, 0, NY, 0, NZ), plan, 0)
            # removal order with dependencies: a piece waits for every piece above it that overlaps it in plan
            def over(a, b): return a['x0'] < b['x1'] and b['x0'] < a['x1'] and a['y0'] < b['y1'] and b['y0'] < a['y1']
            n = len(pieces); deps = [set() for _ in range(n)]
            for a in range(n):
                for b in range(n):
                    if a != b and over(pieces[a], pieces[b]) and pieces[b]['z0'] >= pieces[a]['z1'] - 1e-6: deps[a].add(b)
            done = [False] * n; order = []
            occ = D['rock'].copy()                                                         # rock still in place, for the free-face check
            while len(order) < n:
                ready = [i for i in range(n) if not done[i] and all(done[d] for d in deps[i])]
                if not ready: ready = [i for i in range(n) if not done[i]]              # cannot happen for a guillotine tree, kept as a guard
                ek = 'y1' if EAST[blk] == '+y' else 'x1'; ok_ = 'x0' if EAST[blk] == '+y' else 'y0'
                i = min(ready, key=lambda q: (-pieces[q][ek], -pieces[q]['z1'], pieces[q][ok_]))        # east first, then top down
                p = pieces[i]; a0, a1, b0, b1 = int(round(p['x0'] / VOX)), int(round(p['x1'] / VOX)), int(round(p['y0'] / VOX)), int(round(p['y1'] / VOX))
                c0, c1 = int(round((p['z0'] - zbot) / VOX)), int(round((p['z1'] - zbot) / VOX)); c1 = min(c1, nz)
                faces = []
                if a1 >= nx or not occ[c0:c1, b0:b1, a1:a1 + 1].any(): faces.append('+x')
                if a0 <= 0 or not occ[c0:c1, b0:b1, a0 - 1:a0].any(): faces.append('-x')
                if b1 >= ny or not occ[c0:c1, b1:b1 + 1, a0:a1].any(): faces.append('+y')
                if b0 <= 0 or not occ[c0:c1, b0 - 1:b0, a0:a1].any(): faces.append('-y')
                if c1 >= nz or not occ[c1:c1 + 1, b0:b1, a0:a1].any(): faces.append('top')
                p['free_faces'] = faces; p['remove_seq'] = len(order) + 1; p['after'] = sorted(pieces[d]['remove_seq'] for d in deps[i])
                occ[c0:c1, b0:b1, a0:a1] = False; done[i] = True; order.append(i)
            blocks_ = [dict((k, v) for k, v in p.items() if k != 'box') for p in pieces if p['kind'] == 'block']
            waste = [dict((k, v) for k, v in p.items() if k != 'box') for p in pieces if p['kind'] == 'waste']
            # clearance self-check of every block against every surface (vertical distance at the block's footprint, absolute frame)
            for p in blocks_:
                a0, a1, b0, b1 = int(round(p['x0'] / VOX)), int(round(p['x1'] / VOX)), int(round(p['y0'] / VOX)), int(round(p['y1'] / VOX)); cl = {}
                for F, e in D['surfaces'].items():
                    sub = e[b0:b1, a0:a1]; ok = np.isfinite(sub)
                    if not ok.any(): continue
                    above = sub[ok] - p['z_top_usable']; below = p['z0'] - sub[ok]
                    cl[F] = round(float(np.min(np.where(above > 0, above, np.where(below > 0, below, 0)))), 2)
                p['min_clearance_m'] = cl
            summ = {nm: dict(n=sum(1 for b in blocks_ if b['cls'] == nm), m3=round(sum(b['vol_m3'] for b in blocks_ if b['cls'] == nm), 1), t=round(sum(b['t'] for b in blocks_ if b['cls'] == nm), 0)) for nm, *_ in CLASSES}
            res = dict(surface_trace_depth_m=sdepth, uncertainty=unc, gross_rock_m3=D['gross_rock_m3'], free_rock_m3=D['free_rock_m3'], packed_m3=round(sum(b['vol_m3'] for b in blocks_), 1), packed_t=round(tons, 0),
                                     recovery_ratio=round(sum(b['vol_m3'] for b in blocks_) / D['gross_rock_m3'], 3), classes=summ, boxes=blocks_, waste=waste, cuts=cuts, n_cuts=len(cuts), n_waste=len(waste),
                                     cut_step_m=STEP, floor=D['floor_desc'], bands=D['bands'], chalk_buffer_m=D['chalk_buffer_m'], z_range=[D['zbot'], D['ztop']], class_weights={nm: wt for nm, _, _, _, wt in CLASSES},
                                     frame='bench-frame absolute elevation, metres, z up; x, y on the painted grid', east=EAST_NOTE, east_axis=EAST[blk])
            if not quiet: print('Block %s %-16s %-9s cuts %3d blocks %2d waste %2d  %5.0f t (%2.0f%% of %.0f m3)  %s  [%.0f s, %d states]' % (
                blk, str(sdepth), unc, len(cuts), len(blocks_), len(waste), tons, 100 * res['recovery_ratio'], D['gross_rock_m3'],
                ' '.join('%s:%d' % (nm.split('_')[0][:5] + ('L' if 'large' in nm else 'S' if 'standard' in nm else ''), summ[nm]['n']) for nm, *_ in CLASSES), time.time() - t0, best.cache_info().currsize))
            best.cache_clear()
            return res


if __name__ == '__main__':
    results = {}
    for blk in blocks:
        results[blk] = {}
        for unc in PD.UNC:
            for sname, sdepth in PD.SCEN.items():
                results[blk][sname + '__' + unc] = solve(blk, PD.build(blk, sdepth, unc), sdepth, unc)
    json.dump(results, open(os.path.join(OUT, 'tables', 'guillotine_packing.json'), 'w'), indent=1)
    print('wrote tables/guillotine_packing.json')
