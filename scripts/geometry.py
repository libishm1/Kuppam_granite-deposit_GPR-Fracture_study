import csv, os
"""Resolve every line to block, orientation, fixed coordinate and along-line span.
Line->coordinate map is taken from the field sketches and cross-checked against
the measured scan lengths and the report's own tables."""
MAP = {
 # block: (family1 range, family1 orientation, family2 range, family2 orientation, step cm)
 'A': dict(f1=(1,12,'X','y'), f2=(13,24,'Y','x'), step=50, nominal=(550,550),
           note='lines 1-12 run in x at fixed y, 13-24 run in y at fixed x: the report convention, confirmed by PARSAN 10-09 '
                'and by the reprojection of the numerals at the x = 0 edge. An earlier reading of the sketch had it the other way.'),
 'B': dict(f1=(1,13,'X','y'), f2=(14,33,'Y','x'), step=50, nominal=(950,600),
           note='sketch and report agree'),
 'C': dict(f1=(1,17,'X','y'), f2=(18,32,'Y','x'), step=50, nominal=(700,800),
           note='sketch and report agree'),
}
inv = {(r['block'], int(r['line_no'])): r for r in
       csv.DictReader(open('tables/line_inventory.csv', encoding='utf-8'))}
out = []
for b, m in MAP.items():
    for (a0, a1, orient, fixax) in [m['f1'], m['f2']]:
        for n in range(a0, a1 + 1):
            r = inv.get((b, n))
            if not r: continue
            fixed = (n - a0) * m['step']
            runax = 'y' if fixax == 'x' else 'x'
            L = float(r['scan_m']) * 100.0
            nom = m['nominal'][0] if runax == 'x' else m['nominal'][1]
            out.append(dict(
                block=b, line=n, orientation=orient + '-line',
                fixed_axis=fixax, fixed_cm=fixed,
                run_axis=runax, run_from_cm=0, run_to_measured_cm=round(L, 1),
                nominal_len_cm=nom, len_error_cm=round(L - nom, 1),
                n_traces=int(r['ntr_HF']), trace_spacing_cm=round(L / (int(r['ntr_HF']) - 1), 4),
                ns_HF=r['ns_HF'], ns_LF=r['ns_LF'],
                window_HF_ns=r['win_HF'], window_LF_ns=r['win_LF'],
                antenna_offset_HF_cm=r['antsp_HF'], antenna_offset_LF_cm=r['antsp_LF'],
                sgy_HF=r['sgy_HF'], sgy_LF=r['sgy_LF']))
out.sort(key=lambda r: (r['block'], r['line']))
w = csv.DictWriter(open('tables/GEOMETRY_resolved.csv','w',newline='',encoding='utf-8'),
                   fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
import statistics as st
print('wrote tables/GEOMETRY_resolved.csv,', len(out), 'lines\n')
print('%-5s %-9s %-10s %8s %10s %10s %10s'%('block','family','fixed range','n','len err med','len err min','len err max'))
for b in 'ABC':
    for orient in ['X-line','Y-line']:
        s=[r for r in out if r['block']==b and r['orientation']==orient]
        if not s: continue
        e=[r['len_error_cm'] for r in s]
        print('%-5s %-9s %3d-%3d cm %8d %10.1f %10.1f %10.1f'%(
            b,orient,min(r['fixed_cm'] for r in s),max(r['fixed_cm'] for r in s),len(s),
            st.median(e),min(e),max(e)))
print('\nalong-line length error is how far the wheel odometer fell short of, or ran past,')
print('the nominal grid dimension. It is the along-line positional error at the far end.')
allе=[abs(r['len_error_cm']) for r in out]
print('  median |error| %.1f cm, 90th percentile %.1f cm, max %.1f cm'
      %(st.median(allе), sorted(allе)[int(.9*len(allе))], max(allе)))
