"""One reproducible summary of the diffraction-hyperbola velocities (tables/hyperbola_velocity.csv), the rule that
gives the working velocity, its spread, per-block medians, how many fits sit exactly at the search limits, and the
depth sensitivity of the alternatives. Writes tables/velocity_summary.json."""
import csv, json, numpy as np, os
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'; V0 = 0.1202; LIM = (0.085, 0.1735)
H = list(csv.DictReader(open(os.path.join(OUT, 'tables', 'hyperbola_velocity.csv'))))
ok = [h for h in H if float(h['vwidth']) <= 0.012 and float(h['t0_ns']) > 10]
v = np.array([float(h['v']) for h in ok]); blk = np.array([h['block'] for h in ok])
out = dict(rule='vwidth <= 0.012 m/ns and apex time > 10 ns (the rule used for the working velocity)', n_candidates=len(H), n_selected=len(ok),
 median=round(float(np.median(v)), 4), p10=round(float(np.percentile(v, 10)), 4), p90=round(float(np.percentile(v, 90)), 4), min=round(float(v.min()), 4), max=round(float(v.max()), 4),
 search_limits=list(LIM), n_at_limits=int(((np.abs(v - LIM[0]) < 1e-9) | (np.abs(v - LIM[1]) < 1e-9)).sum()), n_within_one_step_of_limits=int(((v <= LIM[0] + 0.0015) | (v >= LIM[1] - 0.0015)).sum()),
 per_block_median={b: round(float(np.median(v[blk == b])), 4) for b in 'ABC'}, per_block_n={b: int((blk == b).sum()) for b in 'ABC'},
 working_velocity=V0, score_note='the "semb" column is an envelope-amplitude coherence along the hyperbola (mean envelope x sqrt(aperture)), not a normalised waveform semblance',
 alternatives={'0.1174 (report RDP 6.52)': round(100 * (0.1174 / V0 - 1), 2), '0.1252 (Zond RDP 5.73)': round(100 * (0.1252 / V0 - 1), 2)},
 depth_sensitivity_cm={'per +/-1 % velocity at 3 m': 3.0, 'p10 vs working at 3 m': round(300 * (float(np.percentile(v, 10)) / V0 - 1), 1), 'p90 vs working at 3 m': round(300 * (float(np.percentile(v, 90)) / V0 - 1), 1), '0.1174 at 3 m': round(300 * (0.1174 / V0 - 1), 1), '0.1252 at 3 m': round(300 * (0.1252 / V0 - 1), 1)},
 statement='0.1202 m/ns is a working assumption: the median of scattered, uncalibrated hyperbola fits; it has not been calibrated against a reflector of known depth')
json.dump(out, open(os.path.join(OUT, 'tables', 'velocity_summary.json'), 'w'), indent=1)
print('n selected %d, median %.4f, p10-p90 %.4f-%.4f, at limits %d (within one step %d)' % (out['n_selected'], out['median'], out['p10'], out['p90'], out['n_at_limits'], out['n_within_one_step_of_limits']))
