"""Structural orientation data for a geologist, all in the GRID frame (no true north is known).
C-2 uses the network-ADJUSTED picks (z_adj), the same version the modelled surface is built from; the other five use their
final or raw picks. Dips are of the modelled, unmigrated surfaces (see uncertainty.py for the migrated planes).
GPR planes: dip, dip direction (bearing from +y toward +x), plane residual, extent. Chalked cracks: strike rose and
length-weighted strike statistics per block. Also the angle between each GPR plane's strike and the dominant
chalked strike, and joint spacing along the two grid axes from the sketch."""
import numpy as np, csv, os, json
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
DIMS = {'A': (5.5, 5.5), 'B': (9.5, 6.0), 'C': (7.0, 8.0)}
FEATS = {'A': ('A1', 'A2'), 'B': ('B1', 'B2'), 'C': ('C1', 'C2')}
S = {}
fig, axes = plt.subplots(1, 3, figsize=(15, 5), subplot_kw=dict(projection='polar'))
for ax, blk in zip(axes, 'ABC'):
    W, H = DIMS[blk]; S[blk] = dict(planes={}, cracks={})
    for F in FEATS[blk]:
        pf = next(p for p in (os.path.join(OUT, 'tables', n % F) for n in ('PICKS_%s_final.csv', 'PICKS_%s_adjusted.csv', 'PICKS_%s_raw.csv')) if os.path.exists(p))
        rr = list(csv.DictReader(open(pf, encoding='utf-8'))); P = np.array([[float(q['x_cm']) / 100, float(q['y_cm']) / 100, float(q.get('z_adj') or q['depth_m'])] for q in rr])
        A = np.c_[P[:, 0], P[:, 1], np.ones(len(P))]; co, *_ = np.linalg.lstsq(A, P[:, 2], rcond=None); res = P[:, 2] - A @ co
        dip = np.degrees(np.arctan(np.hypot(co[0], co[1]))); ddir = np.degrees(np.arctan2(co[0], co[1])) % 360      # bearing from +y toward +x, of the DOWN-dip direction
        strike = (ddir - 90) % 180
        S[blk]['planes'][F] = dict(n_picks=len(P), lines=len({q['line'] for q in rr}), dip_deg=round(float(dip), 1), dip_direction_grid_deg=round(float(ddir), 0), strike_grid_deg=round(float(strike), 0),
                                   depth_min_m=round(float(P[:, 2].min()), 2), depth_max_m=round(float(P[:, 2].max()), 2), plane_rms_m=round(float(res.std()), 3), plane_max_m=round(float(abs(res).max()), 3),
                                   footprint_x_m=[round(float(P[:, 0].min()), 1), round(float(P[:, 0].max()), 1)], footprint_y_m=[round(float(P[:, 1].min()), 1), round(float(P[:, 1].max()), 1)])
    # chalked cracks
    tr = {}
    for q in csv.DictReader(open(os.path.join(OUT, 'tables', 'sketch_chained_%s.csv' % blk), encoding='utf-8')): tr.setdefault(int(q['trace_id']), []).append((float(q['x_cm']) / 100, float(q['y_cm']) / 100))
    segs = []
    for v in tr.values():
        v = np.array(v)
        for a, b in zip(v[:-1], v[1:]):
            L = np.hypot(*(b - a))
            if L > 0.02: segs.append((np.degrees(np.arctan2(b[0] - a[0], b[1] - a[1])) % 180, L))     # strike as bearing from +y toward +x
    st = np.array([s[0] for s in segs]); ln = np.array([s[1] for s in segs])
    hist, edges = np.histogram(st, bins=18, range=(0, 180), weights=ln)
    # dominant set: circular mean over doubled angles, length weighted
    th = np.radians(2 * st); C = np.sum(ln * np.cos(th)) / ln.sum(); Sn = np.sum(ln * np.sin(th)) / ln.sum(); dom = (np.degrees(np.arctan2(Sn, C)) / 2) % 180; R = np.hypot(C, Sn)
    # trace length stats and spacing: intersections of a line along x and along y with the cracks
    lens = [sum(np.hypot(*np.diff(np.array(v), axis=0).T)) for v in tr.values()]
    def crossings(axis):
        cnt = []
        for pos in np.arange(0.5, (H if axis == 'x' else W) - 0.49, 0.5):
            n = 0
            for v in tr.values():
                v = np.array(v)
                for a, b in zip(v[:-1], v[1:]):
                    k = 1 if axis == 'x' else 0
                    if (a[k] - pos) * (b[k] - pos) < 0: n += 1
            cnt.append(n)
        return np.mean(cnt), (W if axis == 'x' else H)
    cx, Lx = crossings('x'); cy, Ly = crossings('y')
    S[blk]['cracks'] = dict(traces=len(tr), total_m=round(float(ln.sum()), 1), mean_trace_m=round(float(np.mean(lens)), 2), max_trace_m=round(float(np.max(lens)), 2),
                            dominant_strike_grid_deg=round(float(dom), 0), concentration_R=round(float(R), 2),
                            crossings_per_m_along_x=round(float(cx / Lx), 2), crossings_per_m_along_y=round(float(cy / Ly), 2),
                            mean_spacing_along_x_m=round(float(Lx / max(cx, 1e-9)), 2), mean_spacing_along_y_m=round(float(Ly / max(cy, 1e-9)), 2))
    for F, pl in S[blk]['planes'].items():
        d = abs(((pl['strike_grid_deg'] - dom) + 90) % 180 - 90); pl['angle_to_dominant_crack_strike_deg'] = round(float(d), 0)
    # rose
    ang = np.radians(edges[:-1] + 5); w = np.radians(10)
    ax.bar(ang, hist, width=w, bottom=0, color='#2457E6', alpha=0.8); ax.bar(ang + np.pi, hist, width=w, bottom=0, color='#2457E6', alpha=0.8)
    for F, pl in S[blk]['planes'].items():
        s_ = np.radians(pl['strike_grid_deg']); ax.plot([s_, s_ + np.pi], [hist.max() * 1.05] * 2, '-', color='#D98E1E' if pl['depth_max_m'] < 2 else '#1F8A80', lw=3, label='%s strike, dip %.0f° toward %.0f°' % (F, pl['dip_deg'], pl['dip_direction_grid_deg']))
    ax.set_theta_zero_location('N'); ax.set_theta_direction(-1); ax.set_thetagrids(range(0, 360, 30), [('+y' if a == 0 else '+x' if a == 90 else '−y' if a == 180 else '−x' if a == 270 else str(a) + '°') for a in range(0, 360, 30)])
    ax.set_yticklabels([]); ax.set_title('Block %s: chalked-crack strike rose (length-weighted), grid frame\ndominant %.0f°, R = %.2f' % (blk, dom, R), fontsize=9); ax.legend(fontsize=7, loc='lower center', bbox_to_anchor=(0.5, -0.28))
fig.tight_layout(rect=(0, 0, 1, 0.94)); fig.suptitle('Bearings are from the grid +y axis toward +x; no true north is known', fontsize=10, y=0.985); fig.savefig(os.path.join(OUT, 'figs', 'STRUCTURAL_roses.png'), dpi=120)
json.dump(S, open(os.path.join(OUT, 'tables', 'structural.json'), 'w'), indent=1)
for blk in 'ABC':
    print('Block %s' % blk)
    for F, pl in S[blk]['planes'].items():
        print('  %s: dip %.1f° toward grid bearing %.0f°, strike %.0f°; %.2f-%.2f m; plane rms %.3f m; %d picks on %d lines; %.0f° to the dominant chalked strike' % (F, pl['dip_deg'], pl['dip_direction_grid_deg'], pl['strike_grid_deg'], pl['depth_min_m'], pl['depth_max_m'], pl['plane_rms_m'], pl['n_picks'], pl['lines'], pl['angle_to_dominant_crack_strike_deg']))
    c = S[blk]['cracks']; print('  cracks: %d traces, %.1f m, mean %.2f m, dominant strike %.0f° (R %.2f); spacing along x %.2f m, along y %.2f m' % (c['traces'], c['total_m'], c['mean_trace_m'], c['dominant_strike_grid_deg'], c['concentration_R'], c['mean_spacing_along_x_m'], c['mean_spacing_along_y_m']))
print('wrote tables/structural.json, figs/STRUCTURAL_roses.png')
