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
is east** on A. The A grid is left-handed with z up, so facing east +y is on the right,
south: y = 0 is the north edge and x = 0 the west edge, **A0 is the north-western
corner**. The mesh's high ground at +x (bearing 72°) is the far end wall.

**Block C.** Photograph 182338, from grid (−2.4, 5.3) looking along grid +x (bearing
82°), shows the ramp on the LEFT and the tan face ahead: **grid +x is east** on C. The C
grid is left-handed, so +y is south and **C0 is the north-western corner**.

![Evidence sheet](figs/ORIENTATION_evidence.png)

## Verdict

All three of the client's statements hold: every bench looks east toward the ramp end,
every origin is the north-western corner, and on Block B east runs from B0 toward B1.
The report's "increasing x is east" is right for A and C and wrong for B, whose grid
was painted with its 9.5 m side across the trench; on B east is +y. The report's "6 m
north–south extent" on B is therefore also wrong: the 6 m side runs east–west.

What this rests on: the ramp being on the north rim at the east end in the satellite
view, which the client's screenshot shows and which a compass on site confirms in a
minute. The cutting order on the page uses these axes (`guillotine_pack.py`, `EAST`);
if a compass says otherwise the order flips and the cuts do not change.

| block | east axis | origin corner | handedness (z up) | source |
| --- | --- | --- | --- | --- |
| A | +x | A0 north-west | left | photo 113557 |
| B | +y | B0 north-west | right | photos 181244, 180430 |
| C | +x | C0 north-west | left | photo 182338 |
