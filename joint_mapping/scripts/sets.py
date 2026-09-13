"""Cluster the extracted facet normals into joint sets, and describe each set.

Axial k-means on the sphere (a pole has no up or down, so the distance is 1 - (n.m)^2), seeded at
random and repeated, with the set count chosen by an axial silhouette over 2 to 6. For each set:
mean pole from the orientation tensor, dip and dip direction, Fisher concentration K and the 95 per
cent cone, facet count and total area, and a crude normal spacing from facet pairs that are close
to each other in plan.

Facets larger than CUT_AREA that are also smooth are flagged as possible saw-cut faces. A wire-sawn
wall is a plane too, and in this pit the biggest planes are quarry faces rather than joints, so
every set is reported twice: with them and without them.

Usage: sets.py A|B|C
"""
import numpy as np, sys, os, json
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

EAST = {'A': '+x', 'B': '+y', 'C': '+y'}   # 12 Sep. Origin is the north-west corner on every bench and both axes run into the bench, but which axis runs east differs: on A the X-line numerals run down the WEST edge from A0 (client, from the site: '9, 12...' from the NW to the SW corner), so X-lines are stacked north-south and run east, +x east, +y south, left-handed. On B and C +y is east (6 m and 8 m sides, verified). See ORIENTATION.md.

OUT = 'D:/code_ws/outputs/2026-09-11/joint_mapping'
CUT_AREA = 4.0
CUT_RMS = 0.025


def axial_kmeans(N, k, iters=60, seed=0):
    rng = np.random.default_rng(seed)
    M = N[rng.choice(len(N), k, replace=False)].copy()
    lab = np.zeros(len(N), int)
    for _ in range(iters):
        d = 1 - (N @ M.T) ** 2
        lab = d.argmin(1)
        for j in range(k):
            Q = N[lab == j]
            if len(Q) < 2:
                M[j] = N[rng.integers(len(N))]
                continue
            T = Q.T @ Q / len(Q)
            w, v = np.linalg.eigh(T)
            M[j] = v[:, -1]
    return lab, M


def silhouette(N, lab, M):
    d = 1 - (N @ M.T) ** 2
    a = d[np.arange(len(N)), lab].copy()
    d[np.arange(len(N)), lab] = np.inf
    b = d.min(1)
    return float(np.mean((b - a) / np.maximum(np.maximum(a, b), 1e-12)))


def describe(Q):
    T = (Q.T @ Q) / len(Q)
    w, v = np.linalg.eigh(T)
    m = v[:, -1]
    if m[2] < 0:
        m = -m
    dip = float(np.degrees(np.arccos(np.clip(abs(m[2]), -1, 1))))
    # the upward normal leans toward the DOWN-dip side, so the dip direction is the trend of
    # its horizontal part: bearing = atan2(n_x, n_y), the convention the GPR study uses
    dd = np.array([m[0], m[1]])
    brg = float(np.degrees(np.arctan2(dd[0], dd[1])) % 360) if np.linalg.norm(dd) > 1e-9 else 0.0
    R = float(np.abs(Q @ m).sum())
    n = len(Q)
    K = (n - 1) / max(n - R, 1e-6)
    cone = float('nan')
    if n > 2 and R < n:
        arg = 1 - (n - R) / R * (20 ** (1 / (n - 1)) - 1)
        if -1 <= arg <= 1:
            cone = float(np.degrees(np.arccos(arg)))
    return m, dip, brg, float(K), cone, float(w[-1] / max(w.sum(), 1e-12))


def spacing(cent, m, maxlat=5.0):
    """normal offsets between facets of one set whose centres are close in plan"""
    t = cent @ m
    proj = cent - np.outer(t, m)
    out = []
    for i in range(len(cent)):
        d = np.linalg.norm(proj - proj[i], axis=1)
        near = (d < maxlat) & (np.arange(len(cent)) != i)
        if near.any():
            off = np.abs(t[near] - t[i])
            off = off[off > 0.05]
            if len(off):
                out.append(float(off.min()))
    return (float(np.median(out)), len(out)) if out else (float('nan'), 0)


if __name__ == '__main__':
    blk = sys.argv[1].upper()
    D = json.load(open(os.path.join(OUT, 'tables', 'facets_%s.json' % blk)))
    P = D['patches']
    N = np.array([p['normal'] for p in P], float)
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    A = np.array([p['area_m2'] for p in P])
    Rr = np.array([p['rms_m'] for p in P])
    Cn = np.array([p['centre'] for p in P], float)
    cut = (A > CUT_AREA) & (Rr < CUT_RMS)
    print('Block %s: %d facets, %.0f m2 total; %d flagged as possible saw-cut faces (%.0f m2)'
          % (blk, len(P), A.sum(), cut.sum(), A[cut].sum()))
    res = {}
    for tag in ('all', 'joints_only'):
        msk = np.ones(len(P), bool) if tag == 'all' else ~cut
        Nm, Am, Cm = N[msk], A[msk], Cn[msk]
        if len(Nm) < 12:
            continue
        best = None
        for k in range(2, 7):
            lab, M = axial_kmeans(Nm, k)
            if np.bincount(lab, minlength=k).min() < 3:
                continue
            s = silhouette(Nm, lab, M)
            if best is None or s > best[0]:
                best = (s, k, lab, M)
        if best is None:
            continue
        s, k, lab, M = best
        print('  %s: %d sets (axial silhouette %.2f)' % (tag, k, s))
        sets = []
        for j in range(k):
            q = lab == j
            m, dip, brg, K, cone, ratio = describe(Nm[q])
            az = (180 - brg) % 360 if EAST[blk] == '+x' else (brg + 90) % 360
            sp, npair = spacing(Cm[q], m)
            sets.append(dict(set=j + 1, n_facets=int(q.sum()), area_m2=round(float(Am[q].sum()), 1),
                             dip_deg=round(dip, 1), dip_dir_grid_bearing_deg=round(brg, 1),
                             dip_dir_azimuth_deg=round(az, 1), strike_azimuth_deg=round((az - 90) % 360, 1),
                             fisher_K=round(K, 1), cone95_deg=(round(cone, 1) if cone == cone else None),
                             tightness=round(ratio, 3), largest_facet_m2=round(float(Am[q].max()), 2),
                             median_normal_spacing_m=(round(sp, 2) if sp == sp else None), spacing_pairs=npair,
                             mean_pole=[round(float(x), 4) for x in m]))
            print('     set %d  dip %4.1f  dip dir az %5.1f  n %3d  area %6.1f m2  K %5.1f  cone95 %s  spacing %s'
                  % (j + 1, dip, az, q.sum(), Am[q].sum(), K,
                     ('%.1f' % cone) if cone == cone else 'na', ('%.2f m' % sp) if sp == sp else 'na'))
        res[tag] = dict(n_sets=k, silhouette=round(s, 3), sets=sorted(sets, key=lambda r: -r['area_m2']))
    res['flagged_cut_faces'] = int(cut.sum())
    res['cut_face_rule'] = 'area > %.1f m2 and rms < %.0f mm' % (CUT_AREA, CUT_RMS * 1000)
    res['block'] = blk
    res['east_axis'] = D['east_axis']
    res['dip_frame'] = D['dip_frame']
    res['azimuth_note'] = D['azimuth_note']
    json.dump(res, open(os.path.join(OUT, 'tables', 'sets_%s.json' % blk), 'w'), indent=1)

    fig, axes = plt.subplots(1, 2, figsize=(11, 5.8))
    for ax, tag, ttl in ((axes[0], 'all', 'every facet'), (axes[1], 'joints_only', 'saw-cut faces removed')):
        if tag not in res:
            ax.axis('off')
            continue
        msk = np.ones(len(P), bool) if tag == 'all' else ~cut
        L = N[msk].copy()
        L[L[:, 2] > 0] *= -1
        Am = A[msk]
        rr = np.sqrt(2.0) * np.sin(np.arccos(np.clip(-L[:, 2], -1, 1)) / 2)
        th = np.arctan2(L[:, 0], L[:, 1])
        ax.scatter(rr * np.sin(th), rr * np.cos(th), s=6 + 40 * np.sqrt(Am / max(Am.max(), 1e-9)),
                   alpha=.55, c='#1F8A80', edgecolors='none')
        for st in res[tag]['sets']:
            m = np.array(st['mean_pole'], float)
            if m[2] > 0:
                m = -m
            r1 = np.sqrt(2.0) * np.sin(np.arccos(np.clip(-m[2], -1, 1)) / 2)
            t1 = np.arctan2(m[0], m[1])
            ax.plot(r1 * np.sin(t1), r1 * np.cos(t1), 'x', color='#C8452B', ms=11, mew=2.5)
            ax.annotate('%d: %.0f/%.0f' % (st['set'], st['dip_deg'], st['dip_dir_azimuth_deg']),
                        (r1 * np.sin(t1), r1 * np.cos(t1)), fontsize=9, color='#C8452B',
                        xytext=(6, 6), textcoords='offset points')
        t = np.linspace(0, 2 * np.pi, 300)
        ax.plot(np.sqrt(2.0) * np.sin(t), np.sqrt(2.0) * np.cos(t), 'k-', lw=1)
        ax.text(0, np.sqrt(2.0) * 1.06, 'grid +y', ha='center', fontsize=8)
        ax.text(np.sqrt(2.0) * 1.08, 0, 'grid +x', va='center', fontsize=8)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title('Block %s, %s\n%d poles' % (blk, ttl, int(msk.sum())), fontsize=10)
    fig.suptitle('Poles to the exposed faces, equal-area lower hemisphere, bench frame '
                 '(dip from the bench plane, not gravity)', fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'figs', 'STEREONET_%s.png' % blk), dpi=130)
    print('  wrote tables/sets_%s.json and figs/STEREONET_%s.png' % (blk, blk))
