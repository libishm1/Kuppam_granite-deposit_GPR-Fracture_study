"""Turn the traces found on the quarry faces into fracture orientations, and separate them from the
marks the quarry itself made.

Three steps.

1. Rake. Every trace lies in the plane of its face, so it is described by its rake: the angle
   between the trace and the horizontal direction in that face. A wire saw and a drill line leave
   lineations that are parallel to one another and, on a vertical face, close to vertical or close
   to horizontal. A natural fracture has no reason to be parallel to them. So within each face the
   length-weighted rake histogram is taken, the dominant mode is called the tooling lineation, and
   traces within RAKE_TOL of it are set aside.

2. A single trace on a single flat face fixes a line, not a plane. Any plane containing that line is
   possible, so a trace alone cannot give dip and dip direction. Two traces of the same fracture on
   two faces that are not parallel do fix it: the plane normal is the cross product of the two trace
   directions. Pairs are formed between faces whose normals differ by more than FACE_ANG, whose
   traces are close in space, and which are coplanar to COPLAN_TOL.

3. The resulting planes are clustered the same axial way as the facets, and reported as dip and dip
   direction in the bench frame, with the same two caveats: dip is from the bench plane rather than
   from gravity, and azimuth comes from the east axis of ORIENTATION.md rather than from a compass.

Usage: traces_to_planes.py A|B|C
"""
import numpy as np, sys, os, json
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

OUT = 'D:/code_ws/outputs/2026-09-11/joint_mapping'
RAKE_TOL = 12.0       # deg either side of a face's dominant lineation
FACE_ANG = 25.0       # deg, minimum angle between two faces used as a pair
COPLAN_TOL = 0.25     # m, how far the second trace may sit off the candidate plane
GAP_MAX = float(os.environ.get('GAP_MAX', 2.0))   # m, maximum separation of the two traces
N_NULL = 200          # random relabellings for the null
MIN_LEN = 0.4         # m, ignore very short traces
EAST = {'A': '+x', 'B': '+y', 'C': '+y'}   # 12 Sep. Origin is the north-west corner on every bench and both axes run into the bench, but which axis runs east differs: on A the X-line numerals run down the WEST edge from A0 (client, from the site: '9, 12...' from the NW to the SW corner), so X-lines are stacked north-south and run east, +x east, +y south, left-handed. On B and C +y is east (6 m and 8 m sides, verified). See ORIENTATION.md.
Z = np.array([0, 0, 1.0])


def rake_of(d, n):
    """angle of trace direction d within the face of normal n, from the horizontal in that face"""
    h = np.cross(n, Z)
    if np.linalg.norm(h) < 1e-6:
        h = np.array([1.0, 0, 0])
    h /= np.linalg.norm(h)
    w = np.cross(n, h)
    return float(np.degrees(np.arctan2(abs(d @ w), abs(d @ h))))


def dip_dipdir(m, blk):
    m = np.asarray(m, float) / np.linalg.norm(m)
    if m[2] < 0:
        m = -m
    dip = float(np.degrees(np.arccos(np.clip(abs(m[2]), -1, 1))))
    # the upward normal leans toward the DOWN-dip side, so the dip direction is the trend of
    # its horizontal part: bearing = atan2(n_x, n_y), the convention the GPR study uses
    dd = np.array([m[0], m[1]])
    brg = float(np.degrees(np.arctan2(dd[0], dd[1])) % 360) if np.linalg.norm(dd) > 1e-9 else 0.0
    az = (180 - brg) % 360 if EAST[blk] == '+x' else (brg + 90) % 360
    return dip, brg, az


def seg_gap(a0, a1, b0, b1):
    """shortest distance between two 3D segments, sampled"""
    ta = np.linspace(0, 1, 12)[:, None]
    A = a0 + ta * (a1 - a0)
    B = b0 + ta * (b1 - b0)
    return float(np.min(np.linalg.norm(A[:, None, :] - B[None, :, :], axis=2)))


def pair_up(cand, blk, gap_max=None):
    """every pair of traces on non-parallel faces that is close enough and coplanar enough"""
    gm = GAP_MAX if gap_max is None else gap_max
    out = []
    for i in range(len(cand)):
        for j in range(i + 1, len(cand)):
            a, b = cand[i], cand[j]
            if a['face'] == b['face']:
                continue
            if abs(float(a['face_n'] @ b['face_n'])) > np.cos(np.radians(FACE_ANG)):
                continue
            g = seg_gap(a['p0'], a['p1'], b['p0'], b['p1'])
            if g > gm:
                continue
            m = np.cross(a['d'], b['d'])
            nm = np.linalg.norm(m)
            if nm < np.sin(np.radians(10)):
                continue
            m /= nm
            off = max(abs(float((b['p0'] - a['p0']) @ m)), abs(float((b['p1'] - a['p1']) @ m)))
            if off > COPLAN_TOL:
                continue
            out.append((i, j, g, off, m))
    return out


def null_pairs(cand, rng, gap_max=None):
    """same test with each trace's direction re-drawn at random inside its own face: this is how
    many coplanar pairs pure chance supplies, given the geometry of the faces and where the traces
    happen to sit"""
    sh = []
    for t_ in cand:
        n = t_['face_n']
        h = np.cross(n, Z)
        h = h / np.linalg.norm(h) if np.linalg.norm(h) > 1e-6 else np.array([1.0, 0, 0])
        w = np.cross(n, h)
        a = rng.uniform(0, np.pi)
        d = np.cos(a) * h + np.sin(a) * w
        c = (t_['p0'] + t_['p1']) / 2
        sh.append(dict(face=t_['face'], face_n=n, d=d, L=t_['L'],
                       p0=c - d * t_['L'] / 2, p1=c + d * t_['L'] / 2))
    return len(pair_up(sh, None, gap_max))


if __name__ == '__main__':
    blk = sys.argv[1].upper()
    T = json.load(open(os.path.join(OUT, 'tables', 'traces_%s.json' % blk)))
    tr = []
    for f in T['faces']:
        n = np.asarray(f['normal'], float)
        n /= np.linalg.norm(n)
        for t in f['traces']:
            p0 = np.asarray(t['p0'], float)
            p1 = np.asarray(t['p1'], float)
            L = float(np.linalg.norm(p1 - p0))
            if L < MIN_LEN:
                continue
            d = (p1 - p0) / L
            tr.append(dict(face=f['face'], face_n=n, face_dip=f['dip_deg'], face_az=f['dip_dir_azimuth_deg'],
                           p0=p0, p1=p1, d=d, L=L, src=t['source'], rake=rake_of(d, n)))
    print('Block %s: %d faces, %d traces over %.1f m' % (blk, len(T['faces']), len(tr), MIN_LEN))

    # 1. tooling lineation per face
    by_face = {}
    for t in tr:
        by_face.setdefault(t['face'], []).append(t)
    n_tool = 0
    for fid, ts in by_face.items():
        r = np.array([t['rake'] for t in ts])
        w = np.array([t['L'] for t in ts])
        h, edges = np.histogram(r, bins=np.arange(0, 91, 10), weights=w)
        mode = (edges[h.argmax()] + edges[h.argmax() + 1]) / 2 if h.sum() > 0 else -99
        share = h.max() / max(h.sum(), 1e-9)
        for t in ts:
            t['tooling'] = bool(abs(t['rake'] - mode) <= RAKE_TOL and share > 0.35 and len(ts) >= 4)
            n_tool += t['tooling']
        by_face[fid] = dict(traces=ts, mode_rake=float(mode), mode_share=float(share))
    cand = [t for t in tr if not t['tooling']]
    print('  %d traces set aside as tooling lineation, %d candidates left' % (n_tool, len(cand)))

    # 2. pairs across non-parallel faces, with a null
    raw = pair_up(cand, blk)
    planes = []
    for i, j, g, off, m in raw:
        a, b = cand[i], cand[j]
        dip, brg, az = dip_dipdir(m, blk)
        planes.append(dict(trace_a=i, trace_b=j, faces=[a['face'], b['face']], gap_m=round(g, 2),
                           coplanarity_m=round(off, 3), len_m=round(a['L'] + b['L'], 2),
                           dip_deg=round(dip, 1), dip_dir_azimuth_deg=round(az, 1),
                           strike_azimuth_deg=round((az - 90) % 360, 1),
                           normal=[round(float(x), 4) for x in m],
                           centre=[round(float(x), 2) for x in (a['p0'] + a['p1'] + b['p0'] + b['p1']) / 4]))
    rng = np.random.default_rng(7)
    nulls = np.array([null_pairs(cand, rng) for _ in range(N_NULL)])
    print('  %d trace pairs are coplanar within %.2f m at a gap of %.1f m' % (len(planes), COPLAN_TOL, GAP_MAX))
    print('  null (trace directions re-drawn at random in their own faces): %.1f pairs on average, '
          'p90 %.0f, max %d over %d draws' % (nulls.mean(), np.percentile(nulls, 90), nulls.max(), N_NULL))
    p_val = float((nulls >= len(planes)).mean())
    print('  chance of getting %d or more by accident: %.3f' % (len(planes), p_val))

    out = dict(block=blk, east_axis=EAST[blk], rake_tol_deg=RAKE_TOL, face_angle_min_deg=FACE_ANG,
               coplanarity_tol_m=COPLAN_TOL, gap_max_m=GAP_MAX,
               dip_frame="from this block's bench plane, not gravity",
               azimuth_note='via the east axis of ORIENTATION.md; not compass-measured',
               caveat='a trace on one flat face fixes a line, not a plane; only the pairs below are orientations',
               n_traces=len(tr), n_tooling=int(n_tool), n_candidates=len(cand),
               null=dict(n_draws=N_NULL, mean=float(nulls.mean()), p90=float(np.percentile(nulls, 90)),
                         max=int(nulls.max()), p_value=p_val,
                         what='each trace direction re-drawn at random within its own face, positions kept'),
               faces=[dict(face=k, mode_rake_deg=round(v['mode_rake'], 1), mode_share=round(v['mode_share'], 2),
                           n_traces=len(v['traces'])) for k, v in sorted(by_face.items())],
               traces=[dict(face=t['face'], source=t['src'], length_m=round(t['L'], 2), rake_deg=round(t['rake'], 1),
                            tooling=t['tooling'], p0=[round(float(x), 2) for x in t['p0']],
                            p1=[round(float(x), 2) for x in t['p1']]) for t in tr],
               planes=planes)
    json.dump(out, open(os.path.join(OUT, 'tables', 'planes_%s.json' % blk), 'w'), indent=1)

    fig, ax = plt.subplots(1, 2, figsize=(11, 4.6))
    r_t = [t['rake'] for t in tr if t['tooling']]
    r_c = [t['rake'] for t in cand]
    ax[0].hist([r_t, r_c], bins=np.arange(0, 91, 6), stacked=True, color=['#B9BFC7', '#C8452B'],
               label=['tooling lineation', 'fracture candidate'])
    ax[0].set_xlabel('rake within the face, degrees from horizontal')
    ax[0].set_ylabel('traces')
    ax[0].legend(fontsize=8)
    ax[0].set_title('Block %s: %d traces on %d faces' % (blk, len(tr), len(T['faces'])), fontsize=10)
    if planes:
        P = np.array([p['normal'] for p in planes], float)
        P[P[:, 2] > 0] *= -1
        rr = np.sqrt(2.0) * np.sin(np.arccos(np.clip(-P[:, 2], -1, 1)) / 2)
        th = np.arctan2(P[:, 0], P[:, 1])
        ax[1].scatter(rr * np.sin(th), rr * np.cos(th), s=26, c='#1F8A80', alpha=.7, edgecolors='none')
    t = np.linspace(0, 2 * np.pi, 300)
    ax[1].plot(np.sqrt(2.0) * np.sin(t), np.sqrt(2.0) * np.cos(t), 'k-', lw=1)
    ax[1].text(0, np.sqrt(2.0) * 1.06, 'grid +y', ha='center', fontsize=8)
    ax[1].text(np.sqrt(2.0) * 1.08, 0, 'grid +x', va='center', fontsize=8)
    ax[1].set_aspect('equal')
    ax[1].axis('off')
    ax[1].set_title('poles of the %d planes from paired traces' % len(planes), fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'figs', 'TRACES_%s.png' % blk), dpi=130)
    print('  wrote tables/planes_%s.json and figs/TRACES_%s.png' % (blk, blk))
