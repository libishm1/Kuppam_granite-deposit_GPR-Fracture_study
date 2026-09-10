"""Positional uncertainty of each GPR surface, as a vertical thickness on its 10 cm grid, so the packers can keep clear
of where the fracture MAY be rather than only where the model draws it.
Components at each grid node (metres, 1 sigma):
  pick scatter      the plane residual rms of the surface (structural.json)
  velocity          VEL_FRAC x depth: the working velocity 0.1202 m/ns is a median of scattered hyperbolae; the
                    alternative estimates in the record are 2.3 % low and 4.2 % high, so 4.2 % is used
  registration      the block's plan registration error times tan(dip): a plan shift moves a dipping surface up or down
  migration         the picks are unmigrated normal-incidence distances. For a planar reflector at constant velocity the
                    true reflection point lies up-dip of the antenna: shift each pick by d * n_hat (unit normal of the
                    plane, into the rock) minus d straight down. The migrated plane's vertical offset from the
                    unmigrated one at each node is carried as a separate, signed term; the packer excludes the union.
Outputs tables/uncertainty.json and model/unc/{F}_sig_10cm.xyz (x cm, y cm, sigma m) and {F}_mig_10cm.xyz
(x cm, y cm, migrated absolute elevation m)."""
import numpy as np, csv, os, json
from scipy.interpolate import RegularGridInterpolator
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
FEATS = {'A': ('A1', 'A2'), 'B': ('B1', 'B2'), 'C': ('C1', 'C2')}
VEL_FRAC = 0.042
SIG_XY = {'A': 0.07, 'B': 0.16, 'C': 0.07}      # plan registration + line-walking error, 1 sigma, from the registration checks
ST = json.load(open(os.path.join(OUT, 'tables', 'structural.json')))
os.makedirs(os.path.join(OUT, 'model', 'unc'), exist_ok=True)


def grid(p):
    a = np.loadtxt(p); gx = np.unique(a[:, 0]); gy = np.unique(a[:, 1]); return gx, gy, a[:, 2].reshape(len(gy), len(gx))


def picks(F):
    pf = next(p for p in (os.path.join(OUT, 'tables', n % F) for n in ('PICKS_%s_final.csv', 'PICKS_%s_adjusted.csv', 'PICKS_%s_raw.csv')) if os.path.exists(p))
    rr = list(csv.DictReader(open(pf, encoding='utf-8')))
    return np.array([[float(q['x_cm']) / 100, float(q['y_cm']) / 100, float(q.get('z_adj') or q['depth_m'])] for q in rr])


res = {}
for blk in 'ABC':
    dgx, dgy, DEM = grid(os.path.join(OUT, 'model', 'v2_topo', 'Block%s_DEM_10cm.xyz' % blk)); fi = RegularGridInterpolator((dgy / 100, dgx / 100), DEM, bounds_error=False, fill_value=None)
    res[blk] = {}
    for F in FEATS[blk]:
        gx, gy, Zd = grid(os.path.join(OUT, 'model', '%s_grid_10cm.xyz' % F)); GX, GY = np.meshgrid(gx / 100, gy / 100)
        hs = fi(np.c_[GY.ravel(), GX.ravel()]).reshape(GX.shape); E = hs - Zd                          # absolute elevation of the modelled (unmigrated) surface
        p = ST[blk]['planes'][F]; dip = np.radians(p['dip_deg']); rms = p['plane_rms_m']
        # migration of the picks as a planar reflector: fit the elevation plane, take its downward unit normal
        P = picks(F); hp = fi(np.c_[P[:, 1], P[:, 0]]); e = hp - P[:, 2]; A = np.c_[P[:, 0], P[:, 1], np.ones(len(P))]; ce, *_ = np.linalg.lstsq(A, e, rcond=None)
        nrm = np.array([-ce[0], -ce[1], 1.0]); nrm /= np.linalg.norm(nrm)                                  # upward normal of e = a x + b y + c
        ndown = -nrm                                                                                       # into the rock
        d = P[:, 2]; Pm = np.c_[P[:, 0] + d * ndown[0], P[:, 1] + d * ndown[1], hp + d * ndown[2]]        # antenna position + d * n_hat (elevation frame)
        Am = np.c_[Pm[:, 0], Pm[:, 1], np.ones(len(Pm))]; cm, *_ = np.linalg.lstsq(Am, Pm[:, 2], rcond=None)
        Em = cm[0] * GX + cm[1] * GY + cm[2]                                                               # migrated plane at the grid nodes
        dip_m = float(np.degrees(np.arctan(np.hypot(cm[0], cm[1])))); shift_plan = float(np.median(np.hypot(Pm[:, 0] - P[:, 0], Pm[:, 1] - P[:, 1])))
        sig = np.sqrt(rms ** 2 + (VEL_FRAC * Zd) ** 2 + (SIG_XY[blk] * np.tan(dip)) ** 2)
        mig = Em - E                                                                                       # signed vertical offset, migrated minus modelled
        ok = np.isfinite(Zd)
        np.savetxt(os.path.join(OUT, 'model', 'unc', '%s_sig_10cm.xyz' % F), np.c_[GX.ravel() * 100, GY.ravel() * 100, sig.ravel()], fmt='%.1f %.1f %.4f', header='x cm, y cm, 1-sigma vertical uncertainty m')
        np.savetxt(os.path.join(OUT, 'model', 'unc', '%s_mig_10cm.xyz' % F), np.c_[GX.ravel() * 100, GY.ravel() * 100, Em.ravel()], fmt='%.1f %.1f %.4f', header='x cm, y cm, migrated plane absolute elevation m (bench frame)')
        dm = float(np.nanmean(Zd))
        res[blk][F] = dict(mean_depth_m=round(dm, 2), sigma_pick_m=rms, sigma_vel_m_at_mean_depth=round(VEL_FRAC * dm, 3), sigma_reg_m=round(SIG_XY[blk] * float(np.tan(dip)), 3),
                           sigma_total_m_at_mean_depth=round(float(np.sqrt(rms ** 2 + (VEL_FRAC * dm) ** 2 + (SIG_XY[blk] * np.tan(dip)) ** 2)), 3),
                           sigma_total_m_max=round(float(np.nanmax(sig[ok])), 3), two_sigma_m_max=round(float(2 * np.nanmax(sig[ok])), 3),
                           dip_modelled_deg=p['dip_deg'], dip_migrated_deg=round(dip_m, 1), migration_plan_shift_median_m=round(shift_plan, 2),
                           migration_vertical_offset_m=dict(min=round(float(np.nanmin(mig[ok])), 2), median=round(float(np.nanmedian(mig[ok])), 2), max=round(float(np.nanmax(mig[ok])), 2)),
                           sig_xy_m=SIG_XY[blk], vel_frac=VEL_FRAC)
        print('%s depth %.2f m: sigma pick %.3f vel %.3f reg %.3f -> total %.3f (max %.3f); migrated dip %.1f (modelled %.1f), plan shift %.2f m, vertical offset %.2f..%.2f m' % (
            F, dm, rms, VEL_FRAC * dm, SIG_XY[blk] * np.tan(dip), res[blk][F]['sigma_total_m_at_mean_depth'], res[blk][F]['sigma_total_m_max'], dip_m, p['dip_deg'], shift_plan,
            res[blk][F]['migration_vertical_offset_m']['min'], res[blk][F]['migration_vertical_offset_m']['max']))
json.dump(res, open(os.path.join(OUT, 'tables', 'uncertainty.json'), 'w'), indent=1)
print('wrote tables/uncertainty.json and model/unc/')
