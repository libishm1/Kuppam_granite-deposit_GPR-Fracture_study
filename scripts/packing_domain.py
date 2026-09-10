"""One physical frame for packing, cut planes and the viewer: bench-frame ABSOLUTE elevation (metres, z up,
bench plane = 0), 10 cm voxels on the painted grid. Rock exists below the photographed surface (DEM) and above the
floor; fractures are forbidden bands around the modelled surfaces, optionally widened to their uncertainty and
joined with the migrated plane; chalked cracks are vertical prisms from the local surface down to an assumed depth.
Used by guillotine_pack.py (exact straight-cut DP) and block_pack.py (free heuristic estimate)."""
import numpy as np, csv, os, json
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import binary_dilation
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
VOX = 0.10
BUF_GPR = 0.15                 # m, clearance kept from a modelled surface in the 'modelled' case
BUF_SK = 0.10                  # m, plan clearance from a chalked crack ('modelled'); 0.20 in the 'uncertain' case
BUF_SK_UNC = 0.20
DIMS = {'A': (5.5, 5.5), 'B': (9.5, 6.0), 'C': (7.0, 8.0)}
FEATS = {'A': ('A1', 'A2'), 'B': ('B1', 'B2'), 'C': ('C1', 'C2')}
BENCH = {'A': 3.0, 'B': 3.0, 'C': None}          # assumed bench thickness below the median surface where no floor was surveyed; C: the C-2 cap
SCEN = {'ignore_surface': 0.0, 'surface_0.5m': 0.5, 'surface_1.0m': 1.0, 'surface_full': 99.0}
UNC = ('modelled', 'uncertain')


def _grid(p):
    a = np.loadtxt(p); gx = np.unique(a[:, 0]) / 100; gy = np.unique(a[:, 1]) / 100
    return RegularGridInterpolator((gy, gx), a[:, 2].reshape(len(gy), len(gx)), bounds_error=False, fill_value=np.nan)


def build(blk, sdepth, unc):
    """returns dict: free, rock, cut (nz,ny,nx bool), zc (nz), xc, yc (cell centres m), dem, floor (ny,nx), surfaces {F: elevation (ny,nx)}, bands"""
    W, H = DIMS[blk]; nx, ny = int(round(W / VOX)), int(round(H / VOX))
    xc = (np.arange(nx) + 0.5) * VOX; yc = (np.arange(ny) + 0.5) * VOX; XC, YC = np.meshgrid(xc, yc); P = np.c_[YC.ravel(), XC.ravel()]
    fd = _grid(os.path.join(OUT, 'model', 'v2_topo', 'Block%s_DEM_10cm.xyz' % blk)); dem = fd(P).reshape(ny, nx)
    dem = np.where(np.isnan(dem), np.nanmedian(dem), dem)
    surf = {}; sig = {}; mig = {}
    for F in FEATS[blk]:
        fz = _grid(os.path.join(OUT, 'model', '%s_grid_10cm.xyz' % F)); d = fz(P).reshape(ny, nx)
        surf[F] = dem - d                                                                   # absolute elevation of the modelled surface (NaN outside its footprint)
        sig[F] = _grid(os.path.join(OUT, 'model', 'unc', '%s_sig_10cm.xyz' % F))(P).reshape(ny, nx)
        mig[F] = _grid(os.path.join(OUT, 'model', 'unc', '%s_mig_10cm.xyz' % F))(P).reshape(ny, nx)
    # floor
    if BENCH[blk] is None:
        e2 = surf['C2']; e2 = np.where(np.isnan(e2), np.nanmedian(e2), e2)
        band2 = BUF_GPR if unc == 'modelled' else np.maximum(BUF_GPR, 2 * np.where(np.isnan(sig['C2']), np.nanmax(sig['C2']), sig['C2']))
        top2 = e2 if unc == 'modelled' else np.maximum(e2, np.where(np.isnan(mig['C2']), e2, mig['C2']))
        floor = e2; floor_desc = 'the C-2 cap (gross rock counts down to the cap; the cap band is forbidden)'
        cap_forbid_top = top2 + band2                                                       # usable rock stops above the cap and its band
    else:
        floor = np.full((ny, nx), float(np.median(dem)) - BENCH[blk]); floor_desc = 'flat floor %.1f m below the median surface (assumed; no floor was surveyed)' % BENCH[blk]; cap_forbid_top = None
    ztop = np.ceil(dem.max() / 0.5) * 0.5; zbot = np.floor(floor.min() / 0.5) * 0.5
    nz = int(round((ztop - zbot) / VOX)); zc = zbot + (np.arange(nz) + 0.5) * VOX
    Z = zc[:, None, None]
    rock = (Z < dem[None]) & (Z > floor[None])
    cut = np.zeros((nz, ny, nx), bool)
    bands = {}
    if cap_forbid_top is not None:
        cut |= Z <= cap_forbid_top[None] + VOX / 2
        bands['C2'] = dict(band_median_m=round(float(np.nanmedian(band2 if np.ndim(band2) else np.full(1, band2))), 3), band_max_m=round(float(np.nanmax(band2 if np.ndim(band2) else np.full(1, band2))), 3), thickness_median_m=round(float(np.nanmedian(cap_forbid_top - e2)), 2))
    for F in FEATS[blk]:
        if blk == 'C' and F == 'C2': continue
        e = surf[F]; ok = np.isfinite(e)
        if unc == 'modelled':
            band = np.full((ny, nx), BUF_GPR); lo = e - band; hi = e + band
        else:
            s = np.where(np.isnan(sig[F]), 0, sig[F]); band = np.maximum(BUF_GPR, 2 * s); em = np.where(np.isnan(mig[F]), e, mig[F])
            lo = np.minimum(e, em) - band; hi = np.maximum(e, em) + band                       # union of the modelled and migrated positions, each with its band
        lo = np.where(ok, lo, np.inf); hi = np.where(ok, hi, -np.inf)
        cut |= (Z >= lo[None] - VOX / 2) & (Z <= hi[None] + VOX / 2)
        bands[F] = dict(band_median_m=round(float(np.nanmedian(band[ok])), 3), band_max_m=round(float(np.nanmax(band[ok])), 3), thickness_median_m=round(float(np.nanmedian((hi - lo)[ok])), 2))
    # chalked cracks: vertical prisms from the local surface down sdepth
    sk = {}
    for q in csv.DictReader(open(os.path.join(OUT, 'tables', 'sketch_chained_%s.csv' % blk), encoding='utf-8')):
        sk.setdefault(int(q['trace_id']), []).append((float(q['x_cm']) / 100, float(q['y_cm']) / 100))
    skmask = np.zeros((ny, nx), bool)
    for pts in sk.values():
        pts = np.array(pts)
        for a, b in zip(pts[:-1], pts[1:]):
            for p in np.linspace(a, b, max(2, int(np.hypot(*(b - a)) / (VOX / 2)) + 1)):
                i, j = int(p[0] / VOX), int(p[1] / VOX)
                if 0 <= i < nx and 0 <= j < ny: skmask[j, i] = True
    bsk = BUF_SK if unc == 'modelled' else BUF_SK_UNC
    skmask = binary_dilation(skmask, iterations=max(1, int(round(bsk / VOX))))
    cut |= skmask[None] & (Z > (dem - sdepth)[None])
    cut &= rock
    free = rock & ~cut
    return dict(free=free, rock=rock, cut=cut, zc=zc, xc=xc, yc=yc, dem=dem, floor=floor, floor_desc=floor_desc, surfaces=surf, bands=bands, chalk_buffer_m=bsk,
                gross_rock_m3=round(float(rock.sum()) * VOX ** 3, 1), free_rock_m3=round(float(free.sum()) * VOX ** 3, 1), nx=nx, ny=ny, nz=nz, zbot=float(zbot), ztop=float(ztop))


if __name__ == '__main__':
    for blk in 'ABC':
        for unc in UNC:
            D = build(blk, 1.0, unc)
            print(blk, unc, 'z %.1f..%.1f (%d levels) rock %.1f m3 free %.1f m3 floor: %s bands %s' % (D['zbot'], D['ztop'], D['nz'], D['gross_rock_m3'], D['free_rock_m3'], D['floor_desc'], D['bands']))
