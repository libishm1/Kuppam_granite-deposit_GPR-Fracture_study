"""Block A: which way do the survey lines run?  A surface crack crossing a line rings down through the
radargram as a vertical "curtain".  Predict where the mapped cracks cross every line under two
hypotheses - lines placed as the picks assume, or with x and y transposed - and score each against
the curtains actually present in the 24 HF radargrams, versus a random-position null.  No compass,
no memory, no picks.

Crack source: the photogrammetry crack polylines (Block_A_surface_cracks_v1.obj, bench frame). Carried
into the painted grid through FRAME.json they come out shifted by about a metre against the weeded
table of the same cracks (surface_cracks_A_weeded.csv, grid cm), so each polyline is registered to its
table row by endpoint matching and the median shift removed.  The table's frame is the one the site
model and the crack test use; the polylines keep the sinuosity the table drops.

Writes figs/A_CURTAIN_TEST.png and tables/curtain_test_A.json.  Read-only on the data."""
import csv, glob, io, json, os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

G = 'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
RAW = 'D:/code_ws/reference/parsans/report/raw/GPR Raw data_Kuppam'
sys.path.insert(0, os.path.join(G, 'scripts'))
import segy  # noqa: E402

DT = 0.0610352                     # ns per sample, HF
T_DEEP = (24.0, 38.0)              # ns: 1.44-2.28 m at v = 0.1202
EDGE = 0.30                        # m: ignore crossings this close to either end of a line
DEDUP = 0.15                       # m: a sinuous crack crossing a line twice within this is one crossing
PEAK = 1.45                        # curtain ratio counted as a detected curtain
TOL = 0.20                         # m: match tolerance between a prediction and a curtain
rng = np.random.default_rng(0)

inv = {int(r['line_no']): r for r in csv.DictReader(io.open(os.path.join(G, 'dataset/picks/line_inventory.csv'), encoding='utf-8')) if r['block'] == 'A'}

# ---------------------------------------------------------------- cracks: polylines registered to the grid table
F = json.load(io.open(os.path.join(G, 'dataset/bench_frame_m/Block_A/FRAME.json'), encoding='utf-8'))
o = np.array(F['report_origin_xy']) * F['scale_m_per_mesh_unit']; M = np.c_[np.array(F['report_x_dir']), np.array(F['report_y_dir'])]
V, L = [], []
for ln in io.open(os.path.join(G, 'dataset/bench_frame_m/Block_A/Block_A_surface_cracks_v1.obj')):
    if ln.startswith('v '): V.append([float(t) for t in ln.split()[1:4]])
    elif ln.startswith('l '): L.append([int(t.split('/')[0]) - 1 for t in ln.split()[1:]])
V = np.array(V); Gxy = (V[:, :2] - o) @ M
polys0 = [Gxy[idx] for idx in L]
tab = list(csv.DictReader(io.open(os.path.join(G, 'dataset/surface_fractures/surface_cracks_A_weeded.csv'), encoding='utf-8')))
tab_len = np.array([float(r['length_m']) for r in tab])
shifts = []
for p in polys0:
    pl = float(np.sum(np.linalg.norm(np.diff(p, axis=0), axis=1)))
    j = int(np.argmin(np.abs(tab_len - pl)))
    if abs(tab_len[j] - pl) > 0.15 * max(pl, 0.5): continue
    r = tab[j]; e0 = np.array([float(r['x0']), float(r['y0'])]) / 100; e1 = np.array([float(r['x1']), float(r['y1'])]) / 100
    a, b = p[0], p[-1]
    d1 = np.linalg.norm(a - e0) + np.linalg.norm(b - e1); d2 = np.linalg.norm(a - e1) + np.linalg.norm(b - e0)
    shifts.append(((e0 - a) + (e1 - b)) / 2 if d1 <= d2 else ((e1 - a) + (e0 - b)) / 2)
shifts = np.array(shifts); shift = np.median(shifts, axis=0)
print('polyline->table registration: %d of %d cracks matched by length; median shift (%.2f, %.2f) m, spread %.2f m'
      % (len(shifts), len(polys0), shift[0], shift[1], float(np.median(np.linalg.norm(shifts - shift, axis=1)))))
polys = [p + shift for p in polys0]
allpts = np.vstack(polys); print('cracks after registration: grid x %.2f..%.2f y %.2f..%.2f (table: 0.04..5.46 both)' % (allpts[:, 0].min(), allpts[:, 0].max(), allpts[:, 1].min(), allpts[:, 1].max()))

# ---------------------------------------------------------------- line paths under each hypothesis
def path(ln, H):
    c = (ln - 1) * 0.5 if ln <= 12 else (ln - 13) * 0.5
    fixed = ('y' if ln <= 12 else 'x') if H == 'as drawn' else ('x' if ln <= 12 else 'y')
    return fixed, c

def crossings(ln, H, rev):
    fixed, c = path(ln, H); scan = float(inv[ln]['scan_m']); out = []
    ia, ib = (1, 0) if fixed == 'y' else (0, 1)
    for p in polys:
        fa = p[:-1, ia] - c; fb = p[1:, ia] - c
        m = ((fa <= 0) & (fb > 0)) | ((fb <= 0) & (fa > 0))
        for k in np.where(m)[0]:
            t = fa[k] / (fa[k] - fb[k]); s = p[k, ib] + t * (p[k + 1, ib] - p[k, ib])
            if EDGE <= s <= scan - EDGE: out.append(scan - s if rev else s)
    out = np.array(sorted(out)); keep = []
    for s in out:
        if not keep or s - keep[-1] > DEDUP: keep.append(s)
    return np.array(keep)

# ---------------------------------------------------------------- curtain profiles from the raw radargrams
def profile(ln):
    f = sorted(glob.glob(os.path.join(RAW, 'A Block', '**', '*new%03d_*_HF.sgy' % ln), recursive=True))[0]
    d = segy.read(f)['data'].astype(float)
    ntr = d.shape[0]; scan = float(inv[ln]['scan_m']); s = np.arange(ntr) * scan / ntr
    t = np.arange(d.shape[1]) * DT; w = (t > T_DEEP[0]) & (t < T_DEEP[1])
    rms = np.sqrt((d[:, w] ** 2).mean(1)); rms /= np.median(rms)
    k = 41; pad = np.pad(rms, k // 2, mode='edge'); base = np.array([np.median(pad[i:i + k]) for i in range(ntr)])
    r = np.convolve(rms / np.maximum(base, 1e-9), np.ones(3) / 3, 'same')
    return s, r

prof = {ln: profile(ln) for ln in range(1, 25)}

def peaks(ln):
    s, r = prof[ln]; out = []
    for i in range(1, len(r) - 1):
        if r[i] >= PEAK and r[i] >= r[i - 1] and r[i] >= r[i + 1] and EDGE <= s[i] <= s[-1] - EDGE:
            if not out or s[i] - out[-1] > DEDUP: out.append(float(s[i]))
    return np.array(out)
PK = {ln: peaks(ln) for ln in range(1, 25)}
print('detected curtains (ratio >= %.2f): %d over 24 lines' % (PEAK, sum(len(v) for v in PK.values())))

# ---------------------------------------------------------------- scoring: precision / recall against the curtains, with a random null
def prec_rec(pred_by_line):
    hit = tot = 0; rec_hit = rec_tot = 0
    for ln in range(1, 25):
        pr = pred_by_line[ln]; pk = PK[ln]
        tot += len(pr); hit += sum(1 for p in pr if len(pk) and np.abs(pk - p).min() <= TOL)
        rec_tot += len(pk); rec_hit += sum(1 for q in pk if len(pr) and np.abs(pr - q).min() <= TOL)
    return (hit / tot if tot else np.nan), (rec_hit / rec_tot if rec_tot else np.nan), tot

def null_prec(counts, n=500):
    out = []
    for _ in range(n):
        pb = {}
        for ln in range(1, 25):
            s, _ = prof[ln]; pb[ln] = np.sort(rng.uniform(EDGE, s[-1] - EDGE, counts[ln]))
        out.append(prec_rec(pb)[0])
    return np.array(out)

results = {}
for H in ('as drawn', 'transposed'):
    for rev in (False, True):
        pb = {ln: crossings(ln, H, rev) for ln in range(1, 25)}
        p, r, n = prec_rec(pb); nul = null_prec({ln: len(pb[ln]) for ln in pb})
        z = (p - nul.mean()) / nul.std() if nul.std() > 0 else np.nan
        key = '%s, along-track %s' % (H, 'reversed' if rev else 'from the start')
        results[key] = dict(n_pred=int(n), precision=round(float(p), 3), null_precision=round(float(nul.mean()), 3), null_sd=round(float(nul.std()), 3), z=round(float(z), 2), recall=round(float(r), 3))
        print('%-40s predictions %3d   precision %.2f  (random %.2f +- %.2f, z = %+5.2f)   recall of curtains %.2f'
              % (key, n, p, nul.mean(), nul.std(), z, r))

# ---------------------------------------------------------------- figure
fig, axes = plt.subplots(12, 2, figsize=(16, 22))
for i, ln in enumerate(range(1, 25)):
    ax = axes[i % 12, i // 12]; s, r = prof[ln]
    ax.fill_between(s, 1, r, where=r > 1, color='#999', alpha=0.6); ax.plot(s, r, color='#444', lw=0.7)
    for q in PK[ln]: ax.plot(q, r[np.argmin(np.abs(s - q))], 'kv', ms=5)
    for p in crossings(ln, 'as drawn', False): ax.axvline(p, color='#c62828', lw=1.6, alpha=0.9)
    for p in crossings(ln, 'transposed', False): ax.axvline(p, color='#1565c0', lw=1.6, alpha=0.9, ls='--')
    ax.set_ylim(0.5, max(3.0, r.max() * 1.05)); ax.set_xlim(0, s[-1])
    fx, c = path(ln, 'as drawn'); fx2, c2 = path(ln, 'transposed')
    ax.text(0.01, 0.95, 'line %2d   as drawn: %s = %.1f (red)   transposed: %s = %.1f (blue dashed)   curtains: %d' % (ln, fx, c, fx2, c2, len(PK[ln])), transform=ax.transAxes, fontsize=8, va='top')
    if i % 12 == 11: ax.set_xlabel('metres along the line from its start')
fig.suptitle('Block A curtain test: deep-window ringing along each HF line (grey; detected curtains marked) versus where the mapped surface cracks cross\n'
             'red = lines placed as the picks assume;  blue dashed = with x and y transposed', fontsize=13)
fig.tight_layout(rect=[0, 0, 1, 0.97]); fig.savefig(os.path.join(G, 'figs', 'A_CURTAIN_TEST.png'), dpi=100); plt.close(fig)
json.dump(dict(window_ns=T_DEEP, edge_m=EDGE, dedup_m=DEDUP, peak=PEAK, tol_m=TOL, shift_m=shift.tolist(), results=results),
          io.open(os.path.join(G, 'tables', 'curtain_test_A.json'), 'w', encoding='utf-8'), indent=1)
print('wrote figs/A_CURTAIN_TEST.png, tables/curtain_test_A.json')
