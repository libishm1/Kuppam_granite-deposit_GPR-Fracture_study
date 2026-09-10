"""Digitise the crew's field sketches: the dashed strokes are the surface fractures they saw, drawn
on the numbered survey grid, so they are in the report frame already. The hand-drawn grid nodes
are the control points; a piecewise-linear map takes sketch pixels to report (x, y) in cm.
usage: sketch_digitise.py [A B C]"""
import numpy as np, os, sys, csv, json, fitz
from PIL import Image
from skimage.morphology import binary_opening, binary_dilation, binary_closing, skeletonize, remove_small_objects, disk, footprint_rectangle
from skimage import measure
from scipy.interpolate import LinearNDInterpolator
from scipy.spatial import ConvexHull, Delaunay
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'; RAW = r'D:/code_ws/reference/parsans/report/raw/GPR Raw data_Kuppam'
# sketch geometry: which family is drawn horizontal on the page, its line numbers bottom->top or top->bottom, etc.
# From the sketches read earlier. 'h' = lines drawn horizontally on the page, 'v' = vertically.
CFG = {
 'A': dict(pdf='A Block/A Block sketch.pdf', nh=12, nv=12, W=550, H=550,
           # horizontal lines are 13..24 numbered TOP->bottom, at report x = (n-13)*50; vertical lines are 1..12 LEFT->right at report y = (n-1)*50
           h_top_to_bottom=True, h_coord='x', h_first=0, v_left_to_right=True, v_coord='y', v_first=0),
 'B': dict(pdf='B Block/B Block sketch.pdf', nh=13, nv=20, W=950, H=600,
           # horizontal 1..13 BOTTOM->top at report y = (n-1)*50; vertical 14..33 left->right at report x = (n-14)*50
           h_top_to_bottom=False, h_coord='y', h_first=0, v_left_to_right=True, v_coord='x', v_first=0),
 'C': dict(pdf='C Block/C Block Sketch.pdf', nh=17, nv=15, W=700, H=800,
           h_top_to_bottom=False, h_coord='y', h_first=0, v_left_to_right=True, v_coord='x', v_first=0),
}
blocks = sys.argv[1:] or ['A', 'B', 'C']


def render(pdf, dpi=220):
    d = fitz.open(pdf); pm = d[0].get_pixmap(dpi=dpi)
    im = Image.frombytes('RGB', (pm.width, pm.height), pm.samples); return np.asarray(im).astype(np.float32) / 255.0


def line_family(ink, horizontal, L):
    fp = footprint_rectangle((1, L)) if horizontal else footprint_rectangle((L, 1))
    m = binary_opening(ink, fp)
    # tolerate small slant: union of openings on slightly sheared copies
    for sh in (-3, 3):
        sk = np.zeros_like(ink)
        H_, W_ = ink.shape
        if horizontal:
            for i in range(H_):  # shear rows by sh px per 300 px of width
                pass
    return m


def clean_components(mask, minlen):
    lab = measure.label(mask, connectivity=2); out = np.zeros_like(mask)
    for p in measure.regionprops(lab):
        if p.major_axis_length >= minlen: out[lab == p.label] = True
    return out


for blk in blocks:
    cfg = CFG[blk]; img = render(os.path.join(RAW, cfg['pdf']))
    Hp, Wp = img.shape[:2]
    R, G, B = img[..., 0], img[..., 1], img[..., 2]
    v = img.max(2); s = (img.max(2) - img.min(2)) / (img.max(2) + 1e-6)
    ink = (v < 0.62) | ((B > R + 0.12) & (s > 0.25) & (v < 0.9))          # dark or blue pen
    ink[int(0.955 * Hp):, :] = False                                      # scanner watermark
    ink = remove_small_objects(ink, 12)
    # ---- the drawn lattice is ONE connected component after a short opening; dashes and text fall out. ----
    ink[int(0.90 * Hp):, :] &= ~(img[int(0.90 * Hp):, :].max(2) < 0.25)     # scanner shadow along the bottom is not ink
    L = 24
    hraw = binary_opening(ink, footprint_rectangle((1, L))); vraw = binary_opening(ink, footprint_rectangle((L, 1)))
    lat = binary_closing(hraw | vraw, disk(3))
    lab = measure.label(lat, connectivity=2); sizes = np.bincount(lab.ravel()); sizes[0] = 0
    lattice = lab == sizes.argmax()
    print('Block %s: lattice component %d px of %d opened px (%.0f%%)' % (blk, lattice.sum(), lat.sum(), 100 * lattice.sum() / max(lat.sum(), 1)))
    # separate the two families INSIDE the lattice and label each line by clustering perpendicular position
    hm_ = binary_opening(lattice, footprint_rectangle((1, L))); vm_ = binary_opening(lattice, footprint_rectangle((L, 1)))
    def lines_of(fam, axis, n):
        """cluster family pixels into n lines by their perpendicular coordinate, walking along the other axis to follow wobble"""
        lab_ = measure.label(fam, connectivity=2); props = measure.regionprops(lab_)
        props = [p for p in props if (p.bbox[3] - p.bbox[1] if axis == 0 else p.bbox[2] - p.bbox[0]) > 0.04 * (Wp if axis == 0 else Hp)]
        vals = np.array([p.centroid[axis] for p in props]); order = np.argsort(vals); props = [props[k] for k in order]; vals = vals[order]
        # one-dimensional clustering into n groups by largest gaps
        if len(vals) <= n: groups = [[p] for p in props]
        else:
            gaps = np.diff(vals); cut = np.sort(np.argsort(-gaps)[:n - 1]); groups = []; s0 = 0
            for c_ in list(cut) + [len(props) - 1]:
                groups.append(props[s0:c_ + 1]); s0 = c_ + 1
        return groups
    hg = lines_of(hm_, 0, cfg['nh']); vg = lines_of(vm_, 1, cfg['nv'])
    print('   %d horizontal lines (expect %d), %d vertical (expect %d)' % (len(hg), cfg['nh'], len(vg), cfg['nv']))
    hidx = np.zeros(ink.shape, int); vidx = np.zeros(ink.shape, int)
    hl = measure.label(hm_, connectivity=2); vl = measure.label(vm_, connectivity=2)
    for i, g in enumerate(hg):
        for p in g: hidx[hl == p.label] = i + 1
    for j, g in enumerate(vg):
        for p in g: vidx[vl == p.label] = j + 1
    hidx_d = np.zeros_like(hidx); vidx_d = np.zeros_like(vidx)
    for k in range(1, len(hg) + 1): hidx_d[binary_dilation(hidx == k, disk(7))] = k
    for k in range(1, len(vg) + 1): vidx_d[binary_dilation(vidx == k, disk(7))] = k
    nodes = []
    for i in range(1, len(hg) + 1):
        for j in range(1, len(vg) + 1):
            m = (hidx_d == i) & (vidx_d == j)
            if m.sum() < 4: continue
            yy, xx = np.nonzero(m); nodes.append((xx.mean(), yy.mean(), i, j))
    hm = lattice; vm = np.zeros_like(lattice)
    print('   %d of %d nodes found by intersection' % (len(nodes), len(hg) * len(vg)))
    nodes = np.array(nodes)
    from scipy.ndimage import distance_transform_edt as _edt
    _d2i = _edt(~ink); _nd = _d2i[np.clip(nodes[:, 1].astype(int), 0, Hp - 1), np.clip(nodes[:, 0].astype(int), 0, Wp - 1)]
    print('   node-to-ink distance: median %.1f px, p90 %.1f px  (%s)' % (np.median(_nd), np.percentile(_nd, 90), 'nodes sit ON the drawn lines' if np.median(_nd) < 4 else 'WARNING nodes are off the lines'))
    gmask = binary_dilation(lattice, disk(5))
    hm = gmask; vm = np.zeros_like(hm)
    # report coordinates of node (i, j): horizontal line i (1 = top) and vertical line j (1 = left)
    def report_xy(i, j):
        hi_ = (i - 1) if cfg['h_top_to_bottom'] else (len(hg) - i)
        vj_ = (j - 1) if cfg['v_left_to_right'] else (len(vg) - j)
        h_val = cfg['h_first'] + hi_ * 50.0; v_val = cfg['v_first'] + vj_ * 50.0
        return (v_val, h_val) if cfg['h_coord'] == 'y' else (h_val, v_val)      # returns (x, y)
    # dedupe nodes per (i, j) by averaging
    from collections import defaultdict
    acc = defaultdict(list)
    for px, py, i, j in nodes: acc[(int(i), int(j))].append((px, py))
    P = []; Q = []
    for (i, j), lst in acc.items():
        px, py = np.mean(lst, axis=0); x, y = report_xy(i, j); P.append((px, py)); Q.append((x, y))
    P = np.array(P); Q = np.array(Q)
    print('   %d grid nodes resolved of %d' % (len(P), cfg['nh'] * cfg['nv']))
    fx = LinearNDInterpolator(P, Q[:, 0]); fy = LinearNDInterpolator(P, Q[:, 1])
    # global affine fallback for points just outside the hull
    A_ = np.c_[P, np.ones(len(P))]; ax_, *_ = np.linalg.lstsq(A_, Q[:, 0], rcond=None); ay_, *_ = np.linalg.lstsq(A_, Q[:, 1], rcond=None)
    resid = np.hypot(A_ @ ax_ - Q[:, 0], A_ @ ay_ - Q[:, 1])
    print('   affine residual of the hand-drawn grid: median %.1f cm, max %.1f cm  (this is how wobbly the sketch is)' % (np.median(resid), resid.max()))
    def to_report(px, py):
        x = fx(px, py); y = fy(px, py); m = np.isnan(x)
        if m.any(): x[m] = np.c_[px[m], py[m], np.ones(m.sum())] @ ax_; y[m] = np.c_[px[m], py[m], np.ones(m.sum())] @ ay_
        return x, y
    # ---- dashed strokes: ink minus grid lines, inside the grid, elongated ----
    dash = ink & ~hm
    dash = remove_small_objects(dash, 20)
    hull = ConvexHull(P); tri = Delaunay(P[hull.vertices])
    # keep every dash fragment inside the node hull (the lattice cut them at every crossing, so they are short); filter AFTER linking
    # pixelwise hull (dilated a fifth of a cell so dashes running just past the edge survive); no centroid test
    YY, XX = np.mgrid[0:Hp, 0:Wp]
    hullpx = (tri.find_simplex(np.c_[XX.ravel(), YY.ravel()]) >= 0).reshape(Hp, Wp)
    pitch_est = 0.75 * min(Hp, Wp) / max(cfg['nh'], cfg['nv'])
    hullpx = binary_dilation(hullpx, disk(int(0.2 * pitch_est)))
    keep = remove_small_objects(dash & hullpx, 8)
    # link dashes of the same trace: close along, then skeletonise. Closing radius = a typical dash gap (about a fifth of a cell)
    pitch_px = 0.5 * (np.median(np.diff(sorted(np.mean([q.centroid[0] for q in g]) for g in hg))) + np.median(np.diff(sorted(np.mean([q.centroid[1] for q in g]) for g in vg))))
    # measured on A: dash gap p50 37 px, p75 58 px at 220 dpi. Close with 40 px, then thin: the skeleton of a closed
    # blob is a tree; the skeleton of the closed mask AND-ed back to a dilated version of the strokes is a line.
    from skimage.morphology import binary_erosion
    linked = binary_closing(keep, disk(40))
    linked = linked & binary_dilation(keep, disk(14))           # keep only the closed region near actual ink: bridges, not blobs
    sk = skeletonize(linked)
    # ---- walk the skeleton into polylines: split at junctions, follow from endpoint to endpoint ----
    from scipy.ndimage import convolve
    nb = convolve(sk.astype(int), np.ones((3, 3), int), mode='constant') - sk.astype(int)
    # bridge the gaps the lattice mask cut into the dashes: close along, re-skeletonise, then walk each component
    # everything outside the node hull is text, numerals, shadow: drop before walking
    hullmask = np.zeros_like(sk); YY, XX = np.mgrid[0:Hp, 0:Wp]
    inside = tri.find_simplex(np.c_[XX.ravel(), YY.ravel()]) >= 0; hullmask = inside.reshape(Hp, Wp)
    hullmask = binary_dilation(hullmask, disk(int(0.15 * pitch_px)))
    sk = sk & hullmask
    sl = measure.label(sk, connectivity=2)
    traces = []
    for p in measure.regionprops(sl):
        if p.area < 6: continue
        pix = set(map(tuple, p.coords)); ys, xs = p.coords.T
        deg = {}
        for (y, x) in pix:
            deg[(y, x)] = sum(((y + dy, x + dx) in pix) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0))
        ends = sorted([q for q, d_ in deg.items() if d_ <= 1])
        unvisited = set(pix)
        while len(unvisited) >= 6:
            cand = [q for q in ends if q in unvisited]
            start = cand[0] if cand else min(unvisited)
            path = [start]; unvisited.discard(start); cur = start; prev_dir = None
            while True:
                nxt = [(cur[0] + dy, cur[1] + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0)]
                nxt = [q for q in nxt if q in unvisited]
                if not nxt: break
                if prev_dir is not None and len(nxt) > 1:
                    nxt.sort(key=lambda q: -((q[0] - cur[0]) * prev_dir[0] + (q[1] - cur[1]) * prev_dir[1]))   # straightest
                else:
                    nxt.sort(key=lambda q: abs(q[0] - cur[0]) + abs(q[1] - cur[1]))
                n_ = nxt[0]
                if len(path) >= 8:
                    a_ = np.array(path[-8]); v1 = np.array(cur) - a_; v2 = np.array(n_) - np.array(cur)
                    if np.linalg.norm(v1) > 0 and (v1 @ v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)) < -0.85: break   # only a true reversal, not a dash kink
                prev_dir = (n_[0] - cur[0], n_[1] - cur[1]); cur = n_; path.append(cur); unvisited.discard(cur)
            if len(path) < 6: continue
            yy = np.array([q[0] for q in path], float); xx = np.array([q[1] for q in path], float)
            xr, yr = to_report(xx, yy); pts = np.c_[xr, yr]
            keep_i = [0]
            for k in range(1, len(pts)):
                if np.hypot(*(pts[k] - pts[keep_i[-1]])) >= 5.0: keep_i.append(k)
            if keep_i[-1] != len(pts) - 1: keep_i.append(len(pts) - 1)
            pts = pts[keep_i]
            if len(pts) < 2: continue
            Lm = np.sum(np.hypot(*np.diff(pts, axis=0).T)) / 100.0
            if Lm < 0.10: continue
            traces.append(dict(id=len(traces) + 1, length_m=round(Lm, 2), n=len(pts), pts=pts))
    traces.sort(key=lambda d: -d['length_m'])
    print('   %d sketch traces, total %.1f m, longest %s' % (len(traces), sum(t['length_m'] for t in traces), ', '.join('%.1f' % t['length_m'] for t in traces[:6])))
    with open(os.path.join(OUT, 'tables', 'sketch_traces_%s.csv' % blk), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['trace_id', 'vertex', 'x_cm', 'y_cm'])
        for t in traces:
            for k, (x, y) in enumerate(t['pts']): w.writerow([t['id'], k, '%.1f' % x, '%.1f' % y])
    json.dump(dict(nodes=[[float(a), float(b), float(c), float(d)] for (a, b), (c, d) in zip(P, Q)], affine_resid_med_cm=float(np.median(resid))),
              open(os.path.join(OUT, 'tables', 'sketch_grid_%s.json' % blk), 'w'))
    # ---- figure ----
    fig, ax = plt.subplots(1, 2, figsize=(15, 8), constrained_layout=True)
    ax[0].imshow(img); ax[0].plot(P[:, 0], P[:, 1], 'g.', ms=4)
    yy, xx = np.nonzero(sk); ax[0].plot(xx, yy, 'r.', ms=1)
    ax[0].set_title('Block %s sketch: grid nodes (green) and digitised dashed strokes (red)' % blk, fontsize=9); ax[0].axis('off')
    for t in traces: ax[1].plot(t['pts'][:, 0], t['pts'][:, 1], '-', lw=1.5)
    for k in range(0, cfg['W'] + 1, 50): ax[1].axvline(k, color='0.85', lw=.4)
    for k in range(0, cfg['H'] + 1, 50): ax[1].axhline(k, color='0.85', lw=.4)
    ax[1].set_xlim(-60, cfg['W'] + 60); ax[1].set_ylim(-60, cfg['H'] + 60); ax[1].set_aspect('equal')
    ax[1].set_xlabel('report x (cm)'); ax[1].set_ylabel('report y (cm)'); ax[1].set_title('sketch traces in the report frame, %d traces' % len(traces), fontsize=9)
    fig.savefig(os.path.join(OUT, 'figs', 'SKETCH_TRACES_%s.png' % blk), dpi=110); plt.close(fig)
    print('   wrote figs/SKETCH_TRACES_%s.png, tables/sketch_traces_%s.csv' % (blk, blk))
