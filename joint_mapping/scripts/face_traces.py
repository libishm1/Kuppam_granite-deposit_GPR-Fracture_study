"""Fracture traces on the big exposed faces of a quarry model, read from the photographic colour
and from the relief, at full mesh resolution.

The facet extractor finds planes, and in a working quarry the biggest planes are wire-sawn walls,
not joints. That is useful: a sawn wall is a clean canvas, and a fracture that cuts it shows as a
dark line in the photo texture and often as a shallow groove in the surface. So each large face is
turned into an ortho image and a relief image, both in the plane of the face, and traces are picked
from them with a ridge filter (the same one the bench crack map uses).

Per face:
  1. take every full-resolution vertex within SLAB of the fitted plane and inside its extent
  2. rasterise mean colour and mean signed relief at PX metres per pixel
  3. fill single-pixel holes, then run a multi-scale Sato ridge filter for dark ridges on the grey
     image, and for grooves on the relief image
  4. hysteresis threshold, skeletonise, and split the skeleton into straight segments
  5. lift each segment back to 3D on the face plane

A trace on one flat face gives a line, and a line does not define a plane: the same fracture has to
be seen on a second, non-parallel face (or on the bench top) before dip and dip direction follow.
That pairing is done in traces_to_planes.py. What this script outputs is the trace geometry and its
rake within each face.

Usage: face_traces.py A|B|C [n_faces]
"""
import numpy as np, sys, os, json, time
from skimage.filters import sato, apply_hysteresis_threshold
from skimage.morphology import skeletonize, remove_small_objects, closing, disk, binary_erosion
from scipy.ndimage import gaussian_filter
from skimage.measure import label as cclabel, regionprops
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

OUT = 'D:/code_ws/outputs/2026-09-11/joint_mapping'
PX = 0.02            # m per pixel of the ortho image
SLAB = 0.15          # m, half-thickness of the slab taken around a face
MIN_FACE = 2.0       # m2, only faces this big are worth rasterising
SIG = [2, 3, 5, 8]   # ridge scales, pixels
THR_LO, THR_HI = 0.06, 0.12
MIN_TRACE_PX = 40
EROD = 4             # px, erode the data footprint before detection
DETREND = 20         # px, high-pass the relief so a curved face is not one big ridge
MIN_DIP_FACE = 40.0  # deg, a face must be this steep to count as a wall
EAST = {'A': '+x', 'B': '+y', 'C': '+y'}   # 12 Sep. Origin is the north-west corner on every bench and both axes run into the bench, but which axis runs east differs: on A the X-line numerals run down the WEST edge from A0 (client, from the site: '9, 12...' from the NW to the SW corner), so X-lines are stacked north-south and run east, +x east, +y south, left-handed. On B and C +y is east (6 m and 8 m sides, verified). See ORIENTATION.md.


def face_frame(n, c):
    n = np.asarray(n, float); n /= np.linalg.norm(n)
    a = np.array([0, 0, 1.0]) if abs(n[2]) < 0.9 else np.array([1.0, 0, 0])
    u = np.cross(a, n); u /= np.linalg.norm(u)
    v = np.cross(n, u)
    return n, u, v


def rasterise(P, C, n, c, u, v, px=PX, box=None):
    """box = (a0, a1, b0, b1) in the face frame, from the facet's own member points, so that one
    raster is one face and not every fragment of wall that happens to touch the same plane"""
    d = (P - c) @ n
    m = np.abs(d) < SLAB
    if box is not None:
        a_ = (P - c) @ u; b_ = (P - c) @ v
        m &= (a_ > box[0] - 0.1) & (a_ < box[1] + 0.1) & (b_ > box[2] - 0.1) & (b_ < box[3] + 0.1)
    if m.sum() < 500:
        return None
    Q = P[m]; col = C[m] if C is not None and len(C) else None; dd = d[m]
    a = (Q - c) @ u; b = (Q - c) @ v
    a0, a1, b0, b1 = a.min(), a.max(), b.min(), b.max()
    W = int(np.ceil((a1 - a0) / px)) + 1; H = int(np.ceil((b1 - b0) / px)) + 1
    if W < 40 or H < 40 or W * H > 8e6:
        return None
    ia = np.clip(((a - a0) / px).astype(int), 0, W - 1)
    ib = np.clip(((b - b0) / px).astype(int), 0, H - 1)
    flat = ib * W + ia
    cnt = np.bincount(flat, minlength=W * H).astype(np.float32)
    rel = np.bincount(flat, weights=dd, minlength=W * H)
    grey = None
    if col is not None:
        g = col.astype(np.float32).mean(1)
        grey = (np.bincount(flat, weights=g, minlength=W * H) / np.maximum(cnt, 1)).reshape(H, W)
    rel = (rel / np.maximum(cnt, 1)).reshape(H, W)
    cnt = cnt.reshape(H, W)
    return dict(grey=grey, rel=rel, cnt=cnt, a0=float(a0), b0=float(b0), W=W, H=H, px=px,
                fill=float((cnt > 0).mean()), n_pts=int(m.sum()))


def fill_holes(img, valid):
    out = img.copy()
    bad = ~valid
    if bad.any():
        from scipy.ndimage import distance_transform_edt
        _, (iy, ix) = distance_transform_edt(bad, return_indices=True)
        out[bad] = img[iy[bad], ix[bad]]
    return out


def ridges(img, valid, detrend=0):
    """ridge response inside the data footprint only; the footprint is eroded first so that the
    edge of the reconstruction is not itself picked up as a fracture"""
    g = fill_holes(img, valid)
    if detrend:
        g = g - gaussian_filter(g, detrend)
    g = (g - np.nanmin(g)) / max(np.nanmax(g) - np.nanmin(g), 1e-9)
    R = np.stack([sato(g, sigmas=[s], black_ridges=True) for s in SIG]).max(0)
    R = R / max(R.max(), 1e-9)
    solid = closing(valid, disk(EROD + 2))                 # close the speckle of a photogrammetric surface
    ve = binary_erosion(solid, disk(EROD)) & closing(valid, disk(2))
    M = apply_hysteresis_threshold(R, THR_LO, THR_HI) & ve
    M = closing(M, disk(1)) & ve
    M = remove_small_objects(M, MIN_TRACE_PX)
    return skeletonize(M), R, ve


def segments(sk, valid, min_px=MIN_TRACE_PX, min_lin=0.82):
    """split the skeleton into connected pieces and keep the ones that are close to straight"""
    out = []
    L = cclabel(sk, connectivity=2)
    for rp in regionprops(L):
        if rp.area < min_px:
            continue
        yx = rp.coords.astype(float)
        c = yx.mean(0)
        u_, s_, vt = np.linalg.svd(yx - c, full_matrices=False)
        lin = s_[0] / max(np.sqrt((s_ ** 2).sum()), 1e-9)
        if lin < min_lin:
            continue
        t = (yx - c) @ vt[0]
        p0 = c + vt[0] * t.min(); p1 = c + vt[0] * t.max()
        k = max(int(np.linalg.norm(p1 - p0)), 2)
        yy = np.linspace(p0[0], p1[0], k).astype(int); xx = np.linspace(p0[1], p1[1], k).astype(int)
        yy = np.clip(yy, 0, valid.shape[0] - 1); xx = np.clip(xx, 0, valid.shape[1] - 1)
        if valid[yy, xx].mean() < 0.85:            # the straight fit must stay on real data
            continue
        out.append(dict(p0=p0, p1=p1, npx=int(rp.area), lin=float(lin),
                        rms_px=float(np.sqrt(np.mean(((yx - c) @ vt[1]) ** 2)))))
    return out


if __name__ == '__main__':
    blk = sys.argv[1].upper(); NF = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    t0 = time.time()
    D = json.load(open(os.path.join(OUT, 'tables', 'facets_%s.json' % blk)))
    walls_only = '--walls' in sys.argv
    big = [p for p in D['patches'] if p['area_m2'] >= MIN_FACE and (p['dip_deg'] >= MIN_DIP_FACE or not walls_only)]
    big.sort(key=lambda p: -p['area_m2'])
    big = big[:NF]
    z = np.load(os.path.join(OUT, 'cache', 'mesh_%s.npz' % blk))
    P = z['xyz'].astype(np.float32); C = z['rgb']
    fc = np.load(os.path.join(OUT, 'cache', 'facets_%s.npz' % blk))
    FX = fc['xyz'].astype(np.float64); FL = fc['lab']
    print('Block %s: %d faces over %.1f m2, full mesh %d points' % (blk, len(big), MIN_FACE, len(P)), flush=True)
    faces = []
    for fi, p in enumerate(big):
        n, u, v = face_frame(p['normal'], p['centre'])
        c = np.asarray(p['centre'], float)
        own = FX[FL == p['patch']]
        if len(own) < 20:
            print('  face %2d skipped (patch not in cache)' % fi, flush=True); continue
        oa = (own - c) @ u; ob = (own - c) @ v
        box = (oa.min(), oa.max(), ob.min(), ob.max())
        R = rasterise(P, C, n, c, u, v, box=box)
        if R is None:
            print('  face %2d skipped (too few points or too big)' % fi, flush=True)
            continue
        valid = R['cnt'] > 0
        segs_c, segs_r = [], []
        if R['grey'] is not None:
            sk, resp, ve = ridges(R['grey'], valid)
            segs_c = segments(sk, ve)
        skr, respr, ve = ridges(-R['rel'], valid, detrend=DETREND)
        segs_r = segments(skr, ve)
        rows = []
        for src, ss in (('colour', segs_c), ('relief', segs_r)):
            for s in ss:
                a0b = np.array([R['a0'] + s['p0'][1] * PX, R['b0'] + s['p0'][0] * PX])
                a1b = np.array([R['a0'] + s['p1'][1] * PX, R['b0'] + s['p1'][0] * PX])
                X0 = c + u * a0b[0] + v * a0b[1]
                X1 = c + u * a1b[0] + v * a1b[1]
                L = float(np.linalg.norm(X1 - X0))
                if L < 0.3:
                    continue
                rows.append(dict(source=src, length_m=round(L, 2), npx=s['npx'], straightness=round(s['lin'], 3),
                                 rms_m=round(s['rms_px'] * PX, 3),
                                 p0=[round(float(x), 3) for x in X0], p1=[round(float(x), 3) for x in X1]))
        faces.append(dict(face=fi, area_m2=p['area_m2'], dip_deg=p['dip_deg'],
                          dip_dir_azimuth_deg=p['dip_dir_azimuth_deg'], centre=p['centre'], normal=p['normal'],
                          raster=dict(W=R['W'], H=R['H'], px=PX, fill=round(R['fill'], 3), n_points=R['n_pts']),
                          n_traces=len(rows), traces=rows))
        print('  face %2d  %5.1f m2  dip %4.1f az %5.1f  raster %dx%d fill %.0f%%  traces %d'
              % (fi, p['area_m2'], p['dip_deg'], p['dip_dir_azimuth_deg'], R['W'], R['H'], 100 * R['fill'], len(rows)), flush=True)
        if fi < 6:
            fig, axes = plt.subplots(1, 3, figsize=(16, 5.2))
            axes[0].imshow(R['grey'] if R['grey'] is not None else R['rel'], cmap='gray', origin='lower')
            axes[0].set_title('photographic colour', fontsize=9)
            axes[1].imshow(R['rel'], cmap='RdBu', origin='lower', vmin=-0.05, vmax=0.05)
            axes[1].set_title('relief about the face plane, +/- 5 cm', fontsize=9)
            axes[2].imshow(R['grey'] if R['grey'] is not None else R['rel'], cmap='gray', origin='lower')
            for s in segs_c:
                axes[2].plot([s['p0'][1], s['p1'][1]], [s['p0'][0], s['p1'][0]], '-', color='#C8452B', lw=1.4)
            for s in segs_r:
                axes[2].plot([s['p0'][1], s['p1'][1]], [s['p0'][0], s['p1'][0]], '-', color='#1F8A80', lw=1.4)
            axes[2].set_title('traces: red from colour, teal from relief', fontsize=9)
            for ax in axes:
                ax.set_xticks([]); ax.set_yticks([])
            fig.suptitle('Block %s face %d: %.1f m2, dip %.0f deg toward azimuth %.0f, %.0f cm per pixel'
                         % (blk, fi, p['area_m2'], p['dip_deg'], p['dip_dir_azimuth_deg'], PX * 100), fontsize=10)
            fig.tight_layout()
            fig.savefig(os.path.join(OUT, 'figs', 'FACE_%s_%02d.png' % (blk, fi)), dpi=110)
            plt.close(fig)
    json.dump(dict(block=blk, px_m=PX, slab_m=SLAB, sigmas_px=SIG, thr=[THR_LO, THR_HI],
                   note='a trace on a single flat face fixes a line, not a plane; pairing across faces is done in traces_to_planes.py',
                   faces=faces), open(os.path.join(OUT, 'tables', 'traces_%s.json' % blk), 'w'), indent=1)
    print('  wrote tables/traces_%s.json  [%.0f s]' % (blk, time.time() - t0), flush=True)
