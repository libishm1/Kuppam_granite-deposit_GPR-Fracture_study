"""Is there a second, deeper east-dipping reflector in the B-1 corridor (x 650-950) at 1.0-1.95 m, as Ronak's
email states, in addition to the 0.46-0.97 m sheet already tracked? Corridor-track both channels on all 13
X-lines with her depths as the seed, free-track a wide gate, and compare energy against the shallow sheet."""
import sys, os, glob, csv
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
exec(open(os.path.join(os.path.dirname(__file__), 'build_b.py')).read().split('# ---------------- B-2')[0])
X0, X1 = 650.0, 950.0
print('%-4s %-3s %-26s %-26s %-12s' % ('line', 'ch', 'shallow seed 0.50->0.94 m', 'deep seed 1.00->1.95 m', 'free 0.3-2.2'))
rows = []
for ln in range(1, 14):
    for ch, dt in (('HF', DTH), ('LF', DTL)):
        r = load(ln, ch); E = agc_env(r['data'], dt); n = r['ntr']; i0, i1 = int(round(X0 / DX)), min(n - 1, int(round(X1 / DX)))
        out = []
        for (za, zb) in ((0.50, 0.94), (1.00, 1.95)):
            j0, j1 = int(round(2 * za / V / dt)), int(round(2 * zb / V / dt))
            idx, jj = corridor(E, i0, i1, j0, j1, corr=int(0.12 / (V / 2) / dt), jump=2, smooth=0.5)
            en = E[idx, jj]; z = jj * dt * V / 2; sl = np.degrees(np.arctan(np.polyfit(idx * DX / 100, z, 1)[0]))
            out.append((en.mean(), z.min(), z.max(), sl))
        j0, j1 = int(round(2 * 0.3 / V / dt)), int(round(2 * 2.2 / V / dt))
        idx, jj = corridor(E, i0, i1, (j0 + j1) // 2, (j0 + j1) // 2, corr=(j1 - j0) // 2, jump=2, smooth=0.35)
        z = jj * dt * V / 2
        rows.append(dict(line=ln, ch=ch, shallow_env=out[0][0], shallow_z=(out[0][1], out[0][2]), shallow_dip=out[0][3], deep_env=out[1][0], deep_z=(out[1][1], out[1][2]), deep_dip=out[1][3], free_z=(z.min(), z.max())))
        print('%-4d %-3s env %.2f  %.2f-%.2f m %+5.1f deg   env %.2f  %.2f-%.2f m %+5.1f deg   %.2f-%.2f m' % (ln, ch, out[0][0], out[0][1], out[0][2], out[0][3], out[1][0], out[1][1], out[1][2], out[1][3], z.min(), z.max()))
for ch in ('HF', 'LF'):
    s = [r for r in rows if r['ch'] == ch]
    print('%s: shallow seed mean envelope %.2f (dip %+.1f), deep seed %.2f (dip %+.1f); free track median depth %.2f-%.2f m' % (
        ch, np.mean([r['shallow_env'] for r in s]), np.mean([r['shallow_dip'] for r in s]), np.mean([r['deep_env'] for r in s]), np.mean([r['deep_dip'] for r in s]),
        np.median([r['free_z'][0] for r in s]), np.median([r['free_z'][1] for r in s])))
