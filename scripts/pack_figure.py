"""Packing figure: per block, plan of packed boxes by class for the mid scenario, and the yield bars across scenarios."""
import numpy as np, json, os
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
P = json.load(open(os.path.join(OUT, 'tables', 'block_packing.json')))
DIMS = {'A': (5.5, 5.5), 'B': (9.5, 6.0), 'C': (7.0, 8.0)}
COL = {'gangsaw_large': '#1b7f3b', 'gangsaw_standard': '#57a639', 'small_block': '#e0a400', 'cutter_block': '#c96a1b'}
LAB = {'gangsaw_large': 'gangsaw large (>=2.7x1.5x1.5)', 'gangsaw_standard': 'gangsaw standard (>=2.1x1.2x1.2)', 'small_block': 'small (>=1.5x0.9x0.9)', 'cutter_block': 'cutter (>=0.9x0.6x0.6)'}
SC = ['ignore_surface', 'surface_0.5m', 'surface_1.0m', 'surface_full']; SCL = ['surface cracks ignored', 'to 0.5 m', 'to 1.0 m', 'full depth']
fig = plt.figure(figsize=(18, 11))
for i, blk in enumerate('ABC'):
    W, H = DIMS[blk]; r = P[blk]['surface_1.0m']
    ax = fig.add_subplot(2, 3, i + 1)
    ax.add_patch(Rectangle((0, 0), W, H, fill=False, lw=1.5, color='k'))
    # sketch traces
    import csv
    tr = {}
    for q in csv.DictReader(open(os.path.join(OUT, 'tables', 'sketch_chained_%s.csv' % blk), encoding='utf-8')): tr.setdefault(int(q['trace_id']), []).append((float(q['x_cm']) / 100, float(q['y_cm']) / 100))
    for v in tr.values(): v = np.array(v); ax.plot(v[:, 0], v[:, 1], '-', color='#2050ff', lw=1.2, alpha=.8)
    # boxes: draw deepest first so shallow ones are on top; label height
    for b in sorted(r['boxes'], key=lambda b: -b['z0']):
        ax.add_patch(Rectangle((b['x0'], b['y0']), b['x1'] - b['x0'], b['y1'] - b['y0'], facecolor=COL[b['cls']], edgecolor='k', lw=.6, alpha=0.55 if b['z0'] > 0 else 0.85))
        if b['cls'].startswith('gangsaw'): ax.text(0.5 * (b['x0'] + b['x1']), 0.5 * (b['y0'] + b['y1']), '%.1fx%.1fx%.1f\n%.0f-%.0f m' % (b['L'], b['Wd'], b['Hh'], b['z0'], b['z1']), ha='center', va='center', fontsize=6)
    ax.set_xlim(-0.2, W + 0.2); ax.set_ylim(-0.2, H + 0.2); ax.set_aspect('equal'); ax.set_xlabel('x (m)'); ax.set_ylabel('y (m)')
    c = r['classes']
    ax.set_title('Block %s, surface cracks to 1.0 m: %d large + %d std gangsaw, %d small, %d cutter = %.0f t of %.0f t rock (%.0f%%)\ndepth limit: %s' % (
        blk, c['gangsaw_large']['n'], c['gangsaw_standard']['n'], c['small_block']['n'], c['cutter_block']['n'], r['packed_t'], r['gross_rock_m3'] * 2.95, 100 * r['recovery_ratio'], r['depth_limit']), fontsize=8)
    ax2 = fig.add_subplot(2, 3, i + 4)
    x = np.arange(len(SC)); bottom = np.zeros(len(SC))
    for cls in COL:
        vals = np.array([P[blk][s]['classes'][cls]['t'] for s in SC]); ax2.bar(x, vals, bottom=bottom, color=COL[cls], label=LAB[cls]); bottom += vals
    gross = P[blk][SC[0]]['gross_rock_m3'] * 2.95
    ax2.axhline(gross, color='k', ls='--', lw=1); ax2.text(len(SC) - 0.5, gross, ' gross rock %.0f t' % gross, va='bottom', ha='right', fontsize=7)
    for k, s in enumerate(SC): ax2.text(k, bottom[k] + 5, '%.0f%%' % (100 * P[blk][s]['recovery_ratio']), ha='center', fontsize=8)
    ax2.set_xticks(x); ax2.set_xticklabels(SCL, fontsize=7); ax2.set_ylabel('tonnes in saleable blocks'); ax2.set_title('Block %s yield by scenario for the surface cracks\' depth' % blk, fontsize=9)
    if i == 0: ax2.legend(fontsize=7, loc='upper right')
fig.suptitle('Kuppam Blocks A, B, C: block packing against the GPR surfaces (15 cm buffer) and the field-sketch surface fractures (10 cm buffer); 5 cm kerf; handling cap 3.3 x 2.0 x 2.0 m', fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(OUT, 'figs', 'PACKING.png'), dpi=120); print('wrote figs/PACKING.png')
