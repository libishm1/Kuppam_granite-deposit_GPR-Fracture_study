"""Bundle everything the web interface needs into web/data.json, in the BENCH frame (metres, z up, right-handed,
bench plane = 0) so nothing is mirrored, plus the report-frame transform for labels. Point clouds subsampled and
base64-packed. Then inject into web/index.template.html -> web/index.html if the template exists."""
import numpy as np, json, os, csv, base64, re, glob
from scipy.interpolate import RegularGridInterpolator
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'; DS = os.path.join(OUT, 'dataset', 'bench_frame_m'); WEB = os.path.join(OUT, 'web'); os.makedirs(WEB, exist_ok=True)
REG = json.load(open(os.path.join(OUT, 'tables', 'registration.json')))
PACK = json.load(open(os.path.join(OUT, 'tables', 'block_packing.json')))
GUIL = json.load(open(os.path.join(OUT, 'tables', 'guillotine_packing.json')))
PANELS = json.load(open(os.path.join(OUT, 'web', 'panels', 'index.json')))
SPEC = json.load(open(os.path.join(OUT, 'tables', 'spectra.json')))
STRUCT = json.load(open(os.path.join(OUT, 'tables', 'structural.json')))
VER = json.load(open(os.path.join(OUT, 'tables', 'VERIFY_all.json')))
DAY = json.load(open(os.path.join(OUT, 'tables', 'sketch_vs_gpr_daylight.json')))
DIMS = {'A': (5.5, 5.5), 'B': (9.5, 6.0), 'C': (7.0, 8.0)}
FEATS = {'A': ('A1', 'A2'), 'B': ('B1', 'B2'), 'C': ('C1', 'C2')}
NPTS = {'A': 45000, 'B': 45000, 'C': 70000}
REL = {  # reliability chips, from VERIFICATION.md and the daylight test
 'A1': ('caution', 'dip corroborated on 12 lines; position vs surface cracks no better than chance'),
 'A2': ('good', 'orthogonal-line check 0.9 cm; never reaches the surface inside the grid'),
 'B1': ('good', 'corridor seeded from the report, dip corroborated not independently measured; HF vs LF 97% within 20 cm; confirmed on the rock by a 4 m sketched crack'),
 'B2': ('caution', 'one line direction only; unmigrated, up to 1.4 m plan shift at depth'),
 'C1': ('good', 'ties the report to 8 cm; 11 cm plane'),
 'C2': ('good', '230 crossings, 11 cm median; the base cap for Block C'),
}
NAMES = {'A1': 'A-1 dipping sheet, NW', 'A2': 'A-2 steep E-W sheet', 'B1': 'B-1 shallow sheet, dips east', 'B2': 'B-2 deep wedge, west', 'C1': 'C-1 shallow sheet, west half', 'C2': 'C-2 base cap'}
DEPTHLIM = {'A': 'assumed 3.0 m bench, no floor was surveyed', 'B': 'assumed 3.0 m bench, no floor was surveyed', 'C': 'the C-2 cap from the GPR'}
HAZ = {'A': [], 'B': ['metal in the top metre near x = 190 to 200 and 390 to 420 cm (report)'], 'C': ['shallow clutter, top metre, y = 350 to 750 cm across the width (PARSAN): treat the whole top metre as suspect for metal', 'a second reflector at 3.9 to 4.3 m below C-2, unpicked']}


def b64(a): return base64.b64encode(np.ascontiguousarray(a).tobytes()).decode('ascii')


def dec_b64(s, dt): return np.frombuffer(base64.b64decode(s), dtype=dt)


def read_ply(p, n):
    with open(p, 'r') as f:
        nv = 0
        for ln in f:
            if ln.startswith('element vertex'): nv = int(ln.split()[2])
            if ln.strip() == 'end_header': break
        a = np.loadtxt(f, max_rows=nv)
    if len(a) > n: a = a[np.random.default_rng(1).choice(len(a), n, replace=False)]
    return a


def read_grid_xyz(p):
    a = np.loadtxt(p); gx = np.unique(a[:, 0]); gy = np.unique(a[:, 1]); return gx, gy, a[:, 2].reshape(len(gy), len(gx))


def read_obj_lines(p):
    V = []; L = []
    for ln in open(p):
        if ln.startswith('v '): V.append([float(t) for t in ln.split()[1:4]])
        elif ln.startswith('l '): L.append([int(t) - 1 for t in ln.split()[1:]])
    V = np.array(V); return [np.round(V[idx], 3).tolist() for idx in L]


data = dict(blocks={}, generated='2026-09-10', spectra=SPEC, frame='bench frame: metres, z up, right-handed, bench plane = 0. Grid coordinates x, y in cm from the painted origin cross.')
for blk in 'ABC':
    r = REG[blk]; sc = r['scale_m_per_unit']; corner = (np.array(r['origin_local_units']) * sc).tolist(); xd = r['xdir_local']; yd = r['ydir_local']
    W, H = DIMS[blk]
    def to_bench(xg_cm, yg_cm): return corner[0] + np.asarray(xg_cm) / 100 * xd[0] + np.asarray(yg_cm) / 100 * yd[0], corner[1] + np.asarray(xg_cm) / 100 * xd[1] + np.asarray(yg_cm) / 100 * yd[1]
    od = os.path.join(DS, 'Block_' + blk); B = dict(name='Block %s' % blk, dims_m=[W, H], origin=corner, xdir=xd, ydir=yd, depth_limit=DEPTHLIM[blk], hazards=HAZ[blk])
    # cloud
    pc = read_ply(os.path.join(od, 'Block_%s_pointcloud.ply' % blk), NPTS[blk])
    B['cloud'] = dict(n=len(pc), xyz=b64(pc[:, :3].astype(np.float32)), rgb=b64(pc[:, 3:6].astype(np.uint8)))
    # DEM
    gx, gy, Z = read_grid_xyz(os.path.join(OUT, 'model', 'v2_topo', 'Block%s_DEM_10cm.xyz' % blk))
    fi = RegularGridInterpolator((gy, gx), Z, bounds_error=False, fill_value=None)
    GX, GY = np.meshgrid(gx, gy); bx, by = to_bench(GX.ravel(), GY.ravel())
    B['dem'] = dict(nx=len(gx), ny=len(gy), xyz=b64(np.c_[bx, by, Z.ravel()].astype(np.float32)), relief_m=round(float(Z.max() - Z.min()), 2))
    tp = os.path.join(OUT, 'web', 'tex', 'bench_%s.jpg' % blk)
    if os.path.exists(tp):
        meta = json.load(open(os.path.join(OUT, 'web', 'tex', 'meta.json')))
        B['dem']['tex'] = base64.b64encode(open(tp, 'rb').read()).decode('ascii'); B['dem']['tex_pad'] = meta['pad_m']
    # surfaces v1 (depth below flat bench) and v2 (on DEM), as grids in the bench frame
    B['surfaces'] = []
    for F in FEATS[blk]:
        fx, fy, Zd = read_grid_xyz(os.path.join(OUT, 'model', '%s_grid_10cm.xyz' % F))
        FX, FY = np.meshgrid(fx, fy); bx, by = to_bench(FX.ravel(), FY.ravel()); hs = fi(np.c_[FY.ravel(), FX.ravel()])
        ok = np.isfinite(Zd.ravel())
        z1 = np.where(ok, -Zd.ravel(), np.nan); z2 = np.where(ok, hs - Zd.ravel(), np.nan)
        rel, why = REL[F]
        B['surfaces'].append(dict(id=F, name=NAMES[F], nx=len(fx), ny=len(fy), xy=b64(np.c_[bx, by].astype(np.float32)), z1=b64(z1.astype(np.float32)), z2=b64(z2.astype(np.float32)),
                                  depth_min=STRUCT[blk]['planes'][F]['depth_min_m'], depth_max=STRUCT[blk]['planes'][F]['depth_max_m'], reliability=rel, why=why,
                                  daylight=DAY[blk][F]['v2_dem'].get('daylights', False)))
    # sketch cracks (draped) and photo cracks
    B['sketch'] = read_obj_lines(os.path.join(od, 'Block_%s_sketch_cracks.obj' % blk))
    pcr = os.path.join(od, 'Block_%s_surface_cracks_v1.obj' % blk); B['photo'] = read_obj_lines(pcr) if os.path.exists(pcr) else []
    B['photo_lift'] = VER['photo'][blk]['lift']
    # blocks (boxes) per scenario, corners in bench frame at surface height minus depth
    B['packing'] = {}
    for sname, res in PACK[blk].items():
        boxes = []
        for b in res['boxes']:
            cx, cy = 50 * (b['x0'] + b['x1']), 50 * (b['y0'] + b['y1']); hs0 = float(fi([[cy, cx]])[0])
            corners = []
            for (x, y) in ((b['x0'], b['y0']), (b['x1'], b['y0']), (b['x1'], b['y1']), (b['x0'], b['y1'])):
                bx_, by_ = to_bench(x * 100, y * 100); corners.append([round(float(bx_), 3), round(float(by_), 3)])
            boxes.append(dict(cls=b['cls'], corners=corners, ztop=round(hs0 - b['z0'], 3), zbot=round(hs0 - b['z1'], 3), L=b['L'], W=b['Wd'], H=b['Hh'], t=b['t'], m3=b['vol_m3'],
                              grid_x=[round(100 * b['x0']), round(100 * b['x1'])], grid_y=[round(100 * b['y0']), round(100 * b['y1'])], depth=[b['z0'], b['z1']]))
        B['packing'][sname] = dict(boxes=boxes, classes=res['classes'], packed_t=res['packed_t'], gross_t=round(res['gross_rock_m3'] * 2.95), recovery=res['recovery_ratio'], depth_limit=res['depth_limit'])
    # guillotine plan: cuttable blocks with removal order, and the cut planes in sequence
    B['guillotine'] = {}
    for sname, res in GUIL[blk].items():
        boxes = []
        for b in res['boxes']:
            cx, cy = 50 * (b['x0'] + b['x1']), 50 * (b['y0'] + b['y1']); hs0 = float(fi([[cy, cx]])[0])
            corners = []
            for (x, y) in ((b['x0'], b['y0']), (b['x1'], b['y0']), (b['x1'], b['y1']), (b['x0'], b['y1'])):
                bx_, by_ = to_bench(x * 100, y * 100); corners.append([round(float(bx_), 3), round(float(by_), 3)])
            boxes.append(dict(cls=b['cls'], corners=corners, ztop=round(hs0 - b['z0'], 3), zbot=round(hs0 - b['z1'], 3), L=b['L'], W=b['Wd'], H=b['Hh'], t=b['t'], m3=b['vol_m3'], marked=b['marked'], seq=b['remove_seq'],
                              grid_x=[round(100 * b['x0']), round(100 * b['x1'])], grid_y=[round(100 * b['y0']), round(100 * b['y1'])], depth=[b['z0'], b['z1']]))
        cuts = []
        for c_ in res['cuts']:
            e = c_['extent']
            if c_['axis'] == 'x': pts = [(c_['pos'], e['y'][0]), (c_['pos'], e['y'][1])]
            elif c_['axis'] == 'y': pts = [(e['x'][0], c_['pos']), (e['x'][1], c_['pos'])]
            else: pts = [(e['x'][0], e['y'][0]), (e['x'][1], e['y'][0]), (e['x'][1], e['y'][1]), (e['x'][0], e['y'][1])]
            bp = []
            for (x, y) in pts:
                bx_, by_ = to_bench(x * 100, y * 100); bp.append([round(float(bx_), 3), round(float(by_), 3), round(float(fi([[y * 100, x * 100]])[0]), 3)])
            cuts.append(dict(seq=c_['seq'], level=c_['level'], axis=c_['axis'], pos=c_['pos'], extent=e, bench=bp, capped=c_.get('capped', False)))
        B['guillotine'][sname] = dict(boxes=sorted(boxes, key=lambda b: b['seq']), cuts=cuts, classes=res['classes'], packed_t=res['packed_t'], gross_t=round(res['gross_rock_m3'] * 2.95), recovery=res['recovery_ratio'], n_cuts=res['n_cuts'], depth_limit=res['depth_limit'], east=res['east'])
    # raw radargram panels for this block
    B['panels'] = []
    for pnl in PANELS:
        if pnl['block'] != blk: continue
        jp = os.path.join(OUT, 'web', 'panels', pnl['file'])
        B['panels'].append(dict(line=pnl['line'], ch=pnl['ch'], orientation=pnl['orientation'], fixed_axis=pnl['fixed_axis'], fixed_cm=pnl['fixed_cm'], run_axis=pnl['run_axis'], length_m=pnl['length_m'], depth_m=pnl['depth_m'], jpg=base64.b64encode(open(jp, 'rb').read()).decode('ascii')))
    B['structural'] = STRUCT[blk]
    # picks per line for the 2D radargram viewer: position along the run axis (cm) and depth (m), by feature
    B['picks'] = {}
    for F in FEATS[blk]:
        fp = glob.glob(os.path.join(OUT, 'dataset', 'picks', 'PICKS_%s_*.csv' % F))[0]
        for q in csv.DictReader(open(fp, encoding='utf-8')):
            ln = int(q['line']); s = float(q['x_cm']) if q['orientation'] == 'X-line' else float(q['y_cm'])
            B['picks'].setdefault(str(ln), {}).setdefault(F, []).append([round(s), round(float(q['depth_m']), 2)])
    # accepted diffraction hyperbolae (velocity check): trace -> position, apex time -> depth at 0.1202
    B['hyp'] = {}
    for hrow in csv.DictReader(open(os.path.join(OUT, 'tables', 'hyperbola_velocity.csv'), encoding='utf-8')):
        if hrow['block'] != blk or float(hrow['vwidth']) > 0.012 or float(hrow['t0_ns']) <= 10: continue
        ln = int(re.search(r'new(\d{3})', hrow['line']).group(1))
        B['hyp'].setdefault(str(ln), []).append([round(int(hrow['trace']) * 2.49), round(float(hrow['t0_ns']) * 0.1202 / 2, 2), float(hrow['v'])])
    # verification summary for the block
    B['verify'] = dict(registration=VER['registration'][blk], dem=VER['dem'][blk], sketch=VER['sketch'][blk], photo=VER['photo'][blk])
    if blk == 'C': B['verify']['picks'] = VER['picks']
    data['blocks'][blk] = B
    print('Block %s: cloud %d pts, %d surfaces, %d sketch traces, %d photo traces, %d scenarios, %d panels, guillotine 1.0 m: %d blocks %d cuts' % (blk, len(pc), len(B['surfaces']), len(B['sketch']), len(B['photo']), len(B['packing']), len(B['panels']), len(B['guillotine']['surface_1.0m']['boxes']), B['guillotine']['surface_1.0m']['n_cuts']))
js = json.dumps(data, separators=(',', ':'))
open(os.path.join(WEB, 'data.json'), 'w').write(js); print('web/data.json %.1f MB' % (len(js) / 1e6))
tp = os.path.join(WEB, 'index.template.html')
if os.path.exists(tp):
    tpl = open(tp, encoding='utf-8').read()
    # 1. artifact: everything embedded (the artifact host allows no fetch)
    html = tpl.replace('/*__DATA__*/', 'window.KDATA=' + js + ';')
    open(os.path.join(WEB, 'index.html'), 'w', encoding='utf-8').write(html); print('web/index.html %.1f MB (embedded, artifact)' % (len(html) / 1e6))
    # 2. GitHub Pages: a small core page; point clouds, bench textures and radar panels are separate files fetched on demand
    import shutil, copy
    SITE = os.path.join(WEB, 'site'); os.makedirs(os.path.join(SITE, 'data'), exist_ok=True); os.makedirs(os.path.join(SITE, 'tex'), exist_ok=True); os.makedirs(os.path.join(SITE, 'panels'), exist_ok=True)
    core = copy.deepcopy(data)
    for blk, B in core['blocks'].items():
        xyz = dec_b64(B['cloud']['xyz'], np.float32); rgb = dec_b64(B['cloud']['rgb'], np.uint8)
        open(os.path.join(SITE, 'data', 'cloud_%s.bin' % blk), 'wb').write(xyz.tobytes() + rgb.tobytes())
        B['cloud'] = dict(n=B['cloud']['n'], url='data/cloud_%s.bin' % blk)
        if 'tex' in B['dem']:
            shutil.copy(os.path.join(WEB, 'tex', 'bench_%s.jpg' % blk), os.path.join(SITE, 'tex')); del B['dem']['tex']; B['dem']['tex_url'] = 'tex/bench_%s.jpg' % blk
        for pnl in B['panels']:
            fn = '%s_%02d_%s.jpg' % (blk, pnl['line'], pnl['ch']); shutil.copy(os.path.join(WEB, 'panels', fn), os.path.join(SITE, 'panels', fn)); del pnl['jpg']; pnl['url'] = 'panels/' + fn
    cjs = json.dumps(core, separators=(',', ':'))
    head = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<meta name="color-scheme" content="light dark"><meta name="theme-color" content="#EDEFF2" media="(prefers-color-scheme: light)"><meta name="theme-color" content="#14171C" media="(prefers-color-scheme: dark)">'
            '<meta name="description" content="GPR fracture surfaces, photographed bench and a straight-cut block plan for three dolerite benches at Kuppam, block by block.">'
            '<meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="Kuppam Bench">'
            '<link rel="manifest" href="manifest.webmanifest"><link rel="icon" href="icon-192.png"><link rel="apple-touch-icon" href="icon-192.png">'
            '<link rel="preconnect" href="https://cdnjs.cloudflare.com"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style></head><body>')
    tail = ('<script>if("serviceWorker" in navigator&&location.protocol==="https:")navigator.serviceWorker.register("sw.js").catch(function(){});</script></body></html>')
    open(os.path.join(SITE, 'index.html'), 'w', encoding='utf-8').write(head + tpl.replace('/*__DATA__*/', 'window.KDATA=' + cjs + ';') + tail)
    print('web/site/index.html %.2f MB core + %d panels + 3 clouds + 3 textures on demand' % ((len(cjs) + len(tpl)) / 1e6, sum(len(B['panels']) for B in core['blocks'].values())))
    # service worker: index network-first, everything else cache-first; versioned by the build
    ver = 'kbm-' + data['generated'] + '-' + str(abs(hash(cjs)) % 100000)
    open(os.path.join(SITE, 'sw.js'), 'w', encoding='utf-8').write("""'use strict';
const V='%s';
self.addEventListener('install',e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(['./','./index.html','./manifest.webmanifest'])).then(()=>self.skipWaiting()));});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==V).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;const u=new URL(e.request.url);
  const isPage=u.origin===location.origin&&(u.pathname.endsWith('/')||u.pathname.endsWith('index.html'));
  if(isPage){e.respondWith(fetch(e.request).then(r=>{const cp=r.clone();caches.open(V).then(c=>c.put(e.request,cp));return r;}).catch(()=>caches.match(e.request,{ignoreSearch:true})));return;}
  e.respondWith(caches.match(e.request).then(hit=>hit||fetch(e.request).then(r=>{if(r&&(r.ok||r.type==='opaque')){const cp=r.clone();caches.open(V).then(c=>c.put(e.request,cp));}return r;})));});
""" % ver)
    json.dump(dict(name='Kuppam Bench Model', short_name='Kuppam Bench', description='GPR fracture surfaces and a straight-cut block plan for the Kuppam benches.', start_url='./', scope='./', display='standalone',
                   background_color='#14171C', theme_color='#C8452B', lang='en', icons=[dict(src='icon-192.png', sizes='192x192', type='image/png', purpose='any maskable'), dict(src='icon-512.png', sizes='512x512', type='image/png', purpose='any maskable')]),
              open(os.path.join(SITE, 'manifest.webmanifest'), 'w'), indent=1)
    from PIL import Image, ImageDraw
    for S in (192, 512):
        im = Image.new('RGB', (S, S), '#14171C'); d = ImageDraw.Draw(im); m = S * 0.16
        d.rounded_rectangle([m, m * 1.4, S - m, S - m * 1.1], radius=S * 0.06, fill='#C9CDD2')
        for k in range(1, 4):
            x = m + (S - 2 * m) * k / 4; d.line([(x, m * 1.4), (x, S - m * 1.1)], fill='#C8452B', width=max(2, S // 64))
            y = m * 1.4 + (S - m * 2.5) * k / 4; d.line([(m, y), (S - m, y)], fill='#C8452B', width=max(2, S // 64))
        r = S * 0.07; cx, cy = m, m * 1.4; d.ellipse([cx - r, cy - r, cx + r, cy + r], outline='#C8452B', width=max(3, S // 40), fill='#14171C')
        im.save(os.path.join(SITE, 'icon-%d.png' % S))
    print('web/site: sw.js (%s), manifest, icons written' % ver)
