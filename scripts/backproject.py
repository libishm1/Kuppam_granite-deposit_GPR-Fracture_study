"""Back-project a pixel in a photo onto the bench plane using the Metashape camera pose.
usage: backproject.py BLOCK LABEL u v [LABEL u v ...]     (u,v in the stored image frame)"""
import numpy as np, json, os, sys
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
blk = sys.argv[1]; args = sys.argv[2:]
cams = json.load(open(os.path.join(OUT, 'tables', 'cameras_%s.json' % blk)))
reg = json.load(open(os.path.join(OUT, 'tables', 'registration.json')))[blk]
R = np.array(reg['plane_R']); c = np.array(reg['plane_c']); sc = reg['scale_m_per_unit']
corner = np.array(reg['origin_local_units']); xd = np.array(reg['xdir_local']); yd = np.array(reg['ydir_local'])
gj = {'A': 'grid_A_paint.json', 'B': 'grid_B_lum.json', 'C': 'grid_Cfull_red.json'}[blk]
K = np.array(json.load(open(os.path.join(OUT, 'tables', gj)))['corners_xy'])
n = R[2]


def undistort(xd_, yd_, cal, it=8):
    x, y = xd_, yd_
    for _ in range(it):
        r2 = x * x + y * y
        rad = 1 + cal['k1'] * r2 + cal['k2'] * r2 ** 2 + cal['k3'] * r2 ** 3
        dx = cal['p1'] * (r2 + 2 * x * x) + 2 * cal['p2'] * x * y
        dy = cal['p2'] * (r2 + 2 * y * y) + 2 * cal['p1'] * x * y
        x = (xd_ - dx) / rad; y = (yd_ - dy) / rad
    return x, y


for i in range(0, len(args), 3):
    lab, u, v = args[i], float(args[i + 1]), float(args[i + 2])
    cam = cams['cameras'][lab]; cal = cams['sensors'][cam['sensor']]; T = np.array(cam['T'])
    xd_ = (u - cal['w'] / 2 - cal['cx']) / cal['f']; yd_ = (v - cal['h'] / 2 - cal['cy']) / cal['f']
    x, y = undistort(xd_, yd_, cal)
    d = T[:3, :3] @ np.array([x, y, 1.0]); o = T[:3, 3]
    t = ((c - o) @ n) / (d @ n); P = o + t * d
    L = (P - c) @ R.T
    graze = np.degrees(np.arcsin(abs(d @ n) / np.linalg.norm(d)))
    dist = np.hypot(K[:, 0] - L[0], K[:, 1] - L[1]) * sc
    # report-frame coordinates under the current registration
    rel = (L[:2] - corner) * sc
    xg = rel @ xd; yg = rel @ yd
    camL = (o - c) @ R.T
    print('%s (%4.0f,%4.0f): plane hit local (%.2f, %.2f) u | report frame x=%.2f y=%.2f m | ray %.0f deg to plane, cam %.1f m away, %.1f m up'
          % (lab, u, v, L[0], L[1], xg, yg, graze, np.hypot(*(camL[:2] - L[:2])) * sc, camL[2] * sc))
    print('     distance to detected corners k0..k3: ' + '  '.join('%.2f' % v_ for v_ in dist) + ' m   nearest k%d' % int(np.argmin(dist)))
