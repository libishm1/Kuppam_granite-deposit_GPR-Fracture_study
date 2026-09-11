"""Write UNCERTAINTY.md from tables/uncertainty.json, tables/uncertainty_mc.json, tables/velocity_summary.json and
tables/guillotine_packing.json, in the structure of the BoEGE paper's uncertainty treatment (tolerance ladder ->
confidence -> detection rung -> uncertainty-safe clearance -> propagation to yield)."""
import json, os, io, math
OUT = r'D:/code_ws/outputs/2026-09-09/gpr_raw_audit'
U = json.load(open(os.path.join(OUT, 'tables', 'uncertainty.json'))); L = U['ladder']
MC = json.load(open(os.path.join(OUT, 'tables', 'uncertainty_mc.json')))
V = json.load(open(os.path.join(OUT, 'tables', 'velocity_summary.json')))
G = json.load(open(os.path.join(OUT, 'tables', 'guillotine_packing.json')))
P = json.load(open(os.path.join(OUT, 'tables', 'block_packing.json')))
g = lambda b, u: G[b]['surface_1.0m__' + u]

lad = '| surface | ch. | mean depth | d·σv/v | λ/4 | v·σt0/2 | σ recon | σ interp | σ mesh | σ reg | **σ total** | % depth | C(15 cm) |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n'
for b in 'ABC':
    for F, u in U[b].items():
        lad += '| %s | %s | %.2f m | %.1f | %.1f | %.1f | %.1f | %.1f | %.2f | %.1f | **%.1f cm** | %.0f %% | %.0f %% |\n' % (
            F, u['channel'], u['mean_depth_m'], 100 * u['sigma_vel_m'], 100 * u['lambda4_m'], 100 * u['sigma_t0_m'], 100 * u['sigma_recon_m'], 100 * u['sigma_interp_m'], 100 * u['sigma_mesh_m'], 100 * u['sigma_reg_m'],
            100 * u['sigma_total_m_at_mean_depth'], u['sigma_total_pct_depth'], 100 * u['C_pos_15cm'])
mig = '| surface | dip modelled → migrated (elevation frame) | plan shift of the reflection point | migrated plane minus drawn plane, at the same position |\n| --- | --- | --- | --- |\n'
for b in 'ABC':
    for F, u in U[b].items():
        mig += '| %s | %.1f° → %.1f° | %.2f m | %.2f to %.2f m |\n' % (F, u['dip_modelled_deg'], u['dip_migrated_deg'], u['migration_plan_shift_median_m'], u['migration_vertical_offset_m']['min'], u['migration_vertical_offset_m']['max'])
yt = '| block | as drawn (15 / 10 cm) | with uncertainty (2σ + migrated, 20 cm chalk) | free heuristic, as drawn | free heuristic, uncertain |\n| --- | --- | --- | --- | --- |\n'
for b in 'ABC':
    yt += '| %s | %.0f t, %d blocks | %.0f t, %d blocks | %.0f t | %.0f t |\n' % (b, g(b, 'modelled')['packed_t'], len(g(b, 'modelled')['boxes']), g(b, 'uncertain')['packed_t'], len(g(b, 'uncertain')['boxes']), P[b]['surface_1.0m__modelled']['packed_t'], P[b]['surface_1.0m__uncertain']['packed_t'])
mct = '| block | plan | planned t | risk-weighted t | mean block risk | blocks over 20 % | re-planned P10 / P50 / P90 |\n| --- | --- | --- | --- | --- | --- | --- |\n'
for b in 'ABC':
    m = MC[b]
    for u, lab in (('modelled', 'as drawn'), ('uncertain', 'with uncertainty')):
        mct += '| %s | %s | %.0f | %.0f | %.0f %% | %d of %d | %.0f / %.0f / %.0f |\n' % (b, lab, m['plan_t'][u], m['plan_risk_weighted_t'][u], 100 * m['mean_risk'][u], m['blocks_over_20pct'][u], len(m['block_risk'][u]), m['replan_t']['p10'], m['replan_t']['p50'], m['replan_t']['p90'])
doc = """# Uncertainty analysis of the Kuppam fracture model and its cutting plan

Written to the structure of the author's paper under review (Murugean 2026, *A managed,
uncertainty-aware pipeline from ground-penetrating radar to dimension-stone block
yield*, Bulletin of Engineering Geology and the Environment): a per-location tolerance
ladder combined in quadrature (GUM), a confidence metric for a clearance, a detection
rung for what the survey cannot see, an uncertainty-safe clearance scaled to the
measured sigma, and the cost of that clearance in yield. The same quantities, the same
formulas, the same names, so the two can be read together. Everything here is produced
by `scripts/uncertainty.py`, `scripts/uncertainty_mc.py` and the packers; the tables are
`tables/uncertainty.json`, `tables/uncertainty_mc.json`.

## 1. Sources of error, and what was measured for each

| term | what it is | value here | where it comes from |
| --- | --- | --- | --- |
| σv/v | velocity share of depth, ½ δεr/εr | %.1f %% | half the spread of the calibrated permittivities (PARSAN Table 1 pipe and plate in dolerite slabs 6.24 to 6.52, Zond 5.73, this diffraction scan 6.22) about the adopted 6.25; `dataset/velocity/` |
| λ/4 | quarter-wavelength resolution floor | HF %.1f cm, LF %.1f cm | v / 4f at the measured peak frequencies 628 and 358 MHz (`tables/spectra.json`) |
| σt0 | time-zero scatter | HF %.2f ns, LF %.2f ns (%.1f and %.1f cm of depth) | standard deviation of the AIC first-break time across the 89 lines per channel (`dataset/velocity/firstbreak_aic.csv`); the time-zero convention itself was closed by PARSAN's email of 10 September |
| σ interp | scatter of the picks about the modelled surface | 3.6 to 14.8 cm | plane residual rms per surface (`tables/structural.json`), the analogue of the paper's kriging posterior |
| σ mesh | h²κ/8 on the 10 cm grid | ≤ 0.1 cm | curvature of the gridded surfaces; negligible |
| σ reg | site term, not in the paper | σxy tan(dip) with σxy = %.2f m (A, C), %.2f m (B) | registration of the painted grid to the mesh (lattice scale and the three painted marks) through the dip |
| migration | planar-reflector geometry | carried as a signed offset, not in σ | picks are normal-incidence distances; the true reflection point lies up-dip by d sin(dip); offset taken plane to plane in absolute elevation |
| detection | what the survey does not see | not a number here | steep fractures (the survey is 2D, 0.5 m lines, unmigrated), hairline dry cracks, and the depth of the chalked cracks |

## 2. The tolerance ladder, per surface

σ_total² = (d σv/v)² + (λ/4)² + (v σt0/2)² + σ_interp² + σ_mesh² + σ_reg², at the mean depth
of each surface; C(T) = erf(T / (σ√2)) is the probability that the surface lies within
T of where it is drawn: 68 %% at T = σ, 95 %% at T = 2σ, and at the as-drawn 15 cm as
tabulated.

""" % (100 * L['sigma_v_over_v'], 100 * L['lambda4_m']['HF'], 100 * L['lambda4_m']['LF'], L['sigma_t0_ns']['HF'], L['sigma_t0_ns']['LF'], 100 * L['sigma_t0_depth_m']['HF'], 100 * L['sigma_t0_depth_m']['LF'], L['sig_xy_m']['A'], L['sig_xy_m']['B']) + lad + """
Reading: the shallow HF surfaces are known to 8 to 12 cm and the as-drawn 15 cm
clearance covers them with 78 to 95 %% confidence; the deep LF surfaces (B-2, C-2) are
known to about 20 cm, dominated by velocity and the LF time-zero scatter, and 15 cm
covers them with only 50 to 55 %% confidence. These totals sit between the paper's
Botticino figures (6.5, 13.2 and 27.8 cm for its three surfaces) for the same reasons:
depth and channel.

## 3. Migration, kept separate

""" + mig + """
For the near-flat surfaces (B-1, C-1, C-2) migration moves nothing. The two A sheets'
reflection points move about 0.6 m up-dip and the planes steepen by 4 to 8 degrees;
B-2's move 0.9 m and its plane steepens by 1.5 degrees. At a given position the migrated
plane is lower than the drawn one (the normal-incidence distance is the vertical depth
times cos(dip)): up to 0.65 m on the A sheets, 13 to 29 cm on B-2. This is the geometric consequence for a planar reflector at
constant velocity, used as an exclusion, not as a correction; migration proper of the
sections is PARSAN's to do.

## 4. Detection rung

The paper's detection rung is calibrated to measured detection rates of open
sub-horizontal fractures in granite (about 80 %% and 91 %% in its two anchors). Nothing
here can improve on that: no fracture of known position has been exposed at Kuppam yet.
What the rung says qualitatively for this survey: the six surfaces are all gently to
moderately dipping, which is what a 0.5 m, two-dimensional, unmigrated survey can
resolve; the steep chalked sets are not constrained; the depth of the chalked cracks is
unknown and is carried as a scenario, not as a distribution.

## 5. Uncertainty-safe clearance and its cost in yield

Two clearance cases are run for every chalk scenario. **As drawn**: 15 cm from each
surface, 10 cm from a chalked crack. **With uncertainty**: 2σ of the ladder (95 %%
coverage), joined with the migrated position, 20 cm from a chalked crack. The paper's
convention is a clearance of one sigma; both C(1σ) = 68 %% and C(2σ) = 95 %% are in the
table above, and the packer takes 2σ because a block that meets a fracture is lost, not
merely mis-sized. Chalked cracks assumed to reach 1.0 m:

""" + yt + """
## 6. Monte Carlo: what each plan risks

`scripts/uncertainty_mc.py` draws %d random truths from the ladder terms (velocity factor
N(1, σv/v); a time-zero shift per channel; a whole-surface vertical shift per surface
from σ interp; a plan registration shift per block; a migration fraction uniform in
0 to 1) and tests every planned block of both cases against each truth: the risk is the
share of truths in which a fracture passes through the block. The risk-weighted tonnage
discounts each block by its risk. %d further truths are re-planned from scratch with the
as-drawn clearance to show the spread of what any plan could yield.

""" % (MC['A']['n_risk'], MC['A']['n_yield']) + mct + """
![Re-planned tonnage over random truths](figs/UNCERTAINTY_mc.png)

The per-block risks are on the Cutting tab of the interface and in each block's
callout. Blocks over 20 %% risk in the uncertain plan sit where the migrated and drawn
positions of a surface diverge or where the registration term is largest; they are the
first to check against a sawn face.

## 7. What would shrink the numbers

1. A core through C-2 near Line 22 or 11: calibrates the velocity in the benches and
   halves the largest term for the deep surfaces.
2. Migrated sections from PARSAN: replaces the migration exclusion with a measurement
   for the two A sheets and B-2.
3. A sawn face or a trench across a chalked crack: turns the chalk-depth scenario into
   a number.
4. A compass on the grid origins and a tape between them: settles east and puts the
   three benches in one frame.

## 8. Consistency with the paper

Same ladder terms and combination rule (GUM quadrature); same velocity term
(½ δεr/εr); same λ/4 floor; the time-zero term the paper added after Xie (2021); the
same confidence metric erf(T/(σ√2)); the same uncertainty-safe clearance idea, taken
here at 2σ rather than 1σ and joined with migration; the same yield cost framing (as
drawn against uncertainty-safe). Differences: σ interp here is a plane residual, not a
kriging posterior (the surfaces were gridded, not kriged); a site registration term is
added; the Monte Carlo per-block risk is new and is what the paper's confidence metric
becomes when applied to a plan rather than to a surface.
"""
doc = doc.replace('%%', '%')
io.open(os.path.join(OUT, 'UNCERTAINTY.md'), 'w', encoding='utf-8').write(doc)
print('UNCERTAINTY.md written')
