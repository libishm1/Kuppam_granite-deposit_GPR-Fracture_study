# Uncertainty analysis of the Kuppam fracture model and its cutting plan

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
| σv/v | velocity share of depth, ½ δεr/εr | 3.2 % | half the spread of the calibrated permittivities (PARSAN Table 1 pipe and plate in dolerite slabs 6.24 to 6.52, Zond 5.73, this diffraction scan 6.22) about the adopted 6.25; `dataset/velocity/` |
| λ/4 | quarter-wavelength resolution floor | HF 4.8 cm, LF 8.4 cm | v / 4f at the measured peak frequencies 628 and 358 MHz (`tables/spectra.json`) |
| σt0 | time-zero scatter | HF 0.27 ns, LF 1.75 ns (1.6 and 10.5 cm of depth) | standard deviation of the AIC first-break time across the 89 lines per channel (`dataset/velocity/firstbreak_aic.csv`); the time-zero convention itself was closed by PARSAN's email of 10 September |
| σ interp | scatter of the picks about the modelled surface | 3.6 to 14.8 cm | plane residual rms per surface (`tables/structural.json`), the analogue of the paper's kriging posterior |
| σ mesh | h²κ/8 on the 10 cm grid | ≤ 0.1 cm | curvature of the gridded surfaces; negligible |
| σ reg | site term, not in the paper | σxy tan(dip) with σxy = 0.07 m (A, C), 0.16 m (B) | registration of the painted grid to the mesh (lattice scale and the three painted marks) through the dip |
| migration | planar-reflector geometry | carried as a signed offset, not in σ | picks are normal-incidence distances; the true reflection point lies up-dip by d sin(dip); offset taken plane to plane in absolute elevation |
| detection | what the survey does not see | not a number here | steep fractures (the survey is 2D, 0.5 m lines, unmigrated), hairline dry cracks, and the depth of the chalked cracks |

## 2. The tolerance ladder, per surface

σ_total² = (d σv/v)² + (λ/4)² + (v σt0/2)² + σ_interp² + σ_mesh² + σ_reg², at the mean depth
of each surface; C(T) = erf(T / (σ√2)) is the probability that the surface lies within
T of where it is drawn: 68 % at T = σ, 95 % at T = 2σ, and at the as-drawn 15 cm as
tabulated.

| surface | ch. | mean depth | d·σv/v | λ/4 | v·σt0/2 | σ recon | σ interp | σ mesh | σ reg | **σ total** | % depth | C(15 cm) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | HF | 1.37 m | 4.3 | 4.8 | 1.6 | 6.9 | 3.6 | 0.00 | 3.6 | **8.7 cm** | 6 % | 92 % |
| A2 | HF | 1.11 m | 3.5 | 4.8 | 1.6 | 6.3 | 4.9 | 0.10 | 4.7 | **9.3 cm** | 8 % | 89 % |
| B1 | HF | 0.71 m | 2.2 | 4.8 | 1.6 | 5.5 | 4.8 | 0.10 | 1.9 | **7.6 cm** | 11 % | 95 % |
| B2 | LF | 2.80 m | 8.8 | 8.4 | 10.5 | 16.2 | 9.7 | 0.10 | 6.5 | **20.0 cm** | 7 % | 55 % |
| C1 | HF | 0.70 m | 2.2 | 4.8 | 1.6 | 5.6 | 11.0 | 0.10 | 0.8 | **12.4 cm** | 18 % | 78 % |
| C2 | LF | 3.08 m | 9.7 | 8.4 | 10.5 | 16.6 | 14.8 | 0.10 | 0.2 | **22.3 cm** | 7 % | 50 % |

Reading: the shallow HF surfaces are known to 8 to 12 cm and the as-drawn 15 cm
clearance covers them with 78 to 95 % confidence; the deep LF surfaces (B-2, C-2) are
known to about 20 cm, dominated by velocity and the LF time-zero scatter, and 15 cm
covers them with only 50 to 55 % confidence. These totals sit between the paper's
Botticino figures (6.5, 13.2 and 27.8 cm for its three surfaces) for the same reasons:
depth and channel.

## 3. Migration, kept separate

| surface | dip modelled → migrated (elevation frame) | plan shift of the reflection point | migrated plane minus drawn plane, at the same position |
| --- | --- | --- | --- |
| A1 | 28.9° → 32.9° | 0.65 m | -0.59 to -0.01 m |
| A2 | 35.3° → 43.1° | 0.64 m | -0.65 to -0.14 m |
| B1 | 7.9° → 7.9° | 0.10 m | -0.01 to -0.01 m |
| B2 | 20.3° → 21.8° | 0.94 m | -0.29 to -0.13 m |
| C1 | 6.0° → 6.0° | 0.06 m | -0.00 to -0.00 m |
| C2 | 2.7° → 2.7° | 0.14 m | -0.00 to -0.00 m |

For the near-flat surfaces (B-1, C-1, C-2) migration moves nothing. The two A sheets'
reflection points move about 0.6 m up-dip and the planes steepen by 4 to 8 degrees;
B-2's move 0.9 m and its plane steepens by 1.5 degrees. At a given position the migrated
plane is lower than the drawn one (the normal-incidence distance is the vertical depth
times cos(dip)): up to 0.65 m on the A sheets, 13 to 29 cm on B-2. This is the geometric consequence for a planar reflector at
constant velocity, used as an exclusion, not as a correction; migration proper of the
sections is PARSAN's to do.

## 4. Detection rung

The paper's detection rung is calibrated to measured detection rates of open
sub-horizontal fractures in granite (about 80 % and 91 % in its two anchors). Nothing
here can improve on that: no fracture of known position has been exposed at Kuppam yet.
What the rung says qualitatively for this survey: the six surfaces are all gently to
moderately dipping, which is what a 0.5 m, two-dimensional, unmigrated survey can
resolve; the steep chalked sets are not constrained; the depth of the chalked cracks is
unknown and is carried as a scenario, not as a distribution.

## 5. Uncertainty-safe clearance and its cost in yield

Two clearance cases are run for every chalk scenario. **As drawn**: 15 cm from each
surface, 10 cm from a chalked crack. **With uncertainty**: 2σ of the ladder (95 %
coverage), joined with the migrated position, 20 cm from a chalked crack. The paper's
convention is a clearance of one sigma; both C(1σ) = 68 % and C(2σ) = 95 % are in the
table above, and the packer takes 2σ because a block that meets a fracture is lost, not
merely mis-sized. Chalked cracks assumed to reach 1.0 m:

| block | as drawn (15 / 10 cm) | with uncertainty (2σ + migrated, 20 cm chalk) | free heuristic, as drawn | free heuristic, uncertain |
| --- | --- | --- | --- | --- |
| A | 85 t, 12 blocks | 46 t, 7 blocks | 99 t | 67 t |
| B | 281 t, 19 blocks | 254 t, 18 blocks | 287 t | 259 t |
| C | 221 t, 21 blocks | 170 t, 24 blocks | 273 t | 200 t |

## 6. Monte Carlo: what each plan risks

`scripts/uncertainty_mc.py` draws 200 random truths from the ladder terms (velocity factor
N(1, σv/v); a time-zero shift per channel; a whole-surface vertical shift per surface
from σ interp; a plan registration shift per block; a migration fraction uniform in
0 to 1) and tests every planned block of both cases against each truth: the risk is the
share of truths in which a fracture passes through the block. The risk-weighted tonnage
discounts each block by its risk. 30 further truths are re-planned from scratch with the
as-drawn clearance to show the spread of what any plan could yield.

| block | plan | planned t | risk-weighted t | mean block risk | blocks over 20 % | re-planned P10 / P50 / P90 |
| --- | --- | --- | --- | --- | --- | --- |
| A | as drawn | 85 | 64 | 27 % | 5 of 12 | 65 / 68 / 86 |
| A | with uncertainty | 46 | 46 | 0 % | 0 of 7 | 65 / 68 / 86 |
| B | as drawn | 281 | 240 | 12 % | 5 of 19 | 266 / 277 / 291 |
| B | with uncertainty | 254 | 217 | 11 % | 5 of 18 | 266 / 277 / 291 |
| C | as drawn | 221 | 197 | 9 % | 5 of 21 | 192 / 217 / 256 |
| C | with uncertainty | 170 | 163 | 5 % | 3 of 24 | 192 / 217 / 256 |

![Re-planned tonnage over random truths](figs/UNCERTAINTY_mc.png)

The per-block risks are on the Cutting tab of the interface and in each block's
callout. Blocks over 20 % risk in the uncertain plan sit where the migrated and drawn
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
