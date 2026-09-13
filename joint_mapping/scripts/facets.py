"""Joint orientations from the exposed rock faces of a photogrammetry model, in that block's bench frame.

After Dewez's FACETS and Riquelme's DSE, written from scratch:
  1. voxel-downsample so the (very uneven) photogrammetric density is level
  2. local PCA on the K nearest neighbours -> normal and planarity (l2 - l3) / l1
  3. drop the painted bench top itself (that surface is the GPR study's subject)
  4. region-grow planar patches over the precomputed K-NN graph: a neighbour joins if its normal
     agrees to ANG_TOL and it lies within PLANE_TOL of the running plane
  5. refit by SVD; keep patches above MIN_PTS and MIN_AREA
  6. dip from the bench plane, dip direction as a grid bearing (0 = +y, 90 = +x), then an
     approximate azimuth through the block's east axis

Two things this cannot do. Dip is measured from the bench plane, not from gravity, and the bench
tilts 1 to 2 degrees, so every dip carries that as a systematic. Azimuth rests on the east axis of
ORIENTATION.md and is not compass-measured. A quarry face cut by a wire saw is also a plane, and
this finds those too; they are flagged, not removed, by area and by their place in the pit.

Usage: facets.py A|B|C [vox_cm]"""
import numpy as np, sys, os, json, time
from scipy.spatial import cKDTree

OUT = 'D:/code_ws/outputs/2026-09-11/joint_mapping'
K = 18
KG = 10             # neighbours used for growing
PLANARITY = 0.55
ANG_TOL = 12.0
PLANE_TOL = 0.035
MIN_PTS = 100
MIN_AREA = 0.25
EAST = {'A': '+x', 'B': '+y', 'C': '+y'}   # 12 Sep. Origin is the north-west corner on every bench and both axes run into the bench, but which axis runs east differs: on A the X-line numerals run down the WEST edge from A0 (client, from the site: '9, 12...' from the NW to the SW corner), so X-lines are stacked north-south and run east, +x east, +y south, left-handed. On B and C +y is east (6 m and 8 m sides, verified). See ORIENTATION.md.


def voxel_down(P, C, vox):
    key = np.floor(P / vox).astype(np.int64)
    _, idx = np.unique(key, axis=0, return_index=True)
    return P[idx], (C[idx] if C is not None and len(C) == len(P) else None)


def normals(P, k=K):
    tree = cKDTree(P)
    _, nb = tree.query(P, k=k, workers=-1)
    Q = P[nb] - P[nb].mean(1, keepdims=True)
    cov = np.einsum('nki,nkj->nij', Q, Q) / k
    w, v = np.linalg.eigh(cov)
    return tree, nb, v[:, :, 0], (w[:, 1] - w[:, 0]) / np.maximum(w[:, 2], 1e-12)


def grow(P, nb, nrm, planarity, keep, scale):
    """region-grow over the K-NN graph; returns labels and patch dicts"""
    order = np.argsort(-planarity); order = order[keep[order]]
    lab = np.full(len(P), -1, np.int32); patches = []
    cos_tol = np.cos(np.radians(ANG_TOL)); nbg = nb[:, 1:1 + KG]
    for seed in order:
        if lab[seed] >= 0: continue
        pid = len(patches); stack = [seed]; lab[seed] = pid; pts = [seed]
        n0 = nrm[seed].copy(); c0 = P[seed].copy(); nref = 64
        while stack:
            i = stack.pop()
            for j in nbg[i]:
                if lab[j] >= 0 or not keep[j]: continue
                if abs(nrm[j] @ n0) < cos_tol: continue
                if abs((P[j] - c0) @ n0) > PLANE_TOL: continue
                lab[j] = pid; stack.append(j); pts.append(j)
            if len(pts) >= nref:
                Q = P[pts]; c0 = Q.mean(0); n0 = np.linalg.svd(Q - c0, full_matrices=False)[2][2]; nref *= 2
        if len(pts) < MIN_PTS:
            for j in pts: lab[j] = -1
            continue
        Q = P[pts]; c = Q.mean(0)
        u, s, vt = np.linalg.svd(Q - c, full_matrices=False)
        n = vt[2]; ext = (Q - c) @ vt.T
        span = [float(ext[:, 0].max() - ext[:, 0].min()), float(ext[:, 1].max() - ext[:, 1].min())]
        area = span[0] * span[1]
        if area < MIN_AREA:
            for j in pts: lab[j] = -1
            continue
        patches.append(dict(n=n, c=c, npts=len(pts), area=float(area), span=span,
                            rms=float(np.sqrt(np.mean(((Q - c) @ n) ** 2))),
                            fill=float(len(pts) * scale ** 2 / max(area, 1e-6))))
    return lab, patches


def dip_of(n):
    n = n / np.linalg.norm(n)
    if n[2] < 0: n = -n
    dip = float(np.degrees(np.arccos(np.clip(n[2], -1, 1))))
    # the upward normal leans toward the DOWN-dip side, so the dip direction is the trend of
    # its horizontal part: bearing = atan2(n_x, n_y), the convention the GPR study uses
    d = np.array([n[0], n[1]])
    if np.linalg.norm(d) < 1e-9: return dip, 0.0
    return dip, float(np.degrees(np.arctan2(d[0], d[1])) % 360)


def azimuth(brg, blk):
    """grid bearing (0 = +y, 90 = +x) to azimuth, using the handedness in ORIENTATION.md:
    on A and C +x is east and +y south, on B +y is east and +x south."""
    return (180 - brg) % 360 if EAST[blk] == '+x' else (brg + 90) % 360


if __name__ == '__main__':
    blk = sys.argv[1].upper(); VOX = (float(sys.argv[2]) if len(sys.argv) > 2 else 3.0) / 100; t0 = time.time()
    z = np.load(os.path.join(OUT, 'cache', 'mesh_%s.npz' % blk))
    P = z['xyz'].astype(np.float64); C = z['rgb']; grid = z['grid']
    print('Block %s: %d points, voxel %.0f cm' % (blk, len(P), VOX * 100), flush=True)
    P, C = voxel_down(P, C, VOX)
    print('  %d after downsample  [%.0f s]' % (len(P), time.time() - t0), flush=True)
    tree, nb, nrm, planarity = normals(P)
    print('  normals  [%.0f s]' % (time.time() - t0), flush=True)
    on_bench = ((P[:, 0] > -0.5) & (P[:, 0] < grid[0] + 0.5) & (P[:, 1] > -0.5) & (P[:, 1] < grid[1] + 0.5)
                & (np.abs(P[:, 2]) < 0.6) & (np.abs(nrm[:, 2]) > np.cos(np.radians(25))))
    keep = (planarity > PLANARITY) & (~on_bench)
    print('  %d planar, %d on the painted bench, %d kept' % ((planarity > PLANARITY).sum(), on_bench.sum(), keep.sum()), flush=True)
    lab, patches = grow(P, nb, nrm, planarity, keep, VOX)
    print('  %d patches  [%.0f s]' % (len(patches), time.time() - t0), flush=True)
    rows = []
    for i, p in enumerate(patches):
        dip, brg = dip_of(p['n'])
        rows.append(dict(patch=i, dip_deg=round(dip, 1), grid_bearing_deg=round(brg, 1),
                         dip_dir_azimuth_deg=round(azimuth(brg, blk), 1), n_points=p['npts'],
                         area_m2=round(p['area'], 2), span_m=[round(s, 2) for s in p['span']],
                         rms_m=round(p['rms'], 4), fill=round(p['fill'], 2),
                         centre=[round(float(x), 2) for x in p['c']], normal=[round(float(x), 4) for x in p['n']]))
    json.dump(dict(block=blk, east_axis=EAST[blk], vox_m=VOX, k=K, k_grow=KG, planarity_min=PLANARITY,
                   ang_tol_deg=ANG_TOL, plane_tol_m=PLANE_TOL, min_pts=MIN_PTS, min_area_m2=MIN_AREA,
                   n_points=int(len(P)), n_kept=int(keep.sum()),
                   dip_frame='from this block\'s bench plane, not gravity; the bench tilts 1 to 2 deg',
                   azimuth_note='via the east axis of ORIENTATION.md; not compass-measured',
                   patches=rows), open(os.path.join(OUT, 'tables', 'facets_%s.json' % blk), 'w'), indent=1)
    np.savez_compressed(os.path.join(OUT, 'cache', 'facets_%s.npz' % blk), xyz=P.astype(np.float32), lab=lab,
                        nrm=nrm.astype(np.float32), planarity=planarity.astype(np.float32), keep=keep,
                        rgb=(C if C is not None else np.zeros((0, 3), np.uint8)))
    print('  wrote tables/facets_%s.json  [%.0f s]' % (blk, time.time() - t0), flush=True)
