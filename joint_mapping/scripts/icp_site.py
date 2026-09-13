"""Register the Block A and Block B photogrammetry models onto the Block C model of the same
Kuppam dolerite pit, and measure how well determined that registration is.

Each of the three Metashape models was already carried into its own bench frame (metres, z up,
that block's painted bench top at z = 0) by scripts/load_mesh.py. The three bench frames share a
scale and a z axis but nothing else: each has its own origin, its own rotation about z and its own
z datum. The unknown between a block and C is therefore close to 4 parameters, a yaw and a
translation, rather than a general 6-DOF pose. The search exploits that. The last stage then
releases roll and pitch and reports how far the 4-DOF premise was actually off, because a bench
plane fitted independently in each model does not land on exactly the same vertical.

Method
  1. voxel-centroid downsample both clouds (0.25 / 0.10 / 0.05 m).
  2. coarse 4-DOF search. C is rasterised at 25 cm, a Euclidean distance transform gives the
     distance from every cell to the nearest C point, and score = exp(-(d/0.35 m)^2). For each yaw
     on a 2 degree sweep the rotated source is rasterised on the same lattice and cross-correlated
     with that score volume by FFT. One FFT per yaw returns the score of EVERY 25 cm translation
     at once, so the translation search is exhaustive over C's extent rather than sampled.
  3. the strongest well-separated peaks (>= 2 m apart, or >= 12 degrees apart in yaw) are kept.
  4. each candidate is refined by point-to-plane ICP at 25, 10 and 5 cm, locked to yaw plus
     translation. Target normals come from local PCA on the 16 nearest neighbours.
     Correspondences beyond the level gate are dropped and the worst 20 percent of the rest are
     trimmed.
  5. roll and pitch are then released for a final 5 cm point-to-plane pass. The extra rotation is
     reported; it is the measured violation of the z-up assumption, not a free parameter that was
     wanted. Uniform scale is checked on a grid and reported, never applied.
  6. every candidate is scored on the same footing: rms of the final residual, and the fraction of
     source points whose nearest C point is within 10 cm.

What the numbers mean, and what they do not
  A high inlier fraction says the two clouds are locally consistent where they were put. It does
  NOT say the pose is unique. A quarry is a stack of near-horizontal benches and near-vertical
  faces, so a wrong pose that slides one bench along another, or swaps one bench for a parallel
  one, can be almost as locally consistent as the right one. Five things are therefore reported
  beside each solution and have to be read with it.
    - the best OTHER local minimum that is far from the best one in pose. If its score is close,
      the pose is not determined by this data, whatever the residual says.
    - two null levels. The loose null randomises all 4 parameters. The strict null keeps the
      solved z and randomises only yaw and x, y, which is the honest chance level once the bench
      planes are stacked: it asks whether anything beyond "put a bench on a bench" was established.
    - the residual split by source surface orientation. If the near-horizontal points fit and the
      near-vertical points do not, the solve has stacked two benches and learned nothing about
      x, y or yaw. Agreement on the quarry faces is what pins the horizontal pose.
    - a sensitivity sweep: the inlier fraction as the solution is pushed off the optimum in x, y,
      z and yaw. The half-width at 90 percent of the peak measures how tightly each parameter is
      held, with no distribution assumption, unlike the covariance from the normal matrix.
    - the eigenvalues of the point-to-plane normal matrix and the 1-sigma spread from it. That
      covariance is local and optimistic: it assumes independent residuals and is blind to the
      other minima. The sensitivity sweep is the one to trust.
  Candidates are ranked on the inlier fraction WITHIN THE OVERLAP, not over every source point.
  The unnormalised fraction is biased: a pose that buries more of the source inside the target
  scores higher because it is covered, not because it fits. That bias is strong enough to pick the
  wrong pose outright when the two clouds only partly overlap, which is what happens on B -> A.

  A -> C, B -> C and B -> A are all solved independently, and the triangle is then closed:
  T(A<-B) composed with T(C<-A) is compared against T(C<-B). When it fails to close, the two rival
  A <- B poses are re-scored inside their real overlap, which identifies which leg slipped. A and
  B carried into C's frame are also compared against each other directly, a check that never
  touches C.

  There is still no ground truth. The method cannot prove a converged pose is the true one. It can
  show whether the data leaves a competing alternative, and whether three independent pairwise
  solves agree. There is also no absolute georeference anywhere in this chain, so the result places
  the benches inside C's own arbitrary frame, not on the ground.

Usage: icp_site.py [yaw_step_deg]
"""
import numpy as np, json, os, sys, time
from scipy.spatial import cKDTree
from scipy import ndimage
from scipy.signal import fftconvolve
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = 'D:/code_ws/outputs/2026-09-11/joint_mapping'
CACHE = os.path.join(OUT, 'cache', 'mesh_%s.npz')

LEVELS = (0.25, 0.10, 0.05)
MAX_D = {0.25: 1.00, 0.10: 0.40, 0.05: 0.20}
ITERS = {0.25: 50, 0.10: 35, 0.05: 30}
FINE = 0.05
COARSE_V = 0.25
COARSE_SIGMA = 0.35
YAW_STEP = 2.0
PEAKS_PER_YAW = 6
N_CAND = 12
SEP_T = 2.0                  # m, below this two candidates are the same minimum
SEP_YAW = 12.0               # deg
TRIM = 0.80
KNORM = 16
N_NULL = 240
NULL_PTS = 25000
SENS_PTS = 30000
HORIZ_NZ = 0.80              # |nz| above this is a bench / floor point
VERT_NZ = 0.50               # |nz| below this is a quarry face point
GATE = 0.10                  # m, the inlier gate every headline fraction is quoted at
COVER_R = 1.00               # m, a source point with target surface this close counts as covered
# Ranking floor. The within-overlap fraction alone can be won by a pose that hangs most of the
# source off the edge of the target and fits the sliver that remains, so a candidate must cover at
# least this much of the source before its within-overlap score is allowed to compete.
MIN_COVER = 0.60
# "sharp" is one order of magnitude tighter than the 2 m / 12 deg scale that defines two poses as
# different minima. Anything looser than this is sliding, not solving.
SHARP_T = 0.50               # m
SHARP_YAW = 3.0              # deg
SEED = 20260911
# east axis of each bench frame, copied from scripts/facets.py in this folder. A prior on yaw, not
# a measurement: these are nearest-cardinal axis labels out of ORIENTATION.md, not compass work,
# so two blocks carrying the same label can still differ by up to 45 degrees.
EAST_TOL = 45.0
EAST = {'A': '+x', 'B': '+y', 'C': '+y'}   # 12 Sep. Origin is the north-west corner on every bench and both axes run into the bench, but which axis runs east differs: on A the X-line numerals run down the WEST edge from A0 (client, from the site: '9, 12...' from the NW to the SW corner), so X-lines are stacked north-south and run east, +x east, +y south, left-handed. On B and C +y is east (6 m and 8 m sides, verified). See ORIENTATION.md.
AXIS = {'+x': 0.0, '+y': 90.0, '-x': 180.0, '-y': 270.0}
ZUP = np.array([0.0, 0.0, 1.0])


def log(s):
    print(s, flush=True)


def Rz(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def wrap180(a):
    return (a + 180.0) % 360.0 - 180.0


def yaw_of(R):
    return float(np.degrees(np.arctan2(R[1, 0], R[0, 0])) % 360.0)


def tilt_of(R):
    return float(np.degrees(np.arccos(np.clip((R @ ZUP)[2], -1.0, 1.0))))


def angle_between(R1, R2):
    return float(np.degrees(np.arccos(np.clip((np.trace(R1 @ R2.T) - 1.0) / 2.0, -1.0, 1.0))))


def vdown(P, v):
    """voxel centroid downsample"""
    k = np.floor(P / v).astype(np.int64)
    k -= k.min(0)
    dims = k.max(0) + 1
    key = (k[:, 0] * dims[1] + k[:, 1]) * dims[2] + k[:, 2]
    order = np.argsort(key, kind='stable')
    key, Ps = key[order], P[order]
    first = np.empty(len(key), bool)
    first[0] = True
    first[1:] = key[1:] != key[:-1]
    inv = np.cumsum(first) - 1
    n = int(inv[-1]) + 1
    out = np.empty((n, 3))
    for j in range(3):
        out[:, j] = np.bincount(inv, Ps[:, j], n)
    return out / np.bincount(inv, None, n)[:, None]


def pca_normals(P, k=KNORM, chunk=150000):
    """unit normal per point, smallest eigenvector of the local covariance. Sign is left
    arbitrary; the point-to-plane residual is invariant to it."""
    tree = cKDTree(P)
    N = np.empty_like(P)
    for i0 in range(0, len(P), chunk):
        idx = tree.query(P[i0:i0 + chunk], k=k, workers=-1)[1]
        Q = P[idx]
        Q = Q - Q.mean(1, keepdims=True)
        cov = np.einsum('mki,mkj->mij', Q, Q)
        N[i0:i0 + chunk] = np.linalg.eigh(cov)[1][:, :, 0]
    return tree, N


def pyramid(P, name):
    """voxel pyramid of a target cloud, with normals and the coarse score volume"""
    lv = {}
    for v in LEVELS:
        t0 = time.time()
        D = vdown(P, v)
        tree, N = pca_normals(D)
        lv[v] = (tree, D, N)
        log('  %s %4.2f m -> %8d pts, normals %.0f s' % (name, v, len(D), time.time() - t0))
    score, ox = target_volume(lv[COARSE_V][1])
    return dict(levels=lv, tree=lv[FINE][0], score=score, ox=ox,
                bbox=(P.min(0), P.max(0)), name=name)


def target_volume(C, v=COARSE_V, sigma=COARSE_SIGMA, pad=2.0):
    ox = C.min(0) - pad
    dims = np.ceil((C.max(0) + pad - ox) / v).astype(int) + 1
    occ = np.zeros(dims, bool)
    occ[tuple(np.floor((C - ox) / v).astype(int).T)] = True
    d = ndimage.distance_transform_edt(~occ, sampling=v)
    return np.exp(-(d / sigma) ** 2).astype(np.float32), ox


def coarse_search(S, score, ox, tbb, v=COARSE_V, yaw_step=YAW_STEP):
    """exhaustive translation search at every yaw by FFT cross-correlation.
    Returns peaks (yaw_deg, t, score) sorted by score, and the per-yaw best score profile."""
    yaws = np.arange(0.0, 360.0, yaw_step)
    peaks, prof = [], np.zeros(len(yaws))
    cen0 = S.mean(0)
    for iy, a in enumerate(yaws):
        R = Rz(np.radians(a))
        P = S @ R.T
        sox = P.min(0)
        sij = np.floor((P - sox) / v).astype(int)
        sdim = sij.max(0) + 1
        src = np.zeros(sdim, np.float32)
        src[tuple(sij.T)] = 1.0
        corr = fftconvolve(score, src[::-1, ::-1, ::-1], mode='full') / float(src.sum())
        prof[iy] = corr.max()
        flat = corr.ravel()
        ntop = min(600, flat.size)
        top = np.argpartition(flat, -ntop)[-ntop:]
        top = top[np.argsort(flat[top])[::-1]]
        kij = np.array(np.unravel_index(top, corr.shape)).T
        t = (kij - (sdim - 1)) * v + (ox - sox)
        cen = cen0 @ R.T + t
        ok = np.all((cen >= tbb[0] - 1.0) & (cen <= tbb[1] + 1.0), axis=1)
        t, sc = t[ok], flat[top][ok]
        kept = []
        for j in range(len(t)):
            if all(np.linalg.norm(t[j] - t[m]) >= 1.5 for m in kept):
                kept.append(j)
            if len(kept) >= PEAKS_PER_YAW:
                break
        for j in kept:
            peaks.append((float(a), t[j].copy(), float(sc[j])))
    peaks.sort(key=lambda p: -p[2])
    return peaks, yaws, prof


def separated(a1, t1, a2, t2):
    return np.linalg.norm(np.asarray(t1) - np.asarray(t2)) >= SEP_T or abs(wrap180(a1 - a2)) >= SEP_YAW


def select(peaks, n=N_CAND):
    out = []
    for a, t, s in peaks:
        if all(separated(a, t, a2, t2) for a2, t2, _ in out):
            out.append((a, t, s))
        if len(out) >= n:
            break
    return out


def icp_4dof(S, tgt, yaw_deg, t, max_d, iters):
    """point-to-plane ICP with the rotation locked to yaw, 4 unknowns.
    p' = Rz(yaw) p + t, residual r = n . (dR p' + dt - q) with dR ~ I + alpha [z]x.
    Composition is exact: yaw <- yaw + alpha, t <- Rz(alpha) t + dt."""
    tree, T, NT = tgt
    yaw = np.radians(yaw_deg)
    H, npairs, sse, nit = np.eye(4), 0, np.nan, 0
    for nit in range(1, iters + 1):
        P = S @ Rz(yaw).T + t
        d, j = tree.query(P, k=1, workers=-1)
        m = d < max_d
        if m.sum() < 60:
            break
        m &= d <= np.quantile(d[m], TRIM)
        p, q, n = P[m], T[j[m]], NT[j[m]]
        J = np.empty((len(p), 4))
        J[:, 0] = n[:, 1] * p[:, 0] - n[:, 0] * p[:, 1]       # n . (z x p)
        J[:, 1:] = n
        r = -np.einsum('ij,ij->i', n, p - q)
        H = J.T @ J
        try:
            x = np.linalg.solve(H + 1e-9 * (np.trace(H) / 4.0 + 1e-12) * np.eye(4), J.T @ r)
        except np.linalg.LinAlgError:
            break
        x[0] = float(np.clip(x[0], -0.25, 0.25))
        t = Rz(x[0]) @ t + x[1:]
        yaw = yaw + x[0]
        npairs, sse = int(len(p)), float(((J @ x - r) ** 2).sum())
        if abs(x[0]) < 1e-7 and np.linalg.norm(x[1:]) < 1e-6:
            break
    return float(np.degrees(yaw)) % 360.0, t, H, npairs, sse, nit


def icp_6dof(S, tgt, R, t, max_d=MAX_D[FINE], iters=40):
    """release roll and pitch. Full point-to-plane, r = n . (dR p' + dt - q), dR ~ I + [w]x,
    so the Jacobian column block for w is (p x n)."""
    tree, T, NT = tgt
    R, t = R.copy(), t.copy()
    for _ in range(iters):
        P = S @ R.T + t
        d, j = tree.query(P, k=1, workers=-1)
        m = d < max_d
        if m.sum() < 60:
            break
        m &= d <= np.quantile(d[m], TRIM)
        p, q, n = P[m], T[j[m]], NT[j[m]]
        J = np.hstack([np.cross(p, n), n])
        r = -np.einsum('ij,ij->i', n, p - q)
        x = np.linalg.lstsq(J, r, rcond=None)[0]
        w = np.clip(x[:3], -0.2, 0.2)
        th = np.linalg.norm(w)
        if th < 1e-12:
            dR = np.eye(3)
        else:
            K = np.array([[0, -w[2], w[1]], [w[2], 0, -w[0]], [-w[1], w[0], 0]]) / th
            dR = np.eye(3) + np.sin(th) * K + (1.0 - np.cos(th)) * K @ K
        R, t = dR @ R, dR @ t + x[3:]
        if th < 1e-7 and np.linalg.norm(x[3:]) < 1e-6:
            break
    return R, t


def hessian_report(H, npairs, sse):
    """local 1-sigma spread of the 4 parameters from the point-to-plane normal matrix.
    Optimistic: independent-residual assumption, and blind to other minima."""
    out = dict(eigenvalues=[], sigma_yaw_deg=None, sigma_t_m=None, cond=None,
               note='local and optimistic; assumes independent residuals, cannot see other minima')
    if npairs <= 5:
        return out
    w = np.linalg.eigvalsh(H)
    out['eigenvalues'] = [float(v) for v in w]
    out['cond'] = float(w[-1] / w[0]) if w[0] > 0 else None
    try:
        cov = (sse / max(npairs - 4, 1)) * np.linalg.inv(H)
        s = np.sqrt(np.clip(np.diag(cov), 0.0, None))
        out['sigma_yaw_deg'] = float(np.degrees(s[0]))
        out['sigma_t_m'] = [float(v) for v in s[1:]]
    except np.linalg.LinAlgError:
        pass
    return out


def nn_dist(S, tree, R, t):
    return tree.query(S @ R.T + t, k=1, workers=-1)[0]


def metrics(d):
    """d is the nearest-target distance for every source point.

    frac_lt_10cm is over EVERY source point, so it is depressed by whatever part of the source the
    target never saw. That makes it unusable for ranking rival poses: a pose that buries more of
    the source inside the target scores higher for coverage reasons alone, not for fit. The
    within-overlap figure divides instead by the source points that have any target surface within
    COVER_R, which is the standard inlier ratio over the overlap, and is what ranks candidates."""
    inl = d < MAX_D[FINE]
    cov = d < COVER_R
    return dict(rms_residual_m=float(np.sqrt((d[inl] ** 2).mean())) if inl.any() else None,
                rms_all_m=float(np.sqrt((d ** 2).mean())), median_nn_m=float(np.median(d)),
                frac_lt_05cm=float((d < 0.05).mean()), frac_lt_10cm=float((d < GATE).mean()),
                frac_lt_20cm=float((d < 0.20).mean()), frac_lt_50cm=float((d < 0.50).mean()),
                coverage_frac=float(cov.mean()),
                frac_lt_10cm_within_overlap=float((d[cov] < GATE).mean()) if cov.any() else 0.0,
                median_nn_within_overlap_m=float(np.median(d[cov])) if cov.any() else None,
                n_source_points=int(len(d)),
                note='rms_residual_m is over correspondences inside the %.2f m gate. frac_lt_10cm '
                     'is over every source point. frac_lt_10cm_within_overlap divides by the '
                     'source points with target surface within %.2f m and is the ranking score.'
                     % (MAX_D[FINE], COVER_R))


def mat4(R, t):
    M = np.eye(4)
    M[:3, :3], M[:3, 3] = R, t
    return M


def as_list(M):
    return [[float(v) for v in row] for row in np.asarray(M)]


def null_level(S, tree, tbb, rng, n=N_NULL, npts=NULL_PTS, fix_z=None):
    """Chance level for the 10 cm inlier fraction.
    fix_z=None randomises all 4 parameters (loose null).
    fix_z=<solved tz> randomises only yaw and x, y and keeps the solved z (strict null): the
    chance level once the bench planes are already stacked."""
    sub = S if len(S) <= npts else S[rng.choice(len(S), npts, replace=False)]
    cen = sub.mean(0)
    f = []
    for _ in range(n):
        R = Rz(np.radians(rng.uniform(0.0, 360.0)))
        t = rng.uniform(tbb[0], tbb[1]) - cen @ R.T
        if fix_z is not None:
            t[2] = fix_z
        f.append(float((nn_dist(sub, tree, R, t) < GATE).mean()))
    f = np.array(f)
    return dict(n=int(n), randomised=('yaw,x,y,z' if fix_z is None else 'yaw,x,y (z held at the solution)'),
                mean=float(f.mean()), p50=float(np.median(f)),
                p95=float(np.percentile(f, 95)), max=float(f.max()))


def orientation_split(S, NS, tree, R, t):
    """residual split by source surface orientation. A fit carried only by the near-horizontal
    points is two benches stacked, which says nothing about x, y or yaw."""
    d = nn_dist(S, tree, R, t)
    out = {}
    for name, m in (('horizontal', np.abs(NS[:, 2]) > HORIZ_NZ),
                    ('vertical', np.abs(NS[:, 2]) < VERT_NZ)):
        if not m.any():
            out[name] = None
            continue
        dd = d[m]
        inl = dd < MAX_D[FINE]
        out[name] = dict(n=int(m.sum()), frac_of_source=float(m.mean()),
                         frac_lt_10cm=float((dd < GATE).mean()), median_nn_m=float(np.median(dd)),
                         rms_residual_m=float(np.sqrt((dd[inl] ** 2).mean())) if inl.any() else None)
    return out


def sensitivity(S, tree, R, t, rng, npts=SENS_PTS):
    """push the solution off the optimum along each parameter and watch the 10 cm inlier
    fraction. The half-width at 90 percent of the peak measures how tightly the data holds that
    parameter, with no distribution assumption."""
    sub = S if len(S) <= npts else S[rng.choice(len(S), npts, replace=False)]

    def f10(dyaw, dt):
        D = Rz(np.radians(dyaw))
        return float((nn_dist(sub, tree, D @ R, D @ t + dt) < GATE).mean())

    peak = f10(0.0, np.zeros(3))
    out = dict(peak_frac_lt_10cm=peak, axes={})
    grids = dict(dx=np.arange(-3.0, 3.001, 0.10), dy=np.arange(-3.0, 3.001, 0.10),
                 dz=np.arange(-3.0, 3.001, 0.10), dyaw=np.arange(-20.0, 20.001, 0.5))
    for ax, g in grids.items():
        vals = []
        for o in g:
            if ax == 'dyaw':
                vals.append(f10(o, np.zeros(3)))
            else:
                dt = np.zeros(3)
                dt[{'dx': 0, 'dy': 1, 'dz': 2}[ax]] = o
                vals.append(f10(0.0, dt))
        vals = np.array(vals)
        thr = 0.90 * peak
        hw = []
        for sgn in (1, -1):
            bad = np.where((g * sgn > 0) & (vals < thr))[0]
            hw.append(float(abs(g[bad[np.argmin(np.abs(g[bad]))]])) if len(bad) else float(np.abs(g).max()))
        out['axes'][ax] = dict(offsets=[float(x) for x in g], frac_lt_10cm=[float(x) for x in vals],
                               half_width_at_90pct=round(float(np.mean(hw)), 4),
                               unit=('deg' if ax == 'dyaw' else 'm'))
    return out


def scale_check(S, tree, R, t, rng, npts=SENS_PTS):
    """uniform scale swept about the solution centroid. Reported, never applied: a scale far from
    1.0 would mean the two Metashape models disagree on metric scale."""
    sub = S if len(S) <= npts else S[rng.choice(len(S), npts, replace=False)]
    P = sub @ R.T + t
    c = P.mean(0)
    ss = np.arange(0.94, 1.0601, 0.005)
    f = [float((tree.query((P - c) * s + c, k=1, workers=-1)[0] < GATE).mean()) for s in ss]
    k = int(np.argmax(f))
    return dict(scales=[float(x) for x in ss], frac_lt_10cm=f, best_scale=float(ss[k]),
                best_frac=float(f[k]), frac_at_unit_scale=float(f[list(np.round(ss, 3)).index(1.0)]))


def footprint(S, R, t):
    lo, hi = S.min(0), S.max(0)
    c = np.array([[lo[0], lo[1], 0.0], [hi[0], lo[1], 0.0], [hi[0], hi[1], 0.0], [lo[0], hi[1], 0.0]])
    return (c @ R.T + t)[:, :2]


def register(sname, src, tgt, rng, yaw_step, full_analysis=True):
    """one pairwise registration, source cloud -> target pyramid"""
    tag = '%s -> %s' % (sname, tgt['name'])
    log('\n=== %s ===' % tag)
    t00 = time.time()
    S = {v: vdown(src, v) for v in LEVELS}
    log('  source %d pts; downsampled %s' % (len(src), {v: len(S[v]) for v in LEVELS}))

    peaks, yaws, prof = coarse_search(S[COARSE_V], tgt['score'], tgt['ox'], tgt['bbox'], yaw_step=yaw_step)
    cands = select(peaks)
    log('  coarse: %d peaks, %d separated candidates, %.0f s' % (len(peaks), len(cands), time.time() - t00))

    sols = []
    for ci, (a0, t0c, s0) in enumerate(cands):
        a, t = a0, t0c.copy()
        H, npairs, sse, nit = np.eye(4), 0, np.nan, 0
        for v in LEVELS:
            a, t, H, npairs, sse, nit = icp_4dof(S[v], tgt['levels'][v], a, t, MAX_D[v], ITERS[v])
        R4 = Rz(np.radians(a))
        m4 = metrics(nn_dist(S[FINE], tgt['tree'], R4, t))
        R6, t6 = icp_6dof(S[FINE], tgt['levels'][FINE], R4, t)
        m6 = metrics(nn_dist(S[FINE], tgt['tree'], R6, t6))
        sols.append(dict(
            candidate=ci, coarse_score=float(s0), coarse_yaw_deg=float(a0),
            coarse_t_m=[float(x) for x in t0c],
            pose_4dof=dict(yaw_deg=float(a), t_m=[float(x) for x in t], matrix=as_list(mat4(R4, t)),
                           metrics=m4),
            pose_released=dict(yaw_deg=yaw_of(R6), t_m=[float(x) for x in t6],
                               matrix=as_list(mat4(R6, t6)),
                               tilt_from_vertical_deg=tilt_of(R6),
                               extra_rotation_vs_4dof_deg=angle_between(R6, R4), metrics=m6),
            n_icp_pairs=int(npairs), icp_iters_final_level=int(nit),
            conditioning=hessian_report(H, npairs, sse)))
        log('    cand %2d -> yaw %6.2f  t %7.3f %7.3f %7.3f | 4dof f10 %.3f | released f10 %.3f  '
            'in-overlap %.3f (cover %.2f)  rms %s  tilt %.2f deg'
            % (ci, a, t[0], t[1], t[2], m4['frac_lt_10cm'], m6['frac_lt_10cm'],
               m6['frac_lt_10cm_within_overlap'], m6['coverage_frac'],
               ('%.4f' % m6['rms_residual_m']) if m6['rms_residual_m'] is not None else 'n/a',
               tilt_of(R6)))

    def rank(s):
        m = s['pose_released']['metrics']
        return (0 if m['coverage_frac'] >= MIN_COVER else 1,
                -m['frac_lt_10cm_within_overlap'], m['median_nn_within_overlap_m'])

    sols.sort(key=rank)
    if sols[0]['pose_released']['metrics']['coverage_frac'] < MIN_COVER:
        log('  WARNING: no candidate covers %.0f %% of the source; ranking is unreliable' % (100 * MIN_COVER))
    best = sols[0]
    bp = best['pose_released']
    Rb, tb = np.array(bp['matrix'])[:3, :3], np.array(bp['t_m'])
    second = next((s for s in sols[1:]
                   if separated(bp['yaw_deg'], tb, s['pose_released']['yaw_deg'], s['pose_released']['t_m'])), None)

    res = dict(source=sname, target=tgt['name'], n_source_points_raw=int(len(src)),
               best=best, second_best=second, all_candidates=sols,
               coarse_yaw_profile=dict(yaw_deg=[float(x) for x in yaws],
                                       best_score=[float(x) for x in prof]))
    log('  BEST 4-DOF     yaw %.3f  t (%.3f, %.3f, %.3f)  f10 %.4f  rms %.4f m'
        % (best['pose_4dof']['yaw_deg'], *best['pose_4dof']['t_m'],
           best['pose_4dof']['metrics']['frac_lt_10cm'], best['pose_4dof']['metrics']['rms_residual_m']))
    log('  BEST released  yaw %.3f  t (%.3f, %.3f, %.3f)  f10 %.4f  in-overlap %.4f  rms %.4f m  tilt %.3f deg'
        % (bp['yaw_deg'], *bp['t_m'], bp['metrics']['frac_lt_10cm'],
           bp['metrics']['frac_lt_10cm_within_overlap'], bp['metrics']['rms_residual_m'],
           bp['tilt_from_vertical_deg']))

    if second is not None:
        sp = second['pose_released']
        b_ov = bp['metrics']['frac_lt_10cm_within_overlap']
        res['separation'] = dict(
            d_yaw_deg=float(abs(wrap180(bp['yaw_deg'] - sp['yaw_deg']))),
            d_translation_m=float(np.linalg.norm(tb - np.array(sp['t_m']))),
            score_ratio=float(sp['metrics']['frac_lt_10cm_within_overlap'] / b_ov) if b_ov > 0 else None,
            score='frac_lt_10cm_within_overlap')
        log('  SECOND         yaw %.3f  t (%.3f, %.3f, %.3f)  in-overlap %.4f  (d_yaw %.1f deg, d_t %.2f m, ratio %.3f)'
            % (sp['yaw_deg'], *sp['t_m'], sp['metrics']['frac_lt_10cm_within_overlap'],
               res['separation']['d_yaw_deg'], res['separation']['d_translation_m'],
               res['separation']['score_ratio']))
    else:
        log('  SECOND         none separated from the best')

    if not full_analysis:
        res['seconds'] = float(time.time() - t00)
        return res, S, nn_dist(S[FINE], tgt['tree'], Rb, tb)

    null = null_level(S[FINE], tgt['tree'], tgt['bbox'], rng)
    null_z = null_level(S[FINE], tgt['tree'], tgt['bbox'], rng, fix_z=float(tb[2]))
    _, NS = pca_normals(S[FINE])
    osplit = orientation_split(S[FINE], NS, tgt['tree'], Rb, tb)
    sens = sensitivity(S[FINE], tgt['tree'], Rb, tb, rng)
    sc = scale_check(S[FINE], tgt['tree'], Rb, tb, rng)
    res.update(null_random_pose=null, null_random_pose_z_held=null_z,
               residual_by_surface_orientation=osplit, sensitivity=sens, scale_check=sc)
    log('  null loose  (yaw,x,y,z random): mean %.4f  p95 %.4f  max %.4f' % (null['mean'], null['p95'], null['max']))
    log('  null strict (z held, yaw+xy)  : mean %.4f  p95 %.4f  max %.4f' % (null_z['mean'], null_z['p95'], null_z['max']))
    for k in ('horizontal', 'vertical'):
        o = osplit[k]
        log('  %-10s %6d pts (%4.1f %%)  f10 %.4f  median nn %.4f m'
            % (k, o['n'], 100 * o['frac_of_source'], o['frac_lt_10cm'], o['median_nn_m']))
    hw = {a: sens['axes'][a]['half_width_at_90pct'] for a in sens['axes']}
    log('  half-width at 90 pct of peak: ' + '  '.join('%s %.2f %s' % (a, hw[a], sens['axes'][a]['unit'])
                                                       for a in ('dx', 'dy', 'dz', 'dyaw')))
    log('  scale: best %.3f (f10 %.3f) vs unit scale f10 %.3f' % (sc['best_scale'], sc['best_frac'], sc['frac_at_unit_scale']))

    exp_yaw = (AXIS[EAST[tgt['name']]] - AXIS[EAST[sname]]) % 360.0
    dev = float(wrap180(bp['yaw_deg'] - exp_yaw))
    res['east_axis_prior'] = dict(
        source_east=EAST[sname], target_east=EAST[tgt['name']], expected_yaw_deg=float(exp_yaw),
        found_minus_expected_deg=dev, tolerance_deg=EAST_TOL, consistent=bool(abs(dev) <= EAST_TOL),
        note='nearest-cardinal axis labels from scripts/facets.py, not compass work, so agreement '
             'is only meaningful to about +/- 45 deg')

    c = res.get('separation')
    f10b = bp['metrics']['frac_lt_10cm']
    tests = dict(
        above_strict_null=bool(f10b > 1.5 * max(null_z['max'], 1e-6)),
        best_absolute=bool(f10b >= 0.50),
        beats_second=bool(second is None or (c and c['score_ratio'] is not None and c['score_ratio'] < 0.70)),
        vertical_faces_support=bool(osplit['vertical'] is not None and osplit['vertical']['n'] >= 5000
                                    and osplit['vertical']['frac_lt_10cm'] >= 0.60 * f10b),
        sharp_optimum=bool(max(hw['dx'], hw['dy'], hw['dz']) <= SHARP_T and hw['dyaw'] <= SHARP_YAW),
        east_axis_prior_consistent=bool(abs(dev) <= EAST_TOL))
    core = ('above_strict_null', 'best_absolute', 'beats_second', 'vertical_faces_support', 'sharp_optimum')
    res['tests'] = tests
    res['determined'] = bool(all(tests[k] for k in core))
    res['verdict'] = 'registered' if res['determined'] else 'ambiguous or unresolved'
    res['verdict_note'] = ('east_axis_prior_consistent is reported but not required: those labels are '
                           'nearest-cardinal, so they can only falsify a result by more than 45 deg.')
    log('  tests %s' % tests)
    log('  VERDICT %s -> %s' % (tag, res['verdict'].upper()))
    res['seconds'] = float(time.time() - t00)
    return res, S, nn_dist(S[FINE], tgt['tree'], Rb, tb)


def overlap_fit(Psrc, tree, Ptgt, T):
    """score a pose only where the source actually lands inside the target's footprint, so two
    rival poses are compared on equal footing instead of one winning by covering more ground"""
    P = Psrc @ T[:3, :3].T + T[:3, 3]
    lo, hi = Ptgt.min(0) + 0.5, Ptgt.max(0) - 0.5
    ins = np.all((P[:, :2] >= lo[:2]) & (P[:, :2] <= hi[:2]), axis=1)
    if ins.sum() < 1000:
        return dict(n_inside=int(ins.sum()), frac_inside=float(ins.mean()), frac_lt_10cm=0.0,
                    median_nn_m=None)
    d = tree.query(P[ins], k=1, workers=-1)[0]
    return dict(n_inside=int(ins.sum()), frac_inside=float(ins.mean()),
                frac_lt_10cm=float((d < GATE).mean()), frac_lt_20cm=float((d < 0.20).mean()),
                median_nn_m=float(np.median(d)))


def triangle(res_ac, res_bc, res_ba, SA, SB, treeA):
    """close the loop: T(C<-A) . T(A<-B) should equal T(C<-B). The three solves never share a
    correspondence, so agreement is independent of the residual statistics above. When it does not
    close, the two rival A<-B poses are re-scored inside their true overlap to say which leg
    slipped."""
    T_ca = np.array(res_ac['best']['pose_released']['matrix'])
    T_cb = np.array(res_bc['best']['pose_released']['matrix'])
    T_ab = np.array(res_ba['best']['pose_released']['matrix'])
    pred_cb = T_ca @ T_ab
    pred_ab = np.linalg.inv(T_ca) @ T_cb
    dR = angle_between(pred_cb[:3, :3], T_cb[:3, :3])
    dt = pred_cb[:3, 3] - T_cb[:3, 3]
    direct = overlap_fit(SB, treeA, SA, T_ab)
    composed = overlap_fit(SB, treeA, SA, pred_ab)
    out = dict(
        predicted_C_from_B=as_list(pred_cb), solved_C_from_B=as_list(T_cb),
        rotation_disagreement_deg=float(dR),
        translation_disagreement_m=[float(x) for x in dt],
        translation_disagreement_norm_m=float(np.linalg.norm(dt)),
        closes=bool(dR < 1.0 and np.linalg.norm(dt) < 0.30),
        rival_A_from_B=dict(direct_B_to_A_solve=direct, composed_from_A_to_C_and_B_to_C=composed,
                            separation_m=float(np.linalg.norm(T_ab[:3, 3] - pred_ab[:3, 3])),
                            better=('composed' if composed['frac_lt_10cm'] > direct['frac_lt_10cm']
                                    else 'direct')),
        note='T(C<-A) composed with T(A<-B) against the independent T(C<-B). rival_A_from_B '
             're-scores the two competing A<-B poses inside their real overlap, which identifies '
             'which of the three legs is the weak one.')
    log('\n=== triangle closure ===')
    log('  rotation disagreement %.4f deg, translation disagreement %.4f m (%s)'
        % (dR, np.linalg.norm(dt), 'CLOSES' if out['closes'] else 'DOES NOT CLOSE'))
    log('  rival A<-B poses %.3f m apart, scored inside the real overlap:' % out['rival_A_from_B']['separation_m'])
    for k, v in (('direct B->A solve', direct), ('composed from the other two legs', composed)):
        log('    %-34s %6d B pts inside A (%4.1f %%)  f10 %.4f  median %s'
            % (k, v['n_inside'], 100 * v['frac_inside'], v['frac_lt_10cm'],
               ('%.4f m' % v['median_nn_m']) if v['median_nn_m'] else 'n/a'))
    log('  -> the %s pose fits better inside the overlap' % out['rival_A_from_B']['better'])
    return out


def ab_agreement(SA, SB, res_ac, res_bc):
    """A and B both carried into C's frame, then compared against EACH OTHER. If both are placed
    correctly they must agree where they overlap, and this never touches C."""
    T_ca = np.array(res_ac['best']['pose_released']['matrix'])
    T_cb = np.array(res_bc['best']['pose_released']['matrix'])
    PB = SB @ T_cb[:3, :3].T + T_cb[:3, 3]
    out = overlap_fit(SA, cKDTree(PB), PB, T_ca)
    out['note'] = ('A points that land inside the registered B footprint, measured against the '
                   'registered B cloud. Two independent photogrammetry models with no common '
                   'control, so this is looser than either block against C.')
    log('\n=== A against B inside C frame ===')
    log('  %d A pts inside B (%.1f %%)  f10 %.4f  f20 %.4f  median %.4f m'
        % (out['n_inside'], 100 * out['frac_inside'], out['frac_lt_10cm'], out['frac_lt_20cm'],
           out['median_nn_m']))
    return out


def figure(results, C10, srcS, dists, path):
    fig, ax = plt.subplots(2, 4, figsize=(23, 10.5))
    rng = np.random.default_rng(SEED)
    Cp = C10 if len(C10) <= 160000 else C10[rng.choice(len(C10), 160000, replace=False)]
    for row, blk in enumerate(('A', 'B')):
        r = results[blk]
        S = srcS[blk][FINE]
        d = dists[blk]
        bp = r['best']['pose_released']
        R = np.array(bp['matrix'])[:3, :3]
        t = np.array(bp['t_m'])
        P = S @ R.T + t
        k = np.arange(len(P)) if len(P) <= 90000 else rng.choice(len(P), 90000, replace=False)

        a0 = ax[row, 0]
        a0.scatter(Cp[:, 0], Cp[:, 1], s=0.6, c='0.78', lw=0, rasterized=True)
        sc = a0.scatter(P[k, 0], P[k, 1], s=0.8, c=np.clip(d[k], 0, 0.30), cmap='viridis',
                        vmin=0, vmax=0.30, lw=0, rasterized=True)
        fp = footprint(S, R, t)
        a0.plot(np.r_[fp[:, 0], fp[0, 0]], np.r_[fp[:, 1], fp[0, 1]], 'k-', lw=1.6, label='best')
        if r['second_best'] is not None:
            sp = r['second_best']['pose_released']
            fp2 = footprint(S, np.array(sp['matrix'])[:3, :3], np.array(sp['t_m']))
            a0.plot(np.r_[fp2[:, 0], fp2[0, 0]], np.r_[fp2[:, 1], fp2[0, 1]], 'r--', lw=1.6,
                    label='2nd min  f10=%.2f' % sp['metrics']['frac_lt_10cm'])
        a0.legend(loc='upper right', fontsize=8)
        a0.set_aspect('equal')
        a0.set_title('%s on C, plan view (C grey). yaw %.2f deg, t (%.2f, %.2f, %.2f) m'
                     % (blk, bp['yaw_deg'], *bp['t_m']), fontsize=9.5)
        a0.set_xlabel('x  C frame (m)')
        a0.set_ylabel('y  C frame (m)')
        plt.colorbar(sc, ax=a0, shrink=0.82, label='nearest C point (m)')

        a1 = ax[row, 1]
        a1.hist(np.clip(d, 0, 1.0), bins=120, color='#3b6ea5')
        a1.axvline(GATE, color='crimson', ls='--', lw=1.4)
        a1.set_yscale('log')
        a1.set_xlabel('distance to nearest C point (m)')
        a1.set_ylabel('source points (5 cm voxels)')
        a1.set_title('%s residual. rms %.3f m, within 10 cm %.1f %%, median %.3f m'
                     % (blk, bp['metrics']['rms_residual_m'], 100 * bp['metrics']['frac_lt_10cm'],
                        bp['metrics']['median_nn_m']), fontsize=9.5)

        a2 = ax[row, 2]
        pr = r['coarse_yaw_profile']
        a2.plot(pr['yaw_deg'], pr['best_score'], '-', color='#444444', lw=1.2)
        a2.axvline(r['best']['coarse_yaw_deg'], color='k', lw=1.4,
                   label='best %.0f deg' % r['best']['coarse_yaw_deg'])
        if r['second_best'] is not None:
            a2.axvline(r['second_best']['coarse_yaw_deg'], color='crimson', ls='--', lw=1.4,
                       label='2nd %.0f deg' % r['second_best']['coarse_yaw_deg'])
        a2.axvline(r['east_axis_prior']['expected_yaw_deg'], color='#1a7f37', ls=':', lw=1.8,
                   label='east-axis prior %.0f deg' % r['east_axis_prior']['expected_yaw_deg'])
        a2.set_xlabel('yaw (deg)')
        a2.set_ylabel('best coarse score over all translations')
        a2.set_title('%s coarse landscape. Flat = yaw not resolved' % blk, fontsize=9.5)
        a2.legend(fontsize=8)

        a3 = ax[row, 3]
        sn = r['sensitivity']
        a3b = a3.twiny()
        for axn, col in (('dx', '#c0392b'), ('dy', '#2e86c1'), ('dz', '#117a65')):
            s = sn['axes'][axn]
            a3.plot(s['offsets'], s['frac_lt_10cm'], color=col, lw=1.4,
                    label='%s  half-width %.2f m' % (axn, s['half_width_at_90pct']))
        s = sn['axes']['dyaw']
        a3b.plot(s['offsets'], s['frac_lt_10cm'], color='#7d3c98', lw=1.4, ls='--',
                 label='dyaw  half-width %.2f deg' % s['half_width_at_90pct'])
        nz = r['null_random_pose_z_held']['max']
        a3.axhline(nz, color='0.4', ls=':', lw=1.3)
        a3.text(-2.9, nz, ' strict null max %.2f' % nz, fontsize=7.5, va='bottom', color='0.35')
        a3.set_xlabel('offset from the solution in x, y, z (m)')
        a3b.set_xlabel('offset in yaw (deg)', color='#7d3c98')
        a3.set_ylabel('fraction of source points within 10 cm')
        a3.set_ylim(0, 1)
        h1, l1 = a3.get_legend_handles_labels()
        h2, l2 = a3b.get_legend_handles_labels()
        a3.legend(h1 + h2, l1 + l2, fontsize=7.5, loc='lower center')
        a3.set_title('%s determinacy. Narrow = the data holds the pose' % blk, fontsize=9.5)
    fig.suptitle('Block A and Block B registered onto Block C, Kuppam. 4-DOF search (yaw + translation), '
                 'roll and pitch released at 5 cm. No ground truth: read the 2nd minimum, the null and '
                 'the determinacy panel with the residual.', fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    fig.savefig(path, dpi=135)
    log('\nwrote %s' % path)


def main():
    yaw_step = float(sys.argv[1]) if len(sys.argv) > 1 else YAW_STEP
    rng = np.random.default_rng(SEED)
    t00 = time.time()

    raw = {b: np.load(CACHE % b)['xyz'].astype(np.float64) for b in 'ABC'}
    for b in 'ABC':
        lo, hi = raw[b].min(0), raw[b].max(0)
        log('Block %s  %9d pts  x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f m'
            % (b, len(raw[b]), lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))

    log('\nbuilding target pyramid for C')
    pyrC = pyramid(raw['C'], 'C')
    log('  coarse score volume %s at %.2f m' % (pyrC['score'].shape, COARSE_V))

    results, dists, srcS = {}, {}, {}
    for blk in ('A', 'B'):
        r, S, d = register(blk, raw[blk], pyrC, rng, yaw_step)
        results[blk], srcS[blk], dists[blk] = r, S, d

    log('\nbuilding target pyramid for A (for the triangle check)')
    pyrA = pyramid(raw['A'], 'A')
    res_ba, SB, _ = register('B', raw['B'], pyrA, rng, yaw_step, full_analysis=False)
    SA_f, SB_f = pyrA['levels'][FINE][1], SB[FINE]
    tri = triangle(results['A'], results['B'], res_ba, SA_f, SB_f, pyrA['tree'])
    agree = ab_agreement(SA_f, SB_f, results['A'], results['B'])

    out = dict(
        generated=time.strftime('%Y-%m-%dT%H:%M:%S'), script='scripts/icp_site.py',
        target='C', sources=['A', 'B'], seconds=float(time.time() - t00),
        parameters=dict(levels=list(LEVELS), max_corr_dist_m=MAX_D, icp_iters=ITERS,
                        coarse_voxel_m=COARSE_V, coarse_sigma_m=COARSE_SIGMA,
                        yaw_step_deg=yaw_step, n_candidates=N_CAND, separation_m=SEP_T,
                        separation_yaw_deg=SEP_YAW, trim_fraction=TRIM, normal_k=KNORM,
                        inlier_gate_m=GATE, sharp_threshold_m=SHARP_T, sharp_threshold_deg=SHARP_YAW,
                        seed=SEED,
                        search_dof='yaw + 3 translations, then roll and pitch released at 5 cm'),
        caveats=[
            'No ground truth. A converged pose cannot be confirmed as the true one here; the '
            'evidence offered is that no competing pose comes close and that three independent '
            'pairwise solves close the triangle.',
            'The conditioning covariance is local and optimistic; the sensitivity sweep is the '
            'measure to read.',
            'Benches and quarry faces are near-planar, so plane-on-plane sliding is the dominant '
            'failure mode. The strict null, the vertical-face residual and the second minimum '
            'test for it.',
            'No absolute georeference: poses are inside C bench frame only, which is itself '
            'arbitrary in x, y and yaw.'],
        blocks={b: results[b] for b in results},
        cross_check_B_to_A=res_ba, triangle_check=tri, ab_agreement_in_C_frame=agree)
    jp = os.path.join(OUT, 'tables', 'icp_site.json')
    with open(jp, 'w') as f:
        json.dump(out, f, indent=1)
    log('\nwrote %s' % jp)

    figure(results, pyrC['levels'][0.10][1], srcS, dists, os.path.join(OUT, 'figs', 'ICP_site.png'))
    log('total %.0f s' % (time.time() - t00))


if __name__ == '__main__':
    main()
