import sys, os, glob, csv, re, json
sys.path.insert(0, os.path.dirname(__file__))
import segy
import numpy as np

ROOT = r'D:/code_ws/reference/parsans/report/raw/GPR Raw data_Kuppam'

def read_meta(p):
    raw = open(p, 'rb').read()
    txt = raw.decode('utf-16-le', 'replace').lstrip('\ufeff')
    d, lines = {}, []
    cur = None
    for ln in txt.splitlines():
        f = ln.split('\t')
        if len(f) == 1 and f[0].strip():
            cur = f[0].strip(); continue
        if len(f) >= 2 and f[0].strip():
            d[f[0].strip()] = [x.strip() for x in f[1:]]
        if f[0].strip().lower().startswith('line ') and len(f) >= 4:
            lines.append(dict(name=f[0].strip(), scan_m=float(f[1]),
                              startx=float(f[2]), starty=float(f[3])))
    d['_lines'] = lines
    return d

rows = []
for blk in ['A Block', 'B Block', 'C Block']:
    csvs = sorted(glob.glob(os.path.join(ROOT, blk, '**', '*.csv'), recursive=True))
    for c in csvs:
        m = re.search(r'new(\d{3})', os.path.basename(c))
        n = int(m.group(1))
        meta = read_meta(c)
        d = os.path.dirname(c)
        rec = dict(block=blk[0], line_no=n, csv=os.path.relpath(c, ROOT))
        for k in ['Repetition Rate [scans/cm]', 'Scan Direction', 'Mode', 'Units',
                  'Firmware Version', 'App Version', 'Probe S/N', 'File Name']:
            rec[k] = meta.get(k, [''])[0]
        for k, tag in [('Scan Length [samples/scan]', 'nsamp'), ('Time Window [ns]', 'win'),
                       ('Sampling Rate [GHz]', 'fs'), ('Antenna Spacing [cm]', 'antsp')]:
            v = meta.get(k, ['', ''])
            rec[tag + '_LF'] = v[0] if len(v) > 0 else ''
            rec[tag + '_HF'] = v[1] if len(v) > 1 else ''
        L = meta['_lines'][0] if meta['_lines'] else {}
        rec['scan_m'] = L.get('scan_m'); rec['startx'] = L.get('startx'); rec['starty'] = L.get('starty')
        rec['n_line_entries'] = len(meta['_lines'])
        for ch in ['HF', 'LF']:
            g = glob.glob(os.path.join(d, '*_%s.sgy' % ch))
            if g:
                r = segy.read(g[0], want_data=False)
                rec['ntr_' + ch] = r['ntr']; rec['ns_' + ch] = r['ns']
                rec['dt_' + ch] = r['bin']['sample_interval_us']
                rec['fmt_' + ch] = r['fc']
                rec['sgy_' + ch] = os.path.relpath(g[0], ROOT)
        rows.append(rec)

rows.sort(key=lambda r: (r['block'], r['line_no']))
keys = list(rows[0].keys())
with open('tables/line_inventory.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
print('lines:', len(rows))
for b in 'ABC':
    sub = [r for r in rows if r['block'] == b]
    print('\n=== BLOCK', b, len(sub), 'lines ===')
    print('  scan_m      :', sorted(set(r['scan_m'] for r in sub)))
    print('  startx set  :', sorted(set(r['startx'] for r in sub)))
    print('  starty set  :', sorted(set(r['starty'] for r in sub)))
    print('  rep rate    :', set(r['Repetition Rate [scans/cm]'] for r in sub))
    print('  scan dir    :', set(r['Scan Direction'] for r in sub))
    print('  ntr HF      :', min(r['ntr_HF'] for r in sub), '-', max(r['ntr_HF'] for r in sub))
    print('  ntr LF      :', min(r['ntr_LF'] for r in sub), '-', max(r['ntr_LF'] for r in sub))
    print('  ns HF/LF    :', set(r['ns_HF'] for r in sub), set(r['ns_LF'] for r in sub))
    print('  dt HF/LF    :', set(r['dt_HF'] for r in sub), set(r['dt_LF'] for r in sub))
    print('  win  HF/LF  :', set(r['win_HF'] for r in sub), set(r['win_LF'] for r in sub))
    print('  antsp HF/LF :', set(r['antsp_HF'] for r in sub), set(r['antsp_LF'] for r in sub))
    print('  scan_m/ntr  :', sorted(set(round(r['scan_m']/r['ntr_HF']*100,3) for r in sub)))
