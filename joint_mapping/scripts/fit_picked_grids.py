"""Fit each surveyed grid rectangle onto the corners picked by hand in the site model.

The corners were clicked on the rock in the viewer, starting at each block's painted origin mark and
going round the edge. The surveyed grid sizes are fixed (A 5.5 x 5.5, B 9.5 x 6.0, C 7.0 x 8.0 m),
so the fit is rigid: rotation about the vertical and translation only, no scaling and no shear, and
the first corner picked is held as the grid origin. That is a Kabsch fit in plan with the scale term
dropped.

The residuals are the honest output. A rigid rectangle cannot absorb a mis-click or a grid that was
painted out of square, so a large residual means the picks and the surveyed size disagree, and the
script says so rather than stretching the rectangle to hide it.
"""
import numpy as np, json, os

OUT = 'D:/code_ws/outputs/2026-09-11/joint_mapping'
GRID = {'A': (5.5, 5.5), 'B': (9.5, 6.0), 'C': (7.0, 8.0)}


def ideal_ring(W, H, first_axis):
    """corners in the block's own grid frame, starting at the origin and going round.
    first_axis 'y' means the second corner picked lies along +y (the H side)."""
    if first_axis == 'y':
        return np.array([[0, 0], [0, H], [W, H], [W, 0]], float)
    return np.array([[0, 0], [W, 0], [W, H], [0, H]], float)


def rigid_fit(src, dst):
    """rotation about vertical plus translation taking src onto dst, no scale (Kabsch in 2D)"""
    sc = src.mean(0)
    dc = dst.mean(0)
    A = src - sc
    B = dst - dc
    H = A.T @ B
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1.0, d]) @ U.T
    t = dc - R @ sc
    res = (src @ R.T + t) - dst
    return R, t, res


def run():
    picks = json.load(open(os.path.join(OUT, 'picked_corners.json')))
    out = {}
    for blk in 'ABC':
        P = np.array(picks[blk], float)
        if len(P) != 4:
            print('Block %s: %d corners, skipped' % (blk, len(P)))
            continue
        xy = P[:, :2]
        z = float(P[:, 2].mean())
        W, H = GRID[blk]
        side1 = float(np.linalg.norm(xy[1] - xy[0]))
        meas = [float(np.linalg.norm(xy[(i + 1) % 4] - xy[i])) for i in range(4)]

        best = None
        for axis in ('y', 'x'):
            ideal = ideal_ring(W, H, axis)
            R, t, res = rigid_fit(ideal, xy)
            rms = float(np.sqrt((res ** 2).sum(1).mean()))
            if best is None or rms < best[0]:
                best = (rms, axis, R, t, res, ideal)
        rms, axis, R, t, res, ideal = best

        fit = ideal @ R.T + t
        ang = float(np.degrees(np.arctan2(R[1, 0], R[0, 0])) % 360)
        first_len = H if axis == 'y' else W
        v1 = fit[1] - fit[0]
        brg_model = float(np.degrees(np.arctan2(v1[1], v1[0])) % 360)
        out[blk] = dict(
            origin_model=[round(float(fit[0][0]), 3), round(float(fit[0][1]), 3), round(z, 3)],
            corners_model=[[round(float(a), 3), round(float(b), 3), round(z, 3)] for a, b in fit],
            picked_side_lengths_m=[round(v, 2) for v in meas],
            surveyed_m=[W, H],
            first_side_is=('the %.1f m side' % first_len),
            first_side_bearing_from_model_x_deg=round(brg_model, 1),
            rotation_deg_about_vertical=round(ang, 2),
            fit_rms_m=round(rms, 3),
            corner_residuals_m=[round(float(np.linalg.norm(r)), 3) for r in res],
            bench_z_m=round(z, 3))
        print('Block %s' % blk)
        print('   picked sides      %.2f, %.2f, %.2f, %.2f m   (surveyed %.1f x %.1f)'
              % (meas[0], meas[1], meas[2], meas[3], W, H))
        print('   first side from the origin is %s, bearing %.1f deg from model +x'
              % (out[blk]['first_side_is'], brg_model))
        print('   rigid fit rms %.3f m, corner errors %s'
              % (rms, ', '.join('%.2f' % v for v in out[blk]['corner_residuals_m'])))
        if rms > 0.5:
            print('   NOTE: the picked outline and the surveyed size disagree by more than 50 cm')
    json.dump(out, open(os.path.join(OUT, 'tables', 'picked_fit.json'), 'w'), indent=1)

    if 'B' in out and 'C' in out:
        bb = out['B']['first_side_bearing_from_model_x_deg']
        print()
        print('Block C grid +x sits at %.1f deg from model +x' % out['C']['first_side_bearing_from_model_x_deg']
              if out['C']['first_side_is'].startswith('the 7') else
              'Block C first side (%s) sits at %.1f deg from model +x'
              % (out['C']['first_side_is'], out['C']['first_side_bearing_from_model_x_deg']))
        print('Block B origin-to-next-corner (%s) sits at %.1f deg from model +x'
              % (out['B']['first_side_is'], bb))
    print('wrote tables/picked_fit.json')


if __name__ == '__main__':
    run()
