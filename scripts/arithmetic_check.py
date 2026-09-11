"""Recompute every number the page and the documents assert, from the tables they come from.

This is an internal-consistency audit, not a validation: it cannot tell you the model is right, only
that the arithmetic on top of it holds together. Each check recomputes a published quantity from its
inputs and compares. Anything that does not agree is printed as FAIL with both values.
"""
import json, os, math, sys

OUT = 'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
DENSITY = 2.95
fails = []
checks = 0


def ok(cond, label, got=None, want=None, tol=None):
    global checks
    checks += 1
    if cond:
        return True
    msg = '  FAIL  %s' % label
    if got is not None:
        msg += '\n          got %s, expected %s' % (got, want)
    fails.append(msg)
    print(msg)
    return False


def near(a, b, tol):
    return abs(a - b) <= tol


def load(p):
    return json.load(open(os.path.join(OUT, 'tables', p)))


G = load('guillotine_packing.json')
P = load('block_packing.json')
U = load('uncertainty.json')
M = load('uncertainty_mc.json')
V = load('velocity_summary.json')
S = load('structural.json')

print('=== the straight-cut plan')
for blk in 'ABC':
    for key, run in G[blk].items():
        boxes = run['boxes']
        # tonnes are volume times density
        vsum = sum(b['vol_m3'] for b in boxes)
        tsum = sum(b['t'] for b in boxes)
        ok(near(run['packed_m3'], vsum, 0.6), '%s %s packed_m3 equals the sum of its blocks' % (blk, key),
           run['packed_m3'], round(vsum, 2))
        ok(near(run['packed_t'], tsum, 1.5), '%s %s packed_t equals the sum of its blocks' % (blk, key),
           run['packed_t'], round(tsum, 1))
        ok(near(vsum * DENSITY, tsum, max(2.0, 0.01 * tsum)),
           '%s %s tonnes equal volume times %.2f' % (blk, key, DENSITY),
           round(tsum, 1), round(vsum * DENSITY, 1))
        # every block carries its own volume correctly
        bad = [b for b in boxes
               if not near(b['L'] * b['Wd'] * b['Hh'], b['vol_m3'], max(0.02, 0.006 * b['vol_m3']))]
        ok(not bad, '%s %s every block volume equals L x W x H, to the printed rounding' % (blk, key),
           len(bad), 0)
        bad = [b for b in boxes if not near(b['vol_m3'] * DENSITY, b['t'], 0.6)]
        ok(not bad, '%s %s every block tonnage equals its volume times density' % (blk, key), len(bad), 0)
        # the class summary adds up to the whole
        cs = run['classes']
        ok(sum(c['n'] for c in cs.values()) == len(boxes),
           '%s %s class counts add to the block count' % (blk, key),
           sum(c['n'] for c in cs.values()), len(boxes))
        ok(near(sum(c['t'] for c in cs.values()), tsum, 2.0),
           '%s %s class tonnes add to the total' % (blk, key),
           round(sum(c['t'] for c in cs.values()), 1), round(tsum, 1))
        # recovery is packed over gross
        ok(near(run['recovery_ratio'], run['packed_m3'] / run['gross_rock_m3'], 0.005),
           '%s %s recovery equals packed over gross rock' % (blk, key),
           run['recovery_ratio'], round(run['packed_m3'] / run['gross_rock_m3'], 4))
        ok(run['packed_m3'] <= run['gross_rock_m3'] + 0.1,
           '%s %s packed volume does not exceed the rock available' % (blk, key))
        ok(run['n_waste'] == len(run['waste']), '%s %s waste count matches the list' % (blk, key),
           run['n_waste'], len(run['waste']))
        # removal order is a permutation, and dependencies come first
        seqs = sorted(b['remove_seq'] for b in boxes + run['waste'])
        ok(seqs == list(range(1, len(seqs) + 1)),
           '%s %s removal order is 1..n with no gaps or repeats' % (blk, key))
        pos = {b['remove_seq']: b for b in boxes + run['waste']}
        viol = 0
        for b in boxes + run['waste']:
            for a in b.get('after', []):
                if a >= b['remove_seq']:
                    viol += 1
        ok(viol == 0, '%s %s nothing is lifted before a piece above it' % (blk, key), viol, 0)
        # clearance actually met
        band = run['bands']
        vals = [v for b in boxes for v in b['min_clearance_m'].values()]
        worst = min(vals) if vals else 9.0
        ok(worst >= 0.149, '%s %s every block keeps its clearance from every surface' % (blk, key),
           round(worst, 3), '>= 0.15')

print('=== the free heuristic')
for blk in 'ABC':
    for key, run in P[blk].items():
        if 'packed_t' not in run:
            continue
        ok(run['packed_t'] >= G[blk][key]['packed_t'] - 1e-6,
           '%s %s the unconstrained estimate is not below the straight-cut plan' % (blk, key),
           run['packed_t'], '>= %.0f' % G[blk][key]['packed_t'])

print('=== the tolerance ladder')
L = U['ladder']
for blk in 'ABC':
    for F, u in U[blk].items():
        q = (u['sigma_recon_m'] ** 2 + u['sigma_interp_m'] ** 2
             + u['sigma_mesh_m'] ** 2 + u['sigma_reg_m'] ** 2) ** 0.5
        ok(near(q, u['sigma_total_m_at_mean_depth'], 0.004),
           '%s total sigma is the quadrature sum' % F,
           u['sigma_total_m_at_mean_depth'], round(q, 4))
        r = (u['sigma_vel_m'] ** 2 + u['lambda4_m'] ** 2 + u['sigma_t0_m'] ** 2) ** 0.5
        ok(near(r, u['sigma_recon_m'], 0.004), '%s reconstruction sigma is the quadrature sum' % F,
           u['sigma_recon_m'], round(r, 4))
        ok(near(u['sigma_vel_m'], u['mean_depth_m'] * L['sigma_v_over_v'], 0.004),
           '%s velocity term is depth times sigma_v over v' % F,
           u['sigma_vel_m'], round(u['mean_depth_m'] * L['sigma_v_over_v'], 4))
        ok(near(u['lambda4_m'], L['lambda4_m'][u['channel']], 0.002),
           '%s quarter-wavelength matches its channel' % F)
        c = math.erf(0.15 / (u['sigma_total_m_at_mean_depth'] * 2 ** 0.5))
        ok(near(c, u['C_pos_15cm'], 0.01), '%s confidence at 15 cm is the error function' % F,
           u['C_pos_15cm'], round(c, 3))
        ok(near(u['C_pos_1sigma'], math.erf(1 / 2 ** 0.5), 0.01), '%s confidence at one sigma is 68 per cent' % F)
        ok(near(u['C_pos_2sigma'], math.erf(2 / 2 ** 0.5), 0.01), '%s confidence at two sigma is 95 per cent' % F)
        ok(near(u['sigma_total_pct_depth'], 100 * u['sigma_total_m_at_mean_depth'] / u['mean_depth_m'], 0.6),
           '%s sigma as a percentage of depth' % F)
        ok(near(u['two_sigma_m_max'], 2 * u['sigma_total_m_max'], 0.005), '%s two sigma is twice one sigma' % F)

print('=== the Monte Carlo')
for blk in 'ABC':
    m = M[blk]
    key = 'surface_%.1fm__' % float(m['chalk_depth_m'])
    for u in ('modelled', 'uncertain'):
        run = G[blk][key + u]
        risk = m['block_risk'][u]
        ok(len(risk) == len(run['boxes']),
           '%s %s one risk per planned block' % (blk, u), len(risk), len(run['boxes']))
        ok(near(m['plan_t'][u], run['packed_t'], 1.0),
           '%s %s the risked plan is the plan on the page' % (blk, u), m['plan_t'][u], run['packed_t'])
        if len(risk) == len(run['boxes']):
            order = sorted(range(len(run['boxes'])), key=lambda i: run['boxes'][i]['remove_seq'])
            w = sum(run['boxes'][i]['t'] * (1 - risk[k]) for k, i in enumerate(order))
            w2 = sum(run['boxes'][i]['t'] * (1 - risk[i]) for i in range(len(risk)))
            ok(near(m['plan_risk_weighted_t'][u], w, 2.0) or near(m['plan_risk_weighted_t'][u], w2, 2.0),
               '%s %s risk-weighted tonnage is the discounted sum' % (blk, u),
               m['plan_risk_weighted_t'][u], round(min(w, w2), 1))
        ok(m['blocks_over_20pct'][u] == sum(1 for r in risk if r > 0.2),
           '%s %s the count over 20 per cent matches the list' % (blk, u),
           m['blocks_over_20pct'][u], sum(1 for r in risk if r > 0.2))
        ok(near(m['mean_risk'][u], sum(risk) / max(len(risk), 1), 0.002),
           '%s %s mean risk is the mean of the list' % (blk, u))
        ok(all(0 <= r <= 1 for r in risk), '%s %s every risk is a probability' % (blk, u))
    r = m['replan_t']
    ok(r['min'] <= r['p10'] <= r['p50'] <= r['p90'] <= r['max'],
       '%s the re-planned spread is ordered' % blk,
       [r['min'], r['p10'], r['p50'], r['p90'], r['max']], 'ascending')

print('=== velocity and structure')
ok(near(V['median'], V['working_velocity'], 0.0005), 'the working velocity is the diffraction median',
   V['working_velocity'], V['median'])
ok(V['n_selected'] <= V['n_candidates'], 'the fits used are a subset of those found',
   V['n_selected'], V['n_candidates'])
ok(V['p10'] <= V['median'] <= V['p90'], 'the velocity percentiles are ordered')
ok(V['min'] <= V['p10'] and V['p90'] <= V['max'], 'the velocity range contains its percentiles')
eps = (0.2998 / V['median']) ** 2
ok(near(eps, L['eps_adopted'], 0.06), 'permittivity and velocity agree', round(eps, 2), L['eps_adopted'])
for blk in 'ABC':
    for F, pl in S[blk]['planes'].items():
        ok(near(pl['strike_grid_deg'], (pl['dip_direction_grid_deg'] - 90) % 360, 1.0)
           or near(pl['strike_grid_deg'], (pl['dip_direction_grid_deg'] + 90) % 360, 1.0),
           '%s strike is perpendicular to dip direction' % F,
           pl['strike_grid_deg'], (pl['dip_direction_grid_deg'] - 90) % 360)
        ok(pl['depth_min_m'] <= pl['depth_max_m'], '%s depth range is ordered' % F)
        ok(pl['plane_rms_m'] <= pl['plane_max_m'], '%s plane rms is not above its maximum' % F)

print()
print('%d checks, %d failed' % (checks, len(fails)))
if fails:
    print('\n'.join(fails))
sys.exit(1 if fails else 0)
