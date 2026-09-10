"""Camera poses and calibration from each Metashape chunk, to a JSON per block."""
import subprocess, re, json, os, numpy as np
SITE = r'D:/code_ws/reference/parsans/site'; OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
SZ = r'C:/Program Files/7-Zip/7z.exe'
for blk, proj in (('A', 'blocka'), ('B', 'blockb'), ('C', 'blockc')):
    x = subprocess.run([SZ, 'e', '-so', os.path.join(SITE, proj + '.files', '0', 'chunk.zip'), 'doc.xml'], capture_output=True).stdout.decode('utf-8', 'replace')
    sensors = {}
    for m in re.finditer(r'<sensor id="(\d+)"[^>]*>(.*?)</sensor>', x, re.S):
        s = m.group(2); cal = {}
        for k in ('f', 'cx', 'cy', 'k1', 'k2', 'k3', 'p1', 'p2', 'b1', 'b2'):
            mm = re.search(r'<%s>([-\d.eE+]+)</%s>' % (k, k), s); cal[k] = float(mm.group(1)) if mm else 0.0
        w = re.search(r'<resolution width="(\d+)" height="(\d+)"', s)
        cal['w'], cal['h'] = int(w.group(1)), int(w.group(2))
        sensors[m.group(1)] = cal
    cams = {}
    for m in re.finditer(r'<camera id="(\d+)" sensor_id="(\d+)"[^>]*label="([^"]+)">(.*?)</camera>', x, re.S):
        t = re.search(r'<transform>([^<]+)</transform>', m.group(4))
        if not t: continue
        T = np.array(t.group(1).split(), float).reshape(4, 4)
        cams[m.group(3)] = dict(sensor=m.group(2), T=T.tolist())
    json.dump(dict(sensors=sensors, cameras=cams), open(os.path.join(OUT, 'tables', 'cameras_%s.json' % blk), 'w'))
    print('Block %s: %d sensors, %d aligned cameras' % (blk, len(sensors), len(cams)))
    for sid, cal in sensors.items(): print('   sensor %s: %dx%d  f %.1f px  cx %.1f cy %.1f  k1 %.4f k2 %.4f' % (sid, cal['w'], cal['h'], cal['f'], cal['cx'], cal['cy'], cal['k1'], cal['k2']))
    lab = sorted(cams)[:2]; print('   e.g.', lab, 'T[:3,3] =', np.round(np.array(cams[lab[0]]['T'])[:3, 3], 2))
