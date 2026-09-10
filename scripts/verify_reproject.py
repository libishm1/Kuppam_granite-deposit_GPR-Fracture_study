"""Verification of the registration by REPROJECTION: draw the registered 0.5 m lattice, the origin and
the axes back INTO the photographs through the Metashape camera model. If plane, scale, rotation and
origin are right, the drawn lattice falls on the painted one. Also draws each GPR plane's daylight line.
usage: verify_reproject.py BLOCK LABEL [LABEL ...]"""
import numpy as np, json, os, sys, csv
from PIL import Image, ImageDraw
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'; SITE = r'D:/code_ws/reference/parsans/site'
PH = {'A': 'photogrammetry/block_A', 'B': 'photogrammetry/Block_B', 'C': 'photogrammetry/BLock_C and overall'}
DIMS = {'A': (5.5, 5.5), 'B': (9.5, 6.0), 'C': (7.0, 8.0)}
blk = sys.argv[1]; labels = sys.argv[2:]
reg = json.load(open(os.path.join(OUT, 'tables', 'registration.json')))[blk]
cams = json.load(open(os.path.join(OUT, 'tables', 'cameras_%s.json' % blk)))
R = np.array(reg['plane_R']); c = np.array(reg['plane_c']); sc = reg['scale_m_per_unit']; upm = 1 / sc
corner = np.array(reg['origin_local_units']) * sc; xd = np.array(reg['xdir_local']); yd = np.array(reg['ydir_local'])
W, H = DIMS[blk]
dem = np.loadtxt(os.path.join(OUT, 'model', 'v2_topo', 'Block%s_DEM_10cm.xyz' % blk))
nn = len(np.unique(dem[:, 0])); mm = len(np.unique(dem[:, 1])); DEM = dem[:, 2].reshape(mm, nn)
from scipy.interpolate import RegularGridInterpolator
fi = RegularGridInterpolator((dem[:, 1].reshape(mm, nn)[:, 0], dem[:, 0].reshape(mm, nn)[0]), DEM, bounds_error=False, fill_value=0.0)


def to_mesh(xg_cm, yg_cm, use_dem=True):
    xy = corner[None, :] + np.outer(np.asarray(xg_cm) / 100.0, xd) + np.outer(np.asarray(yg_cm) / 100.0, yd)
    z = fi(np.c_[np.asarray(yg_cm), np.asarray(xg_cm)]) if use_dem else np.zeros(len(xy))
    Lm = np.c_[xy, z]
    return c + (Lm * upm) @ R


def project(P, T, cal):
    Ti = np.linalg.inv(T); Xc = (Ti[:3, :3] @ P.T).T + Ti[:3, 3]
    z = Xc[:, 2]; ok = z > 0.05
    x = Xc[:, 0] / np.where(ok, z, 1); y = Xc[:, 1] / np.where(ok, z, 1)
    r2 = x * x + y * y; rad = 1 + cal['k1'] * r2 + cal['k2'] * r2 ** 2 + cal['k3'] * r2 ** 3
    xd_ = x * rad + cal['p1'] * (r2 + 2 * x * x) + 2 * cal['p2'] * x * y
    yd_ = y * rad + cal['p2'] * (r2 + 2 * y * y) + 2 * cal['p1'] * x * y
    u = cal['w'] / 2 + cal['cx'] + cal['f'] * xd_; v = cal['h'] / 2 + cal['cy'] + cal['f'] * yd_
    ok &= (u > -0.2 * cal['w']) & (u < 1.2 * cal['w']) & (v > -0.2 * cal['h']) & (v < 1.2 * cal['h'])
    return u, v, ok


# GPR plane daylight lines (v2 on DEM), as polylines in report cm
FE = {'A': ('A1', 'A2'), 'B': ('B1', 'B2'), 'C': ('C1', 'C2')}
from skimage import measure
day = {}
GX, GY = np.meshgrid(np.arange(0, W * 100 + 1, 5.0), np.arange(0, H * 100 + 1, 5.0)); hs = fi(np.c_[GY.ravel(), GX.ravel()]).reshape(GX.shape)
for F in FE[blk]:
    for nm in ('PICKS_%s_final.csv', 'PICKS_%s_raw.csv', 'PICKS_%s_adjusted.csv'):
        pf = os.path.join(OUT, 'tables', nm % F)
        if os.path.exists(pf): break
    rr = list(csv.DictReader(open(pf, encoding='utf-8'))); Pp = np.array([[float(q['x_cm']), float(q['y_cm']), float(q.get('z_adj') or q['depth_m'])] for q in rr])
    co, *_ = np.linalg.lstsq(np.c_[Pp[:, 0], Pp[:, 1], np.ones(len(Pp))], Pp[:, 2], rcond=None)
    cs = measure.find_contours(co[0] * GX + co[1] * GY + co[2] + hs, 0.0)
    day[F] = [np.c_[cc[:, 1] * 5.0, cc[:, 0] * 5.0] for cc in cs if len(cc) > 5]
# sketch traces
sk = {}
for q in csv.DictReader(open(os.path.join(OUT, 'tables', 'sketch_chained_%s.csv' % blk), encoding='utf-8')):
    sk.setdefault(int(q['trace_id']), []).append((float(q['x_cm']), float(q['y_cm'])))

for lab in labels:
    cam = cams['cameras'][lab]; cal = cams['sensors'][cam['sensor']]; T = np.array(cam['T'])
    p = os.path.join(SITE, PH[blk], lab + '.jpg'); im = Image.open(p)
    if im.size != (cal['w'], cal['h']): print('size mismatch', lab); continue
    dr = ImageDraw.Draw(im, 'RGBA'); lw = max(3, cal['w'] // 700)
    def draw_poly(xs, ys, col, width, use_dem=True):
        P = to_mesh(xs, ys, use_dem); u, v, ok = project(P, T, cal)
        for i in range(len(u) - 1):
            if ok[i] and ok[i + 1]: dr.line([(u[i], v[i]), (u[i + 1], v[i + 1])], fill=col, width=width)
    nx, ny = int(W / 0.5) + 1, int(H / 0.5) + 1; t = np.linspace(0, 1, 40)
    for i in range(nx): draw_poly(np.full(40, i * 50.0), t * H * 100, (0, 255, 255, 190), lw)
    for j in range(ny): draw_poly(t * W * 100, np.full(40, j * 50.0), (0, 255, 255, 190), lw)
    draw_poly(t * W * 100, np.zeros(40), (255, 255, 0, 255), lw * 2); draw_poly(np.zeros(40), t * H * 100, (255, 255, 0, 255), lw * 2)
    draw_poly(t * 100.0, np.zeros(40), (255, 0, 0, 255), lw * 3)          # x axis, 1 m, red
    draw_poly(np.zeros(40), t * 100.0, (0, 255, 0, 255), lw * 3)          # y axis, 1 m, green
    u, v, ok = project(to_mesh([0.0], [0.0]), T, cal)
    if ok[0]: dr.ellipse([u[0] - 6 * lw, v[0] - 6 * lw, u[0] + 6 * lw, v[0] + 6 * lw], outline=(255, 255, 0, 255), width=lw * 2); dr.text((u[0] + 8 * lw, v[0]), '%s0 (report 0,0)' % blk, fill=(255, 255, 0, 255))
    for F, segs in day.items():
        for s in segs: draw_poly(s[:, 0], s[:, 1], (255, 0, 255, 230), lw * 2)
    for pts in sk.values():
        pts = np.array(pts); draw_poly(pts[:, 0], pts[:, 1], (0, 90, 255, 230), lw * 2)
    dr.text((20, 20), 'cyan: registered 0.5 m lattice | yellow: block outline | red/green: 1 m x/y axes | magenta: GPR plane daylight (v2) | blue: field-sketch fractures', fill=(255, 255, 255, 255))
    s = 1400 / max(im.size); im2 = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    fn = os.path.join(OUT, 'figs', 'REPROJ_%s_%s.jpg' % (blk, lab)); im2.save(fn, quality=88); print('wrote', fn)
