# Block C 3D model, built from the raw SEG-Y

09-09-2026. Built without waiting for any of the three outstanding answers,
because none of them change the shape of a surface. Two are rigid transforms and
one is anchor points.

## What exists now

| file | what |
| --- | --- |
| `model/C2_surface.dxf` | the base cap, 71 x 81 grid at 10 cm. **Rhino reads DXF natively** |
| `model/C1_surface.dxf` | the shallow fracture, western half |
| `model/C2_grid_10cm.xyz`, `model/C1_grid_10cm.xyz` | same surfaces as plain XYZ |
| `tables/PICKS_C2_adjusted.csv` | 9,481 picks, per trace, with TWT kept so velocity can be changed |
| `tables/PICKS_C1_raw.csv` | 1,292 picks on 9 HF lines |
| `tables/C2_crossing_misfit.csv` | the 230 crossings the surface was validated against |

DXF is in **centimetres with z negative downward**, so it lands at survey scale
with the block top at z = 0.

## C-2, the base cap

Tracked on **all 32 Block C LF lines** by dynamic programming through the 44 to
62 ns window. The report published 8 lines as depth ranges; this is 9,481 picks.

The first pass striped badly, because a 358 MHz wavelet has a 2.8 ns period and
the tracker skipped cycles between lines. Fixed by a **least-squares network
adjustment**: one depth shift per line, solved against all 230 X-line / Y-line
crossings with a robust reweighting, datum fixed by zero mean shift, then
re-anchored to the report's own mid-depths on its eight published lines. The
anchor moved it +4.2 cm, so our tracking and their picking agree to within that.

| crossing misfit | before | after |
| --- | --- | --- |
| median absolute | 7.3 cm | **10.6 cm** |
| 90th percentile | 46.6 cm | **23.6 cm** |
| within 20 cm | 67 % | **84 %** |

The adjustment trades a little median for a much better tail, which is the right
trade when the tail is cycle skips. **Take the surface as good to about 11 cm,
with 84 per cent of independent checks inside 20 cm.**

Result: depth **2.77 to 3.57 m**, mean 3.08. The report's band was 2.95 to 3.37.
Best-fit plane dips 2.8 degrees but the residual RMS is 18.6 cm with a 53 cm
maximum, so **C-2 is not a plane at tolerance** and the flat band in the report
understates the relief.

**The shallowest point is 2.77 m at x = 550, y = 380 cm.** That is the binding
constraint on a single full-height block, and it is 18 cm above the report's own
band minimum.

## C-1, the shallow fracture

Tracked on the nine HF Y-lines the report picked, inside a corridor that runs
between **PARSAN's own published endpoints** on each line. So their
interpretation sets the ends and the data fills in between: 1,292 picks where
they published 18.

Per-line depth ranges reproduce theirs closely, for example Line 24 at 0.37 to
1.04 m against their 0.38 to 1.08.

Best-fit plane **dips 6.9 degrees, down-dip azimuth 31 degrees from +y toward
+x**, residual RMS 11.0 cm. That reproduces the report's stated south-east dip
azimuth independently, and sits inside their 6.0 to 14.0 degree apparent-dip
range. **C-1 is genuinely planar at about 11 cm.**

Footprint 31.6 m2 of the 56, depth 0.19 to 1.20 m. Clearance down to C-2 is 1.88
m at worst.

## Extractable volume

Over the 7.0 x 8.0 m grid, at 2.95 t/m3.

| | volume | mass |
| --- | --- | --- |
| above C-1, western strip | 22.0 m3 | 65 t |
| C-1 down to C-2, western strip | 76.2 m3 | 225 t |
| above C-2, rest of the block | 79.2 m3 | 234 t |
| **total above C-2** | **177.4 m3** | **523 t** |

Planning flat at the report band mid of 3.16 m would give 177.0 m3, so the total
is almost unchanged. **The value is not in the total, it is in knowing where the
2.77 m high spot is**, because a single block cut to the mean would hole through
there.

## Gaps, now that the model exists

**Blocked, needs an answer**

1. ~~Block A cannot be built.~~ **Built, see Block A below.** The axis convention
   was resolved from the report's own Figure 10 against the sketch, A-2 was seeded
   from Figure 7, and A-1's 77 cm non-coplanarity turned out to be a transposed
   depth order on Line 10, found and confirmed in the raw data.
2. **The 18 cm time-zero question** applies to everything here as a single scalar.
   `depth_m` is derived from `twt_ns` in both pick tables, so it re-runs in
   seconds if a fixed offset comes back.

**Not blocked, just not done yet**

3. ~~B-2~~ **done, see Block B below.**
4. ~~B-1~~ **done, see Block B below**, with a caveat on independence.
5. **The second reflector at 3.9 to 4.3 m**, below C-2 on both Line 22 and Line
   11, is unpicked and absent from the report. If real it is a second cap.

**Structural, and no answer from PARSAN will fix them**

6. **No datum.** Every depth is below the antenna, and there is no levelling
   anywhere in the survey. The three block models float relative to each other and
   to the quarry floor. Only a level run ties them together.
7. **No registration.** The grid was never tied to the rock. The internal geometry
   is good, crossings tie at 5 to 10 cm, but its position and azimuth on the bench
   are unmeasured. Tape and compass over the three origins is still the highest
   value hour available.
8. **Along-line odometer error** of median 7.5 cm, worst 40 cm, is already inside
   these surfaces and cannot be removed after the fact.

## To re-run

```
python scripts/pick_c2.py       # track C-2 on 32 lines
python scripts/adjust_c2.py     # network adjustment, grid, DXF
python scripts/build_c1.py      # C-1 corridor tracking, grid, DXF
python scripts/volumes.py       # volumes and figures
```

Velocity is a constant `V` at the top of each picker, currently 0.1202 m/ns from
our own hyperbola scan. The report uses 0.1200. The difference is 0.2 per cent,
about 6 mm at 3 m.


---

# Block B

Built 09-09-2026, same session. `scripts/build_b.py`, `scripts/finish_b.py`.

| file | what |
| --- | --- |
| `model/B1_surface.dxf`, `model/B1_grid_10cm.xyz` | shallow eastern fracture |
| `model/B2_surface.dxf`, `model/B2_grid_10cm.xyz` | deep western fracture |
| `tables/PICKS_B1_raw.csv` | 1,580 picks on 13 HF X-lines. **The report published none** |
| `tables/PICKS_B2_raw.csv` | 969 picks on 6 LF Y-lines, against 12 published endpoints |

## B-2, the deep western wedge

Corridor-tracked between the Table 2 endpoints on the six published LF Y-lines,
the same method used for C-1. Per-line ranges reproduce theirs closely, for
example Line 18 at 1.98 to 3.93 m against their 1.86 to 4.00.

Plane fit: **dip 22.2 degrees, down-dip azimuth 350 degrees from +y toward +x**,
residual RMS 9.7 cm. That sits inside their 17.2 to 24.4 degree apparent-dip
range and reproduces their stated southward down-dip direction.

**Constrained in one direction only.** B-2 appears on Y-lines and nothing else,
so the surface is effectively a cylinder swept along x. The report says the same.
There is no crossing check available and none can be manufactured.

Depth 1.69 to 3.92 m over a 25.0 m2 footprint, 69.9 m3 above it, about 206 t.
Shallowest 1.69 m at x = 500, y = 0, capping the north-west corner.

## B-1, the shallow eastern fracture, and how it nearly went wrong

**The first attempt failed and is worth recording.** With no published depths to
anchor to, a free tracker over the x = 650 to 950 corridor returned apparent dips
of -4.2 to +5.8 degrees against the report's 5.1 to 14.4, and only three of
thirteen lines crossed 0.75 m. It had locked onto flat ringing, because a long
flat event beats a short steep one under any continuity-maximising tracker.

Checking against the report's own Figure 12 turned up why it was hard, and a new
finding: **the radargram image in Figure 12 is inserted rotated 180 degrees
relative to its caption.** Depth reads 2.68 at the top and 0 at the bottom, the
distance axis runs right to left, and the axis text is upside down. Rotating the
image back puts depth 0 at the top and turns the caption upside down, which
confirms it. Read correctly the pick runs from about x = 7.5 m at 0.45 m to
x = 9.3 m at 0.95 m, deepening east, exactly as the text describes.

Re-tracked with the corridor seeded from the report's own description, x 650 to
950 deepening at their stated mean of 8.3 degrees:

- apparent dips **4.8 to 10.7 degrees, mean 6.9**, against their 5.1 to 14.4,
  mean 8.3
- **all thirteen lines deepen toward increasing x**, as the report states
- plane fit dip 6.89 degrees, azimuth 84 degrees, residual RMS **4.8 cm**, max
  11.8 cm. B-1 is the flattest and cleanest surface in the survey.

### The independent check

The report says B-1 is also visible on Y-lines in the LF channel. Tracking it
there gives a genuine cross-check: different channel, orthogonal line direction.

**1,662 comparisons. Median absolute misfit 9.8 cm, 90th percentile 15.8 cm, 97
per cent within 20 cm.** That is the best-validated surface in either block.

### The honest caveat

The corridor was seeded from the report's mean dip, so **the dip magnitude is not
independent of their number.** What is independent is that a continuous coherent
reflector exists there, that it deepens east on all thirteen lines, and that HF
X-lines and LF Y-lines agree on its depth to 10 cm.

Our 0.75 m crossing fits x = -0.172 y + 883 cm against their tie-position fit of
x = -0.067 y + 753 cm. Both rotate the same way. They are not like for like,
because the depth their tie positions correspond to is not stated.

## Volumes

| | footprint | volume | mass |
| --- | --- | --- | --- |
| above B-1, eastern strip | 18.9 m2 | 13.5 m3 | 40 t |
| above B-2, western wedge | 25.0 m2 | 69.9 m3 | 206 t |

**B-1 at 0.46 m caps the eastern 3 m of the block**, which is the harshest
constraint anywhere in the survey. **The 150 cm strip between x = 500 and x = 650
carries no picked feature in either channel** and is the cleanest ground in
Block B on present evidence.

## What Block B changed about the gaps

- **B-1 no longer needs their depths to be modelled**, but it did need their
  described geometry to seed the corridor. Their picks would still convert this
  from corroborated to independent, so the email ask stands.
- **Figure 12's 180 degree rotation is new**, and it is the second figure-level
  error found after Figure 22's line number. Both are editorial, neither changes
  a number.
- **B-2 cannot be cross-checked at all.** One orientation, one channel. That is a
  property of the acquisition, not of the processing, and only oblique or
  X-oriented lines over the western half would fix it.

---

# Block A

Built 09-09-2026, same session, after it had been declared blocked. `scripts/build_a1.py`,
`scripts/build_a2.py`, `scripts/finish_a.py`, `scripts/a1_transposition.py`,
`scripts/walk_direction.py`.

| file | what |
| --- | --- |
| `model/A1_surface.dxf`, `.obj`, `A1_grid_10cm.xyz` | A-1, NE-SW striking, dips NW, daylights in the SE corner |
| `model/A2_surface.dxf`, `.obj`, `A2_grid_10cm.xyz` | A-2, E-W striking, dips toward +y, steep |
| `tables/PICKS_A1_final.csv` | 428 picks on 12 lines. **Report: 2 lines, 4 endpoints** |
| `tables/PICKS_A2_final.csv` | 565 picks on 9 lines. **Report: 5 lines, no depths at all** |

## What unblocked it, item by item

**The axis convention is resolved from the report itself, not assumed.** Figure 10
draws lines 13-24 vertical, stepped along x, and lines 1-12 horizontal, stepped
along y. The field sketch numbers 1-12 along the A0-A1 edge and 13-24 down the
A0-A3 edge. Put together: **report x is distance from A0 along A0-A3, report y is
distance from A0 along A0-A1.** That holds whether PARSAN chose it or applied the
B/C convention by rote, because the along-line distance in the data is what it
is. The field-drawn vertical dashed trace at sketch column 3 is exactly where the
report's A-2 lands under that mapping. The sent question will only confirm this.

**Which end each line was walked from is testable, and was tested.** It is not a
mirror. Four hypotheses per block against every crossing: B and C each pick "both
families from the origin end" with margins of 0.14 and 0.22 in median correlation.
Block A gives a margin of 0.018, with even the wrong hypotheses at 3 to 6 per
cent no-match against 20 to 34 for B and C. **Block A's shallow HF is laterally
uniform ringing and its crossings cannot discriminate.** The best hypothesis is
the same one B and C chose, and the sketch agrees, so it is adopted.

**A-1's 77 cm non-coplanarity was a transposed depth order on Line 10.** In the
report's own frame Line 19 deepens toward +y and Line 10 toward +x, which puts the
down-dip to the NE. But the arrows say NW, the text says SW, and a NE-SW strike
needs NW or SE. Reversing Line 10's two depths makes every statement true at once
and the four points coplanar to under a centimetre. Ronak's email answer covered
TWT-to-depth order, not position-to-depth pairing, so this was still open. The raw
data settles it three ways:

| test | as printed | reversed |
| --- | --- | --- |
| mean envelope along the tracked path | 1.021 | **1.317** |
| minimum envelope along it | 0.628 | **0.966** |
| free track, no ordering imposed, x 380-560 | | 1.57 m at x=381 to 1.35 m at x=545, **shallows with x** |

**Line 10's depths are printed in the wrong order.** Their magnitude, 13.7
degrees, is right; the sign is the finding.

**A-2 was never blocked.** Figure 7 shows it on Line 13 from about 0.45 to 2.3 m
between y 60 and 380 cm, clean between 80 and 230. That is a seed.

## A-1

Four-point plane with Line 10 reversed: dip 26.6, down-dip azimuth 329 (NW),
strike 59 (NE-SW), residual 0.9 cm. Then a hunt along that plane on all 24 lines,
both channels, keeping runs of 40 cm or more with smoothed envelope above 1.25.
Found on **12 lines**, 428 picks after deduplication. The free hunt found Line 10
on its own at 448 to 545 cm running 1.50 to 1.28 m, the reversed direction, with
no ordering imposed.

Refit on all picks: **dip 26.9, azimuth 328, strike 58, residual RMS 3.6 cm, max
8.1.** The report says NE-SW, arrows NW, "14-24 degrees" apparent. True dip above
the apparent range is correct.

**Not independent:** the hunt corridor lay on the four-point plane, so finding
energy there corroborates rather than proves. What is independent: Line 10's
direction from the free track, and that ten further lines lit up where the plane
predicted.

The plane daylights in the south-east corner: at (550, 0) it is 65 cm above the
block top. **That edge of Block A should show the fracture on the face.** Check
it.

## A-2

Seeded on the five stated Y-lines from Figure 7's geometry, HF above 1.3 m and LF
below, then the same hunt on all 24 lines. Kept: the report's own extent, y 80 to
240, on the seeded lines, plus every bright hit. **565 picks on 9 lines.**

| line | fixed x | apparent dip | report |
| --- | --- | --- | --- |
| 13 | 0 | 33.2 | 32-41, mean 38 |
| 15 | 100 | 33.6 | |
| 16 | 150 | 35.2 | |
| 19 | 300 | 39.1 | |
| 22 | 450 | 32.3 | |

Plane: **dip 34.0, down-dip azimuth 1, which is +y exactly, strike 91, which is
E-W exactly, residual RMS 4.9 cm.** The report's "trends approximately E-W" and
"dipping towards increasing Y" are reproduced to the degree.

**The cross-check the report never had.** X-lines run along x at fixed y, so they
should see A-2 as a near-flat reflector whose depth grows with y at the 34 degree
slope. Lines 2, 3 and 4 at y = 50, 100, 150 cm show bright flat runs at 0.45,
0.80 and 1.10 m. The plane fitted to the Y-lines alone predicts those depths with
a **median misfit of 0.9 cm, 90th percentile 2.7 cm, over 120 picks.** Orthogonal
lines, same surface. A-2 is real and it is planar.

Their "position y = 128-148 cm" is where the plane passes about 1.0 m depth.

**Not independent:** the seed dip. The corridor was centred at 35 degrees. Per-line
results of 32 to 39 are data within that corridor, and the X-line check is a
different family of lines with no seed from the Y-lines beyond the plane itself.

## The two planes together

The report puts the A-1 / A-2 intersection near x = 90, y = 135. Ours, at y = 135,
is **x = 147 cm, z = 0.99 m.** Theirs was computed on the transposed A-1, so the
57 cm is not a like-for-like difference.

A-2 daylights near y = 0 to 50 along the whole A0-A1 edge. A-1 daylights at the
SE corner. **Both should be visible on the block faces, and either one seen on the
rock is the registration check for free.**

## What Block A changed about the gaps

- **Nothing in the sent email is wrong,** but question 2 is now answered and
  question 1 is half answered: A-2 has depths, A-1 has ten more lines. B-1 was
  answered by Block B. What remains genuinely unanswerable at this end is the
  18 cm time-zero question.
- **One new item for PARSAN:** Line 10's depth order. Worth one line, because it
  is what makes their own Figure 10 arrows correct.
- Block A's HF is uniform ringing to about 1 m. That is a data property worth
  knowing before anyone tries to pick anything shallow there.

---

# Registration to the photogrammetry, 10-09-2026

`scripts/paint_plane.py`, `redness.py`, `grid_detect.py`, `c_fullres.py`, `register.py`, `package.py`.
Deliverable: `dataset/`, read `dataset/README.md`. Overview: `figs/REGISTERED_all.png`.

## The problem

Three Metashape projects, checked in the `.psx` and chunk XML: **zero markers, zero
scale bars, no GPS, empty chunk transform.** Galaxy A16 phone, Block B on the
1.43 mm ultrawide at 1932 x 2576. So each mesh has its own arbitrary scale and
orientation, and the earlier note that they "cannot be co-registered" was true
as far as it went.

## What broke the deadlock

The survey grid is painted on the rock: white lime on A, red on B and C, with
chalk ticks at every node on B and white corner labels on all three. **Paint is
in the vertex colours, the grid is 0.5 m by definition, and it is coplanar.**
That gives scale, in-plane rotation and position from the mesh alone.

| block | scale m/unit | lattice | evidence |
| --- | --- | --- | --- |
| A | 0.7281 | 12 x 12, 89.9 deg between families | `figs/grid_A_paint.png`: every line on a chalk line |
| B | 0.9843 | 20 x 13, **84.8 deg** | `figs/grid_B_lum.png`: node ticks; mesh is sheared |
| C | 0.6745 | 15 x 17, 90.0 deg, spacings to 0.07 % | `figs/grid_Cfull_red.png`, full 21.5 M mesh |

Two things were withdrawn on the way. The first B result put a 12 x 12 white
lattice in B's mesh and I read it as Block A seen from B; a 20 x 13 window
captured 100 % against 74 % and it is B's own node ticks. And B's 0.5 m red
lines did not survive into vertex colour at all; the red that did is the slab
outline, which slid the first extent by a metre. Both are in the transcript, not
the deliverable.

## What the registration does not do

- **Origin corner.** Four valid placements for A, two each for B and C. C's was
  chosen by paint density outside the corner and matches the photographed C0
  label. A and B are placement #0, unverified. One integer in
  `tables/registration_choice.json`.
- **No inter-block positions.** No mesh contains another block's grid.
- B's mesh is metric to about 5 % and a few degrees. A and C are rigid.

## Accuracy that matters for the saw

On A and C, a GPR surface now sits on the rock to a few centimetres in plan
relative to the painted lines the crew can see. Depth is the report's, with the
18 cm time-zero question still open. The origin-corner choice is the remaining
step change, and it is the tape-and-compass afternoon, unchanged.

## Correction, 10-09-2026, from the painted labels

Libish marked three things on the first registration figures: the A box was one
cell off, the B grid belongs on the central slab right of the seam, and the
origin corners had to come from the rock, not from an enumeration. All three
were right. `scripts/cameras.py`, `backproject.py`, `frames.py`.

**Method.** The Metashape chunks carry every camera's pose and calibration, so a
label seen in a photo can be back-projected onto the bench plane in mesh
coordinates. Cameras were 0.7 to 1.7 m from the marks at 42 to 67 degrees to
the plane, so each hit is good to a few centimetres.

| block | evidence | result |
| --- | --- | --- |
| A | chalk numerals 9, 10, 11 at the ends of lines 9-11 in photo 76, 0.687 units apart = 0.500 m | they mark the wall-side edge at x = 0 (camera had its back to the wall); A0 is 8 lines before the "9"; the box moves **one cell** toward them, numerals now 0.12 m outside the edge |
| B | circle-cross marks B0 (photo 55), B1 (44), B3 (60) | a 9.5 x 6 rectangle fits all three to **4 cm rms**; scale 1.0138 m/unit; B0 at the seam top, 6 m edge along the slab top, 9.5 m running down |
| C | the C0 circle-cross in photo 36, with "W" and an arrow beside it | lands 1.1 m outside lattice corner **k2**, 6.5 m or more from every other corner; my paint-density pick of k3 was wrong |

**Two things withdrawn.** The 20 x 13 dot lattice on B's left slab, which the
first pass took for B's grid, is not the survey grid; the labels put the grid
on the central slab, exactly where Libish drew it. And the code's right-handed
constraint on x, y with z up was wrong: A and C are laid out **left-handed with
z up**, which is right-handed with depth down, the GPR convention. B is the
other way. The rock decides; no handedness is assumed any more.

**Still open.** North. Block C has a "W" painted beside C0 with an arrow, which
is a bearing on the rock and not yet read into the model. Nothing else on the
origin corners is open.


---

# Surface fractures against the GPR, 10-09-2026

`scripts/dem_v2.py`, `crack_map.py`, `sketch_digitise.py`, `chain_and_weed.py`.
Figures `figs/FRACTURES_A.png`, `_B`, `_C`; DEMs `figs/DEM_*.png`. Products in `dataset/`.

## v2: every surface re-datumed to the photogrammetry surface

The bench is not flat. From the meshes, at 10 cm: A relief 31 cm, B 41 cm, C 27 cm;
median slope 2 to 3 degrees. **v1 is kept untouched**; v2 puts each pick below the
surface height at its own (x, y). Corrections are 0.2 to 0.27 m of relief across every
feature, mean within plus or minus 5 cm. On B the surface rises 30 cm over the 6 m
y-axis, so B-2's true dip against horizontal is about 19.5 degrees, not the 22 measured
against the antenna. The two Block B surfaces are disjoint because they are two
features, picked on different channels and line families; the DEM has nothing to do
with it.

## Two independent surface-fracture witnesses

**The crew's sketches.** Each dashed stroke is a fracture they saw, drawn on the
numbered grid, so it is already in the report frame. Digitised by taking the drawn
lattice as one connected component (a short opening keeps it and drops the dashes),
mapping through the 142 to 260 recovered nodes, and chaining dashes whose endpoints
continue within 35 cm and 40 degrees. The hand-drawn grid is wobbly to 9 to 31 cm
median against an affine fit, which is the positional accuracy of everything on it.

| block | dashes | chained traces | total | longest |
| --- | --- | --- | --- | --- |
| A | 51 | 14 | 15.3 m | 2.4 m |
| B | 59 | 25 | 24.3 m | 4.2 m |
| C | 84 | 39 | 34.4 m | 2.0 m |

**The photographs.** Dark-ridge (Sato) detection on all 384 posed photos, skeletonised,
back-projected through the Metashape poses onto the bench, accumulated as persistence
across photos. Paint excluded by colour. Widths from ridge scale times ground sampling
distance: 7 to 54 mm. The persistence raster is dominated by chalk-line *edges*, and
distance-to-lattice alone does not weed them; a trace is chalk when it is **both**
parallel to a lattice axis within 12 degrees **and** on a lattice line within 8 cm.
That removed 12, 2 and 4 traces on A, B, C. What remains: A 59 traces, of which 21
within 30 cm of a sketch dash; B 27, 11 confirmed; C 55, 17 confirmed. The 18.6 m
photo trace on A at 84 degrees is the bench edge.

## Where the GPR planes reach the surface, against the sketch

Distance from each plane's daylight line to the nearest sketch ink, with a null: a
random point in the grid is within 30 cm of sketch ink 27 to 36 per cent of the time.

| plane | v1 flat bench | v2 on the DEM | verdict |
| --- | --- | --- | --- |
| A-1 | 28 % within 30 cm | 31 % | **no better than chance.** One 0.7 m sketch trace runs parallel at 22 cm; a coincidence, not a confirmation |
| A-2 | plane top 7 cm, no daylight | 10 cm | the sketch's E-W dash at y 65 to 70 sits on A-2's 0.25 m contour; suggestive, not testable |
| B-1 | 32 % | **66 %, 2.4x the null** | a 2.3 m sketch trace tracks the daylight over 4 m at 25 cm. **Confirmed on the rock.** |
| B-2 | plane top 1.36 m | 1.18 m | never reaches the surface; cannot be tested this way |
| C-1 | plane top 11 cm | 0.8 m of daylight, 2 m from any ink | not seen at the surface |
| C-2 | 2.84 m | 2.64 m | as expected |

**B-1 closes the geometry.** The report places it at x 650 to 950, dipping east at 5 to
14 degrees. Its plane daylights at x about 200, on the west side, and the crew drew a
4 m fracture there. So B-1 is a shallow east-dipping sheet that outcrops on the west
and is 0.5 to 1 m down where PARSAN picked it. The report's picks and the crew's
crack are the same surface seen at two depths.

**Block C is the important negative.** The sketch's largest system is a NE-SW network
at x 350 to 700, y 100 to 300, at right angles to C-1. It is a steep set the radar did
not pick, exactly what Section 9 of the report says the method is blind to. **The
steep joints that control how a block splits are on the sketch and not in the GPR.**

## Caveats that stay

- Sketch positions are good to the hand-drawn grid, 10 to 30 cm.
- The photo detector finds dark lines. Wet streaks, dust edges and saw marks are dark
  lines too. The sketch is the cleaner witness; the photos add width.
- Width is a ridge-scale estimate at 2 to 4 cm per pixel, so 7 mm means "the thinnest
  the camera could see", not 7 mm.
- The DEM is the bench-plane height of a mesh with no scale control beyond the painted
  grid; on B it carries the 5 degree shear.


---

# Closed by PARSAN's reply, 10-09-2026

Ronak Dahiya answered the three-question email the same day. Each answer was tested
against the raw data before being accepted.

| question | answer | test | status |
| --- | --- | --- | --- |
| Figure 2 (4.74 ns) vs Table 1 (1.67 ns) | 4.74 is the displayed apex, 1.67 the time-zero-corrected TWT; the 3.07 ns is display offset; use corrected values | the raw SEG-Y is already on the corrected axis: their Line 21 pick sits on the raw reflector at its printed TWT (`figs/C_line21_HF_pick.png`), and the HF direct wave peaks at 0.8 ns where air wave plus half a wavelet belongs | **closed. Nothing in the model moves.** Section 2.2 above is answered |
| Block A, lines 1-12 fixed x or fixed y | fixed y, running in x | matches `build_a1.py`/`build_a2.py` and the registration; the reprojection put the numerals at the x = 0 edge | **closed.** Section 2.6's reading of the sketch was wrong; the report's convention stands |
| A-2 depth | 0.50 to 1.35 m, representative 0.93 m at 15.4 ns | our A-2 surface runs 0.6 to 1.8 m over y 82 to 239; hers brackets its upper part | consistent |
| B-1 depth | 0.997 to 1.953 m, representative 1.48 m at 24.5 ns | `scripts/b1_deep_test.py`: a corridor seeded at 1.0 to 1.95 m tracks its own ramp on all 13 lines (1.12 to 1.84 m, identical, at the corridor's 13.5 degrees) with 25 per cent less energy than the 0.5 to 0.9 m sheet; a free track with no seed locks at **0.55 to 0.68 m on both channels**. The report's own slice windows (0.47 to 1.02 m) and Figure 12 (0.45 to 0.95 m) agree with the raw data | **not accepted.** Our B-1 at 0.46 to 0.97 m stands; the emailed depth disagrees with the report and the data and is the one item to put back |

The 18 cm question that ran through every document since 09-09 is gone. The raw
SEG-Y time axis is the corrected one, which is why every pick made here landed on
the report's reflectors without an offset.
