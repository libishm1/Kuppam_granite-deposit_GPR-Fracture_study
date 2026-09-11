# Response to the read-only audit of 10 September 2026

Every numbered finding of the audit, what was done, where, and what remains with the
geophysicists. Nothing in the "owned by the geophysicist" column has been guessed at;
those items are carried as uncertainty or as open questions.

| # | finding | action | where | left with PARSAN |
| --- | --- | --- | --- | --- |
| 1 | B-1 "confirmed on the rock" used plane depth + bench height = 0 | Withdrawn everywhere. New `daylight_test.py` fits each surface as a depth plane (v1) and as an absolute-elevation plane met with the DEM (v2), scores the daylight line against the chalked cracks with a null of 600 random placements, and flags extrapolation beyond the pick footprint. B-1: 18 % on the DEM, 31 % flat, chance 27 %, 0 % of the line inside the picks. Chip set to caution. | `scripts/daylight_test.py`, `tables/sketch_vs_gpr_daylight.json`, `figs/DAYLIGHT_*.png`, REPORT §3 §6 §8, GEOLOGIST_AUDIT §4.7, VERIFICATION, MODEL, dataset README, interface (chip, How sure, B-1 paragraph) | which line, channel and event PARSAN picked as B-1 |
| 2 | optimizer, boxes and cut planes on different height references | One frame: `packing_domain.py` builds a 10 cm voxel domain in bench-frame absolute elevation (rock below the DEM, above the floor; surfaces as bands at their absolute elevation; chalk prisms from the local surface). `guillotine_pack.py` runs on it; horizontal cuts are true planes at absolute levels; a block's usable height runs from its bottom cut to the lowest surface point over it. Clearance of every block to every surface is re-measured after the solve: minimum 0.15 m in all 24 runs. The viewer draws boxes and cut planes at those absolute elevations, no per-centre offsets. | `scripts/packing_domain.py`, `guillotine_pack.py`, `block_pack.py`, `web_bundle.py`, template | none |
| 3 | 15 / 10 cm buffers smaller than the acknowledged uncertainty | `uncertainty.py` builds a 1σ vertical error per node on the tolerance ladder of the author's BoEGE paper (velocity 3.2 %, quarter-wavelength floor, time-zero scatter, pick scatter, mesh, registration × tan dip, in quadrature; UNCERTAINTY.md) and the migrated plane of each surface (planar-reflector geometry). Every scenario is run twice: as drawn (15 / 10 cm) and with uncertainty (2σ bands, union with the migrated position, 20 cm from chalk). The uncertain case is the default and the one labelled "plan on this"; tonnages are shown as the pair. | `scripts/uncertainty.py`, `tables/uncertainty.json`, `model/unc/`, REPORT §7.3, interface (clearance selector, Yield, How sure) | migrating the sections; calibrating the velocity |
| 4 | removal order not verified top-down or accessible | Pieces (blocks and waste) are sequenced under a dependency rule: nothing before every piece above it that overlaps it in plan; among ready pieces, east first, then top down. Zero violations in all 24 runs (checked). Each block lists the pieces that must be out first and its free faces at its turn. Wording changed from "lifts out" / "the saw can actually free" to "candidate blocks under these assumptions" and "whether the saw and the loader can reach a piece is a site judgement". | `guillotine_pack.py`, REPORT §7.2, interface Cutting tab and callout | site access, wire threading, lifting |
| 5 | velocity precision overstated; two filters; "semblance"; ±2 % arithmetic wrong | One rule everywhere (vwidth ≤ 0.012, t0 > 10 ns); `velocity_summary.json` with median, p10–p90 (0.088–0.172), block medians (0.112 / 0.126 / 0.130), 15 exactly at the search limits (22 within one step), depth sensitivity; score renamed an envelope-amplitude coherence; the audit's arithmetic corrected (−2.3 %, +4.2 %; −7 / +12.5 cm at 3 m). 0.1202 is called a working assumption in every document and on the page. | `scripts/hyperbola_velocity.py` (print rule), `tables/velocity_summary.json`, REPORT §3 §8 §12, GEOLOGIST_AUDIT §4.3, interface How sure | calibration against a reflector of known depth |
| 6 | "verification" reuses fitting constraints | Section 8 of the report and the How-sure tab now open with "every check here is an internal-consistency check"; the C-2 crossings, corridor endpoints, grid scale and tie search are named as such; tie-search limits stated (±20 cm; 66 of 608 at the boundary, 180 below 0.3). Chips read "consistent", not "checked". | REPORT §3 §8, VERIFICATION, interface | independent validation (core, trench, sawn face) |
| 7 | footprint rounding (5.6, 9.6 m); boxes beyond the footprint; node-summed C-2 volume; free packing called an upper bound | Free packer rebuilt on the shared 10 cm domain pooled to 20 cm (exact footprint, nothing above the surface). `volumes.py` integrates cells: 172.7 m³ (was 177.4). Free packing renamed an unconstrained heuristic estimate, "neither a bound nor a plan", in the report, the JSON and the page. | `scripts/block_pack.py`, `volumes.py`, MODEL, REPORT §7.1, interface | none |
| 8 | C-2 statistics from raw picks, surface from adjusted | `structural.py` prefers the adjusted picks for C-2 (dip 1.8°, was 2.8°); the radargram viewer shows adjusted picks filled and raw picks as rings for C-2. | `scripts/structural.py`, `web_bundle.py`, template | none |
| 9 | stale packaged override; relief 27 vs 22 cm; "at right angles"; daylight generator missing; xyz units; PDF page count | Packaged `frame_override.json` refreshed from the current one; relief corrected to 22 cm in the documents; "at right angles" replaced by "about 35 degrees" in REPORT and MODEL; the daylight generator is now a script; dataset README states the units and sign of each format; handoff page count corrected. | `dataset/registration/frame_override.json`, MODEL, REPORT, GEOLOGIST_AUDIT, `dataset/README.md`, handoff | none |
| 10 | geophysical wording | "cannot see steep cracks" → "this survey and processing do not reliably constrain steep fractures"; "the chalked cracks are the steep set" → their dip and persistence are unknown; "true dip" → dip of the modelled, unmigrated surface; 6.9° → 5.5° at 628 MHz; quarter-wavelength values called theoretical scales; 1–2 GHz → 3 to 1.5 cm, no detection guarantee; polarity sentence corrected; centimetre phone-survey promise softened; "only sawn faces" → sawn faces, trench or core. | REPORT §1 §5 §10, GEOLOGIST_AUDIT §5 §7, interface texts | none |
| 11 | interface wording and behaviour | "checked" → "consistent"; compass labels the east grid axis and asks "east?"; east is set per block from the registered photographs and the satellite view (ORIENTATION.md): +y on B, +x on A and C, every origin the north-western corner; PARSAN's +x reading on B is contradicted by the photographs; "candidate blocks under these assumptions"; kerf glossary corrected (5 cm per dimension, shared); A-2 no longer "vertical" in Tamil; limitations paragraph in Tamil (velocity, migration, registration, chalk depth, steep fractures); document language set on restore; sheet handle keyboard-operable (arrows, Enter); service worker deletes only its own `kbm-` caches; WebGL creation inside a guarded block; radar panels retry up to four times. | template, `web_bundle.py` (sw.js) | none |
| 12 | B-1 disagreement; time-zero provenance | Both B-1 readings stay side by side in REPORT §9, GEOLOGIST_AUDIT, VERIFICATION and the page, with the question stated (which line, channel, event). Time-zero closure attributed to PARSAN's email of 10 September and marked as not independently verified. | REPORT §8 §9, GEOLOGIST_AUDIT §4.4, interface | naming the B-1 reflector; the calibration behind the time-zero statement |

## What the numbers became

Candidate blocks in straight cuts, chalked cracks assumed to reach 1.0 m:

| block | with uncertainty (plan on this) | as drawn (best case) | earlier page (mixed frame) |
| --- | --- | --- | --- |
| A | 46 t | 85 t | 46 t |
| B | 264 t | 281 t | 238 t |
| C | 183 t | 221 t | 240 t |

The as-drawn figures rose on B because the absolute frame no longer wastes a whole
0.5 m level to relief (the first lift's top is the rough bench); the uncertain figures
fell on C because the shallow sheet and the cap carry 23 to 42 cm of two-sigma band.
None of these is a promise; section 7 of the report says what each assumes.

## Still owned by the geophysicists

1. Which line, channel and event PARSAN picked as B-1 (their 1.0 to 1.95 m against the
   0.4 to 1.0 m event modelled here).
2. Migration of the sections. The planar-reflector migration used here is an error
   term, not a correction.
3. Velocity calibration in the benches themselves against a reflector of known depth (a core through C-2); the slab calibration of their Table 1 stands and is packaged.
4. The calibration behind the statement that the raw files are already time-zero
   corrected.
5. Whether a denser 3D survey with migration is worth running for the steep set.

## Second pass: what the re-verification found, and what changed

A read-only re-verification (recomputation of every item above) confirmed the rebuild
and found these edges, all fixed in the same pass:

| residual | fix |
| --- | --- |
| the "migration" column was migrated plane minus the gridded surface, so for the near-flat B-1, C-1 and C-2 it reported the plane-to-grid misfit (±0.1 to ±0.4 m) as migration | `uncertainty.py` now takes the offset plane to plane (migrated plane minus unmigrated plane, both in absolute elevation); B-1, C-1, C-2 move by millimetres, the A sheets by 0.6 m, B-2 by 0.13 to 0.29 m. The "migrated surface" file is the gridded surface shifted by that offset. Packing re-run: straight-cut tonnages unchanged; the free heuristic moved by a few tonnes |
| "dip modelled → migrated" mixed a depth-frame dip with an elevation-frame one, so two surfaces appeared to flatten under migration | both dips are now in the elevation frame (the depth-frame dip is kept as a separate field); every surface steepens or holds |
| REPORT.md still said 27 to 41 cm of relief | 22 to 41 cm |
| the free-packing badge on the page read "bound" | "estimate" |
| the layer caption and the Yield paragraph hard-coded 15 / 10 cm while the page defaulted to the uncertain case | both now state the clearance of the case selected |
| VERIFICATION.md called the velocity "confirmed to 0.5 %" | consistent with the diffraction median and with PARSAN's slab calibration; PARSAN's Table 1 is now transcribed in `dataset/velocity/` |
| `n_at_limits` 22 counted fits within one search step; 15 sit exactly at the limits; the summary had no generator | `scripts/velocity_summary.py` writes it; both counts are stated |
| two Tamil strings still said the radar cannot see steep cracks and that the chalked cracks are the steep set; the Tamil time-zero sentence lacked the not-independently-checked qualifier | rewritten to match the English |
| `dataset/README.md` still said the 0.46 to 0.97 m surface "stands" | both readings side by side, carried as caution |
| "the other four do not reach the bench" ignored a 5 cm sliver of A-2 | stated |
| `hyperbola_velocity.py` docstrings still said semblance | envelope coherence; the CSV column name `semb` is kept for compatibility and says so |
| free-packing cells can sit up to 5 cm above the lowest surface point | stated in REPORT §7.1; absorbed by the kerf |

## Third pass: calibration, the ladder, Monte Carlo and orientation

| what | change |
| --- | --- |
| the documents called the velocity "uncalibrated" | PARSAN's Table 1 calibration exists (steel pipe and iron plate under 0.10 and 1.00 m dolerite slabs, 0.1174 to 0.120 m/ns, RDP 6.24 to 6.52; Zond 0.1252, RDP 5.73; adopted 0.1200, RDP 6.25). It is transcribed in `dataset/velocity/PARSAN_calibration_table1.csv` with the diffraction scan and the first-break times beside it, and every document now says slab-calibrated, not calibrated in the benches |
| the uncertainty was a three-term sum with a 4.2 % velocity guess | rebuilt on the BoEGE paper's tolerance ladder: velocity ½ δεr/εr = 3.2 % from the spread of the calibrated permittivities, λ/4 at the measured peak frequencies, time-zero scatter from the AIC first breaks, pick scatter, mesh, registration; combined in quadrature; C(T) = erf(T / σ√2) per surface. Totals 8 to 12 cm on the HF surfaces, about 20 cm on B-2 and C-2 (`UNCERTAINTY.md`, REPORT §7.3, the How-sure tab) |
| no propagation of the uncertainty into the plan itself | `uncertainty_mc.py`: random truths from the ladder terms, the risk of every planned block (share of truths in which a fracture passes through it), risk-weighted tonnage, and the P10 / P50 / P90 of re-planned yield. On the page as a risk column, a callout line per block, and a section on the How-sure tab (REPORT §7.4, `tables/uncertainty_mc.json`) |
| east taken from the report (+x on B) | proven from the registered camera poses, the photographs and the client's satellite view: every origin is the north-western corner, every bench looks east toward the ramp; B has +y east, A and C +x (`ORIENTATION.md`, `figs/ORIENTATION_evidence.png`). The cutting order uses these per block; PARSAN's "+x east" and "6 m north–south" on B are contradicted. A compass still confirms |
