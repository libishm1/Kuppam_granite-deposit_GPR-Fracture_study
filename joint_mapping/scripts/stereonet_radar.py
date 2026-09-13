"""A stereonet of the three benches from the radar-picked surfaces.

The six modelled surfaces are not planes; they are gridded at 10 cm, so every node carries a local
orientation. Taking the local gradient of the surface in absolute bench-frame elevation gives a pole
per node, and a pole per node gives a real spread rather than six lonely points. The spread is the
curvature of the modelled surface, not a measurement error.

    elevation(x, y) = DEM(x, y) - depth(x, y)

The gradient is taken after a light Gaussian smooth, so the poles describe the surface at roughly
the half-metre scale rather than the noise of the picking.

Only the radar-picked surfaces are plotted. The chalked surface cracks are deliberately left out:
their dip has never been measured, so they have no pole and do not belong on a stereonet.

Azimuth runs through each block's east axis (ORIENTATION.md: B has +y east, A and C +x), which is
what lets three benches in three separate grid frames share one sheet. Dip is measured from each
block's own bench plane, not from gravity, and those planes tilt 1 to 2 degrees.

Usage: stereonet_radar.py
"""
import numpy as np, os, json
from scipy.ndimage import gaussian_filter
from scipy.interpolate import RegularGridInterpolator
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = 'D:/code_ws/outputs/2026-09-11/joint_mapping'
GPR = 'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
FEATS = {'A': ['A1', 'A2'], 'B': ['B1', 'B2'], 'C': ['C1', 'C2']}
NAME = {'A1': 'A-1 dipping sheet', 'A2': 'A-2 inclined sheet', 'B1': 'B-1 shallow sheet',
        'B2': 'B-2 deep wedge', 'C1': 'C-1 shallow sheet', 'C2': 'C-2 base cap'}
EAST = {'A': '+x', 'B': '+y', 'C': '+y'}   # 12 Sep. Origin is the north-west corner on every bench and both axes run into the bench, but which axis runs east differs: on A the X-line numerals run down the WEST edge from A0 (client, from the site: '9, 12...' from the NW to the SW corner), so X-lines are stacked north-south and run east, +x east, +y south, left-handed. On B and C +y is east (6 m and 8 m sides, verified). See ORIENTATION.md.
COL = {'A1': '#C8452B', 'A2': '#E08A3C', 'B1': '#1F8A80', 'B2': '#2F6DB5', 'C1': '#7B4EA3', 'C2': '#4B7F32'}
SMOOTH = 2.5          # grid cells of 10 cm, so about a half-metre window
DIPMAX = 45.0         # the nets are zoomed to this dip; every surface here is gentler


def load_grid(p):
    a = np.loadtxt(p)
    gx = np.unique(a[:, 0]) / 100
    gy = np.unique(a[:, 1]) / 100
    return gx, gy, a[:, 2].reshape(len(gy), len(gx))


def elevation(blk, F):
    gx, gy, d = load_grid(os.path.join(GPR, 'model', '%s_grid_10cm.xyz' % F))
    ex, ey, dem = load_grid(os.path.join(GPR, 'dataset', 'bench_frame_m', 'Block_%s' % blk,
                                         'Block%s_DEM_10cm.xyz' % blk))
    de = RegularGridInterpolator((ey, ex), dem, bounds_error=False, fill_value=np.nan)
    X, Y = np.meshgrid(gx, gy)
    E = de(np.c_[Y.ravel(), X.ravel()]).reshape(X.shape) - d
    return gx, gy, E


def lsq_pole(gx, gy, E):
    """upward normal of the least-squares plane through the surface, which is what the GPR study
    reports; the local poles describe the scatter about it"""
    X, Y = np.meshgrid(gx, gy)
    ok = np.isfinite(E)
    A = np.c_[X[ok], Y[ok], np.ones(ok.sum())]
    co, *_ = np.linalg.lstsq(A, E[ok], rcond=None)
    n = np.array([-co[0], -co[1], 1.0])
    return n / np.linalg.norm(n)


def local_poles(gx, gy, E):
    ok = np.isfinite(E)
    Ef = np.where(ok, E, np.nanmean(E))
    W = gaussian_filter(ok.astype(float), SMOOTH)
    S = gaussian_filter(np.where(ok, Ef, 0.0), SMOOTH) / np.maximum(W, 1e-6)
    hy = float(gy[1] - gy[0]); hx = float(gx[1] - gx[0])
    dzdy, dzdx = np.gradient(S, hy, hx)
    n = np.stack([-dzdx, -dzdy, np.ones_like(S)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    er = W > 0.92                                    # keep away from the ragged edge
    return n[ok & er]


def dip_az(n, blk):
    """dip and dip direction of the plane whose UPWARD normal is n.

    The upward normal of a surface leans toward the down-dip side, so the dip direction is the
    trend of its horizontal part: bearing = atan2(n_x, n_y) with 0 = +y and 90 = +x, the same
    convention the GPR study uses.

    Grid bearing to true azimuth follows the east axis recorded in EAST above. On every bench the
    origin sits at the north-western corner, so the axis that is not east runs south: on A, +x is
    east and +y south, giving azimuth = 180 - bearing; on B and C, +y is east and +x south, giving
    azimuth = bearing + 90. Fitting the grid to the site model from the drawn blocks measures the
    two axes at A +x 105.0 / +y 195.0, B +y 103.3 / +x 193.3, C +y 103.0 / +x 193.0 degrees, which
    is where the south reading and C's right handedness come from. The idealised 90 and 180 are
    kept here because the site frame's north is taken from the satellite view, not a compass.
    """
    n = np.atleast_2d(n).copy()
    n[n[:, 2] < 0] *= -1
    dip = np.degrees(np.arccos(np.clip(np.abs(n[:, 2]), -1, 1)))
    brg = np.degrees(np.arctan2(n[:, 0], n[:, 1])) % 360
    az = (180 - brg) % 360 if EAST[blk] == '+x' else (brg + 90) % 360
    return dip, az


def to_net(n, blk):
    """pole (downward normal) of the plane, on an equal-area lower hemisphere drawn NORTH UP.

    The grid axes are not compass axes, so the pole has to be rotated out of the grid before it is
    plotted against N, E, S, W, and the rotation must come from the same EAST table `dip_az` uses.
    It did not until 12 September: this function carried its own hard-coded `blk in 'AC'` test, so
    after A's and C's east axes were corrected the plotted poles disagreed with the dip directions
    printed beside them on two benches out of three. Read the table, never restate the convention.
    """
    L = np.atleast_2d(n).copy()
    L[L[:, 2] > 0] *= -1
    if EAST[blk] == '+x':
        e, nn = L[:, 0], -L[:, 1]
    else:
        e, nn = L[:, 1], -L[:, 0]
    r = np.sqrt(2.0) * np.sin(np.arccos(np.clip(-L[:, 2], -1, 1)) / 2)
    t = np.arctan2(e, nn)
    return r * np.sin(t), r * np.cos(t)


def fisher(N):
    N = np.atleast_2d(N).copy()
    N[N[:, 2] < 0] *= -1
    T = N.T @ N / len(N)
    w, v = np.linalg.eigh(T)
    m = v[:, -1]
    if m[2] < 0:
        m = -m
    R = float(np.abs(N @ m).sum())
    n = len(N)
    K = (n - 1) / max(n - R, 1e-9)
    cone = float('nan')
    if n > 2 and R < n:
        arg = 1 - (n - R) / R * (20 ** (1 / (n - 1)) - 1)
        if -1 <= arg <= 1:
            cone = float(np.degrees(np.arccos(arg)))
    return m, K, cone, float(w[-1] / w.sum())


def net_axes(ax, dipmax=DIPMAX):
    R = np.sqrt(2.0) * np.sin(np.radians(dipmax) / 2)
    t = np.linspace(0, 2 * np.pi, 400)
    ax.plot(R * np.sin(t), R * np.cos(t), 'k-', lw=1.3)
    for d_ in (10, 20, 30):
        rr = np.sqrt(2.0) * np.sin(np.radians(d_) / 2)
        ax.plot(rr * np.sin(t), rr * np.cos(t), '-', color='#D2D2D2', lw=.8, zorder=0)
        ax.text(0, rr, '%d' % d_, fontsize=7, color='#8A8A8A', ha='center', va='bottom', zorder=1)
    for lab, a_ in (('N', 0), ('E', 90), ('S', 180), ('W', 270)):
        ax.text(R * 1.16 * np.sin(np.radians(a_)), R * 1.16 * np.cos(np.radians(a_)), lab,
                ha='center', va='center', fontsize=10, fontweight='bold')
    ax.set_xlim(-R * 1.3, R * 1.3)
    ax.set_ylim(-R * 1.3, R * 1.3)
    ax.set_aspect('equal')
    ax.axis('off')


if __name__ == '__main__':
    fig = plt.figure(figsize=(17.0, 6.6))
    gs = fig.add_gridspec(1, 5, width_ratios=[1, 1, 1, 1, 0.82], wspace=0.06)
    summary = {}
    store = []
    for k, blk in enumerate('ABC'):
        ax = fig.add_subplot(gs[0, k])
        rows = []
        for j, F in enumerate(FEATS[blk]):
            gx, gy, E = elevation(blk, F)
            N = local_poles(gx, gy, E)
            mv, K, cone, tight = fisher(N)
            m = lsq_pole(gx, gy, E)
            dip, az = dip_az(m[None, :], blk)
            dipv, azv = dip_az(mv[None, :], blk)
            dps, azs = dip_az(N, blk)
            store.append((blk, F, N, m, float(dip[0]), float(az[0])))
            x, y = to_net(N, blk)
            ax.scatter(x, y, s=1.8, alpha=.05, c=COL[F], edgecolors='none')
            mx, my = to_net(m[None, :], blk)
            ax.plot(mx, my, 'o', color=COL[F], ms=10, mec='k', mew=1.2, zorder=5)
            ax.annotate('%s  %.0f/%03.0f' % (F, dip[0], az[0]), (mx[0], my[0]), fontsize=9.5, zorder=6,
                        xytext=(11, 9 if j == 0 else -16), textcoords='offset points',
                        bbox=dict(fc='white', ec='none', alpha=.82, pad=1.4))
            rows.append(dict(feature=F, name=NAME[F], n_nodes=int(len(N)),
                             plane_dip_deg=round(float(dip[0]), 1),
                             plane_dip_dir_azimuth_deg=round(float(az[0]), 1),
                             vector_mean_dip_deg=round(float(dipv[0]), 1),
                             vector_mean_dip_dir_azimuth_deg=round(float(azv[0]), 1),
                             strike_azimuth_deg=round(float((az[0] - 90) % 360), 1),
                             dip_p10_p90=[round(float(np.percentile(dps, 10)), 1),
                                          round(float(np.percentile(dps, 90)), 1)],
                             dip_dir_p10_p90=[round(float(np.percentile(azs, 10)), 1),
                                              round(float(np.percentile(azs, 90)), 1)],
                             fisher_K=round(float(K), 1),
                             cone95_deg=(round(cone, 2) if cone == cone else None),
                             tightness=round(tight, 4)))
            print('Block %s %s: %d nodes  plane dip %.1f toward azimuth %.0f  (local dip 10th to 90th '
                  '%.1f-%.1f)  K %.0f' % (blk, F, len(N), dip[0], az[0], np.percentile(dps, 10),
                                          np.percentile(dps, 90), K))
        net_axes(ax)
        ax.set_title('Block %s' % blk, fontsize=12)
        summary[blk] = rows

    axc = fig.add_subplot(gs[0, 3])
    for blk, F, N, m, dip, az in store:
        x, y = to_net(N, blk)
        axc.scatter(x, y, s=1.5, alpha=.045, c=COL[F], edgecolors='none')
        mx, my = to_net(m[None, :], blk)
        axc.plot(mx, my, 'o', color=COL[F], ms=9, mec='k', mew=1.1, zorder=5)
        axc.annotate(F, (mx[0], my[0]), fontsize=9.5, zorder=6, xytext=(9, 6), textcoords='offset points',
                     bbox=dict(fc='white', ec='none', alpha=.82, pad=1.1))
    net_axes(axc)
    axc.set_title('all three benches together', fontsize=12)

    axt = fig.add_subplot(gs[0, 4])
    axt.axis('off')
    lines = ['surface   dip / dip dir   dip 10th-90th', '']
    for blk, F, N, m, dip, az in store:
        r = [q for q in summary[blk] if q['feature'] == F][0]
        lines.append('%-4s     %4.1f / %03.0f      %4.1f to %4.1f'
                     % (F, dip, az, r['dip_p10_p90'][0], r['dip_p10_p90'][1]))
    lines += ['', 'One pole per 10 cm node of the', 'modelled surface. The spread is',
              'the curvature of that surface,', 'not a measurement error.', '',
              'Markers are poles, so each sits', 'opposite its dip direction.', '',
              'Nets are north up and zoom to', '%d degrees of dip.' % int(DIPMAX), '',
              'Dip is from each bench plane,', 'which tilts 1 to 2 degrees, not',
              'from gravity. Azimuth runs through', 'the east axis of ORIENTATION.md',
              'and is not compass-measured.', '',
              'Radar-picked surfaces only. The', 'chalked cracks have no measured',
              'dip, so they have no pole.']
    axt.text(0, 1, '\n'.join(lines), fontsize=8.8, family='monospace', va='top', ha='left',
             transform=axt.transAxes)

    fig.suptitle('The three Kuppam benches from the radar: poles to the six picked fracture surfaces, '
                 'one pole per 10 cm node\nequal-area lower hemisphere, zoomed to %d degrees of dip'
                 % int(DIPMAX), fontsize=12)
    fig.savefig(os.path.join(OUT, 'figs', 'STEREONET_RADAR.png'), dpi=130, bbox_inches='tight')
    summary['settings'] = dict(smooth_cells=SMOOTH, grid_cm=10, dip_zoom_deg=DIPMAX,
                               projection='equal-area lower hemisphere',
                               content='radar-picked surfaces only; the chalked cracks are excluded '
                                       'because their dip has never been measured',
                               frame='each block bench frame; dip from the bench plane, not gravity',
                               azimuth='via the east axis of ORIENTATION.md; not compass-measured')
    json.dump(summary, open(os.path.join(OUT, 'tables', 'stereonet_radar.json'), 'w'), indent=1)
    print('wrote figs/STEREONET_RADAR.png and tables/stereonet_radar.json')
