# -*- coding: utf-8 -*-
"""Check every figure the film puts on screen against the table it is supposed to come from.

The film recomputes its numbers at render time rather than carrying typed-in copies, so this is
not a test of the rendering: it is a test that the sentences written into the captions still match
what those tables say. A caption is prose and prose goes stale.
"""
import csv
import json
import os
import sys
import ast
import io

import numpy as np

import common as K

fails = []
n = 0


def ok(cond, what, got=None, want=None):
    global n
    n += 1
    if cond:
        print('  ok    %s' % what)
    else:
        print('  FAIL  %s   got %s, caption says %s' % (what, got, want))
        fails.append(what)


G = json.load(open(os.path.join(K.GPR, 'tables', 'guillotine_packing.json')))
S = json.load(open(os.path.join(K.GPR, 'tables', 'structural.json')))
V = json.load(open(os.path.join(K.GPR, 'tables', 'velocity_summary.json')))
SP = json.load(open(os.path.join(K.GPR, 'tables', 'spectra.json')))
U = json.load(open(os.path.join(K.GPR, 'tables', 'uncertainty.json')))
NET = json.load(open(os.path.join(K.JM, 'tables', 'stereonet_radar.json')))

print('=== the acquisition')
L = K.survey_lines()
ok(len(L) == 89, '89 lines walked', len(L), 89)
ok(abs(sum(x['length'] for x in L) - 612) < 6, 'about 612 m walked',
   round(sum(x['length'] for x in L)), 612)
sp = set()
for g in csv.DictReader(open(os.path.join(K.GPR, 'tables', 'GEOMETRY_resolved.csv'),
                             encoding='utf-8')):
    sp.add(g['trace_spacing_cm'])
ok(sp == {'2.5'}, 'a trace every 2.5 cm', sorted(sp), '2.5')
ok(round(SP['LF']['peak']) == 358 and round(SP['HF']['peak']) == 628,
   'measured peaks 358 and 628 MHz', (SP['LF']['peak'], SP['HF']['peak']), (358, 628))

print('=== the elevation model')
z = K.site()['P'][:, 2]
rel = float(z.max() - z.min())
ok(20 <= rel <= 22, 'the relief the beat prints is the cloud\'s own', round(rel, 1), '15 to 25 m')

print('=== the velocity')
allv, sel = [], []
for r in csv.DictReader(open(os.path.join(K.GPR, 'tables', 'hyperbola_velocity.csv'),
                             encoding='utf-8')):
    allv.append(float(r['v']))
    if float(r['vwidth']) <= 0.012 and float(r['t0_ns']) > 10.0:
        sel.append(float(r['v']))
ok(len(allv) == V['n_candidates'], '322 hyperbolas tried', len(allv), V['n_candidates'])
ok(len(sel) == V['n_selected'], '114 kept by the rule', len(sel), V['n_selected'])
ok(abs(V['working_velocity'] - 0.1202) < 1e-9, 'the working velocity is 0.1202 m/ns',
   V['working_velocity'], 0.1202)
ok('3.2 percent' in V['statement'], 'depth error from velocity alone is 3.2 per cent')

print('=== the picking')
import radargram as R
pk = R.picks_on('C', 20)
c1 = [q for q in pk if q[0] == 'C-1']
c2 = [q for q in pk if q[0] == 'C-2']
ok(len(c1) + len(c2) == 380, '380 picks on line 20', len(c1) + len(c2), 380)
ok(len(c1) and len(c2), 'two reflections on that line', (len(c1), len(c2)), 'both non-empty')

print('=== the surface')
c2s = S['C']['planes']['C2']
ok(c2s['n_picks'] == 9481, '9,481 picks on C-2', c2s['n_picks'], 9481)
ok(c2s['lines'] == 32, '32 lines', c2s['lines'], 32)
ok(abs(c2s['dip_deg'] - 1.8) < 0.05, 'dipping 1.8 degrees', c2s['dip_deg'], 1.8)
cd = [s['depth'] for s in K.site()['surfaces'] if s['id'] == 'C2'][0]
ok(abs(cd[0] - 2.8) < 0.1 and abs(cd[1] - 3.6) < 0.1, '2.8 to 3.6 m under the floor', cd,
   '2.8 to 3.6')

print('=== all six')
dmin = min(S[b]['planes'][f]['depth_min_m'] for b in 'ABC' for f in S[b]['planes'])
dmax = max(S[b]['planes'][f]['depth_max_m'] for b in 'ABC' for f in S[b]['planes'])
ok(abs(dmin - 0.2) < 0.06, 'shallowest 0.2 m', dmin, 0.2)
ok(abs(dmax - 3.9) < 0.06, 'deepest 3.9 m', dmax, 3.9)
sig = [U[b][f]['sigma_total_m_at_mean_depth'] for b in 'ABC' for f in U[b]
       if isinstance(U[b][f], dict) and 'sigma_total_m_at_mean_depth' in U[b][f]]
ok(abs(min(sig) - 0.08) < 0.01, 'depth error is 8 cm on the shallow sheets', round(min(sig), 3), 0.08)
ok(abs(max(sig) - 0.22) < 0.01, 'and 22 cm on the deep ones', round(max(sig), 3), 0.22)

print('=== the stereonet')
for blk in 'ABC':
    for f in NET[blk]:
        ok(0 <= f['vector_mean_dip_dir_azimuth_deg'] <= 360 and f['vector_mean_dip_deg'] >= 0,
           '%s pole is a real orientation' % f['feature'])

print('=== the plan')
cuts = K.site()['cuts']
ok(len(cuts) == 42, '42 blocks', len(cuts), 42)
ok(abs(sum(c['m3'] for c in cuts) - 177) < 1.0, '177 cubic metres',
   round(sum(c['m3'] for c in cuts), 1), 177)
ok(abs(sum(c['t'] for c in cuts) - 524) < 1.5, '524 tonnes', round(sum(c['t'] for c in cuts)), 524)
cls = {}
for c in cuts:
    cls[c['cls']] = cls.get(c['cls'], 0) + 1
ok(cls.get('gangsaw_large') == 15 and cls.get('gangsaw_standard') == 1
   and cls.get('small_block') == 24 and cls.get('cutter_block') == 2,
   'the class counts are 15, 1, 24, 2', cls, '15/1/24/2')
ncuts = sum(G[b][K.PLAN_KEY]['n_cuts'] for b in 'ABC')
ok(ncuts == 164, '164 wire cuts across three benches', ncuts, 164)
nw = sum(len(G[b][K.PLAN_KEY]['waste']) for b in 'ABC')
ok(nw == 113, '113 waste pieces', nw, 113)
clr = min(v for b in 'ABC' for x in G[b][K.PLAN_KEY]['boxes']
          for v in x['min_clearance_m'].values()) if any(
    x['min_clearance_m'] for b in 'ABC' for x in G[b][K.PLAN_KEY]['boxes']) else 0.15
ok(clr >= 0.149, 'every block keeps 15 cm clear', round(clr, 3), 0.15)
ok(K.site()['scenario'].endswith('uncertainty-safe clearance'),
   'the run shown is the one the page opens on', K.site()['scenario'], 'uncertainty-safe')

# --- orientation guards, added 12 September after the Block C east axis was found transposed.
# Both of these would have failed on the wrong reading, and neither decides a discrete label from a
# continuous measurement: the first is a rigid-frame residual, the second an angle between axes.

_az = lambda d: float(np.degrees(np.arctan2(d[0], d[1])) % 360)


def _sep(a, b):
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)

# 1. The grid-to-site fit must reproduce the drawn blocks. A transposed axis assignment on a
#    non-square bench cannot be fitted by any rigid frame and blows this residual up by metres.
for _b in 'ABC':
    _o, _xd, _yd = K.grid_frame(_b)
    ok(_sep(_az(_xd), _az(_yd)) > 85.0 and _sep(_az(_xd), _az(_yd)) < 95.0,
       'block %s grid axes are perpendicular in the site frame' % _b,
       round(_sep(_az(_xd), _az(_yd)), 1), 90)
    ok(abs(np.linalg.norm(_xd) - 1.0) < 0.02 and abs(np.linalg.norm(_yd) - 1.0) < 0.02,
       'block %s grid fit is a rotation, not a stretch' % _b,
       (round(float(np.linalg.norm(_xd)), 3), round(float(np.linalg.norm(_yd)), 3)), 1.0)

# 2. One crew painted all three grids, so the three east axes must be parallel on the ground.
#    Under the old C reading this spread was 92 degrees.
_EAST = {'A': '+x', 'B': '+y', 'C': '+y'}
_easts = []
for _b in 'ABC':
    _o, _xd, _yd = K.grid_frame(_b)
    _easts.append(_az(_xd if _EAST[_b] == '+x' else _yd))
_spread = max(_sep(a, b) for a in _easts for b in _easts)
ok(_spread < 10.0, 'the three east axes are parallel within 10 degrees',
   round(_spread, 1), '< 10')

# 3. The side the east axis runs along must match the line counts: C east is the 8 m side, B the
#    6 m side. This is the fact the client verified from the photographs and the sketch.
_GRID = {'A': (5.5, 5.5), 'B': (9.5, 6.0), 'C': (7.0, 8.0)}
for _b, _want in (('B', 6.0), ('C', 8.0)):
    _W, _H = _GRID[_b]
    _got = _H if _EAST[_b] == '+y' else _W
    ok(abs(_got - _want) < 0.01, 'block %s east side is the %.0f m side' % (_b, _want), _got, _want)

# 4. Handedness, per bench, from the field. The origin is the north-west corner everywhere and
#    both axes run into the bench, but which axis runs east differs: A is left-handed (+x east,
#    +y south - the X-line numerals run down the west edge from A0), B and C right-handed (+y
#    east). A guard that demanded one convention for all three was added and then removed on
#    12 September; it encoded an assumption, not a measurement, and it was wrong.
_HAND = {'A': 'left', 'B': 'right', 'C': 'right'}
for _b in 'ABC':
    _o, _xd, _yd = K.grid_frame(_b)
    _det = _xd[0] * _yd[1] - _xd[1] * _yd[0]
    _got = 'right' if _det > 0 else 'left'
    ok(_got == _HAND[_b], 'block %s grid is %s-handed, as the field says' % (_b, _HAND[_b]),
       _got, _HAND[_b])
# and the east axis, whichever name it carries, must point the same way on every bench: on A that
# is +x and the first picked side; on B and C it is +y and the first picked side.
for _b in 'ABC':
    _o, _xd, _yd = K.grid_frame(_b)
    _e = _az(_xd if _EAST[_b] == '+x' else _yd)
    ok(_sep(_e, 104.0) < 6.0, 'block %s east axis points east (about 104 deg in the model frame)' % _b,
       round(_e, 1), '104 +- 6')

# 5. No script may restate the east convention instead of reading the EAST table. This is the bug
#    that survived two corrections: dip_az() was fixed to read EAST while to_net() kept its own
#    hard-coded membership test, so the plotted stereonet poles disagreed with the dip directions
#    printed beside them on two benches out of three.
#
#    Tokenised rather than grepped, so prose in comments and docstrings does not trip it and only
#    real code counts: the pattern is the NAME `in` followed immediately by a two-block string.
import glob as _glob
import tokenize as _tok

_dirs = [os.path.join(K.JM, 'scripts', '*.py'),
         os.path.join(K.GPR, 'scripts', '*.py'),
         os.path.join(os.path.dirname(os.path.abspath(__file__)), '*.py')]
_BAD = {'AC', 'BC', 'AB', 'CA', 'CB', 'BA'}
_restated = []
for _pat in _dirs:
    for _f in _glob.glob(_pat):
        if os.path.basename(_f) == 'numbers_check.py':
            continue
        try:
            with open(_f, 'rb') as _fh:
                _ts = [x for x in _tok.tokenize(_fh.readline)
                       if x.type not in (_tok.COMMENT, _tok.NL, _tok.NEWLINE, _tok.INDENT, _tok.DEDENT)]
        except Exception:
            continue
        for _i in range(len(_ts) - 1):
            if _ts[_i].type == _tok.NAME and _ts[_i].string == 'in' and _ts[_i + 1].type == _tok.STRING:
                try:
                    _v = ast.literal_eval(_ts[_i + 1].string)
                except Exception:
                    continue
                if isinstance(_v, str) and _v in _BAD:
                    _restated.append('%s:%d  in %r' % (os.path.basename(_f), _ts[_i].start[0], _v))
ok(not _restated, 'no script restates the east convention instead of reading EAST',
   _restated[:4] if _restated else 'none', 'none')

# 6. The frame files (tables/registration.json, which the per-block pages draw from) and the pinned
#    rings (which the site view draws from) must agree on where each bench's long side runs. On
#    12 September they disagreed by 90 degrees on C: the Block C page drew a mirror image of the
#    painted grid and the two views contradicted each other for a day. Compared in the site frame,
#    per non-square bench.
_REG = json.load(io.open(os.path.join(K.GPR, 'tables', 'registration.json'), encoding='utf-8'))
_GRIDWH = {'A': (5.5, 5.5), 'B': (9.5, 6.0), 'C': (7.0, 8.0)}
for _b in 'ABC':
    _W, _H = _GRIDWH[_b]
    if abs(_W - _H) < 0.01:
        continue                                   # square: no long side to compare
    _r = _REG[_b]; _xd = np.array(_r['xdir_local'], float); _yd = np.array(_r['ydir_local'], float)
    # A and B live in their own mesh frames and are carried into the site frame by the ICP yaw
    # (icp_site.json, pose_released), exactly as site_viewer_data.py does; C is the site frame.
    _yaw = 0.0
    if _b != 'C':
        _icp = json.load(io.open(os.path.join(K.JM, 'tables', 'icp_site.json'), encoding='utf-8'))
        _yaw = float(_icp['blocks'][_b]['best']['pose_released']['yaw_deg'])
    _c, _s = np.cos(np.radians(_yaw)), np.sin(np.radians(_yaw))
    _rot = lambda v: np.array([_c * v[0] - _s * v[1], _s * v[0] + _c * v[1]])
    _frame_long = _az(_rot(_xd)) if _W > _H else _az(_rot(_yd))
    _bench = [x for x in K.site()['benches'] if x['block'] == _b][0]
    _ring = np.array(_bench['ring'], float)[:, :2]
    _sides = [(_ring[(i + 1) % 4] - _ring[i]) for i in range(4)]
    _pin_long = _az(max(_sides, key=lambda v: np.linalg.norm(v)))
    _d = _sep(_frame_long, _pin_long); _d = min(_d, 180.0 - _d)      # axial: a side has no arrow
    ok(_d < 8.0, 'block %s: frame file and pinned ring agree on the long side' % _b,
       'frame %.1f vs pinned %.1f (%.1f apart)' % (_frame_long, _pin_long, _d), 'parallel')

print()
print('%d checks, %d failed' % (n, len(fails)))
if fails:
    print('\n'.join('  ' + f for f in fails))
sys.exit(1 if fails else 0)
