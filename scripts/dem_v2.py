"""Version 2 of every GPR surface: re-datumed to the photogrammetry surface (DEM).
v1 (kept untouched) puts depth below a flat bench at z = 0. v2 puts each pick below the
actual surface height at its own (x, y): z_v2 = z_surface(x, y) - depth.
Outputs go to model/v2_topo/ and dataset/bench_frame_m/Block_X/*_v2_topo.*; nothing v1 is overwritten."""
import numpy as np, json, os
from scipy.spatial import cKDTree
from scipy.ndimage import median_filter, uniform_filter
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
SITE = r'D:/code_ws/reference/parsans/site'; OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
REG = json.load(open(os.path.join(OUT, 'tables', 'registration.json')))
MESH = {'A': ('block a.obj', 2), 'B': ('block b.obj', 1), 'C': ('block c.obj', 4)}
FEATS = {'A': ('A1', 'A2'), 'B': ('B1', 'B2'), 'C': ('C1', 'C2')}
DIMS = {'A': (5.5, 5.5), 'B': (9.5, 6.0), 'C': (7.0, 8.0)}
os.makedirs(os.path.join(OUT, 'model', 'v2_topo'), exist_ok=True)


def stream_local(path, stride, R, c, sc, box, zlim=(-1.0, 1.5)):
    keep = []; n = 0; buf = []
    def flush(buf):
        a = np.array(b' '.join(buf).split(), dtype=float).reshape(-1, 6)[:, :3]
        L = ((a - c) @ R.T) * sc
        m = (L[:, 0] > box[0]) & (L[:, 0] < box[1]) & (L[:, 1] > box[2]) & (L[:, 1] < box[3]) & (L[:, 2] > zlim[0]) & (L[:, 2] < zlim[1])
        keep.append(L[m])
    with open(path, 'rb') as f:
        for ln in f:
            if ln[:2] != b'v ': continue
            n += 1
            if n % stride: continue
            buf.append(ln[2:].strip())
            if len(buf) >= 1_000_000: flush(buf); buf = []
    if buf: flush(buf)
    return np.vstack(keep)


def obj_dxf(path, GX, GY, Z, name):
    m, n = Z.shape; ok = np.isfinite(Z); vid = -np.ones((m, n), int); V = []; F = []; Q = []
    for j in range(m):
        for i in range(n):
            if ok[j, i]: vid[j, i] = len(V) + 1; V.append((GX[j, i], GY[j, i], Z[j, i]))
    for j in range(m - 1):
        for i in range(n - 1):
            ids = [vid[j, i], vid[j, i + 1], vid[j + 1, i + 1], vid[j + 1, i]]
            if min(ids) > 0: F.append(ids); Q.append([V[k - 1] for k in ids])
    L = ['# %s v2 topo-corrected, z = surface height minus depth, metres' % name, 'o %s_v2' % name] + ['v %.4f %.4f %.4f' % v for v in V] + ['f %d %d %d %d' % tuple(f) for f in F]
    open(path + '.obj', 'w').write('\n'.join(L) + '\n')
    D = ['0', 'SECTION', '2', 'ENTITIES']
    for q in Q:
        D += ['0', '3DFACE', '8', name + '_v2']
        for k, (x, y, z) in enumerate(q): D += [str(10 + k), '%.4f' % x, str(20 + k), '%.4f' % y, str(30 + k), '%.4f' % z]
    D += ['0', 'ENDSEC', '0', 'EOF']; open(path + '.dxf', 'w').write('\n'.join(D) + '\n')
    return len(V), len(F)


summary = {}
import sys as _s
for blk in (_s.argv[1:] or 'ABC'):
    r = REG[blk]; R = np.array(r['plane_R']); c = np.array(r['plane_c']); sc = r['scale_m_per_unit']
    corner = np.array(r['origin_local_units']) * sc; xd = np.array(r['xdir_local']); yd = np.array(r['ydir_local'])
    W, H = DIMS[blk]
    def to_local(xg_cm, yg_cm):
        return corner[None, :] + np.outer(np.asarray(xg_cm) / 100.0, xd) + np.outer(np.asarray(yg_cm) / 100.0, yd)
    # bench points around the grid
    cnr = to_local([0, W * 100, W * 100, 0], [0, 0, H * 100, H * 100])
    box = (cnr[:, 0].min() - 1.5, cnr[:, 0].max() + 1.5, cnr[:, 1].min() - 1.5, cnr[:, 1].max() + 1.5)
    P = stream_local(os.path.join(SITE, MESH[blk][0]), MESH[blk][1], R, c, sc, box)
    tree = cKDTree(P[:, :2])
    gx = np.arange(0, W * 100 + 0.1, 10.0); gy = np.arange(0, H * 100 + 0.1, 10.0); GX, GY = np.meshgrid(gx, gy)
    Lq = to_local(GX.ravel(), GY.ravel())
    nb = tree.query_ball_point(Lq, r=0.15)
    zs = np.array([np.median(P[i, 2]) if len(i) >= 4 else np.nan for i in nb]).reshape(GX.shape)
    cnt = np.array([len(i) for i in nb]).reshape(GX.shape)
    # fill holes from nearest filled node, then light median
    if np.isnan(zs).any():
        ok = np.isfinite(zs); t2 = cKDTree(np.c_[GX[ok], GY[ok]]); _, ii = t2.query(np.c_[GX[~ok], GY[~ok]]); zs[~ok] = zs[ok][ii]
    DEM = median_filter(zs, 3)
    gyy, gxx = np.gradient(DEM, 0.10); slope = np.degrees(np.arctan(np.hypot(gxx, gyy)))
    np.savetxt(os.path.join(OUT, 'model', 'v2_topo', 'Block%s_DEM_10cm.xyz' % blk), np.c_[GX.ravel(), GY.ravel(), DEM.ravel()], fmt='%.1f %.1f %.4f',
               header='report x cm, y cm, surface height above the bench plane (m), from photogrammetry')
    print('\nBlock %s DEM: %d bench points, %.0f%% of nodes filled directly; surface height %.3f..%.3f m (std %.3f), median slope %.1f deg, p95 %.1f'
          % (blk, len(P), 100 * (cnt >= 4).mean(), DEM.min(), DEM.max(), DEM.std(), np.median(slope), np.percentile(slope, 95)))
    # profiles that matter: along x at mid-y, along y at mid-x
    jm, im = DEM.shape[0] // 2, DEM.shape[1] // 2
    px = DEM[jm, :]; py = DEM[:, im]
    print('   profile along x at y=%.0f cm: %.3f -> %.3f m, max step between 10 cm nodes %.3f m' % (gy[jm], px[0], px[-1], np.abs(np.diff(px)).max()))
    print('   profile along y at x=%.0f cm: %.3f -> %.3f m, max step between 10 cm nodes %.3f m' % (gx[im], py[0], py[-1], np.abs(np.diff(py)).max()))
    # v2 surfaces
    od = os.path.join(OUT, 'dataset', 'bench_frame_m', 'Block_' + blk)
    feat = {}
    for F in FEATS[blk]:
        a = np.loadtxt(os.path.join(OUT, 'model', '%s_grid_10cm.xyz' % F)); n = len(np.unique(a[:, 0])); m = len(np.unique(a[:, 1]))
        FX, FY, Zd = a[:, 0].reshape(m, n), a[:, 1].reshape(m, n), a[:, 2].reshape(m, n)
        # surface height at each feature node (feature grids are subsets/offsets of the block grid: interpolate)
        from scipy.interpolate import RegularGridInterpolator
        fi = RegularGridInterpolator((gy, gx), DEM, bounds_error=False, fill_value=None)
        zsurf = fi(np.c_[FY.ravel(), FX.ravel()]).reshape(FX.shape)
        Zv2 = zsurf - Zd                                         # v1 was -Zd
        np.savetxt(os.path.join(OUT, 'model', 'v2_topo', '%s_v2_topo_10cm.xyz' % F), np.c_[FX.ravel(), FY.ravel(), Zv2.ravel()], fmt='%.2f %.2f %.4f',
                   header='report x cm, y cm, z (m) = surface height - depth; v1 is -depth')
        # bench-frame metres version, alongside v1 in the dataset
        Lm = to_local(FX.ravel(), FY.ravel()); S = np.c_[Lm, Zv2.ravel()].reshape(m, n, 3)
        nv, nf = obj_dxf(os.path.join(od, '%s_surface_v2_topo' % F), S[..., 0], S[..., 1], S[..., 2], F)
        d = zsurf[np.isfinite(Zd)]
        feat[F] = dict(mean_shift_m=float(np.nanmean(d)), min_shift_m=float(np.nanmin(d)), max_shift_m=float(np.nanmax(d)), relief_m=float(np.nanmax(d) - np.nanmin(d)))
        print('   %s v2: surface correction mean %+.3f m, range %+.3f..%+.3f (relief %.3f m across the feature)' % (F, feat[F]['mean_shift_m'], feat[F]['min_shift_m'], feat[F]['max_shift_m'], feat[F]['relief_m']))
    summary[blk] = dict(dem_min=float(DEM.min()), dem_max=float(DEM.max()), dem_std=float(DEM.std()), slope_med=float(np.median(slope)), features=feat)
    # figure
    fig, ax = plt.subplots(1, 2, figsize=(13, 5.4), constrained_layout=True)
    im_ = ax[0].pcolormesh(GX, GY, DEM, shading='auto', cmap='terrain'); plt.colorbar(im_, ax=ax[0], label='surface height above bench plane (m)')
    cs = ax[0].contour(GX, GY, DEM, levels=10, colors='k', linewidths=.4); ax[0].clabel(cs, fmt='%.2f', fontsize=6)
    ax[0].set_aspect('equal'); ax[0].set_title('Block %s bench DEM from photogrammetry, report frame' % blk, fontsize=10); ax[0].set_xlabel('x (cm)'); ax[0].set_ylabel('y (cm)')
    ax[1].plot(gx, px, label='along x at y=%.0f' % gy[jm]); ax[1].plot(gy, py, label='along y at x=%.0f' % gx[im])
    ax[1].set_xlabel('distance (cm)'); ax[1].set_ylabel('surface height (m)'); ax[1].grid(alpha=.3); ax[1].legend(fontsize=8)
    ax[1].set_title('surface profiles: this is the v1 -> v2 depth correction', fontsize=10)
    fig.savefig(os.path.join(OUT, 'figs', 'DEM_%s.png' % blk), dpi=120); plt.close(fig)
json.dump(summary, open(os.path.join(OUT, 'tables', 'dem_v2_summary.json'), 'w'), indent=1)
print('\nwrote model/v2_topo/, dataset bench_frame_m/*/X_surface_v2_topo.obj/.dxf, figs/DEM_*.png, tables/dem_v2_summary.json')
