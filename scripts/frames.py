"""Report frames from the painted labels, back-projected with the camera poses, snapped to the lattice.
Writes tables/frame_override.json for register.py. No handedness assumption: the rock decides."""
import numpy as np, json, os
from scipy.optimize import least_squares
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
T = lambda n: os.path.join(OUT, 'tables', n)
OV = {}

# ------------------------------------------------------------------ A
g = json.load(open(T('grid_A_paint.json'))); sc = g['scale_m_per_unit']; sp = g['spacing_units']; th = np.radians(g['theta_deg'])
Ud = np.array([np.cos(th), np.sin(th)]); Vd = np.array([-np.sin(th), np.cos(th)])       # U along 106 deg, V along 16 deg
P = {'9': (-4.88, -1.57), '10': (-4.73, -2.24), '11': (-4.48, -2.77)}                   # back-projected numerals, local units
pts = np.array(list(P.values()))
U = pts @ Ud; V = pts @ Vd
# numerals label lines 9,10,11 of the 1-12 family: their U coordinates are those lines' U values
phU = g['lines_U'][0] % sp
kU = np.round((U - phU) / sp); print('A numerals sit at lattice-U index', kU, ' (should step by 1: 9,10,11)')
sgn = np.sign(kU[-1] - kU[0])                                                            # direction of increasing line number
k9 = kU[0]; k1 = k9 - 8 * sgn                                                            # line 1 is 8 lines back
Ulines = phU + (k1 + sgn * np.arange(12)) * sp                                           # lines 1..12
ydir = sgn * Ud                                                                          # report y increases with line number
# numerals sit just OUTSIDE the x = 0 edge, which is a constant-V lattice line; the grid is on the side of the lattice centre
Vn = V.mean(); phV = g['lines_V'][0] % sp
kV = np.round((Vn - phV) / sp)
centreV = (np.array(g['corners_xy']).mean(0)) @ Vd
sV = np.sign(centreV - Vn)                                                               # into the grid
# edge line = first lattice line on the grid side of the numerals (numerals are 0.2-0.6 m outside)
kedge = kV if (Vn - (phV + kV * sp)) * sV < 0 else kV + sV     # nearest line already on the grid side -> it is the edge
Vlines = phV + (kedge + sV * np.arange(12)) * sp
xdir = sV * Vd
origin = Ulines[0] * Ud + Vlines[0] * Vd
print('A: numerals V offset from x=0 edge line: %.2f m outside' % ((Vlines[0] - Vn) * sV * sc))
old = np.array(g['corners_xy']); oldU = old @ Ud; oldV = old @ Vd
print('A: old box U range %.2f..%.2f  new %.2f..%.2f  (shift %.1f cells)' % (oldU.min(), oldU.max(), Ulines.min(), Ulines.max(), (Ulines.min() - oldU.min()) / sp))
print('A: old box V range %.2f..%.2f  new %.2f..%.2f  (shift %.1f cells)' % (oldV.min(), oldV.max(), Vlines.min(), Vlines.max(), (Vlines.min() - oldV.min()) / sp))
hand = xdir[0] * ydir[1] - xdir[1] * ydir[0]
print('A: origin local (%.2f, %.2f), x-dir (%.3f, %.3f) along %.0f deg, y-dir (%.3f, %.3f), %s-handed with z up'
      % (*origin, *xdir, np.degrees(np.arctan2(xdir[1], xdir[0])) % 360, *ydir, 'right' if hand > 0 else 'LEFT'))
OV['A'] = dict(origin_local_units=origin.tolist(), xdir_local=xdir.tolist(), ydir_local=ydir.tolist(), scale_m_per_unit=sc,
               source='chalk numerals 9,10,11 in 20260819_113938 back-projected, snapped to the white lattice; A0 = 8 lines before 9',
               lattice_lines_U=Ulines.tolist(), lattice_lines_V=Vlines.tolist())

# ------------------------------------------------------------------ B
B0 = np.array([-1.72, 3.59]); B1 = np.array([4.20, 3.73]); B3 = np.array([-1.27, -5.84])   # circle-cross marks, local units
def model(p):
    ox, oy, t, s = p
    xh = np.array([np.cos(t), np.sin(t)]); yh = np.array([-np.sin(t), np.cos(t)])
    o = np.array([ox, oy])
    return o, o + 6.0 / s * yh, o + 9.5 / s * xh
def res(p):
    o, b1, b3 = model(p); return np.r_[o - B0, b1 - B1, b3 - B3]
t0 = np.arctan2(*(B3 - B0)[::-1]); s0 = 9.5 / np.linalg.norm(B3 - B0)
best = None
for tt in (t0, t0 + np.pi):                        # y may be either perpendicular; the fit picks
    r = least_squares(res, [B0[0], B0[1], tt, s0])
    if best is None or r.cost < best.cost: best = r
ox, oy, t, s = best.x; o, b1, b3 = model(best.x)
xh = np.array([np.cos(t), np.sin(t)]); yh = np.array([-np.sin(t), np.cos(t)])
rms = np.sqrt(np.mean(res(best.x) ** 2)) * s
print('B: rectangle fit to the three marks: origin (%.2f, %.2f), x-dir %.1f deg, scale %.4f m/unit, rms %.2f m'
      % (ox, oy, np.degrees(t) % 360, s, rms))
hand = xh[0] * yh[1] - xh[1] * yh[0]
print('B: fitted corners B0 (%.2f,%.2f) B1 (%.2f,%.2f) B3 (%.2f,%.2f); %s-handed with z up' % (*o, *b1, *b3, 'right' if hand > 0 else 'LEFT'))
OV['B'] = dict(origin_local_units=o.tolist(), xdir_local=xh.tolist(), ydir_local=yh.tolist(), scale_m_per_unit=float(s),
               source='circle-cross marks B0 (photo 55), B1 (44), B3 (60) back-projected; 9.5 x 6 rectangle least squares, rms %.2f m' % rms)

# ------------------------------------------------------------------ C
g = json.load(open(T('grid_Cfull_red.json'))); K = np.array(g['corners_xy']); sc = g['scale_m_per_unit']
k2, k1, k3 = K[2], K[1], K[3]
xd = (k1 - k2) / np.linalg.norm(k1 - k2); yd = (k3 - k2) / np.linalg.norm(k3 - k2)
print('C: origin k2 (%.2f, %.2f); x toward k1, %.2f m; y toward k3, %.2f m; angle between %.1f deg; %s-handed with z up'
      % (*k2, np.linalg.norm(k1 - k2) * sc, np.linalg.norm(k3 - k2) * sc, np.degrees(np.arccos(xd @ yd)),
         'right' if xd[0] * yd[1] - xd[1] * yd[0] > 0 else 'LEFT'))
OV['C'] = dict(origin_local_units=k2.tolist(), xdir_local=xd.tolist(), ydir_local=yd.tolist(), scale_m_per_unit=sc,
               source='C0 circle-cross in 20260819_182441 back-projected to 1.1 m outside lattice corner k2; 7 m side to k1, 8 m side to k3')
json.dump(OV, open(T('frame_override.json'), 'w'), indent=1); print('wrote tables/frame_override.json')
