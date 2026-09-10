# Kuppam GPR fracture model: audit notes for the geophysicist and the geologist

Libish M, 10 September 2026. Written for PARSAN (Dr Sanjay Rana, Ronak Dahiya) and for
the regional geologist. It says how every number in the model was produced, what was
checked and how, where the model and the report disagree, and what nobody can claim
yet. Every figure is in `figs/`, every table in `tables/`, every method in `scripts/`.
The tone is deliberate: this is the work laid open for correction, not a verdict.

## 1. Frame and conventions

- **Coordinates** are the survey grid: x and y in the report's sense, in metres here,
  origin at the crew's painted ⊕ on each block. **No true north is known.** Every
  bearing below is measured from the grid +y axis toward +x. One compass reading of
  +y per block converts all of it; the "W" and arrow chalked beside C0 may be that
  reading but has not been used.
- **Depth** is two-way time times v/2, v = 0.1202 m/ns (RDP 6.22), the median of 114 well-focused
  diffraction apices below 0.6 m on the blocks (of 322 candidates; filter vwidth <= 0.012, t0 > 10 ns in `tables/hyperbola_velocity.csv`); PARSAN's 0.1200 differs by 0.2 per cent. Version 1
  is depth below the antenna on a flat bench; version 2 subtracts the photogrammetric
  surface height at each (x, y). Both are delivered.
- **Time axis.** PARSAN confirmed on 10 September that the tabulated TWTs are
  time-zero corrected and the 3.07 ns in Figure 2 is display offset. The raw SEG-Y
  used here is on the corrected axis: the report's own Line 21 pick sits on the raw
  reflector at its printed TWT (`figs/C_line21_HF_pick.png`).
- **Frequencies**, measured from the direct wave on all 89 lines (`tables/spectra.json`): HF peak 628 MHz
  (−6 dB 412–888), LF peak 358 MHz (110–658). The report's "500 MHz nominal" is
  neither. Quarter-wavelength resolution 4.8 cm (HF) and 8.4 cm (LF) at v = 0.12.

## 2. How each surface was picked

| surface | method | independence from the report |
| --- | --- | --- |
| C-2 | dynamic-programming tracker through 44–62 ns on all 32 LF lines; per-line depth shifts solved by least squares over 230 X/Y crossings (robust reweighting), datum re-anchored to the report's 8 mid-depths | picks independent; datum tied to the report by +4.2 cm |
| C-1, B-2 | corridor tracker between the report's published endpoints on each line, corridor half-width 8–12 cm | ends theirs, path ours |
| B-1 | free tracking failed (locked on flat ringing); corridor seeded from the report's description (x 650–950, 8.3° east, 0.5→0.94 m) on 13 HF X-lines; cross-checked on 7 LF Y-lines | **dip magnitude seeded from the report**; existence, continuity, direction and HF/LF agreement are independent |
| A-2 | corridor seeded from Figure 7's geometry (0.45 m at y 60, ~35°) on the five stated Y-lines; then a hunt along the fitted plane on all 24 lines | seed from their figure; X-line cross-check independent |
| A-1 | plane through the four published picks with Line 10's depth order reversed; hunt for bright runs along it on all 24 lines, both channels | corroboration, not independent measurement |

Every pick is a per-trace row with TWT kept, so velocity or offset can be changed
without re-picking (`tables/PICKS_*.csv`).

## 3. Orientation data, grid frame

Dip direction is the bearing of the down-dip vector; strike = dip direction − 90.
Plane residuals are about the best-fit plane through all picks.

| surface | picks / lines | depth m | dip | dip dir | strike | plane rms | max | constraint |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A-1 | 428 / 12 | 0.47–2.32 | 26.9° | 328° | 58° | 3.6 cm | 8 cm | both line families, but seeded |
| A-2 | 565 / 9 | 0.44–1.81 | 34.0° | 1° | 91° | 4.9 cm | 13 cm | Y-lines, X-lines cross-check 0.9 cm |
| B-1 | 1580 / 13 | 0.42–0.99 | 6.9° | 84° | 174° | 4.8 cm | 12 cm | X-lines HF, LF Y-lines agree 97 % within 20 cm (internal); not confirmed on the rock |
| B-2 | 969 / 6 | 1.96–3.95 | 22.2° | 350° | 80° | 9.7 cm | 25 cm | **Y-lines only**; a cylinder along x |
| C-1 | 1292 / 9 | 0.23–1.04 | 6.9° | 31° | 121° | 11.0 cm | 30 cm | Y-lines; X-lines "visually consistent" per report |
| C-2 | 9481 / 32 | 2.64–3.70 | 2.8° | 279° | 9° | 18.6 cm | 53 cm | both families, 230 crossings |

C-2 is not a plane at tolerance: 53 cm of relief across 7 × 8 m, shallowest 2.77 m
at (5.5, 3.8). B-2's dip against horizontal is 19.5° once the 30 cm bench rise along
y is removed (v2). Unmigrated: B-2 at 22° sits up to z·sin 22° ≈ 1.4 m from its true
plan position at 3.9 m depth; A-2 at 34° up to 1.0 m.

**Chalked surface cracks** (field sketches, digitised; positions good to the drawn
grid, 10–30 cm), length-weighted strike roses in `figs/STRUCTURAL_roses.png`:

| block | traces | total | mean trace | sets seen | spacing along x / y |
| --- | --- | --- | --- | --- | --- |
| A | 14 | 15.2 m | 1.1 m | ≈165° and ≈70° | 3.4 / 4.6 m |
| B | 25 | 24.1 m | 1.0 m | ≈70° dominant, ≈165° secondary | 4.5 / 5.1 m |
| C | 39 | 34.1 m | 0.9 m | ≈85° and ≈150° | 4.0 / 2.6 m |

Spacing is crossings per metre along traverses parallel to each grid axis, a P10-type
measure. **B-2's strike (80°) is within 8° of B's dominant chalked set.** On C the
dominant chalked strike is 35° from C-1's strike, not orthogonal; an earlier note of
mine said "at right angles" and was wrong.

## 4. The checks, and their results

1. **Crossing consistency.** C-2 at 230 crossings: median 10.6 cm, 90th percentile
   23.6 cm, 84 % within 20 cm. Grid tie of the raw HF traces at all 608 crossings in
   the three blocks: median lateral mismatch 5–10 cm.
2. **Tie to the report, per line** (`VERIFICATION.md`), for the four surfaces with
   published picks. C-1 endpoints within 8 cm on every line, dips within 2°; B-2 within
   12 cm, dips within 0.3°; C-2 median 3 cm on the 8 published lines with Line 17 a
   +25 cm edge outlier; B-1 and A-2 have no published depths and are checked indirectly; A-1's published dips reproduce (24.0 and 13.7°) once Line 10's
   depths are reversed. The 8–12 cm residuals equal the corridor half-width: the
   tracker stops at peak energy where a human follows the fading event, so the
   report's endpoints stand.
3. **Velocity.** Diffraction scan median 0.1202 (114 apices under one rule, 10th to 90th
   percentile 0.088 to 0.172 m/ns, block medians 0.112 / 0.1263 / 0.13, 15 fits exactly at the search limits, 22 within one step);
   Proceq plate at 1.00 m 0.1174 (RDP 6.52), which is 2.3 % low; Zond combined RDP 5.73
   (0.1252), 4.2 % high; adopted 0.1200. At 3 m those alternatives are −7 and +12.5 cm.
   The score in `hyperbola_velocity.csv` is an envelope-amplitude coherence, not a
   normalised semblance. 0.1202 is a working assumption, uncalibrated; the uncertainty
   model (`uncertainty.py`) carries 4.2 % of depth for it.
4. **Time zero.** See §1. Closed on PARSAN's word (email of 10 September) and on the
   internal consistency of their picks with the raw axis; not independently verified.
5. **Registration to the photogrammetry.** The three Metashape projects have no
   markers, scale bars or GPS. The painted 0.5 m grid in the mesh vertex colours gave
   scale, rotation and position; origins from the crew's painted labels back-projected
   through the camera poses. Verified by drawing the registered lattice back into two
   photographs per block (`figs/REPROJ_*.jpg`): on paint on all three. A 0.7281,
   C 0.6745 m per mesh unit, lattices rigid (families 89.9° and 90.0° apart); B 1.0138
   from three corner marks, 4 cm rms, the mesh itself sheared ~5° by the ultrawide lens.
6. **Bench surface.** Relief 22–41 cm (A 31, B 41, C 22), tilt 1–3°, non-planar residual 1–4 cm, roughness
   1–2 mm at 30 cm. The baked texture sits on its own lattice to within one 5 cm step
   in all three blocks (`tables/texture_orientation.json`).
7. **Surface cracks against the planes** (`tables/sketch_vs_gpr_daylight.json`,
   `scripts/daylight_test.py`). The earlier version of this test contoured plane depth
   plus bench height, which is not the intersection of anything; its B-1 result (66 %,
   "confirmed on the rock") is withdrawn. Each surface is now fitted as a plane in
   absolute elevation and met with the DEM, and its daylight line scored against the
   chalked cracks with a null of random placements of the same line: B-1 18 % within
   30 cm (flat definition 31 %) against 27 % for chance, 95th percentile 59 %,
   and 0 % of the line inside the area where B-1 was picked; A-1 30 % against 34 %.
   Both at chance. The other four do not reach the bench inside the grid, apart from a
   5 cm sliver of A-2 on the DEM definition, 0.95 m beyond its picks. A photo-based dark-line detector was also run on all 384 posed
   photographs and scored 0.77–1.34× chance against the sketches: **rejected**.

## 5. What the catalogue is biased toward

All six GPR surfaces dip 2–34° as modelled (unmigrated; the migrated planes are
steeper, up to 43° for A-2, `tables/uncertainty.json`). A surface antenna returns
little from a plane steeper than about 45°, and at 0.5 m line spacing the slice
sampling of a 628 MHz reflector on the idealised quarter-wavelength argument is about
5.5° of dip (6.9° would be 500 MHz), so the line-by-line picks are the only route to the
moderate dips and this survey does not reliably constrain the steep set; dense
full-resolution 3D surveys with migration have imaged sub-vertical fractures elsewhere.
The chalked cracks reach the surface; whether they are steep, and how far they persist,
is not measured by anything here. The two sets seen in every sketch do not appear in
the GPR list. **The joint set that will control how a block
splits is the one this survey cannot see.** That is a property of the method, stated
in the report's own Section 9, and it is the reason the block yield here ranges from
65 % to 30 % on Block C depending on how deep those cracks are assumed to run.

## 6. Where the model and PARSAN disagree, for resolution

| item | PARSAN | model | status |
| --- | --- | --- | --- |
| B-1 depth | email 10-09: 0.997–1.953 m, 1.48 m at 24.5 ns | 0.46–0.97 m; a corridor seeded at 1.0–1.95 m tracks its own ramp on all 13 lines with 25 % less energy; a free track locks at 0.55–0.68 m on both channels; the report's own slices (0.47–1.02 m) and Figure 12 (0.45–0.95 m) agree with the model | **open**: which line and channel is the 24.5 ns pick on? |
| A-1 Line 10 | 422→1.30 m, 542→1.60 m | reversed: the free track shallows with x (1.57→1.35 m), path energy 1.29× higher reversed, and the report's own NW arrows and NE–SW strike need it | printed order is transposed |
| Figure 12 | radargram | inserted rotated 180°; depth reads 2.68 at the top | editorial |
| Figure 22 | "line 20, x = 150 cm" | x = 150 is Line 21 | editorial |
| LF centre frequency | not stated | 358 MHz measured | for the record |
| second reflector under C-2 | not in the report | continuous band at 3.9–4.3 m on Lines 22 and 11 | worth a look |
| Zond block data | sketches say "PROCEQ & ZOND (500 & 300)" | not supplied | does it exist? |

## 7. What cannot be claimed

- True north, absolute datum, or the position of one block relative to another.
- Aperture or infill from polarity: the picks are envelope maxima and discard sign;
  the signed raw samples are still in the SEG-Y, but reading polarity would need a
  wavelet and phase calibration that has not been done.
- Persistence beyond each grid.
- The depth of any chalked crack.
- That the C-2 undulation is structural rather than partly odometer error (median
  7.5 cm, worst 40 cm along-line) and cycle-skip residue.

## 8. Questions for the geologist

1. Which of these are cooling joints, sheeting or stress-relief in this dolerite? A
   near-horizontal 2.8° cap with 50 cm of relief across 7 × 8 m and a second one a metre
   below reads as sheeting, but sheeting in dolerite is the exception.
2. Joint character on the sawn faces: open, clay-filled or healed decides what
   reflects; the GPR saw six surfaces and the chalk saw two steep sets, and the sawn
   faces will show which of those is open.
3. A compass bearing of grid +y on each block, so that every orientation above becomes
   geographic and the three blocks can be compared to the quarry's mapped sets.
4. Whether the two chalked sets (≈70° and ≈165° grid) are the regional joint pair,
   which would let the bench's split behaviour be predicted from the map.

## 9. For the crew on the bench: things a tape can check

- **Block B:** from B0 walk 2.0 m along x; the B-1 sheet reaches the surface there,
  running along y, and the crew chalked a 4 m crack on it. If it is not there, the
  model is wrong.
- **Block C:** the cap is shallowest at x 5.5 m, y 3.8 m from C0, 2.77 m down. That
  is the place for the core.
- **Block A:** A-1 meets the surface just inside the corner at x 5.5, y 0; the face
  there should show it.
- **Every block:** the packed block corners are listed in grid centimetres from the ⊕
  in the interface's Cutting tab and in `tables/block_packing.json`; stake them from
  the painted lines, not from the model.
