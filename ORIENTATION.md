# Orientation of the painted grids: where east is, and which corner the origin is

The client, who laid the grids, states three things: the benches all look east; every
origin corner (A0, B0, C0) is the north-western corner of its block; on Block B east is
the direction from B0 toward B1. PARSAN's report reads increasing x as east and the 6 m
side of Block B as north–south. This note tests the client's statements against the
data that exist, without a compass reading.

## What was used

1. **Registered camera poses.** Every photograph's position and view direction is known
   in its block's grid frame from the photogrammetry (`tables/cameras_X.json`) and the
   grid registration (`dataset/bench_frame_m/Block_X/FRAME.json`). The registration was
   verified by drawing the lattice back into the photographs (`figs/REPROJ_*.jpg`): it
   lands on the paint, so a photograph's view bearing in grid coordinates is trustworthy.
2. **What the photographs show.** The pit is a trench with two long walls. One end has a
   haul ramp climbing one wall to the rim (a yellow generator parked at the top), a big
   tan overburden face, and an excavator; the other end has more benches and a rough
   wall.
3. **The client's satellite view** (Google Maps, north up): the pit runs east–west; the
   ramp track leaves along the north rim at the east end; the large tan cut face is at
   the east end; the red dot marks the benches.
4. **The block meshes**: high ground (z above 1.5 m) around each bench, in grid axes.
5. **Sun position** at the photograph times (EXIF): Block A 11:33 IST, sun azimuth 89°,
   elevation 78° (shadows too short to use); Blocks B and C 18:04 to 18:34, sun azimuth
   282°, elevation 7° to 0°, overcast and below the pit wall (no usable shadows or glow).
   No photograph carries a GPS heading. The field sketches carry no north arrow.

## The chain, block by block

**Block B.** Photograph 181244 was taken from grid (7.3, −1.6) looking along grid +y
(bearing 342°). It shows the ramp climbing the wall on the LEFT, the tan face and the
excavator straight ahead. The ramp is on the north rim at the east end of the pit, so
the camera looks east, and the left-hand wall is the north wall: **grid +y is east**.
The B grid is right-handed with z up (`FRAME.json`), so facing east +x is on the right,
to the south. Then x = 0 is the north edge and y = 0 the west edge: **B0 is the
north-western corner**, B1 (0, 6) the north-eastern, B3 (9.5, 0) the south-western.
Photograph 180430, from grid (−0.8, 8.0) looking toward B0, agrees: the registered
origin is the far corner (the client's red dot), the painted B1 is by the camera, the
tall sawn wall is at +x (the south wall, 8.5 m from the bench centre in the mesh), and
the bench with the white lattice beyond B0 lies to the west (it is Block A).

**Block A.** Photograph 113557, from grid (−3.1, 3.0) looking along grid +x (bearing
96°), shows the same ramp on the LEFT, the same tan face and excavator ahead: **grid +x
is east** on A. Confirmed on 12 September by the crew's own numbering (below), after being
wrongly overturned for two hours that day. The A grid is left-handed with z up, so facing east +y is on the right,
south: y = 0 is the north edge and x = 0 the west edge, **A0 is the north-western
corner**. The mesh's high ground at +x (bearing 72°) is the far end wall.

**Block C.** Photograph 182338, from grid (−2.4, 5.3) looking along grid +x (bearing
82°), shows the ramp on the LEFT and the tan face ahead, which was read as **grid +x is
east** on C. That reading is **superseded** — see "Block C's east axis is +y, 12 September"
below. The photograph fixes the east *direction*, which nobody disputes; what it cannot fix is
which painted axis carries that direction, and on C it was assigned to the wrong one.
**C0 is the north-western corner** either way.

![Evidence sheet](figs/ORIENTATION_evidence.png)

## Verdict

All three of the client's statements hold: every bench looks east toward the ramp end,
every origin is the north-western corner, and on Block B east runs from B0 toward B1.
The report's "increasing x is east" is right for A and wrong for B and C. The origin is the
north-western corner on every bench and both axes run into the bench, but which axis the crew
walked first differs: on A the X-lines are stacked north to south and run east, so +x is east; on
B and C the X-lines run north-south and +y is east. On B the grid was painted with its 9.5 m side
across the trench, so the report's "6 m north–south extent" is also wrong: the 6 m side runs
east–west. On C east is +y along the 8 m side (corrected 12 September, below).

What this rests on: the ramp being on the north rim at the east end in the satellite
view, which the client's screenshot shows and which a compass on site confirms in a
minute. The cutting order on the page uses these axes (`guillotine_pack.py`, `EAST`);
if a compass says otherwise the order flips and the cuts do not change.

| block | east axis | origin corner | handedness (z up) | source |
| --- | --- | --- | --- | --- |
| A | +x | A0 north-west | left | photo 113557, photo 113938, and the crew's numbering: X-line numerals 9, 12 ... run down the WEST edge from A0 (client, on site, 12 Sep); 5.5 x 5.5, no length test exists |
| B | +y | B0 north-west | right | photos 181244, 180430; the 6 m side, client-confirmed |
| C | +y | C0 north-west | right | site photographs and the surveyors' sketch correlated to the photogrammetry mesh; the 8 m side (corrected 12 Sep) |

## Confirmed by the client on the mesh, 11 September

Asked directly which side of Block B runs east, the client confirms from the photogrammetry mesh
that **the shorter, 6 m side runs east**: B0 to B1 is the east direction, so +y is east on B and
+x is south. That is the reading already used everywhere here and in the cutting order, and it is
unchanged. Note that B0 sitting at the north-western corner is true under either reading and does
not by itself decide the question; the length of the side that runs east does.

### What the dip directions become

| surface | grid bearing of dip | azimuth | reading |
| --- | --- | --- | --- |
| A-1 | 328 | 212 | dips SSW at 29 deg |
| A-2 | 359 | 181 | dips S at 35 deg |
| B-1 | 094 | 184 | dips S at 8 deg, direction poorly determined |
| B-2 | 347 | 077 | dips ENE at 20 deg |
| C-1 | 026 | 116 | dips ESE at 7 deg, direction poorly determined |
| C-2 | 271 | 001 | dips 2.5 deg, direction not determined at all |

Grid bearing runs 0 at +y and 90 at +x. It becomes an azimuth through the handedness: on A
+x is east and +y south, so azimuth = 180 minus bearing; on B and C +y is east and +x south, so
azimuth = bearing plus 90. C's two rows changed on 12 September when its east axis was corrected;
A's two rows were changed the same day and changed back within two hours (below). In every case
the **dips did not change**, only the compass direction they point in. Only A-1, A-2 and B-2 have a dip direction worth quoting; the other three are too
close to flat, and C-2's local dip directions scatter over 101 degrees.

The surface names carried an older reading and are corrected: B-1 was labelled "dips east" and dips
south; A-1 was labelled "NW" although it covers the whole bench and dips SSW; A-2's "+y" is south.

### The registration was read wrongly, and now confirms the reading

An earlier draft of this note recorded that registering the three models into one frame contradicted
the +y reading on Block B. That was an error of mine, not a disagreement in the data, and it is
withdrawn.

The mistake: a block's mesh frame is **not** its painted grid frame. Each `FRAME.json` carries the
grid's own origin and axis directions inside the mesh frame, and a grid corner at (X, Y) metres sits
at `origin x scale + X * x_dir + Y * y_dir`. Those axes are rotated differently in each block, by
16 degrees on A, 272 on B and 347 on C. I had compared mesh axes and called them grid axes.

The mapping is confirmed against the paint itself. Block A's grid is white lime: points within 4 cm
of a predicted grid line are 10.9 brightness units lighter than points between the lines, and under
the mesh-axis assumption that signal drops to 0.2.

Read correctly, the registration agrees with the client:

| block | painted east axis, expressed in the site frame | corner picked by hand in the model |
| --- | --- | --- |
| A, +x east | 342.2 deg | 343.4 deg |
| B, +y east | 342.3 deg | 343.3 deg |
| ~~C, +x east~~ (withdrawn, see below) | ~~346.6 deg~~ | ~~346.2 deg~~ |

The three east axes span 4.4 degrees, so they are parallel on the ground, which is what the client
said from the start: the same convention and the same orientation on all three benches.

**The C row is withdrawn as of 12 September, and the parallelism above must not be read as
supporting it.** This whole table is computed from the frame files, and C's frame file is now known
to be 90 degrees wrong: it places C's 8 m side at bearing 193 in the model frame, pointing **south**,
where the site photographs and the surveyors' sketch both put that side facing **east** toward the
ramp. Both readings are internally parallel, which is what makes this trap so easy to fall into:

| axes used | with C east = +x | with C east = +y |
| --- | --- | --- |
| frame-file axes | parallel, 4.4 deg spread | fails, 85.7 deg |
| hand-pinned axes, which the model actually draws in | fails, about 90 deg | **parallel, 2.1 deg** |

Parallelism alone therefore decides nothing here; it is satisfied either way. What breaks the tie is
the one thing neither frame can argue with: **the side that faces the ramp measures 8 m**, and only
the pinned reading puts the 8 m side to the east. An earlier version of this section relabelled the
C row to "+y east" while keeping 346.6 and claimed the direction had not moved. That was wrong and
is retracted: in the frame-file world the direction does move, by 90 degrees. The corners
clicked by hand in the site model land within 1.2 degrees of the axes the frame files predict, on
every block, which is independent of both the registration and the photographs.

One indication still points the other way and is kept here: of the three surfaces whose dip
direction is well determined, A-1 (212), A-2 (181) and B-2 (077) span 135 degrees. Had A's east
axis been +y they would read 058, 089 and 077, a 31 degree spread. On 12 September that argument
was allowed to flip A for two hours, and it was wrong: the crew's numbering on the ground says +x
is east on A, and a plausibility argument does not outrank a field observation. Three benches need
not share one joint set. This stays as it is, unexplained, and that is the honest state of it.

**A compass bearing on the B0 to B1 line would still close the question outright**, and costs a
minute on the next visit. Nothing about the cuts depends on it; the order of removal and every
compass direction in these documents do.

## Block C's east axis is +y, 12 September

**Corrected: on Block C the east direction runs along the painted +y axis, the 8 m side, not +x.**
`EAST` now reads `{'A': '+x', 'B': '+y', 'C': '+y'}`.

Nothing about the east *direction* changed. Every source agrees the benches look east toward the
ramp at about 103 to 108 degrees in the site model. What was wrong was which of C's two painted
axes was said to carry that direction, and therefore whether C's east side is 7 m or 8 m.

### What settled it

| evidence | says C's east side is | independent of |
| --- | --- | --- |
| the client's site photographs: C0 toward C1 faces the ramp | the C0-C1 side | the model entirely |
| the surveyors' hand sketch correlated to the photogrammetry mesh | 8 m | the model entirely |
| the line counts: 17 X-lines at fixed y span 8.0 m, 15 Y-lines at fixed x span 7.0 m | +y is the 8 m axis | the photographs |
| the hand-clicked corner ring: first side 8.83 m, nearer 8.0 than 7.0 | the 8 m side | the sketch |

Two field observations and two independent properties of the dataset agree. The frame files are the
only source that said +x, and a frame file names axes; it cannot see which side the crew walked
first.

### What this changed

Re-running `stereonet_radar.py` moved **C's two dip directions and nothing else**:

| surface | dip | dip direction before | after |
| --- | --- | --- | --- |
| C-1 shallow sheet | 6.6 deg, unchanged | 154 | 116 |
| C-2 base cap | 2.5 deg, unchanged | 269 | 001 |

The two conversions differ by an exact reflection, `new = 270 - old`, which both rows satisfy; A's
and B's four rows are untouched. **Dips are frame-independent and did not move.** Both C surfaces
are too close to flat for their dip direction to carry weight in any case.

Re-running `guillotine_pack.py` left every block footprint, volume and cut count **byte-identical**
and resequenced C's removal order on 16 of its 17 blocks, which is the whole point of the east
label: it decides which end of the bench is freed first. The published plan still reads 42 blocks,
177.4 m3, 524 t, classes 15/1/24/2, 164 cuts, 113 waste pieces.

## Block A's east axis is +x, and was flipped and flipped back, 12 September

**Stands: on Block A, +x runs east and +y runs south; the grid is left-handed.** `EAST['A']` reads
`'+x'`, as it did before today.

### What settled A

The crew's own numbering, from the client on site: **walking from A0 at the north-western corner
down to the south-western corner, the line numbers 9, 12 ... are painted along that west edge.**
From `PICKS_A*_final.csv`, lines 1 to 12 are X-lines at y = 50(n-1) cm and lines 13 to 24 are
Y-lines at x = 50(n-13) cm, so those are X-line numbers. The X-lines are therefore stacked north
to south, each starting at the west edge and running east. +y indexes them, so **+y is south**;
+x runs along them from the numbered end, so **+x is east**.

Two photographs agree, and had all along:

- **20260819_113938**, the one A's frame is anchored to: numerals 9, 10, 11 along the near edge,
  spread left to right, each labelling a line receding from the camera. With the near edge as the
  west edge the camera looks east: receding is east, +x; left to right is north to south, +y.
  Left-handed. Exactly the picks' convention.
- **113557**: looking along grid +x, the ramp on the LEFT, which is north. Consistent.

That also closes what `FRAME.json` records as `"origin_corner_ambiguity": "4-fold (square),
unverified"`: A0 is the north-western corner and the X numerals run down the west edge from it.

### The flip, recorded because it was wrong for two hours

The client had said "A's x axis runs north to south", meaning the X-lines as a sequence run north
to south. I read it as the +x coordinate pointing north-south, and let two plausibility arguments
carry it - that one crew would use one convention on all three benches, and that A-1, A-2 and B-2
would then close from a 135 degree spread to 31. Both are plausible. Neither is a measurement, and
this document already said "three benches need not share one joint set". The correct reading of
photograph 113938 was sitting in this section labelled a counter-indication. `EAST['A']` was set
to '+y', the stereonet, packing and site model regenerated, and the films sent to re-render.
Reverted on the client's clarification; the packing footprints and removal order and the
stereonet table are byte-identical to the state before the flip. Nothing reached production.

The lesson is the same one as this morning's C error and is worth stating once more: **a
coherence argument is not evidence about which axis a crew painted first.** A is square, so no
length test exists; the painted lattice is 12 lines at 0.500 m in *both* directions, so no paint
test can ever settle it; and the frame files are disqualified on C. The only things that can
decide A are the crew's numbering and a compass, and the numbering has now been read.

### What this leaves

| bench | +x | +y | east | handedness | first family walked |
| --- | --- | --- | --- | --- | --- |
| A | 105.0, east | 195.0, south | +x | left | east-west, numbered down the west edge |
| B | 193.3, south | 103.3, east | +y | right | north-south |
| C | 193.0, south | 103.0, east | +y | right | north-south |

Origin north-west on all three, both axes into the bench on all three, three east axes parallel to
2.1 degrees. The handedness differs because on A the crew walked the first family east-west and on
B and C north-south. That is all it is.

`numbers_check.py` now carries per-bench handedness guards from the field (A left, B right, C
right) and a guard that every east axis, whichever name it carries, points at about 104 degrees in
the model frame. A guard demanding one convention for all three was added and removed the same
day; it encoded the assumption, not the field.

### A second counter-indication, noted by the client late on 12 September

Looking at the joints on the bench walls, the client's intuition is that A's sheets should run
east to west, whereas the model has them dipping north to south: A-1 toward 212 at 28.8 degrees,
A-2 toward 181 at 35.1. Under the alternative reading (A east = +y) they would dip toward 058 and
089 - an east-west dip axis, matching the walls, and the same reading that closes the three
cross-bench dip directions from 135 to 31 degrees. So the walls and the cross-bench coherence point
one way; the painted numerals 9, 12 ... running down the west edge from A0 point the other.
PARSAN's frame on A is +x east, +y south, the same as ours, and Ronak's "A-1 getting deeper
towards SW" supports the current reading - but only if PARSAN's compass is right on A, which it is
not on B or C. **Recorded, not acted on.** Two things settle it on site: on which walls the sheets
appear inclined (a sheet dipping south is inclined on the east and west walls and near-horizontal
on the north and south walls; a sheet dipping east or west is the reverse), and a compass bearing.

**Settled by the photogrammetry, 13 September 00:30 - and it is the picks, not the frame.** The
client supplied two photographs (20260819_183034, north wall; 20260819_183354, south wall) showing
the same sheet dipping down from west to east at 30-40 degrees, continuing the surface crack on A.
Checked in A's own bench frame from `cache/facets_A.npz`, no compass: the moderately dipping
(25-60 degree) planar faces immediately west of A (grid x -4..0) dip toward **+x, 73 % of 942
points, median dip 39 degrees**; around A as a whole they dip +x, -y and +x-y (east, north,
north-east; 21,580 points). The GPR sheets in the same frame dip toward +y and -x (A-1 bearing 328,
A-2 bearing 359: south, south-south-west). Rock and sheets disagree by 90-120 degrees in one
coordinate system. Because the client places those faces at -x and dipping toward +x, the frame's
+x is east: the frame, the texture, the numerals reading and `EAST['A'] = '+x'` are all right.
**What is transposed is A's picks** (x and y swapped relative to the painted grid). Transposing
them gives A-2 toward +x (089) and A-1 toward +x-y (058), matching the wall population, and is the
same transformation the surface-crack test selected (7 degrees against 33). Not done: unlike C it
moves the sheets relative to the grid, so A's cut plan, its 8 blocks and 48 t, the films' headline
numbers and the stereonet card all change; and the provenance of the X/Y assignment in A's picks
(which raw PARSAN lines were called X-lines, and why) must be checked first. A fresh-session job.

**Taken further at 01:00 on the 13th, and held.** Figures saved: `joint_mapping/figs/FACETS_A_vs_GPR_plan.png`
and `_net.png` (facet segmentation of A's photogrammetry against the two GPR sheets, bench frame, no
compass; table `joint_mapping/tables/facets_A_vs_gpr.json`) and `joint_mapping/figs/A_RADARGRAMS_X_vs_Y.jpg`
(HF radargrams of lines 3, 6, 19, 22 from the raw SEG-Y). What they show: on the stereonet both sheet
poles as drawn sit in an empty part of the net where the rock has no faces, and both transposed poles
land inside the rock's clusters, A-2's in the middle of the faces west of A. On the radargrams the sheet
is inclined only on lines 13-24 (line 19 and 22: a clean reflector descending from the line's start end
to ~2 m at 4 m along, the 34 degree apparent dip; picks: +0.66 depth slope on that family, +0.01 on
lines 1-12); lines 3 and 6 show diffraction arches and no comparable sheet. So the sheet dips along the
13-24 family's direction, deepening away from those lines' start.

**Everything hinges on which way lines 13-24 physically run, and the evidence is split by kind.**
For east-west (sheet dips east, client right): the rock faces, the wall photographs, the crack test,
the cross-bench coherence. For north-south (sheet dips south as drawn, and the east-dipping joint is a
second set the picks never traced): the chalk numerals 9-11 back-projected through the camera pose in
`frames.py` step along the frame's +y, south in the site frame where A sits by ICP with +x parallel to
B's and C's east - which puts lines 9-11 at fixed y, so 1-12 run east-west and 13-24 north-south, as
`geom()` assumes. That back-projection is a measurement, not a memory, so the transposition was NOT
applied on the weight of the other side alone.

**The test that decides it from the data:** the surface cracks crossing each line produce vertical
ringing "curtains" in the radargrams (at ~0.7 m along lines 19 and 22, mid-line on 3, near the end of
6). Predict where the mapped cracks cross every line under each hypothesis (`surface_cracks_A_weeded.csv`
against the line paths as drawn and transposed), extract the curtain positions from all 24 HF
radargrams, and score both. About an hour; uses no compass and no memory. Where the provenance sits:
`build_a1.py`/`build_a2.py` work in PARSAN's frame (`geom()`, the published seed picks, the corridors);
`finish_a.py` writes the finals and grids and prints "report frame (x along A0->A3, y along A0->A1)";
`radargram_panels.py` places panels from `tables/GEOMETRY_resolved.csv`. If the transposition is
confirmed, apply it once in `finish_a.py` (and A's rows of `GEOMETRY_resolved.csv`), not in the
builders, then re-run stereonet, packing, dem_v2 A, package, site data, bundles, numbers_check (the
published plan totals change), films, push, and put the Block A page to the client's eyes.

**The curtain test was run at 01:40 on the 13th (`scripts/curtain_test_A.py`,
`figs/A_CURTAIN_TEST.png`, `tables/curtain_test_A.json`) and is inconclusive.** Curtain detection
works: deep-window (24-38 ns) ringing relative to a 1 m running median finds 46 clear curtains on
the 24 HF lines (line 18 at 3.05 m, line 21 at 2.0, line 22 at 1.55 and 5.15, line 19 at 3.25 ...).
The crack side failed: the photogrammetry crack polylines carried into the grid through `FRAME.json`
land a metre off the weeded table of the same cracks, and registering them by endpoint matching
gives a median shift of (1.34, 0.43) m with a 2 m residual spread - the polylines and the table do
not relate by one shift, so the predicted crossings are unreliable. With those crossings every
variant sits at random: precision 0.12-0.15 against a random 0.15-0.16 (z from -1.3 to +0.1) for
as-drawn and transposed, either along-track direction. **No verdict from it.** To make it work, the
crack polylines need a trustworthy grid placement (re-run `crack_map.py` through the current frame, or
use the chained sketch traces if their frame is established), and a curtain-only comparison would
then be quick.

**Where A stands after the night's work.** For the sheets dipping east: the rock's moderately dipping
faces around A dip +x 27 %, +x-y 18 %, -y 26 %, and only **5 %** dip +y, where both GPR sheets point;
the client's two wall photographs; the surface-crack fit (weak, one sinuous crack); cross-bench
coherence (plausibility). Against: the chalk numerals 9-11 back-projected through the camera pose in
`frames.py` step along +y = south, which puts lines 1-12 east-west and 13-24 north-south, and the
radargrams show the picked sheet inclined only on 13-24 - so it dips south. The two are compatible
only if the picked sheet and the wall joint are different sets: a south-dipping sheet under the bench
that the radar sees, and an east-dipping set on the walls that the picks never traced. That is what
the data says as it stands, and **nothing was transposed.** Even were the picks misplaced, the fix is
a transposition of x and y, not a 90 degree rotation, which would swing the lines off the painted
square.

**Resolved at 02:10 on the 13th by the technician's own field sheet, not by a compass.**
`reference/parsans/report/raw/GPR Raw data_Kuppam/A Block/A Block sketch.pdf`, dated 20 August, the
survey day (rendered to `figs/A_TECHNICIAN_SKETCH_20260820.png`). It shows Block A with corners A0
(top-left), A1 (top-right), A2 (bottom-right), A3 (bottom-left); **lines 1-12 numbered along the
A0-A1 edge**, each with its start tick there, running across to the A3-A2 edge; **lines 13-24
numbered down the A0-A3 edge**, running across to A1-A2. That is exactly the pipeline's
`geom()` and `finish_a.py`'s "report frame (x along A0->A3, y along A0->A1)": lines 1-12 sit at
fixed y (their positions along A0-A1) and run along x; lines 13-24 sit at fixed x and run along y.
So the picks are in the frame the technician drew. Which way is that frame on the ground?
`frames.py` back-projected numerals 9, 10, 11 through the camera pose: they step along FRAME.json's
+y, which in the site frame is 197.8 degrees - north to south - with the numerals "just outside the
x = 0 edge" and the grid on the +x side. So the A0-A1 edge is the **west** edge, A0 at its north
end, lines 1-12 run **east-west** (+x = 107.8 degrees, parallel to B's and C's verified east), and
lines 13-24 run north-south. The technician simply drew the west edge along the top of the page.
The client's memory - numerals 9, 12 running down the west edge from A0 - was right all along;
the client's own clicked corners in the site model use a different corner naming (A0-A1 along the
north edge), which is why the pinned frame carries +x along the 105 degree side; the directions
agree.

**Therefore: picks, frame file and pinned ring are all in one frame on A. Nothing is transposed.
`EAST['A'] = '+x'` stands. The GPR sheets A-1 and A-2 dip south, as modelled** - and the
radargrams say the same: the sheet is inclined on lines 13-24, which run north-south. PARSAN's
"A-1 getting deeper towards SW" agrees. **The east-dipping joint in the client's wall photographs
is real and is a second set the picks never traced.** The facet analysis says so directly: around A
the moderately dipping faces dip east and north-east at about 39 degrees, only 5 per cent dip
south, and the surface cracks strike roughly north-south (grid bearing 014-047) - the strike of an
east-dipping set, not of A-1 (058) or A-2 (091). That is also why the surface cracks never fitted
the modelled sheets: they belong to the other set. The south-dipping sheets would show on the east
and west walls; the east wall of A has almost no exposed face in the mesh (10 facet points), and the
west side is dominated by the east-dipping set, so their absence from the walls is not evidence
against them.

**Consequence for the block plan on A:** an east-dipping set at 30-40 degrees, daylighting on the
west side of A and crossing under the bench, is not in the model and not in the cut plan. It should
go to the geologist and to PARSAN (were east-dipping reflectors present on lines 1-12 and left
unpicked? lines 3 and 6 show diffraction arches in that window). Until then the Block A plan is
conditioned on two south-dipping sheets and silent on the east-dipping set.

**Closed at 03:30 on the 13th: the last place a 90 degree flip could hide was A's placement in the
pit, and it is excluded by number.** `joint_mapping/tables/icp_site.json` records the coarse yaw
scan that placed A's mesh into C's frame, every 2 degrees: the score (fraction of points within
10 cm inside the overlap) peaks at **yaw 326: 0.867**; the three rotated alternatives score
**56: 0.608, 146: 0.627, 236: 0.591**; 240 random poses average 0.007 (p95 0.018). The refined fit
at 326.2 reaches rms 4.9 cm, median 3.1 cm, 90.3 % within 10 cm, with `vertical_faces_support`,
`sharp_optimum`, `beats_second` and `above_strict_null` all true; the runner-up is the same yaw
6.6 m away, not a rotation. A square bench with its surroundings gives rotated placements a partial
fit, which is why the alternatives are not zero, but a 90 degree error in A's placement - and with
it the transposition of the picks - is ruled out.

**The LF records then say what each set is** (`joint_mapping/figs/A_RADARGRAMS_LF_east_dipping_test.jpg`,
0-66 ns = 0-4 m): on lines 16 and 19 (north-south) the radar shows steep reflectors at 35-40
degrees, several parallel members, descending southward - unmistakable; on lines 3, 6, 9 and 12
(east-west) there is nothing along the path an east-dipping 39 degree sheet from the wall face at
x = -1.7 m would have to follow (1.4 m deep at the west edge, 4 m by x = 3), only sub-horizontal
banding and gentle features under 20 degrees. So the radar's set dips south and the wall set dips
east, both at 30-40 degrees, near-perpendicular in direction. The facet study in `joint_mapping/STUDY.md`
had already found the walls' moderately dipping faces split into a NE-dipping population (028-069)
and a SW-dipping one (224-251) at about 46 degrees - a conjugate pair - and A-1's 212 sits with
the SW-dipping population. **The likeliest reading: two conjugate sets; the radar traced the
less-exposed one, the walls show the dominant one, and the dominant one does not continue under
the bench at a depth the radar resolves, or is too tight or healed to reflect.** Which of those is
the geologist's "joint character" question. Genuine geology, not an axis error.

**Client, 03:45:** recalls a south-dipping joint on A's north face. A-2's plane daylights at
y = -0.16 m, the top of the north edge, dipping 34 degrees south into the bench, so that is where
the radar's set should show on the rock. The mesh does not corroborate it (0-3 % of moderately
dipping faces along the north edge dip south, 45-48 % dip east), but a south-dipping surface on a
north-descending face turns away from the cameras and is what photogrammetry from above misses.
Recorded as a field observation consistent with the radar, to be photographed next visit and put
to the geologist beside the east-dipping set.

### The surface cracks on A still do not follow the sheet, and that is separate

The client observed that A's surface cracks do not look like they belong to the sheet beneath. They
do not, and no east-axis reading explains it - an east label maps grid bearings to compass azimuths
and cannot move the cracks relative to the sheet, because that relationship lives entirely in the
grid frame.

Crack orientation is the fitted `angle_deg` from `surface_cracks_*_weeded.csv` converted by
`bearing = 90 - angle_deg`; strike is a least-squares plane through the surface's own 10 cm grid.
Axial grid bearings:

| bench, sheet | dip | strike | cracks | off strike, as drawn | if transposed |
| --- | --- | --- | --- | --- | --- |
| **B, B-2** (control) | 22.1 | 080 | 089 | **9 deg** | 79 deg |
| C, C-1 | 7.1 | 122 | 130 | 8 deg | 19 deg |
| A, A-1 | 26.8 | 058 | 025 | **33 deg** | 7 deg |
| A, A-2 | 33.7 | 091 | 025 | 66 deg | 26 deg |

The crack tables are in the picks' own frame on every bench, which their extents prove: B's spans
x 0.04 to 9.28 and y 0.04 to 5.88 against a 9.5 by 6.0 grid, C's spans x 0.04 to 6.96 and
y 0.04 to 7.92 against 7.0 by 8.0, each fits as written and neither fits transposed. So A's
33 degrees is real, and it is not a frame error. It is weakly determined: A's crack mean swings
33 degrees across three defensible weightings (014 by traced length, 025 by endpoint length, 047
unweighted), its concentration is R 0.19 to 0.41 against B's 0.35 to 0.58, and 38 per cent of A's
entire traced crack length is a single 18.62 m crack, straightness 0.26, the most sinuous in the
set. A-1's strike and A-2's are 31 degrees apart, so A's cracks cannot follow both sheets.

**The observation stands as a question for the geologist**, together with whether A-1 and A-2 are one
joint set at all. See `figs/A_ROTATION_CHECK.png`. Nothing was changed on the strength of it.

### What is still not closed

A compass bearing on any one of the three benches would tie the whole thing to true north, which no
source here does; north comes from the satellite view. It costs a minute on the next visit. With C
corrected, the removal order and every compass direction in these documents depend on it, and the
cuts do not.
