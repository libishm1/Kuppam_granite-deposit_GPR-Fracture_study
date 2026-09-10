"""Every raw radargram as a small greyscale JPEG panel for the 3D interface: 89 lines x HF/LF.
Each panel is AGC'd envelope-free amplitude (grey), 2 px per trace along the line, depth axis 0 to the channel's
usable depth at v = 0.1202. Geometry per line from GEOMETRY_resolved.csv: which axis it runs along, its fixed
coordinate, its measured length. Written to web/panels/{blk}_{line}_{ch}.jpg and an index JSON."""
import sys, os, glob, csv, json, base64
sys.path.insert(0, os.path.dirname(__file__))
import segy, numpy as np
from PIL import Image
from scipy.signal import hilbert
ROOT = r'D:/code_ws/reference/parsans/report/raw/GPR Raw data_Kuppam'; OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
V = 0.1202; DX = 2.49
CH = {'HF': (0.0610352, 20.0), 'LF': (0.1220703, 66.0)}     # dt ns, time window shown (ns): HF to 1.2 m, LF to 4.0 m
os.makedirs(os.path.join(OUT, 'web', 'panels'), exist_ok=True)
geom = list(csv.DictReader(open(os.path.join(OUT, 'tables', 'GEOMETRY_resolved.csv'), encoding='utf-8')))
BLK = {'A': 'A Block', 'B': 'B Block', 'C': 'C Block'}
index = []


def agc(d, dt, w_ns=3.0):
    e = np.abs(hilbert(d, axis=1)); w = max(3, int(w_ns / dt)); k = np.ones(w) / w
    sm = np.apply_along_axis(lambda r: np.convolve(r, k, 'same'), 1, e); return d / (sm + 1e-12)


for g in geom:
    blk, ln = g['block'], int(g['line'])
    for ch, (dt, tmax) in CH.items():
        f = sorted(glob.glob(os.path.join(ROOT, BLK[blk], '**', '*new%03d_*_%s.sgy' % (ln, ch)), recursive=True))
        if not f: continue
        d = segy.read(f[0])['data']; a = agc(d, dt)[:, :int(tmax / dt)]
        cl = np.percentile(np.abs(a), 98); img = np.clip(0.5 + 0.5 * a / cl, 0, 1)
        # downsample: 2 px per trace along, 128 px in time
        n, m = img.shape; im = Image.fromarray((img.T * 255).astype(np.uint8))       # rows = time, cols = trace
        im = im.resize((max(64, n * 2 // 2), 128), Image.LANCZOS)
        p = os.path.join(OUT, 'web', 'panels', '%s_%02d_%s.jpg' % (blk, ln, ch)); im.save(p, quality=70)
        index.append(dict(block=blk, line=ln, ch=ch, orientation=g['orientation'], fixed_axis=g['fixed_axis'], fixed_cm=float(g['fixed_cm']), run_axis=g['run_axis'],
                          length_m=float(g['run_to_measured_cm']) / 100, depth_m=round(tmax * V / 2, 2), file=os.path.basename(p), kb=round(os.path.getsize(p) / 1e3, 1)))
json.dump(index, open(os.path.join(OUT, 'web', 'panels', 'index.json'), 'w'))
tot = sum(i['kb'] for i in index)
print('%d panels, %.1f MB total; HF to %.2f m, LF to %.2f m' % (len(index), tot / 1e3, CH['HF'][1] * V / 2, CH['LF'][1] * V / 2))
