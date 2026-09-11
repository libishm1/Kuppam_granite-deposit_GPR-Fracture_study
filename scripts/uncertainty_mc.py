"""Monte Carlo propagation of the surface uncertainties into the straight-cut plan.
Each realisation draws, from the same terms as the tolerance ladder (uncertainty.py):
  velocity factor         N(1, sigma_v/v), common to all surfaces
  time-zero shift         N(0, sigma_t0) per channel, common to that channel's surfaces
  surface scatter         N(0, sigma_interp) per surface, a whole-surface vertical shift (conservative simplification)
  plan registration       N(0, sig_xy) in x and y per block, applied by resampling the surface
  migration fraction      U(0, 1) of the plane-to-plane migration offset (0 = as recorded, 1 = specular planar reflector)
and builds the perturbed surfaces e'(x, y) = DEM - d'(x, y) (+ shifts). Two questions:
  (a) block risk: for the two planned cases (as drawn, with uncertainty) at chalk 1.0 m, the fraction of realisations
      in which a perturbed surface passes through each planned block (N_RISK draws);
  (b) yield distribution: re-solve the straight-cut plan against each perturbed truth with the as-drawn 15 cm band
      (N_YIELD draws): P10 / P50 / P90 of tonnes per block.
Writes tables/uncertainty_mc.json and figs/UNCERTAINTY_mc.png."""
import numpy as np, os, json, sys, time
from scipy.interpolate import RegularGridInterpolator
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
import packing_domain as PD, guillotine_pack as GP
OUT = PD.OUT; VOX = PD.VOX
U = json.load(open(os.path.join(OUT, 'tables', 'uncertainty.json'))); G = json.load(open(os.path.join(OUT, 'tables', 'guillotine_packing.json')))
N_RISK = int(os.environ.get('N_RISK', 200)); N_YIELD = int(os.environ.get('N_YIELD', 30))
SDEPTH = float(os.environ.get('CHALK_DEPTH', 0.5))          # the scenario the plan defaults to
SKEY = 'surface_%.1fm' % SDEPTH
rng = np.random.default_rng(11)
CHAN = {'A1': 'HF', 'A2': 'HF', 'B1': 'HF', 'B2': 'LF', 'C1': 'HF', 'C2': 'LF'}
SIG_VV = U['ladder']['sigma_v_over_v']; SIG_T0 = U['ladder']['sigma_t0_ns']; V0 = U['ladder']['v0']


def grid_interp(p):
    a = np.loadtxt(p); gx = np.unique(a[:, 0]) / 100; gy = np.unique(a[:, 1]) / 100
    return RegularGridInterpolator((gy, gx), a[:, 2].reshape(len(gy), len(gx)), bounds_error=False, fill_value=np.nan)


def realisation(blk, base, draw):
    """perturbed absolute-elevation surfaces at the domain's cell centres"""
    out = {}
    for F in PD.FEATS[blk]:
        fd, fmig = base['d'][F], base['mig'][F]
        X = base['XC'] - draw['dx']; Y = base['YC'] - draw['dy']; P = np.c_[Y.ravel(), X.ravel()]
        d = fd(P).reshape(X.shape) * draw['vf'] + V0 * draw['t0'][CHAN[F]] / 2                       # depth below the local surface, rescaled and time-shifted
        e = base['dem'] - d                                                                             # elevation as recorded
        em = fmig(P).reshape(X.shape); e_rec = base['dem'] - fd(P).reshape(X.shape)
        e = e + draw['u'] * (em - e_rec) + draw['ds'][F]                                                # migration fraction and surface scatter
        out[F] = e
    return out


def draw(blk):
    return dict(vf=float(rng.normal(1.0, SIG_VV)), t0={ch: float(rng.normal(0, SIG_T0[ch])) for ch in SIG_T0}, dx=float(rng.normal(0, U[blk][PD.FEATS[blk][0]]['sig_xy_m'])), dy=float(rng.normal(0, U[blk][PD.FEATS[blk][0]]['sig_xy_m'])),
                u=float(rng.uniform(0, 1)), ds={F: float(rng.normal(0, U[blk][F]['sigma_interp_m'])) for F in PD.FEATS[blk]})


results = {}
fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
for ax, blk in zip(axes, 'ABC'):
    t0 = time.time(); D0 = PD.build(blk, SDEPTH, 'modelled')
    XC, YC = np.meshgrid(D0['xc'], D0['yc'])
    base = dict(dem=D0['dem'], XC=XC, YC=YC, d={}, mig={}, sig={})
    for F in PD.FEATS[blk]:
        base['d'][F] = grid_interp(os.path.join(OUT, 'model', '%s_grid_10cm.xyz' % F))
        base['mig'][F] = grid_interp(os.path.join(OUT, 'model', 'unc', '%s_mig_10cm.xyz' % F))
    # (a) block risk for the two plans
    plans = {u: G[blk][SKEY + '__' + u]['boxes'] for u in ('modelled', 'uncertain')}
    hits = {u: np.zeros(len(plans[u])) for u in plans}
    for it in range(N_RISK):
        E = realisation(blk, base, draw(blk))
        for u, boxes in plans.items():
            for i, b in enumerate(boxes):
                a0, a1, b0, b1 = int(round(b['x0'] / VOX)), int(round(b['x1'] / VOX)), int(round(b['y0'] / VOX)), int(round(b['y1'] / VOX))
                hit = False
                for F, e in E.items():
                    sub = e[b0:b1, a0:a1]; ok = np.isfinite(sub)
                    if ok.any() and np.any((sub[ok] > b['z0']) & (sub[ok] < b['z_top_usable'])): hit = True; break
                hits[u][i] += hit
    risk = {u: [round(float(h / N_RISK), 3) for h in hits[u]] for u in hits}
    # (b) yield distribution, re-planned per realisation with the as-drawn band
    tons = []
    for it in range(N_YIELD):
        E = realisation(blk, base, draw(blk)); Dr = PD.build(blk, SDEPTH, 'modelled', override=E)
        r = GP.solve(blk, Dr, SDEPTH, 'mc', quiet=True); tons.append(r['packed_t'])
    tons = np.array(tons); p10, p50, p90 = np.percentile(tons, [10, 50, 90])
    tw = {u: sum(b['t'] * (1 - risk[u][i]) for i, b in enumerate(plans[u])) for u in plans}
    results[blk] = dict(n_risk=N_RISK, n_yield=N_YIELD, chalk_depth_m=SDEPTH, block_risk=risk,
                        plan_t={u: G[blk][SKEY + '__' + u]['packed_t'] for u in plans}, plan_risk_weighted_t={u: round(tw[u], 0) for u in tw},
                        blocks_over_20pct={u: int(sum(1 for r_ in risk[u] if r_ > 0.2)) for u in risk}, mean_risk={u: round(float(np.mean(risk[u])), 3) if risk[u] else 0 for u in risk},
                        replan_t=dict(p10=round(float(p10), 0), p50=round(float(p50), 0), p90=round(float(p90), 0), min=round(float(tons.min()), 0), max=round(float(tons.max()), 0), draws=[float(x) for x in tons]))
    ax.hist(tons, bins=12, color='#1F8A80', alpha=.8); ax.axvline(results[blk]['plan_t']['modelled'], color='#C8452B', ls='--', label='as-drawn plan'); ax.axvline(results[blk]['plan_t']['uncertain'], color='#D98E1E', ls='-', label='uncertain plan')
    ax.set_title('Block %s: re-planned tonnes over %d truths' % (blk, N_YIELD), fontsize=10); ax.set_xlabel('t'); ax.legend(fontsize=8)
    print('Block %s: risk (as drawn) mean %.2f, %d of %d blocks over 20%%; risk (uncertain) mean %.2f, %d of %d over 20%%; re-plan P10/P50/P90 %.0f/%.0f/%.0f t (plans %.0f / %.0f)  [%.0f s]' % (
        blk, results[blk]['mean_risk']['modelled'], results[blk]['blocks_over_20pct']['modelled'], len(risk['modelled']), results[blk]['mean_risk']['uncertain'], results[blk]['blocks_over_20pct']['uncertain'], len(risk['uncertain']),
        p10, p50, p90, results[blk]['plan_t']['modelled'], results[blk]['plan_t']['uncertain'], time.time() - t0))
fig.tight_layout(); fig.savefig(os.path.join(OUT, 'figs', 'UNCERTAINTY_mc.png'), dpi=120)
json.dump(results, open(os.path.join(OUT, 'tables', 'uncertainty_mc.json'), 'w'), indent=1)
print('wrote tables/uncertainty_mc.json, figs/UNCERTAINTY_mc.png')
