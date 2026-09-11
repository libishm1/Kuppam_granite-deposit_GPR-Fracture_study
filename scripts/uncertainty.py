"""Positional uncertainty of each GPR surface, on the tolerance ladder of the BoEGE paper (Murugean 2026, "A managed,
uncertainty-aware pipeline from GPR to dimension-stone block yield"), so the two are consistent. Per surface node,
one-sigma vertical terms combined in quadrature (GUM):

  sigma_total^2 = sigma_recon^2 + sigma_interp^2 + sigma_mesh^2 + sigma_reg^2
  sigma_recon^2 = (d * sigma_v/v)^2 + (lambda/4)^2 + (v * sigma_t0 / 2)^2
      sigma_v/v  = 1/2 * delta_eps / eps : half the spread of the calibrated permittivities about the adopted 6.25
                   (PARSAN Table 1 plate and pipe in dolerite slabs 6.24-6.52, Zond 5.73, this diffraction scan 6.22)
      lambda/4   = v / (4 f) at the picked channel's peak frequency (HF 628 MHz, LF 358 MHz): the resolution floor
      sigma_t0   = scatter of the AIC first-break time across the 89 lines of the picked channel (firstbreak_aic.csv)
  sigma_interp   = the plane residual rms of the surface: the scatter of the picks about the modelled surface
  sigma_mesh     = h^2 kappa / 8 for the 10 cm grid: negligible, kept for the record
  sigma_reg      = site-specific, not in the paper: plan registration of the painted grid to the mesh x tan(dip)
Confidence that the surface lies within a clearance T: C_pos(T) = erf(T / (sigma sqrt 2)).
Migration is carried separately as a signed, plane-to-plane offset (migrated plane minus unmigrated plane, both in
absolute elevation, planar-reflector geometry at constant velocity); the packer excludes both positions.
Outputs tables/uncertainty.json, model/unc/{F}_sig_10cm.xyz, model/unc/{F}_mig_10cm.xyz."""
import numpy as np, csv, os, json, math
from scipy.interpolate import RegularGridInterpolator
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
FEATS = {'A': ('A1', 'A2'), 'B': ('B1', 'B2'), 'C': ('C1', 'C2')}
CHAN = {'A1': 'HF', 'A2': 'HF', 'B1': 'HF', 'B2': 'LF', 'C1': 'HF', 'C2': 'LF'}      # channel the surface was picked on
V0 = 0.1202; EPS0 = 6.25
EPS_CAL = {'PARSAN Table 1 steel pipe 0.10 m slab': 6.24, 'PARSAN Table 1 steel pipe 1.00 m slab': 6.35, 'PARSAN Table 1 iron plate 0.10 m slab': 6.47, 'PARSAN Table 1 iron plate 1.00 m slab': 6.52,
           'PARSAN Zond combined': 5.73, 'this work, 114 diffraction hyperbolae': 6.22}
DELTA_EPS = (max(EPS_CAL.values()) - min(EPS_CAL.values())) / 2; SIG_VV = 0.5 * DELTA_EPS / EPS0
FPEAK = {'HF': 628e6, 'LF': 358e6}; LAM4 = {ch: V0 / (4 * FPEAK[ch] * 1e-9) for ch in FPEAK}     # metres
SIG_XY = {'A': 0.07, 'B': 0.16, 'C': 0.07}      # plan registration + line-walking error, 1 sigma, from the registration checks
ST = json.load(open(os.path.join(OUT, 'tables', 'structural.json')))
fb = list(csv.DictReader(open(os.path.join(OUT, 'tables', 'firstbreak_aic.csv'))))
SIG_T0 = {ch: float(np.std([float(r['t0_ns']) for r in fb if r['ch'] == ch])) for ch in ('HF', 'LF')}
os.makedirs(os.path.join(OUT, 'model', 'unc'), exist_ok=True)


def grid(p):
    a = np.loadtxt(p); gx = np.unique(a[:, 0]); gy = np.unique(a[:, 1]); return gx, gy, a[:, 2].reshape(len(gy), len(gx))


def picks(F):
    pf = next(p for p in (os.path.join(OUT, 'tables', n % F) for n in ('PICKS_%s_final.csv', 'PICKS_%s_adjusted.csv', 'PICKS_%s_raw.csv')) if os.path.exists(p))
    rr = list(csv.DictReader(open(pf, encoding='utf-8')))
    return np.array([[float(q['x_cm']) / 100, float(q['y_cm']) / 100, float(q.get('z_adj') or q['depth_m'])] for q in rr])


res = dict(ladder=dict(sigma_v_over_v=round(SIG_VV, 4), delta_eps=round(DELTA_EPS, 3), eps_adopted=EPS0, eps_calibrations=EPS_CAL, lambda4_m={k: round(v, 4) for k, v in LAM4.items()},
                       sigma_t0_ns=SIG_T0, sigma_t0_depth_m={ch: round(V0 * SIG_T0[ch] / 2, 4) for ch in SIG_T0}, sig_xy_m=SIG_XY, v0=V0,
                       formula='sigma_total^2 = (d sigma_v/v)^2 + (lambda/4)^2 + (v sigma_t0/2)^2 + sigma_interp^2 + sigma_mesh^2 + sigma_reg^2; C_pos(T) = erf(T/(sigma sqrt2))'))
for blk in 'ABC':
    dgx, dgy, DEM = grid(os.path.join(OUT, 'model', 'v2_topo', 'Block%s_DEM_10cm.xyz' % blk)); fi = RegularGridInterpolator((dgy / 100, dgx / 100), DEM, bounds_error=False, fill_value=None)
    res[blk] = {}
    for F in FEATS[blk]:
        ch = CHAN[F]
        gx, gy, Zd = grid(os.path.join(OUT, 'model', '%s_grid_10cm.xyz' % F)); GX, GY = np.meshgrid(gx / 100, gy / 100)
        hs = fi(np.c_[GY.ravel(), GX.ravel()]).reshape(GX.shape); E = hs - Zd                          # absolute elevation of the modelled (unmigrated) surface
        p = ST[blk]['planes'][F]; dip = np.radians(p['dip_deg']); rms = p['plane_rms_m']
        # migration of the picks as a planar reflector: fit the elevation plane, take its downward unit normal
        P = picks(F); hp = fi(np.c_[P[:, 1], P[:, 0]]); e = hp - P[:, 2]; A = np.c_[P[:, 0], P[:, 1], np.ones(len(P))]; ce, *_ = np.linalg.lstsq(A, e, rcond=None)
        nrm = np.array([-ce[0], -ce[1], 1.0]); nrm /= np.linalg.norm(nrm); ndown = -nrm
        d = P[:, 2]; Pm = np.c_[P[:, 0] + d * ndown[0], P[:, 1] + d * ndown[1], hp + d * ndown[2]]
        Am = np.c_[Pm[:, 0], Pm[:, 1], np.ones(len(Pm))]; cm, *_ = np.linalg.lstsq(Am, Pm[:, 2], rcond=None)
        Em = cm[0] * GX + cm[1] * GY + cm[2]; Ep = ce[0] * GX + ce[1] * GY + ce[2]; Emg = E + (Em - Ep)
        dip_e = float(np.degrees(np.arctan(np.hypot(ce[0], ce[1])))); dip_m = float(np.degrees(np.arctan(np.hypot(cm[0], cm[1])))); shift_plan = float(np.median(np.hypot(Pm[:, 0] - P[:, 0], Pm[:, 1] - P[:, 1])))
        # the ladder, per node
        s_vel = SIG_VV * Zd; s_lam = np.full_like(Zd, LAM4[ch]); s_t0 = np.full_like(Zd, V0 * SIG_T0[ch] / 2)
        s_recon = np.sqrt(s_vel ** 2 + s_lam ** 2 + s_t0 ** 2)
        # mesh term: h^2 kappa / 8 with the gridded surface's curvature
        gyy, gxx = np.gradient(np.gradient(E, 0.1, axis=0), 0.1, axis=0), np.gradient(np.gradient(E, 0.1, axis=1), 0.1, axis=1)
        kappa = np.nan_to_num(np.abs(gxx) + np.abs(gyy)); s_mesh = 0.1 ** 2 * kappa / 8
        s_reg = np.full_like(Zd, SIG_XY[blk] * np.tan(dip))
        sig = np.sqrt(s_recon ** 2 + rms ** 2 + s_mesh ** 2 + s_reg ** 2)
        mig = Em - Ep; ok = np.isfinite(Zd); dm = float(np.nanmean(Zd))
        np.savetxt(os.path.join(OUT, 'model', 'unc', '%s_sig_10cm.xyz' % F), np.c_[GX.ravel() * 100, GY.ravel() * 100, sig.ravel()], fmt='%.1f %.1f %.4f', header='x cm, y cm, 1-sigma vertical uncertainty m (tolerance ladder)')
        np.savetxt(os.path.join(OUT, 'model', 'unc', '%s_mig_10cm.xyz' % F), np.c_[GX.ravel() * 100, GY.ravel() * 100, Emg.ravel()], fmt='%.1f %.1f %.4f', header='x cm, y cm, modelled surface shifted by its planar migration offset, absolute elevation m (bench frame)')
        at = lambda a: round(float(np.nanmean(a[ok])), 3)
        s_tot_mean = float(np.sqrt(np.nanmean(sig[ok] ** 2)))
        cpos = lambda T, s: round(float(math.erf(T / (s * math.sqrt(2)))), 3)
        res[blk][F] = dict(channel=ch, mean_depth_m=round(dm, 2), sigma_vel_m=at(s_vel), lambda4_m=round(LAM4[ch], 3), sigma_t0_m=round(V0 * SIG_T0[ch] / 2, 3), sigma_recon_m=at(s_recon),
                           sigma_interp_m=rms, sigma_mesh_m=at(s_mesh), sigma_reg_m=round(SIG_XY[blk] * float(np.tan(dip)), 3),
                           sigma_total_m_at_mean_depth=round(s_tot_mean, 3), sigma_total_m_max=round(float(np.nanmax(sig[ok])), 3), two_sigma_m_max=round(float(2 * np.nanmax(sig[ok])), 3),
                           sigma_total_pct_depth=round(100 * s_tot_mean / dm, 1), C_pos_15cm=cpos(0.15, s_tot_mean), C_pos_1sigma=cpos(s_tot_mean, s_tot_mean), C_pos_2sigma=cpos(2 * s_tot_mean, s_tot_mean),
                           dip_modelled_deg=round(dip_e, 1), dip_modelled_depthframe_deg=p['dip_deg'], dip_migrated_deg=round(dip_m, 1), migration_plan_shift_median_m=round(shift_plan, 2),
                           migration_vertical_offset_m=dict(min=round(float(np.nanmin(mig[ok])), 2), median=round(float(np.nanmedian(mig[ok])), 2), max=round(float(np.nanmax(mig[ok])), 2)),
                           sig_xy_m=SIG_XY[blk], sigma_v_over_v=round(SIG_VV, 4))
        r_ = res[blk][F]
        print('%s (%s) depth %.2f: vel %.3f  lam/4 %.3f  t0 %.3f -> recon %.3f | interp %.3f mesh %.4f reg %.3f => total %.3f (%.0f%% of depth, max %.3f); C_pos(15 cm) %.2f; migrated dip %.1f (modelled %.1f), offset %.2f..%.2f m' % (
            F, ch, dm, r_['sigma_vel_m'], r_['lambda4_m'], r_['sigma_t0_m'], r_['sigma_recon_m'], rms, r_['sigma_mesh_m'], r_['sigma_reg_m'], s_tot_mean, r_['sigma_total_pct_depth'], r_['sigma_total_m_max'], r_['C_pos_15cm'], dip_m, dip_e, r_['migration_vertical_offset_m']['min'], r_['migration_vertical_offset_m']['max']))
json.dump(res, open(os.path.join(OUT, 'tables', 'uncertainty.json'), 'w'), indent=1)
print('ladder: sigma_v/v %.4f (delta eps %.3f about %.2f), lambda/4 HF %.3f LF %.3f m, sigma_t0 HF %.2f LF %.2f ns' % (SIG_VV, DELTA_EPS, EPS0, LAM4['HF'], LAM4['LF'], SIG_T0['HF'], SIG_T0['LF']))
print('wrote tables/uncertainty.json and model/unc/')
