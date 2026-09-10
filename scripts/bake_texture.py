"""Bake each block's bench colour, from the full mesh vertex colours, into an image in the report frame
(x, y in cm over the grid, 1 cm per pixel) for draping on the DEM mesh in the interface."""
import numpy as np, json, os, sys, time
from scipy.ndimage import binary_dilation, distance_transform_edt
from PIL import Image
SITE = r'D:/code_ws/reference/parsans/site'; OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
REG = json.load(open(os.path.join(OUT, 'tables', 'registration.json')))
MESH = {'A': ('block a.obj', 1), 'B': ('block b.obj', 1), 'C': ('block c.obj', 2)}
DIMS = {'A': (5.5, 5.5), 'B': (9.5, 6.0), 'C': (7.0, 8.0)}
PX = 0.01; PAD = 0.5
os.makedirs(os.path.join(OUT, 'web', 'tex'), exist_ok=True)
for blk in (sys.argv[1:] or 'ABC'):
    r = REG[blk]; R = np.array(r['plane_R']); c = np.array(r['plane_c']); sc = r['scale_m_per_unit']
    corner = np.array(r['origin_local_units']) * sc; xd = np.array(r['xdir_local']); yd = np.array(r['ydir_local'])
    W, H = DIMS[blk]; nx, ny = int((W + 2 * PAD) / PX), int((H + 2 * PAD) / PX)
    acc = np.zeros((ny, nx, 3)); cnt = np.zeros((ny, nx)); n = 0; t0 = time.time()
    M = np.array([xd, yd])                                  # rows: report axes in local coords (orthonormal for A, C; near for B)
    Minv = np.linalg.inv(M.T)
    def flush(buf):
        a = np.array(b' '.join(buf).split(), dtype=float).reshape(-1, 6)
        L = ((a[:, :3] - c) @ R.T) * sc
        keep = np.abs(L[:, 2]) < 0.6
        L = L[keep]; col = a[keep, 3:6]
        g = (L[:, :2] - corner) @ Minv.T                    # report frame metres
        ix = ((g[:, 0] + PAD) / PX).astype(int); iy = ((g[:, 1] + PAD) / PX).astype(int)
        m = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
        np.add.at(acc, (iy[m], ix[m]), col[m]); np.add.at(cnt, (iy[m], ix[m]), 1)
    with open(os.path.join(SITE, MESH[blk][0]), 'rb') as f:
        buf = []
        for ln in f:
            if ln[:2] != b'v ': continue
            n += 1
            if n % MESH[blk][1]: continue
            buf.append(ln[2:].strip())
            if len(buf) >= 1_000_000: flush(buf); buf = []
        if buf: flush(buf)
    img = acc / np.maximum(cnt, 1)[..., None]; has = cnt > 0
    # fill holes from the nearest filled pixel (small gaps only; large gaps stay dark)
    if (~has).any():
        d, (jj, ii) = distance_transform_edt(~has, return_indices=True)
        fill = (~has) & (d <= 6); img[fill] = img[jj[fill], ii[fill]]; has |= fill
    img[~has] = 0.08
    # display stretch: the sawn, dusty bench top photographs pale; stretch luminance p1..p99 to 0.06..0.94 so
    # paint and cracks read. Hue is untouched. This is legibility, not the rock's colour.
    lum = img @ np.array([0.299, 0.587, 0.114]); lo, hi = np.percentile(lum[has], [1, 99])
    gain = np.clip((lum - lo) / max(hi - lo, 1e-6) * 0.88 + 0.06, 0.02, 1.0) / np.maximum(lum, 1e-6)
    img = np.clip(img * gain[..., None], 0, 1); img[~has] = 0.08
    im = Image.fromarray(np.clip(img * 255, 0, 255).astype(np.uint8))
    p = os.path.join(OUT, 'web', 'tex', 'bench_%s.jpg' % blk); im.save(p, quality=82)
    print('Block %s: %d vertices streamed, %.0f%% of pixels covered, texture %dx%d px, %.0f kB, %.0f s' % (blk, n, 100 * has.mean(), nx, ny, os.path.getsize(p) / 1e3, time.time() - t0))
json.dump(dict(px_m=PX, pad_m=PAD), open(os.path.join(OUT, 'web', 'tex', 'meta.json'), 'w'))
