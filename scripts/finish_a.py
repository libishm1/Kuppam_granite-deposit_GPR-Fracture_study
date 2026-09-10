"""Block A: filter, grid, export, figure, and per-line verification against the report."""
import csv, os, numpy as np
from scipy.interpolate import griddata
from scipy.ndimage import uniform_filter
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa


def rd(p):
    R = list(csv.DictReader(open(p, encoding='utf-8')))
    for r in R:
        r['line'] = int(r['line']); r['x'] = float(r['x_cm']); r['y'] = float(r['y_cm'])
        r['z'] = float(r['depth_m']); r['env'] = float(r['envelope'])
    return R


A1 = rd('tables/PICKS_A1_raw.csv'); A2 = rd('tables/PICKS_A2_raw.csv')
# A-2: keep the report's stated extent on the seeded lines, plus every hunt hit
A2 = [r for r in A2 if (r['src'] == 'hunt') or (80 <= r['y'] <= 240)]
# A-1: dedupe Line 10 overlap (explicit segment + hunt on the same traces)
seen = set(); A1d = []
for r in A1:
    k = (r['line'], r['channel'], round(r['x']), round(r['y']))
    if k in seen: continue
    seen.add(k); A1d.append(r)
A1 = A1d
for nm, R in (('A1', A1), ('A2', A2)):
    flds = [k for k in R[0] if k not in ('x', 'y', 'z', 'env')]
    w = csv.DictWriter(open('tables/PICKS_%s_final.csv' % nm, 'w', newline='', encoding='utf-8'), fieldnames=flds)
    w.writeheader()
    for r in R: w.writerow({k: r[k] for k in flds})


def plane(R):
    P = np.array([[r['x'], r['y'], r['z']] for r in R]); A = np.c_[P[:, 0], P[:, 1], np.ones(len(P))]
    co, *_ = np.linalg.lstsq(A, P[:, 2], rcond=None); res = P[:, 2] - A @ co
    dip = np.degrees(np.arctan(np.hypot(co[0], co[1]) * 100)); az = np.degrees(np.arctan2(co[0], co[1])) % 360
    return co, dip, az, res.std(), abs(res).max(), P


def write_dxf(path, GX, GY, Z, layer):
    L = ['0', 'SECTION', '2', 'ENTITIES']; ny, nx = Z.shape
    for j in range(ny - 1):
        for i in range(nx - 1):
            q = [(GX[j, i], GY[j, i], Z[j, i]), (GX[j, i + 1], GY[j, i + 1], Z[j, i + 1]),
                 (GX[j + 1, i + 1], GY[j + 1, i + 1], Z[j + 1, i + 1]), (GX[j + 1, i], GY[j + 1, i], Z[j + 1, i])]
            if any(np.isnan(p[2]) for p in q): continue
            L += ['0', '3DFACE', '8', layer]
            for k, (x, y, z) in enumerate(q):
                L += [str(10 + k), '%.3f' % x, str(20 + k), '%.3f' % y, str(30 + k), '%.4f' % (-z * 100)]
    L += ['0', 'ENDSEC', '0', 'EOF']; open(path, 'w').write('\n'.join(L) + '\n')


def write_obj(path, GX, GY, Z, name):
    O = ['# Kuppam Block A %s, metres, z negative = depth' % name, 'o %s' % name]; vid = {}; c = 0
    ny, nx = Z.shape
    for j in range(ny):
        for i in range(nx):
            if np.isnan(Z[j, i]): continue
            c += 1; vid[(j, i)] = c; O.append('v %.4f %.4f %.4f' % (GX[j, i] / 100, GY[j, i] / 100, -Z[j, i]))
    for j in range(ny - 1):
        for i in range(nx - 1):
            k = [(j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i)]
            if all(t in vid for t in k): O.append('f %d %d %d %d' % tuple(vid[t] for t in k))
    open(path, 'w').write('\n'.join(O) + '\n')


out = {}
print('BLOCK A, 5.5 x 5.5 m, report frame (x along A0->A3, y along A0->A1)\n')
for nm, R, ext in (('A1', A1, ((0, 550), (0, 550))), ('A2', A2, ((0, 550), (40, 260)))):
    co, dip, az, rms, mx, P = plane(R); strike = (az + 90) % 180
    print('%s  %d picks on %d lines: plane dip %.1f deg, down-dip azimuth %.0f from +y toward +x, strike %.0f, residual RMS %.3f m max %.3f'
          % (nm, len(R), len({r['line'] for r in R}), dip, az, strike, rms, mx))
    gx = np.arange(ext[0][0], ext[0][1] + .1, 10.); gy = np.arange(ext[1][0], ext[1][1] + .1, 10.); GX, GY = np.meshgrid(gx, gy)
    Z = griddata(P[:, :2], P[:, 2], (GX, GY), 'linear'); Gp = np.c_[GX.ravel(), GY.ravel(), np.ones(GX.size)] @ co
    Z = np.where(np.isnan(Z.ravel()), Gp, Z.ravel()).reshape(GX.shape); Z = uniform_filter(Z, size=5, mode='nearest')
    Z = np.where(Z < 0.05, np.nan, Z)   # the plane daylights; clip above the block top
    out[nm] = (GX, GY, Z, co)
    np.savetxt('model/%s_grid_10cm.xyz' % nm, np.c_[GX.ravel(), GY.ravel(), Z.ravel()], fmt='%.2f %.2f %.4f')
    write_dxf('model/%s_surface.dxf' % nm, GX, GY, Z, nm); write_obj('model/%s_surface.obj' % nm, GX, GY, Z, nm)
print('wrote model/A1_*, model/A2_* (dxf, obj, xyz)')

# ---- verification against every A-block number the report published ----
print('\n=== A-1 vs report ===')
co1 = out['A1'][3]
for ln, fx, a0, a1, z0, z1, dp, ch in ((19, 300, 266, 342, 1.13, 1.47, 24.0, 'HF'), (10, 450, 422, 542, 1.30, 1.60, 13.7, 'LF')):
    s = [r for r in A1 if r['line'] == ln and r['channel'] == ch]
    key = 'y' if ln >= 13 else 'x'; a = np.array([r[key] for r in s]); z = np.array([r['z'] for r in s])
    o = np.argsort(a); a = a[o]; z = z[o]
    d = np.degrees(np.arctan(np.polyfit(a / 100, z, 1)[0]))
    print('  line %2d %s fixed %d: report %.2f->%.2f m over %d-%d (dip %.1f); ours %.2f->%.2f (dip %+.1f)  %s'
          % (ln, ch, fx, z0, z1, a0, a1, dp, z[0], z[-1], d, 'as printed' if ln == 19 else 'REVERSED, the sign of the dip is the finding'))
print('  report: "NE-SW trending", arrows NW, text "deeper towards the southwest", "14-24 deg"')
print('  ours:   strike %.0f (NE-SW), down-dip azimuth %.0f (NW), dip %.1f'
      % ((np.degrees(np.arctan2(co1[0], co1[1])) + 90) % 180, np.degrees(np.arctan2(co1[0], co1[1])) % 360, np.degrees(np.arctan(np.hypot(co1[0], co1[1]) * 100))))
print('  report: intersection with A-2 near x=90, y=135')
co2 = out['A2'][3]
yy = 135.0
x = ((co2[1] - co1[1]) * yy + (co2[2] - co1[2])) / (co1[0] - co2[0]); z = co1[0] * x + co1[1] * yy + co1[2]
print('  ours:   planes intersect at y=%.0f -> x=%.0f cm, z=%.2f m' % (yy, x, z))

print('\n=== A-2 vs report ===')
print('  report: lines 13,15,16,19,22 at y=128-148, dips 32-41 (mean 38), "E-W", "dipping towards increasing Y", NO depths')
for ln in (13, 15, 16, 19, 22):
    s = [r for r in A2 if r['line'] == ln]; y = np.array([r['y'] for r in s]) / 100; z = np.array([r['z'] for r in s])
    print('    line %2d: %d picks, y %.0f-%.0f cm, z %.2f-%.2f m, apparent dip %.1f'
          % (ln, len(s), y.min() * 100, y.max() * 100, z.min(), z.max(), np.degrees(np.arctan(np.polyfit(y, z, 1)[0]))))
print('  ours: dip %.1f, azimuth %.0f (= +y), strike %.0f (E-W)'
      % (np.degrees(np.arctan(np.hypot(co2[0], co2[1]) * 100)), np.degrees(np.arctan2(co2[0], co2[1])) % 360, (np.degrees(np.arctan2(co2[0], co2[1])) + 90) % 180))
y_at = lambda zz: (zz - co2[2] - co2[0] * 275) / co2[1]
print('  "position y=128-148": our plane crosses z=0.50 m at y=%.0f, z=0.75 at y=%.0f -> their "position" is the 0.5-0.7 m crossing' % (y_at(0.5), y_at(0.75)))
xl = [r for r in A2 if r['orientation'] == 'X-line']
print('  X-line cross-check (report has none): %d picks on lines %s' % (len(xl), sorted({r['line'] for r in xl})))

fig = plt.figure(figsize=(13, 5.8))
ax = fig.add_subplot(121, projection='3d')
ax.plot([0, 550, 550, 0, 0], [0, 0, 550, 550, 0], [0] * 5, 'k-', lw=1.5)
for nm, cm_ in (('A1', 'autumn'), ('A2', 'winter')):
    GX, GY, Z, _ = out[nm]; s = 2; ax.plot_surface(GX[::s, ::s], GY[::s, ::s], -Z[::s, ::s], cmap=cm_, alpha=.88, linewidth=0)
ax.set_xlim(0, 550); ax.set_ylim(0, 550); ax.set_zlim(-3.2, 0.2); ax.set_xlabel('x (cm)'); ax.set_ylabel('y (cm)'); ax.set_zlabel('depth (m)')
ax.set_title('Block A: A-1 (warm, NE-SW, dips NW) and A-2 (cool, E-W, dips +y)', fontsize=10); ax.view_init(elev=38, azim=-128); ax.set_box_aspect((5.5, 5.5, 3.2))
ax2 = fig.add_subplot(122)
for nm, cm_ in (('A1', 'Oranges'), ('A2', 'Blues')):
    GX, GY, Z, _ = out[nm]; ax2.pcolormesh(GX, GY, Z, shading='auto', cmap=cm_, alpha=.9)
    cs = ax2.contour(GX, GY, Z, levels=np.arange(0.25, 3.0, 0.25), colors='k', linewidths=.4); ax2.clabel(cs, fmt='%.2f', fontsize=6)
for R, c, lab in ((A1, 'r', 'A-1 picks'), (A2, 'b', 'A-2 picks')):
    ax2.scatter([r['x'] for r in R], [r['y'] for r in R], s=2, c=c, alpha=.6, label=lab)
ax2.plot([300, 300], [266, 342], 'k-', lw=3, alpha=.5); ax2.plot([422, 542], [450, 450], 'k-', lw=3, alpha=.5, label='report picks')
ax2.legend(fontsize=7, loc='upper left'); ax2.set_aspect('equal'); ax2.set_xlim(0, 550); ax2.set_ylim(0, 550)
ax2.set_xlabel('x (cm)'); ax2.set_ylabel('y (cm)'); ax2.set_title('Block A plan, depth contours in m', fontsize=10)
fig.tight_layout(); fig.savefig('figs/BlockA_model.png', dpi=135); print('\nwrote figs/BlockA_model.png')
