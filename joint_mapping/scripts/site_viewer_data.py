"""Pack the whole-site model into a single small payload for a standalone 3D viewer.

The Block C photogrammetry covers the entire pit, 49 by 48 m with 21 m of relief. It is 21.5 million
vertices, far too many to put in a web page, so it is voxel-downsampled, quantised to 16-bit
positions over the bounding box and 8-bit colour, and base64-encoded.

The A and B benches are placed into C's frame with the transforms from the ICP registration
(tables/icp_site.json, pose_released). Those two placements carry the caveats recorded in
ORIENTATION.md: they are a geometric fit with no surveyed control, good to roughly 0.2 to 0.3 m in
plan, and the Block B placement is the one that disagrees with the confirmed east axis.
"""
import numpy as np, json, os, base64
from scipy.interpolate import RegularGridInterpolator as RGI

OUT = 'D:/code_ws/outputs/2026-09-11/joint_mapping'
GPR = 'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
VOX = float(os.environ.get('SITE_VOX_CM', '8')) / 100.0
OUT_JSON = os.environ.get('SITE_OUT_JSON', 'site_data.json')
GRID = {'A': (5.5, 5.5), 'B': (9.5, 6.0), 'C': (7.0, 8.0)}

# Which painted axis runs east, per bench. Corner 0 to 1 of the ring below is built along +y,
# and on B and C that side measures 6.0 and 8.0 m, which is the side the client confirms runs
# east from the site photographs and the surveyors' sketch. A is 5.5 by 5.5, so no length test
# exists there and A's entry rests on photograph 113557 alone. See ORIENTATION.md.
EAST = {'A': '+x', 'B': '+y', 'C': '+y'}   # 12 Sep. Origin is the north-west corner on every bench and both axes run into the bench, but which axis runs east differs: on A the X-line numerals run down the WEST edge from A0 (client, from the site: '9, 12...' from the NW to the SW corner), so X-lines are stacked north-south and run east, +x east, +y south, left-handed. On B and C +y is east (6 m and 8 m sides, verified). See ORIENTATION.md.

# For a square bench, which grid axis the first hand-picked side (corner 0 to 1, the east side)
# runs along. Only A needs it. From the crew's numbering: X-line numerals 9, 12 ... run down the
# west edge from A0 to the SW corner, so X-lines are stacked N-S and run E-W; A0-A1 is +x.
SQUARE_FIRST_AXIS = {'A': 'x'}
BF = os.path.join(GPR, 'dataset', 'bench_frame_m')


def voxel(P, C, v):
    k = np.floor(P / v).astype(np.int64)
    _, idx = np.unique(k, axis=0, return_index=True)
    return P[idx], C[idx]


if __name__ == '__main__':
    z = np.load(os.path.join(OUT, 'cache', 'mesh_C.npz'))
    P = z['xyz'].astype(np.float64); C = z['rgb']
    P, C = voxel(P, C, VOX)
    print('%d points after %.0f cm voxel' % (len(P), VOX * 100))
    lo = P.min(0); hi = P.max(0)
    q = np.clip(((P - lo) / (hi - lo) * 65535.0), 0, 65535).astype(np.uint16)
    I = json.load(open(os.path.join(OUT, 'tables', 'icp_site.json')))

    # The painted grid is NOT the mesh axes. Each FRAME.json carries the grid's own origin and axis
    # directions inside that block's mesh frame, and the grid corner (X, Y) in metres lands at
    #     origin * scale  +  X * x_dir  +  Y * y_dir
    # Checked against the paint itself: on Block A, whose grid is white lime, points within 4 cm of a
    # predicted line are 10.9 brightness units lighter than points between the lines, and under the
    # mesh-axes assumption that difference vanishes to 0.2.
    def grid_ring(blk):
        F = json.load(open(os.path.join(BF, 'Block_%s' % blk, 'FRAME.json')))
        o = np.array(F['report_origin_xy'], float) * float(F['scale_m_per_mesh_unit'])
        xd = np.array(F['report_x_dir'], float); yd = np.array(F['report_y_dir'], float)
        W, H = GRID[blk]
        pts = [(0, 0), (0, H), (W, H), (W, 0)]
        return [list(o + X * xd + Y * yd) + [0.0] for X, Y in pts]

    benches = []
    benches.append(dict(block='C', ring=grid_ring('C'), origin=grid_ring('C')[0], east=EAST['C'],
                        placed='painted grid in its own frame', chip='model frame'))
    for b in ('A', 'B'):
        M = np.array(I['blocks'][b]['best']['pose_released']['matrix'], float)
        R = M[:3, :3]; tr = M[:3, 3]
        ring = [(R @ np.array(q) + tr).tolist() for q in grid_ring(b)]
        m = I['blocks'][b]['best']['pose_released']['metrics']
        benches.append(dict(block=b, ring=ring, origin=ring[0], east=EAST[b],
                            placed='registered to C, rms %.0f cm, %.0f%% of points within 10 cm'
                                   % (100 * m['rms_residual_m'], 100 * m['frac_lt_10cm']),
                            chip='fitted %.0f cm' % (100 * m['rms_residual_m'])))

    picked = None
    pf = os.path.join(OUT, 'picked_corners.json')
    if os.path.exists(pf):
        picked = json.load(open(pf))

    # Where the corners were picked by hand, the surveyed rectangle is pinned to them: held at the
    # picked origin, turned onto the picked first side, kept at its measured size. Rotation and
    # translation only, so the grid is never stretched to reach a corner. The frame-file placement
    # is kept beside it as ring_frame.
    def pinned(blk, P):
        if not P or len(P) < 3:
            return None
        P = [np.array(q[:2], float) for q in P]
        W, H = GRID[blk]
        d = P[1] - P[0]
        L = float(np.linalg.norm(d))
        if L < 0.2:
            return None
        u = d / L
        v = np.array([-u[1], u[0]])
        if (P[2] - P[1]) @ v < 0:
            v = -v

        # Which grid axis did the first picked side run along? Normally the side length decides,
        # and on B and C it does: their first picked sides measure 6.0 and 8.0 m, which is +y on
        # both. Block A is 5.5 x 5.5 so both lengths match and no measurement can separate them,
        # and the frame file cannot arbitrate either (it puts C's 8 m side to the south, where the
        # site photographs put it east). On a tie the answer comes from the crew's own numbering,
        # recorded in SQUARE_FIRST_AXIS: on A the X-line numerals run down the west edge from A0,
        # so the X-lines are stacked north to south and run east, which makes the east side -
        # the first side picked, A0 to A1 - the +x axis. Client, from the site, 12 September.
        if abs(L - H) < abs(L - W) - 1e-9:
            first_is = 'y'
        elif abs(L - W) < abs(L - H) - 1e-9:
            first_is = 'x'
        else:
            first_is = SQUARE_FIRST_AXIS[blk]

        if first_is == 'y':
            first, other = H, W
            uy, ux = u, v
        else:
            first, other = W, H
            ux, uy = u, v

        z = float(np.mean([q[2] for q in picked[blk]]))
        ring = [P[0], P[0] + u * first, P[0] + u * first + v * other, P[0] + v * other]
        ax = {'first_axis': first_is, 'ux': [float(ux[0]), float(ux[1])],
              'uy': [float(uy[0]), float(uy[1])],
              'origin': [float(P[0][0]), float(P[0][1])], 'z': z}
        return [[round(float(q[0]), 4), round(float(q[1]), 4), round(z, 4)] for q in ring], ax

    frames = {}
    for bn in benches:
        got = pinned(bn['block'], picked.get(bn['block']) if picked else None)
        pin, ax = got if got else (None, None)
        if pin:
            frames[bn['block']] = ax
            bn['ring_frame'] = bn['ring']
            bn['ring'] = pin
            bn['placed'] = 'grid pinned to the corners picked on the rock, size unchanged'
            bn['chip'] = 'pinned to picks'
            v = np.array(pin[1][:2]) - np.array(pin[0][:2])
            bn['first_side_bearing_deg'] = round(float(np.degrees(np.arctan2(v[1], v[0])) % 360), 1)
    data = dict(n=int(len(P)), lo=lo.tolist(), hi=hi.tolist(),
                pos=base64.b64encode(q.tobytes()).decode('ascii'),
                col=base64.b64encode(C.astype(np.uint8).tobytes()).decode('ascii'),
                benches=benches, picked=picked, vox_cm=VOX * 100,
                note='Block C photogrammetry, the whole pit. A and B bench outlines placed by ICP.')
    # The fracture surfaces and the chalked cracks, carried into the site frame the same way.
    # A surface is gridded at 10 cm in report coordinates as depth below the local rock surface, so
    # its elevation is DEM minus depth. The chalked cracks are stored in the block's mesh frame, so
    # they are turned back into report coordinates first.
    FEATS = {'A': ['A1', 'A2'], 'B': ['B1', 'B2'], 'C': ['C1', 'C2']}
    FCOL = {'A1': '#C8452B', 'A2': '#E08A3C', 'B1': '#1F8A80',
            'B2': '#2F6DB5', 'C1': '#7B4EA3', 'C2': '#4B7F32'}
    FNAME = {'A1': 'A-1 dipping sheet', 'A2': 'A-2 inclined sheet', 'B1': 'B-1 shallow sheet',
             'B2': 'B-2 deep wedge', 'C1': 'C-1 shallow sheet', 'C2': 'C-2 base cap'}
    STEP = 2                      # every other 10 cm node, so the mesh is 20 cm

    def load_xyz(path):
        a_ = np.loadtxt(path)
        gx = np.unique(a_[:, 0]) / 100.0
        gy = np.unique(a_[:, 1]) / 100.0
        return gx, gy, a_[:, 2].reshape(len(gy), len(gx))

    def to_site(blk, X, Y, Z):
        """report metres and bench elevation -> site frame"""
        ax = frames[blk]
        o = np.array(ax['origin'], float)
        ux = np.array(ax['ux'], float)
        uy = np.array(ax['uy'], float)
        return (o[0] + X * ux[0] + Y * uy[0],
                o[1] + X * ux[1] + Y * uy[1],
                ax['z'] + Z)

    surfaces = []
    for blk, fl in FEATS.items():
        if blk not in frames:
            continue
        dem_p = os.path.join(BF, 'Block_%s' % blk, 'Block%s_DEM_10cm.xyz' % blk)
        ex, ey, dem = load_xyz(dem_p)
        di = RGI((ey, ex), dem, bounds_error=False, fill_value=np.nan)
        for F in fl:
            gp_ = os.path.join(GPR, 'model', '%s_grid_10cm.xyz' % F)
            if not os.path.exists(gp_):
                continue
            gx, gy, dep = load_xyz(gp_)
            gx = gx[::STEP]; gy = gy[::STEP]; dep = dep[::STEP, ::STEP]
            GX, GY = np.meshgrid(gx, gy)
            elev = di(np.c_[GY.ravel(), GX.ravel()]).reshape(GX.shape) - dep
            ok = np.isfinite(elev)
            idx = -np.ones(elev.shape, int)
            n = 0
            verts = []
            for j in range(elev.shape[0]):
                for i in range(elev.shape[1]):
                    if ok[j, i]:
                        sx, sy, sz = to_site(blk, float(GX[j, i]), float(GY[j, i]), float(elev[j, i]))
                        verts += [sx, sy, sz]
                        idx[j, i] = n
                        n += 1
            tris = []
            for j in range(elev.shape[0] - 1):
                for i in range(elev.shape[1] - 1):
                    q = (idx[j, i], idx[j, i + 1], idx[j + 1, i + 1], idx[j + 1, i])
                    if min(q) < 0:
                        continue
                    tris += [q[0], q[1], q[2], q[0], q[2], q[3]]
            if not tris:
                continue
            surfaces.append(dict(
                id=F, block=blk, name=FNAME[F], colour=FCOL[F], n_vertices=n, n_triangles=len(tris) // 3,
                pos=base64.b64encode(np.asarray(verts, np.float32).tobytes()).decode('ascii'),
                idx=base64.b64encode(np.asarray(tris, np.uint32).tobytes()).decode('ascii'),
                depth_range=[round(float(np.nanmin(dep)), 2), round(float(np.nanmax(dep)), 2)]))

    cracks = []
    for blk in frames:
        cp = os.path.join(BF, 'Block_%s' % blk, 'Block_%s_sketch_cracks.obj' % blk)
        if not os.path.exists(cp):
            continue
        F_ = json.load(open(os.path.join(BF, 'Block_%s' % blk, 'FRAME.json')))
        o_ = np.array(F_['report_origin_xy'], float) * float(F_['scale_m_per_mesh_unit'])
        xd = np.array(F_['report_x_dir'], float)
        yd = np.array(F_['report_y_dir'], float)
        V = []
        L = []
        for ln in open(cp, 'rb'):
            if ln[:2] == b'v ':
                q = ln.split()
                V.append((float(q[1]), float(q[2]), float(q[3])))
            elif ln[:2] == b'l ':
                L.append([int(x.split(b'/')[0]) - 1 for x in ln.split()[1:]])
        if not V or not L:
            continue
        V = np.asarray(V, float)
        d_ = V[:, :2] - o_

        # The cracks reach report coordinates through FRAME.json's axes, while the surfaces reach
        # them through the picks' own grid. Those two namings do agree: projecting this .obj onto
        # xd/yd reproduces the extents of sketch_traces_B.csv to 0.48 m, where transposing them is
        # 6.01 m out (B is the test that works, being 9.5 by 6.0; A is square and C's .obj carries a
        # translation offset against its table, so neither discriminates). What the frame files get
        # wrong is the *direction* those axes point on the ground, 90 degrees out on A and C, and
        # that is already corrected here because to_site places everything through the pinned axes
        # rather than the frame file. So project as written and let the placement do the rest.
        Xr = d_ @ xd
        Yr = d_ @ yd
        seg = []
        for poly in L:
            for k in range(len(poly) - 1):
                for e in (poly[k], poly[k + 1]):
                    sx, sy, sz = to_site(blk, float(Xr[e]), float(Yr[e]), float(V[e, 2]) + 0.02)
                    seg += [sx, sy, sz]
        if seg:
            cracks.append(dict(block=blk, n_segments=len(seg) // 6,
                               pos=base64.b64encode(np.asarray(seg, np.float32).tobytes()).decode('ascii')))

    data_extra = dict(surfaces=surfaces, cracks=cracks)

    # The cut plan lives in each block's grid metres with z as bench-frame elevation. Carry it into
    # the site frame through the pinned axes, so the blocks sit where the client placed the grids.
    DEPTH = {'A': 3.0, 'B': 3.0, 'C': 3.65}
    cuts = []
    gp = os.path.join(GPR, 'tables', 'guillotine_packing.json')
    if os.path.exists(gp) and frames:
        G = json.load(open(gp))
        for blk, ax in frames.items():
            key = 'surface_0.5m__uncertain'
            if blk not in G or key not in G[blk]:
                continue
            o = np.array(ax['origin'], float)
            ux = np.array(ax['ux'], float)
            uy = np.array(ax['uy'], float)
            for bx in G[blk][key]['boxes']:
                c = []
                for X, Y in ((bx['x0'], bx['y0']), (bx['x1'], bx['y0']),
                             (bx['x1'], bx['y1']), (bx['x0'], bx['y1'])):
                    q = o + X * ux + Y * uy
                    c.append([round(float(q[0]), 3), round(float(q[1]), 3)])
                cuts.append(dict(block=blk, foot=c,
                                 z0=round(float(ax['z'] + bx['z0']), 3),
                                 z1=round(float(ax['z'] + bx['z_top_usable']), 3),
                                 cls=bx.get('cls', 'small_block'),
                                 t=round(float(bx.get('t', 0)), 1),
                                 m3=round(float(bx.get('vol_m3', 0)), 2),
                                 seq=int(bx.get('remove_seq', 0))))
    for bn in benches:
        ax = frames.get(bn['block'])
        bn['depth_m'] = DEPTH.get(bn['block'], 3.0)
        if ax:
            bn['bench_z'] = round(float(ax['z']), 3)

    data['cuts'] = cuts
    data['surfaces'] = data_extra['surfaces']
    data['cut_scenario'] = 'straight-cut plan, chalked cracks assumed to reach 0.5 m, uncertainty-safe clearance'
    js = json.dumps(data, separators=(',', ':'))
    open(os.path.join(OUT, OUT_JSON), 'w').write(js)
    print('payload %.1f MB  (extent %.1f x %.1f x %.1f m)' % (len(js) / 1e6, *(hi - lo)))
