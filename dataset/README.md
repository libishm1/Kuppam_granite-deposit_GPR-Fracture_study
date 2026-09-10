# Kuppam GPR dataset: fracture surfaces on the photogrammetry

10-09-2026. Blocks A, B and C, each registered to its own photogrammetry mesh
by detecting the painted 0.5 m survey grid in the vertex colours. Every block
is delivered in one metric frame so its point cloud, surfaces and grid load
together in Rhino, CloudCompare or anything that reads PLY and OBJ.

**Look at `OVERVIEW.jpg` first.**

## The frame, per block: `bench_frame_m/Block_X/`

| file | what |
| --- | --- |
| `Block_X_pointcloud.ply` | coloured point cloud of the bench and walls, metres. A 298 k, B 230 k, C 600 k from the full 21.5 M mesh |
| `X1_surface.obj`, `X2_surface.obj` | the two GPR fracture surfaces, 10 cm grid |
| `X1_surface.dxf`, `X2_surface.dxf` | same, as 3DFACE for AutoCAD/Rhino |
| `Block_X_grid.obj` | the 0.5 m survey lattice as polylines, on the bench |
| `FRAME.json` | the exact transform from Metashape units and the report frame |
| `X1_surface_v2_topo.*` | **v2**: the same surface re-datumed to the real bench height at each (x, y). v1 kept beside it |
| `BlockX_DEM_10cm.xyz` | bench surface height above the bench plane, report frame, from the mesh |
| `Block_X_sketch_cracks.obj` | the field-sketch surface fractures, chained, draped on the DEM |
| `Block_X_surface_cracks_v1.obj` | dark-line traces from the photos, on the DEM |

Frame definition: origin and axes are the **report frame**, x and y as PARSAN's
tables use them, but rotated and translated into the bench plane. **z is up,
bench top = 0, depth is negative.** Units metres. The bench plane is the plane
through the painted grid, fitted to the paint-coloured vertices.

## How the registration was done, and what it is worth

Each mesh is a separate Metashape project with **no markers, no scale bars, no
GPS** (Galaxy A16 phone, checked in the `.psx`). Scale and orientation were
recovered from the painted grid itself:

| block | paint | scale, m per mesh unit | lattice angles | lines found | fit |
| --- | --- | --- | --- | --- | --- |
| A | white lime | **0.7281** | 16.0 / 106.0 deg, 89.9 apart | 12 x 12, 92 % / 90 % of contrast | rigid, clean |
| B | red; frame from the B0/B1/B3 marks | **1.0138** | rectangle fit to three marks, 4 cm rms | central slab, right of the seam | ultrawide lens, no control; ~3 % scale spread across the mesh |
| C | red | **0.6745** | 76.6 / 166.6 deg, 90.0 apart | 15 x 17, spacings agree to 0.07 % | rigid, clean, full mesh |

Method: bench plane from paint-coloured vertices, top-down colour raster, 2D
spectrum of the paint mask for the two lattice wave-vectors (angle and spacing,
0.5 m by definition), then phase by folding modulo the spacing and extent by a
matched window of the known line count scored on paint-versus-rock contrast.
Scripts and figures are in `registration/`.

**Accuracy.** A and C: the lattice is rigid to a tenth of a degree and the
spacing is known exactly, so in-plane position on the grid is good to a few
centimetres. B: the two line families are 5 degrees off perpendicular, which is
a reconstruction shear, and two grids in the same mesh gave scales 5 % apart.
B's frame comes from three painted corner marks rather than the lattice, fitted to 4 cm; treat positions inside the grid as good to about 10 cm.

**What is NOT resolved, and matters for a cut plan**

1. ~~Which lattice corner is the report origin.~~ **Resolved from the painted
   labels, 10-09-2026.** Each origin was found by back-projecting the crew's own
   marks through the Metashape camera poses: A from the chalk line numerals
   (A0 is eight lines before the "9"), B from the B0/B1/B3 circle-crosses (a
   9.5 x 6 rectangle fits them to 4 cm), C from the C0 circle-cross, which is the
   corner itself (the detected lattice had been phased two rows off). No handedness was assumed; A and C are
   left-handed with z up, B right-handed. `registration/frame_override.json`
   holds the frames and their evidence.
2. **The blocks are not positioned relative to each other.** Each mesh is its
   own frame. No mesh contains another block's grid. A site survey is the only
   fix.
3. ~~Time zero.~~ **Closed 10-09.** PARSAN confirmed the table TWTs are time-zero
   corrected and the 3.07 ns is display-only. The raw SEG-Y used here is already
   on the corrected axis (their picks land on it without an offset). No surface moves.
4. **Migration.** Surfaces are where the reflections were recorded, not where
   the fractures are, per the report's convention. B-2 at 22 degrees is up to
   1.4 m out in plan at its deepest.

**One open item with PARSAN.** Their emailed B-1 depth (1.0 to 1.95 m) disagrees
with their report's slice windows (0.5 to 1.0 m) and with the raw data, which
free-tracks the sheet at 0.55 to 0.68 m on both channels. The 0.46 to 0.97 m surface
here stands.

## Surface fractures: `surface_fractures/`

Sketch digitisation, photo detection weeded of chalk lines, and each GPR plane's
daylight line against the sketch with a random-line null (`sketch_vs_gpr_daylight.json`).
Headline: **B-1 is confirmed on the rock** (66 % of its daylight within 30 cm of a
sketched fracture, 2.4x chance); A-1 is no better than chance; Block C's main surface
joint set is steep, NE-SW, and absent from the GPR. Details in `../MODEL.md`.

## Other folders

- `report_frame/`: the same surfaces in the report's own x, y (cm) with z
  negative down, before any registration. Rhino-ready.
- `picks/`: every per-trace pick with two-way time retained, and the resolved
  geometry of all 89 lines.
- `registration/`: the detection JSONs, the figures that prove each one, and the
  placement choice file.

## Provenance

Raw SEG-Y and meshes are outside git at `reference/parsans/`. The full audit is
`../AUDIT.md`, the model `../MODEL.md`, the tie to the report `../VERIFICATION.md`.
Everything regenerates from `../scripts/`.
