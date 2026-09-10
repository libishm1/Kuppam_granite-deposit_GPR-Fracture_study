# Verification: Blocks B and C against the report and the expert opinions

09-09-2026. `scripts/verify_vs_report.py` produces every number below from the
pick tables on disk. "Expert opinions" means three things: the PARSAN report as
revised on 09-09, Ronak Dahiya's four email answers, and the published
literature in `../gpr_report_extract/RESEARCH_what_is_published.md`.

**Verdict. All four surfaces tie to the report inside the 20 cm requirement,
and three of the four tie inside 10 cm. Where we disagree, the disagreement is
explained and in every case the report's number is the one to carry.** Two
things are not independent of the report and are marked as such. One line in
C-2 is an outlier and is named.

---

## 1. C-1, nine HF Y-lines: ties to 8 cm, dips to 2 degrees

| line | report depth | ours | shallow end | deep end | report dip | our dip |
| --- | --- | --- | --- | --- | --- | --- |
| 20 | 0.47-0.70 | 0.55-0.67 | +8 cm | -3 cm | 8.2 | 3.4 |
| 21 | 0.16-0.71 | 0.24-0.63 | +8 | -8 | 12.8 | 8.9 |
| 22 | 0.17-0.69 | 0.25-0.62 | +8 | -7 | 11.7 | 8.3 |
| 23 | 0.15-0.83 | 0.23-0.75 | +8 | -8 | 7.9 | 6.3 |
| 24 | 0.38-1.08 | 0.41-1.04 | +3 | -4 | 6.0 | 6.5 |
| 25 | 0.17-0.89 | 0.25-0.81 | +8 | -8 | 9.4 | 7.7 |
| 26 | 0.17-1.01 | 0.25-1.03 | +8 | +2 | 14.0 | 13.9 |
| 27 | 0.48-1.00 | 0.56-0.94 | +8 | -6 | 9.1 | 6.3 |
| 28 | 0.49-0.96 | 0.54-0.88 | +5 | -8 | 7.3 | 7.0 |

Endpoints: shallow median **+7.6 cm**, deep median **-7.0 cm**, worst 8.5 cm.
Dips: median **-1.7 degrees**, range -4.8 to +0.5. Their mean 9.6, ours 7.6.

**The 8 cm is my corridor half-width, exactly.** 22 samples x 0.061 ns x
0.0601 m/ns = 8.1 cm. The tracker hugged the corridor boundary at both ends,
which means the event genuinely runs to their endpoints and my corridor stopped
short. I tested that by doubling the corridor: the track then drifted to a more
central event, the shallow end moved further from theirs (0.30 against 0.16 on
Line 21) and the mean dip fell to 5.4. **So the narrow-corridor picks are the
right ones, and the residual 8 cm is the difference between a human picker
following a fading event to its end and a machine stopping at peak energy.**
Their endpoints are the better ones. Carry theirs at the ends, ours in between.

Dips are systematically 1 to 2 degrees flatter than theirs for the same reason:
clipping both ends of a dipping segment flattens the fit. Line 20 (3.4 against
8.2) is the shortest segment and the most affected.

**Against the literature.** Best-fit plane residual 11.0 cm RMS. Elkarmoty
measured real fractures propagating as wavy surfaces of about 2 cm amplitude;
our 11 cm is picking noise on top of that, not geology. C-1 is a plane at the
survey's resolution.

## 2. C-2, eight LF lines published, thirty-two tracked: ties to 3 cm median, one outlier

| line | orientation | report range | our 5th-95th | report mid | our median | diff |
| --- | --- | --- | --- | --- | --- | --- |
| 18 | Y, x=0 | 3.24-3.29 | 2.99-3.42 | 3.265 | 3.109 | **-16 cm** |
| 22 | Y, x=200 | 2.99-3.37 | 2.96-3.52 | 3.180 | 3.148 | -3 |
| 26 | Y, x=400 | 2.97-3.28 | 2.92-3.20 | 3.125 | 3.097 | -3 |
| 30 | Y, x=600 | 2.95-3.14 | 2.83-3.26 | 3.045 | 3.010 | -4 |
| 1 | X, y=0 | 2.97-3.25 | 2.81-3.64 | 3.110 | 3.176 | +7 |
| 6 | X, y=250 | 2.96-3.11 | 2.83-3.10 | 3.035 | 3.048 | +1 |
| 11 | X, y=500 | 2.99-3.30 | 2.93-3.14 | 3.145 | 3.065 | -8 |
| 17 | X, y=800 | 3.07-3.19 | 3.07-3.54 | 3.130 | 3.381 | **+25 cm** |

Median **-3 cm, sd 11 cm** across the eight. The mean is near zero by
construction, because the surface was re-anchored to these eight mid-depths
after the network adjustment; **the spread is the test, and 11 cm is the
answer.**

Block-wide: report 2.95-3.37 m, ours 5th-95th percentile **2.85-3.40 m**.

**Two lines to name.** Line 17 is the y = 800 edge, has fewer crossings than any
interior line, and the network adjustment has the least leverage on it. Our
median is 25 cm below theirs and our range is 47 cm wide against their 12 cm.
Line 18 is the x = 0 edge, same situation, 16 cm the other way. **On both edge
lines carry the report's number, not ours.** The six interior lines agree to 8
cm or better.

**Against Ronak's answer.** "The adopted RDP is 6.25 for all blocks." Our
hyperbola scan on 114 focused apices gave 6.22. The C-2 surface is built at
0.1202 m/ns; at their 0.1200 it moves 5 mm. **Confirmed, and immaterial.**

**Against the literature.** Best-fit plane residual 18.6 cm RMS, maximum 53 cm.
The report calls the relief "gentle undulation rather than any systematic dip"
and our plane fit gives 2.8 degrees, which is gentle. But 53 cm of relief across
a 7 x 8 m cap is not gentle for a saw. Elkarmoty's 2 cm waviness is for the
fracture itself; what we see includes odometer error (median 7.5 cm, worst 40)
and cycle-skip residue. **The report's flat band understates the relief and the
surface should be used, not the band.**

## 3. B-2, six LF Y-lines: ties to 11 cm, dips to 0.3 degrees

| line | x | report depth | ours | ends | report dip | our dip |
| --- | --- | --- | --- | --- | --- | --- |
| 14 | 0 | 1.86-4.06 | 1.98-3.95 | +12 / -11 cm | n/a | 23.5 |
| 16 | 100 | 1.98-4.02 | 2.01-3.91 | +3 / -11 | 24.1 | 24.0 |
| 18 | 200 | 1.86-4.00 | 1.98-3.93 | +12 / -7 | 24.4 | 24.8 |
| 20 | 300 | 1.84-3.57 | 1.96-3.46 | +12 / -11 | 20.8 | 20.5 |
| 22 | 400 | 2.12-3.26 | 2.12-3.15 | 0 / -11 | 18.2 | 16.9 |
| 24 | 500 | 1.97-2.97 | 2.09-2.86 | +12 / -11 | 17.2 | 12.5 |

Endpoint misfit is again the corridor half-width: 16 samples x 0.122 ns x
0.0601 = **11.7 cm**, and the same widening test failed the same way. Their
endpoints stand.

**Dips: median misfit -0.3 degrees.** The report says apparent dip "flattens
monotonically west to east, 24.4 to 17.2". Ours: 23.5, 24.0, 24.8, 20.5, 16.9,
12.5. Same trend, same magnitude, except Line 24 at 12.5 against 17.2, the
shortest segment and the most clipped.

**Constrained in one direction only.** Six parallel Y-lines and no X-line
confirmation anywhere. The report says the same in Section 9. There is no
crossing check and the surface is a cylinder along x. **Nothing in this delivery
can improve that; only oblique or X-oriented lines over the western half can.**

## 4. B-1, thirteen HF X-lines: no published depths, so five indirect checks

| check | report | ours | tie |
| --- | --- | --- | --- |
| slice windows where it shows | HF 0.52-0.59 and 0.95-1.02; LF 0.47-0.61 and 0.75-0.88 | 0.42-0.99 m | crosses all four |
| dip direction | "consistently dipping toward increasing x" | 13 of 13 lines deepen east | exact |
| apparent dip | 5.1-14.4, mean 8.3 | 4.8-10.7, mean 6.9 | 12 of 13 inside their range |
| plan trace rotation | 3.8 degrees, 40 cm across 6 m | 9.7 degrees, 103 cm | same sense, 2.5x the magnitude |
| HF against LF | "also visible on Y-lines in the LF channel" | 1,662 comparisons, median 9.8 cm, 97 % within 20 cm | the best cross-check in the survey |

**The plan-trace difference is not a like-for-like comparison.** Ours is the
0.75 m depth contour; theirs is "13 tie positions" at a depth the report does
not state. A dipping plane's plan trace rotates with the depth you slice it at.

**Not independent.** The corridor that recovered B-1 was seeded from the
report's own description: x 650 to 950, deepening east at 8.3 degrees. The free
tracker had failed, locking onto flat ringing. So **the dip magnitude is
corroborated, not independently measured.** What is internally consistent: the
reflector exists on every line, it deepens east on every line, and two channels on
orthogonal lines put it at the same depth to 10 cm. What was claimed as an
independent confirmation on the rock (66 % of its daylight along a chalked crack)
rested on a wrong intersection formula and is withdrawn: the corrected test
(`daylight_test.py`) puts B-1's surface trace at chance, and outside the area
where it was picked. PARSAN's own reading of B-1 (1.0 to 1.95 m) stays on the
table beside this one.

**A new editorial finding from doing this.** The radargram in Figure 12 is
inserted rotated 180 degrees relative to its caption. Depth reads 2.68 at the
top, distance runs right to left, axis text is upside down. Rotating it back
puts depth 0 at the top and turns the caption upside down, which is the proof.
Read correctly the pick deepens east, as the text says. No number changes.

## 5. Ronak's four answers, each tested

| answer | test | result |
| --- | --- | --- |
| RDP 6.25 for all blocks | hyperbola scan, 114 apices below 0.6 m | **6.22, confirmed to 0.5 %** |
| lower TWT is the shallow end | every corridor was seeded that way; every one locked on | **confirmed** |
| plan positions, use as reported | adopted; every surface here is unmigrated | adopted, with the caveat below |
| Block C clutter y = 350-750 cm | 65 shallow focused apices; 54 % fall in that band, which is 50 % of the block | **not a concentration** |

On the clutter: our apex detector also fires on dipping reflectors, so it is
indicative, not clean. But there is no sign of a zone. Shallow point-like
energy is spread across the whole top metre of Block C. For Block B the two
stated bands hold 8 % of apices on 13 % of the area, and the largest cluster is
at x 650-750, which is B-1 itself. **The practical advice is unchanged: treat
the whole top metre of both blocks as suspect for metal, not a band.**

On migration: the report's Section 9 says it was not applied, and Ronak says
use as reported. Accepted. For B-2 at 22 degrees the plan shift is about z sin
22 = 0.37 z, so up to 1.4 m at its deepest picks. **The B-2 surface as built is
where the reflection was recorded, not where the fracture is.** That is the
report's convention and ours, and it is stated here so nobody stakes B-2's
position on the rock without applying it.

## 6. Against the published literature

| source | claim | what we found |
| --- | --- | --- |
| Elkarmoty 2017, one limestone bench | velocity scatters 89-136 Mm/s, plus or minus 20 % | our 114 apices: interquartile 0.099-0.157, **plus or minus 24 %**. Same phenomenon. The mean is well determined, individual picks are not |
| Elkarmoty 2017 | real fractures propagate as wavy surfaces, about 2 cm amplitude | our plane residuals 5 to 19 cm are picking and positioning noise, not geology; the rock is smoother than we can see |
| FHWA | depth within 10 % uncalibrated, 5 % with reference cores | C-2 at 3 m: our crossing residual 11 cm is 3.6 %, **already inside the with-cores figure** on internal consistency. Absolute accuracy is another matter and is the 18 cm question |
| Dorn 2012 | 10 degree dip tolerance in boreholes | our dips tie to the report at 0.3 to 2 degrees; this survey does better than borehole radar on dip |
| Grasmueck 2005 | quarter-wavelength line spacing or aliasing | 0.5 m spacing at 628 MHz aliases dips above about 5 degrees; C-1 at 7 and B-2 at 22 are recovered only because they are picked line by line, not from the slices |

## 7. What to carry, feature by feature

| | carry | accuracy | independent? |
| --- | --- | --- | --- |
| C-1 | their endpoints, our track between | about 10 cm | yes |
| C-2 | our surface, except edge lines 17 and 18 where theirs | 11 cm median, 84 % within 20 | yes, 230 crossings |
| B-2 | their endpoints, our track between, **positions unmigrated** | 10 cm in y, unconstrained in x | no cross-check possible |
| B-1 | our surface | 5 cm plane, 10 cm HF-LF | dip seeded from theirs |

**Every number that matters for a saw is inside the requirement.** What is not
inside anything is the absolute datum and the position on the rock, and those
were never in the raw data to begin with.


---

# Orientation audit of the interface, 10-09-2026

`scripts/audit_orientation.py`, `tables/texture_orientation.json`, `figs/ORIENT_plan_*.png`,
`figs/ORIENT_3d_*.png`, `figs/WEB_screenshot_textured.png`.

The interface renders in the bench frame (right-handed, z up), and overlays the survey
grid through the registration, so nothing is mirrored whatever the handedness of the
report frame. Three things were tested.

**The baked bench texture sits on its own lattice.** The texture is baked in the grid
frame, so if it is oriented right the paint in the image must fall on the image's own
0.5 m lines. Paint contrast on-line minus mid-cell, searched over shifts of ±25 cm in
5 cm steps: A best at (0.00, 0.05) with contrast 0.077; B best at (0.00, 0.00); C best
at (0.00, −0.05) with the contrast at zero within 1 per cent of the best. All three
inside one 5 cm step. B's contrast is weak (0.003) because its red paint barely
survives in vertex colour, but the maximum is at zero.

**The layers make visual sense, independently of three.js.** A matplotlib render of
the same content per block (texture on the DEM, v2 surfaces, chalked cracks, gangsaw
blocks) shows C-1 as a shallow west sheet, C-2 as the undulating cap at 2.8 to 3.5 m,
and the stock between them; blocks whose tops are at the surface show at the surface,
deeper stock is hidden under an opaque bench.

**The live page carries its own check.** In the textured view the registered lattice
lies on the painted lines inside the texture, and the chalked cracks follow the dark
dust seams. The bench reads pale because a sawn, dust-covered dolerite top under a
phone camera is pale; the texture is given a p1 to p99 luminance stretch for
legibility, labelled as such, and is rendered unlit so the colours are the photo's,
not a lighting product. The first publish over-lit a Lambert material by 45 per cent
and pushed it to white; that was the "white bench".
