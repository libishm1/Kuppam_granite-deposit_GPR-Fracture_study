"""Which trace-pair orientations are real, and which are the accidents the null predicts.

Pairing coplanar traces across faces finds more coplanar pairs than chance (traces_to_planes.py),
but not every pair is a fracture: at a gap of 8 m the null supplies about 8 accidental pairs to the
22 observed. No individual plane can be trusted. The distribution can: this bins the observed poles
and the pooled null poles the same way and reports where the observed density stands above the null.
"""
import numpy as np, os, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('GAP_MAX', '8.0')
import importlib.util
spec = importlib.util.spec_from_file_location('t2p', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'traces_to_planes.py'))
t2p = importlib.util.module_from_spec(spec); spec.loader.exec_module(t2p)
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

OUT = 'D:/code_ws/outputs/2026-09-11/joint_mapping'
blk = sys.argv[1].upper() if len(sys.argv) > 1 else 'C'
T = json.load(open(os.path.join(OUT, 'tables', 'traces_%s.json' % blk)))
tr = []
for f in T['faces']:
    n = np.asarray(f['normal'], float); n /= np.linalg.norm(n)
    for t in f['traces']:
        p0 = np.asarray(t['p0'], float); p1 = np.asarray(t['p1'], float)
        L = float(np.linalg.norm(p1 - p0))
        if L < t2p.MIN_LEN: continue
        tr.append(dict(face=f['face'], face_n=n, p0=p0, p1=p1, d=(p1 - p0) / L, L=L, src=t['source'],
                       rake=t2p.rake_of((p1 - p0) / L, n)))
by = {}
for t in tr: by.setdefault(t['face'], []).append(t)
for fid, ts in by.items():
    r = np.array([t['rake'] for t in ts]); w = np.array([t['L'] for t in ts])
    h, e = np.histogram(r, bins=np.arange(0, 91, 10), weights=w)
    mode = (e[h.argmax()] + e[h.argmax() + 1]) / 2 if h.sum() else -99
    share = h.max() / max(h.sum(), 1e-9)
    for t in ts: t['tooling'] = bool(abs(t['rake'] - mode) <= t2p.RAKE_TOL and share > 0.35 and len(ts) >= 4)
cand = [t for t in tr if not t['tooling']]

def orients(pairs, C):
    out = []
    for i, j, g, off, m in pairs:
        dip, brg, az = t2p.dip_dipdir(m, blk); out.append((dip, az))
    return np.array(out) if out else np.zeros((0, 2))

obs = orients(t2p.pair_up(cand, blk), cand)
rng = np.random.default_rng(11); NU = 200
nul = []
for _ in range(NU):
    sh = []
    for t_ in cand:
        n = t_['face_n']; h = np.cross(n, t2p.Z)
        h = h / np.linalg.norm(h) if np.linalg.norm(h) > 1e-6 else np.array([1.0, 0, 0])
        w = np.cross(n, h); a = rng.uniform(0, np.pi); d = np.cos(a) * h + np.sin(a) * w
        c = (t_['p0'] + t_['p1']) / 2
        sh.append(dict(face=t_['face'], face_n=n, d=d, L=t_['L'], p0=c - d * t_['L'] / 2, p1=c + d * t_['L'] / 2))
    o = orients(t2p.pair_up(sh, None), sh)
    if len(o): nul.append(o)
nul = np.vstack(nul) if nul else np.zeros((0, 2))
print('observed %d planes, null pooled %d planes over %d draws (%.1f per draw)' % (len(obs), len(nul), NU, len(nul) / NU))
bins = [0, 20, 40, 60, 75, 90]
ho, _ = np.histogram(obs[:, 0], bins=bins)
hn, _ = np.histogram(nul[:, 0], bins=bins); hn = hn / NU
print('dip band      observed   null/draw   excess')
rows = []
for k in range(len(bins) - 1):
    ex = ho[k] - hn[k]
    print('  %2d to %2d deg  %5d      %6.1f    %+6.1f' % (bins[k], bins[k + 1], ho[k], hn[k], ex))
    rows.append(dict(dip_from=bins[k], dip_to=bins[k + 1], observed=int(ho[k]), null_per_draw=round(float(hn[k]), 2),
                     excess=round(float(ex), 1)))
json.dump(dict(block=blk, gap_max_m=float(os.environ['GAP_MAX']), n_observed=int(len(obs)),
               null_draws=NU, null_per_draw=round(len(nul) / NU, 2), dip_bands=rows,
               note='the excess is the part of the observed count that the null does not explain; '
                    'individual planes are still not separable into real and accidental'),
          open(os.path.join(OUT, 'tables', 'excess_%s.json' % blk), 'w'), indent=1)
fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
ax[0].hist([obs[:, 0], nul[:, 0]], bins=np.arange(0, 91, 10), density=True, color=['#C8452B', '#B9BFC7'],
           label=['observed pairs', 'null, pooled'])
ax[0].set_xlabel('dip of the paired-trace plane, degrees from the bench plane'); ax[0].set_ylabel('density')
ax[0].legend(fontsize=8); ax[0].set_title('Block %s: %d observed, %.1f expected per draw' % (blk, len(obs), len(nul) / NU), fontsize=10)
ax[1].hist([obs[:, 1], nul[:, 1]], bins=np.arange(0, 361, 30), density=True, color=['#C8452B', '#B9BFC7'])
ax[1].set_xlabel('dip direction, azimuth via the east axis'); ax[1].set_ylabel('density')
ax[1].set_title('orientation of the pairs against chance', fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(OUT, 'figs', 'EXCESS_%s.png' % blk), dpi=130)
print('wrote tables/excess_%s.json and figs/EXCESS_%s.png' % (blk, blk))
