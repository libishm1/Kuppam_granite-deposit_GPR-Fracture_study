"""Combined render and dataset export.
For each block, everything in ONE metric frame: bench plane = z 0, metres, z up, depth negative,
report x,y axes as registered. Point cloud (PLY, colours), GPR surfaces (OBJ, DXF), lattice (OBJ).
Plus a montage figure for immediate viewing."""
import numpy as np, json, os, shutil, csv
from PIL import Image
SITE = r'D:/code_ws/reference/parsans/site'; OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
DS = os.path.join(OUT, 'dataset'); os.makedirs(DS, exist_ok=True)
REG = json.load(open(os.path.join(OUT, 'tables', 'registration.json')))
MESH = {'A': ('block a.obj', 4), 'B': ('block b.obj', 2), 'C': ('block_c_decimated_1M.obj', 2)}
FEATS = {'A': ('A1', 'A2'), 'B': ('B1', 'B2'), 'C': ('C1', 'C2')}
DIMS = {'A': (5.5, 5.5), 'B': (9.5, 6.0), 'C': (7.0, 8.0)}


def load_v(path, stride):
    xyz = []; rgb = []; k = 0
    with open(path, 'rb') as f:
        for ln in f:
            if ln[:2] != b'v ': continue
            k += 1
            if k % stride: continue
            q = ln.split(); xyz.append((float(q[1]), float(q[2]), float(q[3]))); rgb.append((float(q[4]), float(q[5]), float(q[6])))
    return np.array(xyz), np.array(rgb)


def ply_write(path, P, C):
    with open(path, 'w') as f:
        f.write('ply\nformat ascii 1.0\ncomment Kuppam bench frame, metres, z up, bench top = 0\n')
        f.write('element vertex %d\nproperty float x\nproperty float y\nproperty float z\n' % len(P))
        f.write('property uchar red\nproperty uchar green\nproperty uchar blue\nend_header\n')
        Cc = np.clip(C * 255, 0, 255).astype(int)
        f.writelines('%.4f %.4f %.4f %d %d %d\n' % (x, y, z, r, g, b) for (x, y, z), (r, g, b) in zip(P, Cc))


def obj_surface(path, S, ok, name):
    m, n = ok.shape; vid = -np.ones((m, n), int); V = []; F = []; Q = []
    for j in range(m):
        for i in range(n):
            if ok[j, i]: vid[j, i] = len(V) + 1; V.append(S[j, i])
    for j in range(m - 1):
        for i in range(n - 1):
            ids = [vid[j, i], vid[j, i + 1], vid[j + 1, i + 1], vid[j + 1, i]]
            if min(ids) > 0: F.append(ids); Q.append([V[k - 1] for k in ids])
    L = ['# %s, bench frame metres, z up, depth negative' % name, 'o %s' % name] + ['v %.4f %.4f %.4f' % tuple(v) for v in V] + ['f %d %d %d %d' % tuple(f) for f in F]
    open(path, 'w').write('\n'.join(L) + '\n')
    D = ['0', 'SECTION', '2', 'ENTITIES']
    for q in Q:
        D += ['0', '3DFACE', '8', name]
        for k, (x, y, z) in enumerate(q): D += [str(10 + k), '%.4f' % x, str(20 + k), '%.4f' % y, str(30 + k), '%.4f' % z]
    D += ['0', 'ENDSEC', '0', 'EOF']; open(path[:-4] + '.dxf', 'w').write('\n'.join(D) + '\n')
    return len(V), len(F)


summary = []
for blk in 'ABC':
    r = REG[blk]; R = np.array(r['plane_R']); c = np.array(r['plane_c']); sc = r['scale_m_per_unit']
    corner = np.array(r['origin_local_units']) * sc; xd = np.array(r['xdir_local']); yd = np.array(r['ydir_local'])
    W, H = DIMS[blk]
    def loc(xg_cm, yg_cm, depth_m):
        xy = corner[None, :] + np.outer(np.asarray(xg_cm) / 100.0, xd) + np.outer(np.asarray(yg_cm) / 100.0, yd)
        return np.c_[xy, -np.asarray(depth_m)]
    od = os.path.join(DS, 'bench_frame_m', 'Block_' + blk); os.makedirs(od, exist_ok=True)
    # point cloud
    P, Cc = load_v(os.path.join(SITE, MESH[blk][0]), MESH[blk][1])
    Lm = ((P - c) @ R.T) * sc
    gc = corner + 0.5 * (W * xd + H * yd); pad = 0.5 * max(W, H) + 4.0
    sel = (np.abs(Lm[:, 0] - gc[0]) < pad) & (np.abs(Lm[:, 1] - gc[1]) < pad) & (Lm[:, 2] > -2.0) & (Lm[:, 2] < 8.0)
    Q = Lm[sel]; Qc = Cc[sel]
    if len(Q) > 400000: k = np.random.default_rng(0).choice(len(Q), 400000, replace=False); Q = Q[k]; Qc = Qc[k]
    ply_write(os.path.join(od, 'Block_%s_pointcloud.ply' % blk), Q, Qc)
    # surfaces
    nv = {}
    for F in FEATS[blk]:
        a = np.loadtxt(os.path.join(OUT, 'model', '%s_grid_10cm.xyz' % F)); n = len(np.unique(a[:, 0])); m = len(np.unique(a[:, 1]))
        GX, GY, Z = a[:, 0].reshape(m, n), a[:, 1].reshape(m, n), a[:, 2].reshape(m, n)
        S = loc(GX.ravel(), GY.ravel(), Z.ravel()).reshape(m, n, 3)
        nv[F] = obj_surface(os.path.join(od, '%s_surface.obj' % F), S, np.isfinite(Z), F)
    # lattice + outline
    V = []; PL = []
    nx, ny = int(W / 0.5) + 1, int(H / 0.5) + 1
    for i in range(nx):
        a = loc([i * 50.0] * 2, [0.0, H * 100], [0, 0]); V += a.tolist(); PL.append((len(V) - 1, len(V)))
    for j in range(ny):
        a = loc([0.0, W * 100], [j * 50.0] * 2, [0, 0]); V += a.tolist(); PL.append((len(V) - 1, len(V)))
    L = ['# Block %s survey lattice, 0.5 m, bench frame metres' % blk, 'o grid_%s' % blk] + ['v %.4f %.4f %.4f' % tuple(v) for v in V] + ['l %d %d' % p for p in PL]
    open(os.path.join(od, 'Block_%s_grid.obj' % blk), 'w').write('\n'.join(L) + '\n')
    # frame definition
    json.dump(dict(block=blk, frame='bench: plane through the painted grid, z up, bench top = 0, metres',
                   report_origin_xy=corner.tolist(), report_x_dir=xd.tolist(), report_y_dir=yd.tolist(),
                   grid_m=[W, H], scale_m_per_mesh_unit=sc, mesh_units_to_bench='L = ((P - plane_c) @ plane_R.T) * scale',
                   plane_R=R.tolist(), plane_c=c.tolist(), placement=r['placement'], n_valid_placements=r['n_valid_placements'],
                   origin_corner_ambiguity={'A': '4-fold (square), unverified', 'B': '2-fold (180 deg), unverified', 'C': '2-fold, k3=C0 chosen from paint density, likely'}[blk]),
              open(os.path.join(od, 'FRAME.json'), 'w'), indent=1)
    summary.append((blk, len(Q), nv, sc))
    print('Block %s: %d cloud points, surfaces %s, scale %.4f' % (blk, len(Q), nv, sc))

# report-frame copies and registration
rf = os.path.join(DS, 'report_frame'); os.makedirs(rf, exist_ok=True)
for F in ('A1', 'A2', 'B1', 'B2', 'C1', 'C2'):
    for ext in ('obj', 'dxf'): shutil.copy(os.path.join(OUT, 'model', '%s_surface.%s' % (F, ext)), rf)
    shutil.copy(os.path.join(OUT, 'model', '%s_grid_10cm.xyz' % F), rf)
for b in 'ABC': shutil.copy(os.path.join(OUT, 'model', 'Block%s_all.obj' % b), rf) if os.path.exists(os.path.join(OUT, 'model', 'Block%s_all.obj' % b)) else None
pk = os.path.join(DS, 'picks'); os.makedirs(pk, exist_ok=True)
for f in ('PICKS_C2_adjusted.csv', 'PICKS_C1_raw.csv', 'PICKS_B1_raw.csv', 'PICKS_B2_raw.csv', 'PICKS_A1_final.csv', 'PICKS_A2_final.csv', 'GEOMETRY_resolved.csv', 'line_inventory.csv'):
    shutil.copy(os.path.join(OUT, 'tables', f), pk)
rg = os.path.join(DS, 'registration'); os.makedirs(rg, exist_ok=True)
for f in ('registration.json', 'grid_A_paint.json', 'grid_B_lum.json', 'grid_Cfull_red.json'): shutil.copy(os.path.join(OUT, 'tables', f), rg)
for f in ('REGISTERED_A.png', 'REGISTERED_B.png', 'REGISTERED_C.png', 'grid_A_paint.png', 'grid_B_lum.png', 'grid_Cfull_red.png', 'MODEL_overview.png'): shutil.copy(os.path.join(OUT, 'figs', f), rg)
json.dump({'A': 0, 'B': 0, 'C': 0}, open(os.path.join(rg, 'registration_choice.json'), 'w'), indent=1)

# montage
ims = [Image.open(os.path.join(OUT, 'figs', 'REGISTERED_%s.png' % b)) for b in 'ABC']
w = 1100; rows = []
for im in ims: rows.append(im.resize((w, int(im.height * w / im.width)), Image.LANCZOS))
ov = Image.open(os.path.join(OUT, 'figs', 'MODEL_overview.png')); ov = ov.resize((w, int(ov.height * w / ov.width)), Image.LANCZOS)
Hh = sum(r.height for r in rows) + ov.height
M = Image.new('RGB', (w, Hh), 'white'); y = 0
for r in rows + [ov]: M.paste(r, (0, y)); y += r.height
M.save(os.path.join(OUT, 'figs', 'REGISTERED_all.png')); M.convert('RGB').save(os.path.join(DS, 'OVERVIEW.jpg'), quality=88)
print('wrote figs/REGISTERED_all.png and dataset/OVERVIEW.jpg  (%d x %d)' % M.size)
print('dataset size: %.1f MB' % (sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(DS) for f in fs) / 1e6))
