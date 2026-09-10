"""Place each block's GPR surfaces on its photogrammetry mesh using the detected painted grid.
Writes registered OBJ/DXF in mesh coordinates, the lattice as polylines, a per-block figure,
and registration.json. Origin-corner choice per block is a setting: edit CHOICE below or
tables/registration_choice.json. usage: register.py [A B C]"""
import numpy as np, json, os, sys, csv
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa
SITE = r'D:/code_ws/reference/parsans/site'; OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
CFG = {
 'A': dict(grid='grid_A_paint.json', nx=12, ny=12, mesh='block a.obj', stride=5, feats=('A1', 'A2'), dims=(5.5, 5.5)),
 'B': dict(grid='grid_B_lum.json', nx=20, ny=13, mesh='block b.obj', stride=2, feats=('B1', 'B2'), dims=(9.5, 6.0)),
 'C': dict(grid='grid_Cfull_red.json', nx=15, ny=17, mesh='block_c_decimated_1M.obj', stride=2, feats=('C1', 'C2'), dims=(7.0, 8.0)),
}
CHOICE = {'A': 0, 'B': 0, 'C': 0}
p = os.path.join(OUT, 'tables', 'registration_choice.json')
if os.path.exists(p): CHOICE.update(json.load(open(p)))
blocks = sys.argv[1:] or list(CFG)


def load_v(path, stride=1):
    xyz = []; rgb = []; k = 0
    with open(path, 'rb') as f:
        for ln in f:
            if ln[:2] != b'v ': continue
            k += 1
            if k % stride: continue
            q = ln.split(); xyz.append((float(q[1]), float(q[2]), float(q[3]))); rgb.append((float(q[4]), float(q[5]), float(q[6])))
    return np.array(xyz), np.array(rgb)


def configs(g, nx, ny):
    """all right-handed placements of the report frame on the detected lattice"""
    t = np.radians(g['theta_deg']); Ud = np.array([np.cos(t), np.sin(t)]); Vd = np.array([-np.sin(t), np.cos(t)])
    rU, rV = g['lines_U'], g['lines_V']; nU, nV = len(rU), len(rV)
    out = []
    for ax_is_U in (True, False):                      # is report-x the coordinate U (lines at constant U = constant x)?
        if (nU if ax_is_U else nV) != nx or (nV if ax_is_U else nU) != ny: continue
        for cu in (0, -1):
            for cv in (0, -1):
                corner = rU[cu] * Ud + rV[cv] * Vd
                su = 1 if cu == 0 else -1; sv = 1 if cv == 0 else -1     # into the grid
                xdir, ydir = (su * Ud, sv * Vd) if ax_is_U else (sv * Vd, su * Ud)
                if xdir[0] * ydir[1] - xdir[1] * ydir[0] <= 0: continue      # must be right-handed (z up)
                out.append(dict(corner=corner.tolist(), xdir=xdir.tolist(), ydir=ydir.tolist(),
                                label='origin at lattice corner (U%s,V%s), x along %s' % ('0' if cu == 0 else 'end', '0' if cv == 0 else 'end', 'U' if ax_is_U else 'V')))
    return out


def obj_write(path, V, F, name, lines=None):
    L = ['# %s, mesh coordinates of %s' % (name, path), 'o %s' % name] + ['v %.5f %.5f %.5f' % tuple(v) for v in V]
    L += ['f %d %d %d %d' % tuple(f) for f in F]
    if lines:
        for pl in lines: L.append('l ' + ' '.join(str(i) for i in pl))
    open(path, 'w').write('\n'.join(L) + '\n')


def dxf_write(path, quads, layer):
    L = ['0', 'SECTION', '2', 'ENTITIES']
    for q in quads:
        L += ['0', '3DFACE', '8', layer]
        for k, (x, y, z) in enumerate(q): L += [str(10 + k), '%.5f' % x, str(20 + k), '%.5f' % y, str(30 + k), '%.5f' % z]
    L += ['0', 'ENDSEC', '0', 'EOF']; open(path, 'w').write('\n'.join(L) + '\n')


REG = {}
for blk in blocks:
    cfg = CFG[blk]; g = json.load(open(os.path.join(OUT, 'tables', cfg['grid'])))
    R = np.array(g['R']); c = np.array(g['c']); scale = g['scale_m_per_unit']; upm = 1.0 / scale
    ovp = os.path.join(OUT, 'tables', 'frame_override.json')
    OVR = json.load(open(ovp)) if os.path.exists(ovp) else {}
    if blk in OVR:                                   # frame from the painted labels, back-projected: the rock decides
        o_ = OVR[blk]; cands = [dict(corner=o_['origin_local_units'], xdir=o_['xdir_local'], ydir=o_['ydir_local'], label='LABELS: ' + o_['source'])]
        ch = 0; C_ = cands[0]
        if 'scale_m_per_unit' in o_: scale = o_['scale_m_per_unit']; upm = 1.0 / scale
    else:
        cands = configs(g, cfg['nx'], cfg['ny'])
        ch = CHOICE[blk] % len(cands); C_ = cands[ch]
    corner = np.array(C_['corner']); xdir = np.array(C_['xdir']); ydir = np.array(C_['ydir'])
    print('\n=== Block %s: %s, scale %.4f m/unit, %d valid placements, using #%d: %s' % (blk, cfg['grid'], scale, len(cands), ch, C_['label']))
    for i, cc_ in enumerate(cands):
        print('    #%d  origin at local (%.2f, %.2f)  x-dir (%.3f, %.3f)  %s' % (i, cc_['corner'][0], cc_['corner'][1], cc_['xdir'][0], cc_['xdir'][1], cc_['label']))

    def to_local_m(xg_cm, yg_cm, depth_m):
        """report frame -> local plane frame in METRES (bench = z 0, depth negative)"""
        xy = corner[None, :] * scale + np.outer(xg_cm / 100.0, xdir) + np.outer(yg_cm / 100.0, ydir)
        return np.c_[xy, -np.asarray(depth_m)]
    def to_mesh(lm): return c + (lm * upm) @ R          # local metres -> mesh units

    od = os.path.join(OUT, 'model', 'registered', blk); os.makedirs(od, exist_ok=True)
    # lattice and outline in mesh coords, as polylines
    W, H = cfg['dims']; V = []; PL = []
    for i in range(cfg['nx']):
        a = to_mesh(to_local_m(np.array([i * 50.0, i * 50.0]), np.array([0.0, H * 100]), np.zeros(2))); V += a.tolist(); PL.append([len(V) - 1, len(V)])
    for j in range(cfg['ny']):
        a = to_mesh(to_local_m(np.array([0.0, W * 100]), np.array([j * 50.0, j * 50.0]), np.zeros(2))); V += a.tolist(); PL.append([len(V) - 1, len(V)])
    obj_write(os.path.join(od, 'grid_lattice.obj'), V, [], 'grid_%s' % blk, PL)
    # surfaces
    for F in cfg['feats']:
        a = np.loadtxt(os.path.join(OUT, 'model', '%s_grid_10cm.xyz' % F)); n = len(np.unique(a[:, 0])); m = len(np.unique(a[:, 1]))
        GX, GY, Z = a[:, 0].reshape(m, n), a[:, 1].reshape(m, n), a[:, 2].reshape(m, n)
        M = to_mesh(to_local_m(GX.ravel(), GY.ravel(), Z.ravel())).reshape(m, n, 3)
        ok = np.isfinite(Z)
        vid = -np.ones((m, n), int); Vs = []; Fs = []; quads = []
        for j in range(m):
            for i in range(n):
                if ok[j, i]: vid[j, i] = len(Vs) + 1; Vs.append(M[j, i])
        for j in range(m - 1):
            for i in range(n - 1):
                ids = [vid[j, i], vid[j, i + 1], vid[j + 1, i + 1], vid[j + 1, i]]
                if min(ids) > 0: Fs.append(ids); quads.append([Vs[k - 1] for k in ids])
        obj_write(os.path.join(od, '%s_in_mesh.obj' % F), Vs, Fs, F); dxf_write(os.path.join(od, '%s_in_mesh.dxf' % F), quads, F)
        print('  %s -> %d verts %d quads in mesh coords' % (F, len(Vs), len(Fs)))
    REG[blk] = dict(grid_json=cfg['grid'], scale_m_per_unit=scale, units_per_m=upm, plane_R=R.tolist(), plane_c=c.tolist(),
                    origin_local_units=corner.tolist(), xdir_local=xdir.tolist(), ydir_local=ydir.tolist(),
                    placement_index=ch, placement=C_['label'], n_valid_placements=len(cands),
                    origin_mesh=to_mesh(to_local_m(np.zeros(1), np.zeros(1), np.zeros(1)))[0].tolist(),
                    note='depth negative along -n; report frame; corner choice unverified, see AUDIT/MODEL')

    # ---- figure: 3D mesh + surfaces in local metres, and plan overlay ----
    P, Cc = load_v(os.path.join(SITE, cfg['mesh']), cfg['stride'])
    Lm = ((P - c) @ R.T) * scale
    gc = corner * scale + 0.5 * (W * xdir + H * ydir)
    pad = 0.5 * max(W, H) + 3.0
    sel = (np.abs(Lm[:, 0] - gc[0]) < pad) & (np.abs(Lm[:, 1] - gc[1]) < pad) & (Lm[:, 2] > -1.0) & (Lm[:, 2] < 6.0)
    Q = Lm[sel]; Qc = np.clip(Cc[sel], 0, 1)
    if len(Q) > 220000: k = np.random.default_rng(0).choice(len(Q), 220000, replace=False); Q = Q[k]; Qc = Qc[k]
    fig = plt.figure(figsize=(16, 8))
    ax = fig.add_subplot(121, projection='3d')
    ax.scatter(Q[:, 0], Q[:, 1], Q[:, 2], c=Qc, s=0.6, linewidths=0, alpha=0.85)
    out = np.array([[0, 0], [W * 100, 0], [W * 100, H * 100], [0, H * 100], [0, 0]], float)
    o = to_local_m(out[:, 0], out[:, 1], np.zeros(5)); ax.plot(o[:, 0], o[:, 1], o[:, 2] + 0.02, 'y-', lw=2.5)
    cm = {'A1': 'autumn', 'A2': 'winter', 'B1': 'autumn', 'B2': 'Blues_r', 'C1': 'autumn', 'C2': 'viridis_r'}
    for F in cfg['feats']:
        a = np.loadtxt(os.path.join(OUT, 'model', '%s_grid_10cm.xyz' % F)); n = len(np.unique(a[:, 0])); m = len(np.unique(a[:, 1]))
        GX, GY, Z = a[:, 0].reshape(m, n), a[:, 1].reshape(m, n), a[:, 2].reshape(m, n)
        S = to_local_m(GX.ravel(), GY.ravel(), Z.ravel()).reshape(m, n, 3); s = 2
        ax.plot_surface(S[::s, ::s, 0], S[::s, ::s, 1], S[::s, ::s, 2], cmap=cm[F], alpha=0.9, linewidth=0)
    ax.set_xlim(gc[0] - pad, gc[0] + pad); ax.set_ylim(gc[1] - pad, gc[1] + pad); ax.set_zlim(-4.5, 3.0)
    ax.set_xlabel('bench x (m)'); ax.set_ylabel('bench y (m)'); ax.set_zlabel('m, bench = 0'); ax.set_box_aspect((1, 1, 0.45))
    ax.view_init(elev=28, azim=-55); ax.set_title('Block %s on its photogrammetry, scale %.3f m/unit' % (blk, scale), fontsize=10)
    ax2 = fig.add_subplot(122)
    d = np.load(os.path.join(OUT, 'tables', 'paint_raster_%s.npz' % blk)); x0, y0, px = float(d['x0']), float(d['y0']), float(d['px']); img = d['img']
    NY, NX = img.shape[:2]
    ax2.imshow(np.clip(img, 0, 1), origin='lower', extent=[x0 * scale, (x0 + NX * px) * scale, y0 * scale, (y0 + NY * px) * scale])
    ax2.plot(o[:, 0], o[:, 1], 'y-', lw=2)
    for F in cfg['feats']:
        a = np.loadtxt(os.path.join(OUT, 'model', '%s_grid_10cm.xyz' % F)); n = len(np.unique(a[:, 0])); m = len(np.unique(a[:, 1]))
        GX, GY, Z = a[:, 0].reshape(m, n), a[:, 1].reshape(m, n), a[:, 2].reshape(m, n)
        S = to_local_m(GX.ravel(), GY.ravel(), Z.ravel()).reshape(m, n, 3)
        cs = ax2.contour(S[..., 0], S[..., 1], Z, levels=6, cmap=cm[F], linewidths=1.0); ax2.clabel(cs, fmt='%.1f', fontsize=6)
    ax2.plot(*to_local_m(np.zeros(1), np.zeros(1), np.zeros(1))[0, :2], 'w*', ms=14, mec='k')
    ax2.text(*to_local_m(np.zeros(1), np.zeros(1), np.zeros(1))[0, :2], '  origin (report 0,0)', color='w', fontsize=8, weight='bold')
    ax2.set_xlim(gc[0] - pad, gc[0] + pad); ax2.set_ylim(gc[1] - pad, gc[1] + pad); ax2.set_aspect('equal')
    ax2.set_xlabel('bench x (m)'); ax2.set_ylabel('bench y (m)'); ax2.set_title('plan: grid outline (yellow) and depth contours on the vertex colours', fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'figs', 'REGISTERED_%s.png' % blk), dpi=120); print('  wrote figs/REGISTERED_%s.png' % blk)
    plt.close(fig)
old = {}
rp = os.path.join(OUT, 'tables', 'registration.json')
if os.path.exists(rp): old = json.load(open(rp))
old.update(REG); json.dump(old, open(rp, 'w'), indent=1); print('\nwrote tables/registration.json')
