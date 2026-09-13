"""Absolute orientation of the site model, by matching its plan view to the client's satellite view.

The photographs fix where the camera looked inside each grid, but nothing in the photogrammetry is
georeferenced, so the chain to a compass direction has always rested on reading the satellite image.
The Block C model covers the whole pit, 49 by 48 m with 21 m of relief, so its plan view can be laid
beside the satellite view and compared directly. That is the one absolute reference available
without going to site.

This renders the site model from above as a shaded elevation map at several rotations, so the pit
outline, the ramp and the benches can be matched against the satellite picture by eye. It measures
the pit's long axis in the model frame, which the satellite shows running east to west, and it finds
the haul ramp as the sloping ground that climbs from the floor to the rim, which the satellite puts
at the east end on the north side. Those two together fix north in the model frame.
"""
import numpy as np, os, json
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter

OUT = 'D:/code_ws/outputs/2026-09-11/joint_mapping'
PX = 0.25


def raster(P, px=PX):
    x0, y0 = P[:, 0].min(), P[:, 1].min()
    W = int((P[:, 0].max() - x0) / px) + 1
    H = int((P[:, 1].max() - y0) / px) + 1
    ix = np.clip(((P[:, 0] - x0) / px).astype(int), 0, W - 1)
    iy = np.clip(((P[:, 1] - y0) / px).astype(int), 0, H - 1)
    f = iy * W + ix
    top = np.full(W * H, -1e9)
    np.maximum.at(top, f, P[:, 2])
    cnt = np.bincount(f, minlength=W * H)
    top = np.where(cnt > 0, top, np.nan).reshape(H, W)
    return top, x0, y0, W, H


def hillshade(Z, px=PX, az=315.0, alt=45.0):
    Zf = np.where(np.isfinite(Z), Z, np.nanmedian(Z))
    Zf = gaussian_filter(Zf, 1.2)
    gy, gx = np.gradient(Zf, px, px)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    a = np.radians(az); z = np.radians(90 - alt)
    hs = np.cos(z) * np.cos(slope) + np.sin(z) * np.sin(slope) * np.cos(a - aspect)
    return np.where(np.isfinite(Z), hs, np.nan)


if __name__ == '__main__':
    z = np.load(os.path.join(OUT, 'cache', 'mesh_C.npz'))
    P = z['xyz'].astype(np.float64)
    Z, x0, y0, W, H = raster(P)
    print('site raster %d x %d at %.2f m, elevation %.1f to %.1f m' % (W, H, PX, np.nanmin(Z), np.nanmax(Z)))

    # the pit floor: the lowest fifth of the elevation range, as a plan-view mask
    lo = np.nanpercentile(Z, 3); hi = np.nanpercentile(Z, 97)
    floor = np.isfinite(Z) & (Z < lo + 0.25 * (hi - lo))
    yy, xx = np.nonzero(floor)
    pts = np.c_[x0 + xx * PX, y0 + yy * PX]
    c = pts.mean(0)
    u, s, vt = np.linalg.svd(pts - c, full_matrices=False)
    long_axis = vt[0]
    ratio = s[0] / s[1]
    brg = np.degrees(np.arctan2(long_axis[0], long_axis[1])) % 180
    print('pit floor: %d cells, long axis along grid bearing %.1f deg (0 = +y, 90 = +x), elongation %.2f'
          % (floor.sum(), brg, ratio))

    # the ramp: ground that is both well above the floor and still sloping, near the rim
    Zf = np.where(np.isfinite(Z), Z, np.nan)
    gy, gx = np.gradient(gaussian_filter(np.where(np.isfinite(Z), Z, np.nanmedian(Z)), 3), PX, PX)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    mid = np.isfinite(Z) & (Z > lo + 0.25 * (hi - lo)) & (Z < lo + 0.8 * (hi - lo)) & (slope > 4) & (slope < 22)
    ry, rx = np.nonzero(mid)
    rp = np.c_[x0 + rx * PX, y0 + ry * PX]
    along = (rp - c) @ long_axis
    print('sloping mid-height ground: %d cells; its centre sits %+.1f m along the long axis from the pit centre'
          % (mid.sum(), along.mean()))

    hs = hillshade(Z)
    fig, axes = plt.subplots(1, 4, figsize=(19, 5.4))
    for ax, rot in zip(axes, (0, 90, 180, 270)):
        im = np.rot90(hs, k=rot // 90)
        ax.imshow(im, cmap='gray', origin='lower')
        ax.set_title('site model plan, rotated %d deg' % rot, fontsize=10)
        ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle('Block C model seen from above (shaded relief). Compare the pit outline, the haul ramp and the '
                 'bench positions with the satellite view, which is north up.', fontsize=11)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'figs', 'PLAN_site.png'), dpi=120)
    json.dump(dict(raster_px_m=PX, w=W, h=H, floor_cells=int(floor.sum()),
                   long_axis_grid_bearing_deg=round(float(brg), 1), elongation=round(float(ratio), 2),
                   ramp_offset_along_long_axis_m=round(float(along.mean()), 1),
                   note='grid bearing 0 = +y, 90 = +x in Block C frame'),
              open(os.path.join(OUT, 'tables', 'plan_site.json'), 'w'), indent=1)
    print('wrote figs/PLAN_site.png')
