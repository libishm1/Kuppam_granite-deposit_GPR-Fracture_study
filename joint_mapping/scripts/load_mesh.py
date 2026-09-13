"""Stream the Metashape OBJ vertex lines (x y z r g b) of one block, transform into that block's
bench frame (metres, z up, bench top = 0) with the transform already fitted in the GPR study
(dataset/bench_frame_m/Block_X/FRAME.json), and cache as .npz.

    L = ((P - plane_c) @ plane_R.T) * scale

Usage: load_mesh.py A|B|C [stride]"""
import numpy as np, sys, os, json, time

SITE = 'D:/code_ws/reference/parsans/site'
GPR = 'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
OUT = 'D:/code_ws/outputs/2026-09-11/joint_mapping'
OBJ = {'A': 'block a.obj', 'B': 'block b.obj', 'C': 'block c.obj'}


def stream(path, stride=1):
    xyz = []; rgb = []; k = 0; t0 = time.time()
    with open(path, 'rb') as f:
        for ln in f:
            if ln[:2] != b'v ': continue
            k += 1
            if stride > 1 and k % stride: continue
            p = ln.split()
            xyz.append((float(p[1]), float(p[2]), float(p[3])))
            if len(p) >= 7: rgb.append((float(p[4]), float(p[5]), float(p[6])))
    print('  %d of %d vertex lines in %.0f s' % (len(xyz), k, time.time() - t0))
    return np.asarray(xyz, np.float64), (np.asarray(rgb, np.float32) if rgb else None)


def frame(blk):
    F = json.load(open(os.path.join(GPR, 'dataset', 'bench_frame_m', 'Block_' + blk, 'FRAME.json')))
    return np.array(F['plane_R']), np.array(F['plane_c']), float(F['scale_m_per_mesh_unit']), F


if __name__ == '__main__':
    blk = sys.argv[1].upper(); stride = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    print('Block %s: %s (stride %d)' % (blk, OBJ[blk], stride))
    P, C = stream(os.path.join(SITE, OBJ[blk]), stride)
    R, c, s, F = frame(blk)
    L = ((P - c) @ R.T) * s
    n = np.array([0, 0, 1.0])
    print('  bench frame extent  x %.1f to %.1f   y %.1f to %.1f   z %.1f to %.1f  m'
          % (L[:, 0].min(), L[:, 0].max(), L[:, 1].min(), L[:, 1].max(), L[:, 2].min(), L[:, 2].max()))
    grid = F['grid_m']
    on = (L[:, 0] > -1) & (L[:, 0] < grid[0] + 1) & (L[:, 1] > -1) & (L[:, 1] < grid[1] + 1) & (np.abs(L[:, 2]) < 1)
    print('  %d points on or near the painted bench (%.1f %%); %d elsewhere (walls, floor, spoil)'
          % (on.sum(), 100 * on.mean(), (~on).sum()))
    np.savez_compressed(os.path.join(OUT, 'cache', 'mesh_%s.npz' % blk), xyz=L.astype(np.float32),
                        rgb=(C * 255).astype(np.uint8) if C is not None else np.zeros((0, 3), np.uint8), stride=stride, grid=grid)
    print('  cached cache/mesh_%s.npz' % blk)
