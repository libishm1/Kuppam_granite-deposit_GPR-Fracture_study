"""Do the fracture surfaces the radar found show up in the photogrammetry?

Both live in the same frame already. The GPR surfaces were modelled in each block's bench frame,
and the photogrammetry of that block was brought into the same frame for this study, so no
registration is involved and the comparison is direct.

Each GPR surface is turned into its plane in absolute bench-frame elevation:
    elevation(x, y) = DEM(x, y) - depth(x, y)
fitted by least squares over the picked footprint, then extended beyond it. Three questions are
asked of every exposed facet and every trace-pair plane found in the photogrammetry:

  orientation   is its pole within ANG of the GPR surface's pole
  proximity     does it lie within DIST of the GPR plane, extended
  continuation  both at once, which is what "the same surface, carrying on into the face" means

Counting matches alone proves nothing, because a quarry face is crowded with planes and some will
agree by luck. So each count is compared with two nulls, 500 draws each:

  spin    the GPR plane keeps its dip but its dip direction is re-drawn at random
  shift   the GPR plane keeps its orientation and is moved along its own normal, anywhere within
          the elevation range the photogrammetry covers

The spin null asks whether the orientation agreement is special. The shift null asks whether the
surface is where the radar says it is, rather than merely parallel to things in the pit.

Usage: radar_vs_photo.py
"""
import numpy as np, os, json
from scipy.interpolate import RegularGridInterpolator

OUT = 'D:/code_ws/outputs/2026-09-11/joint_mapping'
GPR = 'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
FEATS = {'A': ['A1', 'A2'], 'B': ['B1', 'B2'], 'C': ['C1', 'C2']}
ANG = 15.0          # deg, pole agreement
DIST = 0.30         # m, distance to the extended plane
NDRAW = 500
EAST = {'A': '+x', 'B': '+y', 'C': '+y'}   # 12 Sep. Origin is the north-west corner on every bench and both axes run into the bench, but which axis runs east differs: on A the X-line numerals run down the WEST edge from A0 (client, from the site: '9, 12...' from the NW to the SW corner), so X-lines are stacked north-south and run east, +x east, +y south, left-handed. On B and C +y is east (6 m and 8 m sides, verified). See ORIENTATION.md.


def load_grid(p):
    a = np.loadtxt(p)
    gx = np.unique(a[:, 0]) / 100
    gy = np.unique(a[:, 1]) / 100
    return gx, gy, a[:, 2].reshape(len(gy), len(gx))


def gpr_plane(blk, F):
    """least-squares plane through the surface in absolute bench-frame elevation"""
    gx, gy, d = load_grid(os.path.join(GPR, 'model', '%s_grid_10cm.xyz' % F))
    ex, ey, dem = load_grid(os.path.join(GPR, 'dataset', 'bench_frame_m', 'Block_%s' % blk,
                                         'Block%s_DEM_10cm.xyz' % blk))
    di = RegularGridInterpolator((gy, gx), d, bounds_error=False, fill_value=np.nan)
    de = RegularGridInterpolator((ey, ex), dem, bounds_error=False, fill_value=np.nan)
    X, Y = np.meshgrid(gx, gy)
    P = np.c_[Y.ravel(), X.ravel()]
    dd = di(P)
    ee = de(P)
    ok = np.isfinite(dd) & np.isfinite(ee)
    x = X.ravel()[ok]; y = Y.ravel()[ok]; z = ee[ok] - dd[ok]
    A = np.c_[x, y, np.ones(ok.sum())]
    coef, *_ = np.linalg.lstsq(A, z, rcond=None)
    n = np.array([-coef[0], -coef[1], 1.0])
    n /= np.linalg.norm(n)
    c = np.array([x.mean(), y.mean(), z.mean()])
    resid = z - (A @ coef)
    return dict(n=n, c=c, rms=float(np.sqrt(np.mean(resid ** 2))), npts=int(ok.sum()),
                z_range=[float(z.min()), float(z.max())],
                foot=[float(x.min()), float(x.max()), float(y.min()), float(y.max())])


def dip_az(n, blk):
    n = n / np.linalg.norm(n)
    if n[2] < 0:
        n = -n
    dip = float(np.degrees(np.arccos(np.clip(abs(n[2]), -1, 1))))
    # the upward normal leans toward the DOWN-dip side, so the dip direction is the trend of
    # its horizontal part: bearing = atan2(n_x, n_y), the convention the GPR study uses
    d = np.array([n[0], n[1]])
    brg = float(np.degrees(np.arctan2(d[0], d[1])) % 360) if np.linalg.norm(d) > 1e-9 else 0.0
    az = (180 - brg) % 360 if EAST[blk] == '+x' else (brg + 90) % 360
    return dip, az


def where(n, c, PN, PC, PA, PD, foot):
    """a match only means something if it is NOT on the quarry floor: a near-horizontal plane
    extended out of the bench crosses floor level somewhere, and the floor is paved with
    near-horizontal facets"""
    o = np.abs(PN @ n) > np.cos(np.radians(ANG))
    m = o & (np.abs((PC - c) @ n) < DIST)
    if not m.any():
        return dict(n=0, on_floor=0, on_wall=0, inside_footprint=0, wall_area_m2=0.0)
    z = PC[m][:, 2]
    ins = ((PC[m][:, 0] > foot[0]) & (PC[m][:, 0] < foot[1]) & (PC[m][:, 1] > foot[2]) & (PC[m][:, 1] < foot[3]))
    floor = np.abs(z) < 0.4
    return dict(n=int(m.sum()), on_floor=int(floor.sum()), on_wall=int((~floor).sum()),
                inside_footprint=int(ins.sum()), wall_area_m2=round(float(PA[m][~floor].sum()), 2),
                z_min=round(float(z.min()), 2), z_max=round(float(z.max()), 2))


def score(n, c, PN, PC, PA):
    """orientation, proximity and continuation counts for one plane against the photogrammetry"""
    cos = np.abs(PN @ n)
    o = cos > np.cos(np.radians(ANG))
    dist = np.abs((PC - c) @ n)
    p = dist < DIST
    cont = o & p
    return int(o.sum()), int(p.sum()), int(cont.sum()), float(PA[cont].sum())


def spin(n, rng):
    """same dip, random dip direction"""
    dip = np.arccos(abs(n[2]))
    a = rng.uniform(0, 2 * np.pi)
    return np.array([np.sin(dip) * np.sin(a), np.sin(dip) * np.cos(a), np.cos(dip)])


if __name__ == '__main__':
    res = {}
    for blk in 'ABC':
        fj = json.load(open(os.path.join(OUT, 'tables', 'facets_%s.json' % blk)))
        pat = fj['patches']
        PN = np.array([p['normal'] for p in pat], float)
        PN /= np.linalg.norm(PN, axis=1, keepdims=True)
        PC = np.array([p['centre'] for p in pat], float)
        PA = np.array([p['area_m2'] for p in pat])
        PD = np.array([p['dip_deg'] for p in pat])
        zlo, zhi = float(PC[:, 2].min()), float(PC[:, 2].max())
        print('=== Block %s: %d exposed facets, centres z %.1f to %.1f m' % (blk, len(pat), zlo, zhi))
        rows = []
        for F in FEATS[blk]:
            g = gpr_plane(blk, F)
            dip, az = dip_az(g['n'], blk)
            o, p, cont, area = score(g['n'], g['c'], PN, PC, PA)
            rng = np.random.default_rng(3)
            so = np.zeros(NDRAW); sc = np.zeros(NDRAW)
            for i in range(NDRAW):
                nn = spin(g['n'], rng)
                a_, b_, c_, _ = score(nn, g['c'], PN, PC, PA)
                so[i] = a_; sc[i] = c_
            hp = np.zeros(NDRAW); hc = np.zeros(NDRAW)
            for i in range(NDRAW):
                cc = g['c'] + g['n'] * rng.uniform(zlo - g['c'][2], zhi - g['c'][2])
                a_, b_, c_, _ = score(g['n'], cc, PN, PC, PA)
                hp[i] = b_; hc[i] = c_
            row = dict(feature=F, dip_deg=round(dip, 1), dip_dir_azimuth_deg=round(az, 1),
                       plane_rms_m=round(g['rms'], 3), picked_z_range=[round(v, 2) for v in g['z_range']],
                       n_facets=len(pat),
                       orientation_match=o, orientation_null_mean=round(float(so.mean()), 1),
                       orientation_p=round(float((so >= o).mean()), 3),
                       proximity_match=p, proximity_null_mean=round(float(hp.mean()), 1),
                       proximity_p=round(float((hp >= p).mean()), 3),
                       continuation_match=cont, continuation_area_m2=round(area, 2),
                       continuation_spin_null_mean=round(float(sc.mean()), 2),
                       continuation_spin_p=round(float((sc >= cont).mean()), 3),
                       continuation_shift_null_mean=round(float(hc.mean()), 2),
                       continuation_shift_p=round(float((hc >= cont).mean()), 3),
                       where=where(g['n'], g['c'], PN, PC, PA, PD, g['foot']))
            rows.append(row)
            print('  %s  dip %4.1f az %5.1f (plane rms %.2f m, picked z %.2f to %.2f)'
                  % (F, dip, az, g['rms'], g['z_range'][0], g['z_range'][1]))
            print('     orientation within %.0f deg : %3d facets   null %5.1f   p %.3f'
                  % (ANG, o, so.mean(), (so >= o).mean()))
            print('     within %.2f m of the plane  : %3d facets   null %5.1f   p %.3f'
                  % (DIST, p, hp.mean(), (hp >= p).mean()))
            print('     both (continuation)        : %3d facets, %.1f m2   spin null %.2f p %.3f   shift null %.2f p %.3f'
                  % (cont, area, sc.mean(), (sc >= cont).mean(), hc.mean(), (hc >= cont).mean()))
            w = row['where']
            print('     of those matches: %d on the quarry floor, %d up on a face (%.1f m2), %d inside the picked footprint'
                  % (w['on_floor'], w['on_wall'], w['wall_area_m2'], w['inside_footprint']))
        res[blk] = dict(n_facets=len(pat), facet_z_range=[round(zlo, 2), round(zhi, 2)], features=rows)
    res['settings'] = dict(angle_tol_deg=ANG, distance_tol_m=DIST, n_draws=NDRAW,
                           nulls='spin keeps dip and re-draws dip direction; shift keeps orientation and '
                                 'moves the plane along its normal within the elevation range the photogrammetry covers',
                           frame='each block bench frame, metres, z up, bench top at 0; dip from the bench plane, not gravity')
    json.dump(res, open(os.path.join(OUT, 'tables', 'radar_vs_photo.json'), 'w'), indent=1)
    print('wrote tables/radar_vs_photo.json')
