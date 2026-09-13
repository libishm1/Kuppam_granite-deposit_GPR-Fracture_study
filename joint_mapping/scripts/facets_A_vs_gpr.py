"""Block A: the joint faces on the rock (facet segmentation of the photogrammetry, cache/facets_A.npz)
against the two GPR sheets, in A's own bench frame. No compass anywhere in this figure: axes are
the painted grid's +x and +y. Writes figs/FACETS_A_vs_GPR_plan.png, figs/FACETS_A_vs_GPR_net.png
and tables/facets_A_vs_gpr.json. Read-only on the data."""
import io, json, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb

J = 'D:/code_ws/outputs/2026-09-11/joint_mapping'
G = 'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
z = np.load(os.path.join(J, 'cache', 'facets_A.npz'))
P = z['xyz'].astype(float); N = z['nrm'].astype(float); pl = z['planarity']; keep = z['keep']; lab = z['lab']
F = json.load(io.open(os.path.join(G, 'dataset/bench_frame_m/Block_A/FRAME.json'), encoding='utf-8'))
o = np.array(F['report_origin_xy']) * F['scale_m_per_mesh_unit']; xd = np.array(F['report_x_dir']); yd = np.array(F['report_y_dir'])
d = P[:, :2] - o; gx = d @ xd; gy = d @ yd
n = N / np.linalg.norm(N, axis=1, keepdims=True); n[n[:, 2] < 0] *= -1
dip = np.degrees(np.arccos(np.clip(n[:, 2], -1, 1)))
nx = n[:, :2] @ xd; ny = n[:, :2] @ yd
brg = np.degrees(np.arctan2(nx, ny)) % 360                     # dip direction as grid bearing, 0 = +y, 90 = +x
mod = (dip > 25) & (dip < 60) & (pl > np.percentile(pl, 50))   # the moderately dipping, planar faces

S = json.load(io.open(os.path.join(J, 'tables', 'stereonet_radar.json'), encoding='utf-8'))
recs = []
def walk(o_):
    if isinstance(o_, dict):
        if 'plane_dip_dir_azimuth_deg' in o_: recs.append(o_)
        for v in o_.values(): walk(v)
    elif isinstance(o_, list):
        for v in o_: walk(v)
walk(S)
# the sheets' grid bearings, recovered from the azimuths with A's formula (az = 180 - brg)
GPR = {}
for r in recs:
    nm = r.get('surface') or r.get('name')
    if nm.startswith('A'):
        az = float(r['plane_dip_dir_azimuth_deg']); GPR[nm.split()[0]] = (float(r['plane_dip_deg']), (180.0 - az) % 360)
print('GPR sheets (dip, grid bearing):', GPR)

# ---------------------------------------------------------------- plan view
fig, ax = plt.subplots(figsize=(11, 10))
sel = mod & (gx > -5) & (gx < 8) & (gy > -5) & (gy < 9)
idx = np.where(sel)[0]; rng = np.random.default_rng(0); idx = rng.choice(idx, min(len(idx), 40000), replace=False)
col = hsv_to_rgb(np.c_[brg[idx] / 360.0, np.ones(len(idx)) * 0.85, np.ones(len(idx)) * 0.9])
ax.scatter(gx[idx], gy[idx], s=2, c=col, linewidths=0)
flat = (dip < 8) & (gx > -6) & (gx < 9) & (gy > -6) & (gy < 10)
fi = np.where(flat)[0]; fi = rng.choice(fi, min(len(fi), 20000), replace=False)
ax.scatter(gx[fi], gy[fi], s=1, c='#d9d9d9', linewidths=0, zorder=0)
ax.plot([0, 5.5, 5.5, 0, 0], [0, 0, 5.5, 5.5, 0], 'k-', lw=2)
for i in range(1, 11):
    ax.plot([i * 0.5] * 2, [0, 5.5], 'k-', lw=0.3, alpha=0.5); ax.plot([0, 5.5], [i * 0.5] * 2, 'k-', lw=0.3, alpha=0.5)
ax.annotate('A0', (0, 0), (-0.55, -0.35), fontsize=12, fontweight='bold')
def arrow(b, x0, y0, L, c, lbl, ls='-'):
    dx, dy = L * np.sin(np.radians(b)), L * np.cos(np.radians(b))
    ax.annotate('', (x0 + dx, y0 + dy), (x0, y0), arrowprops=dict(arrowstyle='-|>', lw=3, color=c, linestyle=ls))
    ax.text(x0 + dx * 1.15, y0 + dy * 1.15, lbl, color=c, fontsize=10, fontweight='bold', ha='center')
for k, (nm, c) in enumerate((('A-1', '#c62828'), ('A-2', '#ef6c00'))):
    dp, b = GPR[nm]
    arrow(b, 2.75, 2.75, 1.6, c, '%s as drawn\n%.0f deg toward %03.0f' % (nm, dp, b))
    bt = (90.0 - b) % 360
    arrow(bt, 2.75, 2.75, 1.6, c, '%s if picks\ntransposed: %03.0f' % (nm, bt), ls='--')
# west-of-A statistic
w = mod & (gx > -4) & (gx < 0) & (gy > -1) & (gy < 6.5)
h, _ = np.histogram(brg[w], bins=8, range=(-22.5, 337.5)); LAB = ['+y', '+x+y', '+x', '+x-y', '-y', '-x-y', '-x', '-x+y']
top = np.argsort(h)[::-1][:2]
ax.text(-4.8, 7.6, 'faces WEST of A (x -4..0), 25-60 deg dip: %d pts, median %.0f deg,\ndip toward %s %d%%, %s %d%%'
        % (w.sum(), np.median(dip[w]), LAB[top[0]], 100 * h[top[0]] / h.sum(), LAB[top[1]], 100 * h[top[1]] / h.sum()), fontsize=10,
        bbox=dict(fc='white', ec='#888'))
# colour wheel legend
for b_, txt in ((0, '+y'), (90, '+x'), (180, '-y'), (270, '-x')):
    ax.scatter([7.2 + 0.5 * np.sin(np.radians(b_))], [-3.2 + 0.5 * np.cos(np.radians(b_))], s=90, c=[hsv_to_rgb((b_ / 360, 0.85, 0.9))])
    ax.text(7.2 + 0.85 * np.sin(np.radians(b_)), -3.2 + 0.85 * np.cos(np.radians(b_)), txt, ha='center', va='center', fontsize=9)
ax.text(7.2, -4.3, 'colour = dip direction\n(grid bearing)', ha='center', fontsize=9)
ax.set_xlim(-5.2, 8.5); ax.set_ylim(9.2, -5.2); ax.set_aspect('equal')
ax.set_xlabel('grid +x  (east, per the field)'); ax.set_ylabel('grid +y  (south, per the field)   [y drawn downward like the page]')
ax.set_title('Block A: joint faces on the rock (facet segmentation of the photogrammetry, 25-60 deg dips)\n'
             'versus the two GPR sheets, in the bench frame. Solid arrows: sheets as drawn. Dashed: if A\'s picks are transposed.', fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(J, 'figs', 'FACETS_A_vs_GPR_plan.png'), dpi=120); plt.close(fig)

# ---------------------------------------------------------------- stereonet, grid axes, equal-area lower hemisphere
def net_xy(dip_deg, brg_deg):
    """pole of the plane: plunges (90 - dip) toward brg + 180; equal-area lower hemisphere, +y up."""
    theta = np.radians(dip_deg); r = np.sqrt(2.0) * np.sin(theta / 2.0)
    t = np.radians(brg_deg + 180.0)
    return r * np.sin(t), r * np.cos(t)
fig, ax = plt.subplots(figsize=(9, 9))
for rr in (np.sqrt(2) * np.sin(np.radians(a) / 2) for a in (30, 60, 90)):
    ax.add_patch(plt.Circle((0, 0), rr, fill=False, lw=0.6, color='#999'))
ax.plot([-1, 1], [0, 0], color='#bbb', lw=0.5); ax.plot([0, 0], [-1, 1], color='#bbb', lw=0.5)
sel2 = mod & (gx > -5) & (gx < 8) & (gy > -5) & (gy < 9)
i2 = np.where(sel2)[0]; i2 = rng.choice(i2, min(len(i2), 30000), replace=False)
x_, y_ = net_xy(dip[i2], brg[i2])
ax.hexbin(x_, y_, gridsize=45, extent=(-1, 1, -1, 1), cmap='Greys', mincnt=1, linewidths=0)
xw, yw = net_xy(dip[w], brg[w]); ax.scatter(xw, yw, s=6, c='#2e7d32', alpha=0.5, label='faces west of A (%d)' % w.sum())
for nm, c in (('A-1', '#c62828'), ('A-2', '#ef6c00')):
    dp, b = GPR[nm]
    x1, y1 = net_xy(dp, b); ax.scatter([x1], [y1], s=260, c=c, edgecolors='k', zorder=5, label='%s pole as drawn (%.0f/%03.0f)' % (nm, dp, b))
    bt = (90 - b) % 360; x2, y2 = net_xy(dp, bt); ax.scatter([x2], [y2], s=260, c=c, marker='D', edgecolors='k', zorder=5, label='%s pole if picks transposed (%.0f/%03.0f)' % (nm, dp, bt))
for b_, txt in ((0, '+y'), (90, '+x'), (180, '-y'), (270, '-x')):
    ax.text(1.07 * np.sin(np.radians(b_)), 1.07 * np.cos(np.radians(b_)), txt, ha='center', va='center', fontsize=13, fontweight='bold')
ax.set_xlim(-1.15, 1.15); ax.set_ylim(-1.15, 1.15); ax.set_aspect('equal'); ax.axis('off')
ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.02), fontsize=9, ncol=2, frameon=True)
ax.set_title('Block A stereonet in the bench frame (poles, equal-area, lower hemisphere; grid +y up)\n'
             'grey: all moderately dipping rock faces around A; green: the faces west of A; circles/diamonds: GPR sheets', fontsize=11)
fig.savefig(os.path.join(J, 'figs', 'FACETS_A_vs_GPR_net.png'), dpi=120, bbox_inches='tight'); plt.close(fig)

# ---------------------------------------------------------------- numbers
def sector_stats(m):
    h, _ = np.histogram(brg[m], bins=8, range=(-22.5, 337.5)); return {LAB[i]: round(100.0 * h[i] / max(h.sum(), 1), 1) for i in range(8)}, int(m.sum()), float(np.median(dip[m])) if m.sum() else None
out = dict(frame='Block A bench frame; grid bearings, 0 = +y, 90 = +x; +x is east per the field (faces west of A at -x dip toward +x)',
           selection='planar (top half by planarity), dip 25-60 deg',
           faces_west_of_A=dict(zip(('pct_by_dip_direction', 'n', 'median_dip'), sector_stats(w))),
           faces_around_A=dict(zip(('pct_by_dip_direction', 'n', 'median_dip'), sector_stats(sel2))),
           gpr_sheets={k: dict(dip=v[0], grid_bearing=v[1], grid_bearing_if_picks_transposed=(90 - v[1]) % 360) for k, v in GPR.items()},
           reading='rock faces dip toward +x / +x-y; GPR sheets as drawn dip toward +y / -x+y; transposing the picks puts the sheets on the rock')
json.dump(out, io.open(os.path.join(J, 'tables', 'facets_A_vs_gpr.json'), 'w', encoding='utf-8'), indent=1)
print(json.dumps(out, indent=1))
print('wrote figs/FACETS_A_vs_GPR_plan.png, figs/FACETS_A_vs_GPR_net.png, tables/facets_A_vs_gpr.json')
