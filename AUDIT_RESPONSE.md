# Response to the read-only audit of 10 September 2026

Every numbered finding of the audit, what was done, where, and what remains with the
geophysicists. Nothing in the "owned by the geophysicist" column has been guessed at;
those items are carried as uncertainty or as open questions.

| # | finding | action | where | left with PARSAN |
| --- | --- | --- | --- | --- |
| 1 | B-1 "confirmed on the rock" used plane depth + bench height = 0 | Withdrawn everywhere. New `daylight_test.py` fits each surface as a depth plane (v1) and as an absolute-elevation plane met with the DEM (v2), scores the daylight line against the chalked cracks with a null of 600 random placements, and flags extrapolation beyond the pick footprint. B-1: 18 % on the DEM, 31 % flat, chance 27 %, 0 % of the line inside the picks. Chip set to caution. | `scripts/daylight_test.py`, `tables/sketch_vs_gpr_daylight.json`, `figs/DAYLIGHT_*.png`, REPORT §3 §6 §8, GEOLOGIST_AUDIT §4.7, VERIFICATION, MODEL, dataset README, interface (chip, How sure, B-1 paragraph) | which line, channel and event PARSAN picked as B-1 |
| 2 | optimizer, boxes and cut planes on different height references | One frame: `packing_domain.py` builds a 10 cm voxel domain in bench-frame absolute elevation (rock below the DEM, above the floor; surfaces as bands at their absolute elevation; chalk prisms from the local surface). `guillotine_pack.py` runs on it; horizontal cuts are true planes at absolute levels; a block's usable height runs from its bottom cut to the lowest surface point over it. Clearance of every block to every surface is re-measured after the solve: minimum 0.15 m in all 24 runs. The viewer draws boxes and cut planes at those absolute elevations, no per-centre offsets. | `scripts/packing_domain.py`, `guillotine_pack.py`, `block_pack.py`, `web_bundle.py`, template | none |
| 3 | 15 / 10 cm buffers smaller than the acknowledged uncertainty | `uncertainty.py` builds a 1σ vertical error per node (pick scatter, 4.2 % velocity, registration × tan dip) and the migrated plane of each surface (planar-reflector geometry). Every scenario is run twice: as drawn (15 / 10 cm) and with uncertainty (2σ bands, union with the migrated position, 20 cm from chalk). The uncertain case is the default and the one labelled "plan on this"; tonnages are shown as the pair. | `scripts/uncertainty.py`, `tables/uncertainty.json`, `model/unc/`, REPORT §7.3, interface (clearance selector, Yield, How sure) | migrating the sections; calibrating the velocity |
| 4 | removal order not verified top-down or accessible | Pieces (blocks and waste) are sequenced under a dependency rule: nothing before every piece above it that overlaps it in plan; among ready pieces, east first, then top down. Zero violations in all 24 runs (checked). Each block lists the pieces that must be out first and its free faces at its turn. Wording changed from "lifts out" / "the saw can actually free" to "candidate blocks under these assumptions" and "whether the saw and the loader can reach a piece is a site judgement". | `guillotine_pack.py`, REPORT §7.2, interface Cutting tab and callout | site access, wire threading, lifting |
| 5 | velocity precision overstated; two filters; "semblance"; ±2 % arithmetic wrong | One rule everywhere (vwidth ≤ 0.012, t0 > 10 ns); `velocity_summary.json` with median, p10–p90 (0.088–0.172), block medians (0.112 / 0.126 / 0.130), 22 at the search limits, depth sensitivity; score renamed an envelope-amplitude coherence; the audit's arithmetic corrected (−2.3 %, +4.2 %; −7 / +12.5 cm at 3 m). 0.1202 is called a working assumption in every document and on the page. | `scripts/hyperbola_velocity.py` (print rule), `tables/velocity_summary.json`, REPORT §3 §8 §12, GEOLOGIST_AUDIT §4.3, interface How sure | calibration against a reflector of known depth |
| 6 | "verification" reuses fitting constraints | Section 8 of the report and the How-sure tab now open with "every check here is an internal-consistency check"; the C-2 crossings, corridor endpoints, grid scale and tie search are named as such; tie-search limits stated (±20 cm; 66 of 608 at the boundary, 180 below 0.3). Chips read "consistent", not "checked". | REPORT §3 §8, VERIFICATION, interface | independent validation (core, trench, sawn face) |
| 7 | footprint rounding (5.6, 9.6 m); boxes beyond the footprint; node-summed C-2 volume; free packing called an upper bound | Free packer rebuilt on the shared 10 cm domain pooled to 20 cm (exact footprint, nothing above the surface). `volumes.py` integrates cells: 172.7 m³ (was 177.4). Free packing renamed an unconstrained heuristic estimate, "neither a bound nor a plan", in the report, the JSON and the page. | `scripts/block_pack.py`, `volumes.py`, MODEL, REPORT §7.1, interface | none |
| 8 | C-2 statistics from raw picks, surface from adjusted | `structural.py` prefers the adjusted picks for C-2 (dip 1.8°, was 2.8°); the radargram viewer shows adjusted picks filled and raw picks as rings for C-2. | `scripts/structural.py`, `web_bundle.py`, template | none |
| 9 | stale packaged override; relief 27 vs 22 cm; "at right angles"; daylight generator missing; xyz units; PDF page count | Packaged `frame_override.json` refreshed from the current one; relief corrected to 22 cm in the documents; "at right angles" replaced by "about 35 degrees" in REPORT and MODEL; the daylight generator is now a script; dataset README states the units and sign of each format; handoff page count corrected. | `dataset/registration/frame_override.json`, MODEL, REPORT, GEOLOGIST_AUDIT, `dataset/README.md`, handoff | none |
| 10 | geophysical wording | "cannot see steep cracks" → "this survey and processing do not reliably constrain steep fractures"; "the chalked cracks are the steep set" → their dip and persistence are unknown; "true dip" → dip of the modelled, unmigrated surface; 6.9° → 5.5° at 628 MHz; quarter-wavelength values called theoretical scales; 1–2 GHz → 3 to 1.5 cm, no detection guarantee; polarity sentence corrected; centimetre phone-survey promise softened; "only sawn faces" → sawn faces, trench or core. | REPORT §1 §5 §10, GEOLOGIST_AUDIT §5 §7, interface texts | none |
| 11 | interface wording and behaviour | "checked" → "consistent"; compass reads "grid +x (east?)"; "candidate blocks under these assumptions"; kerf glossary corrected (5 cm per dimension, shared); A-2 no longer "vertical" in Tamil; limitations paragraph in Tamil (velocity, migration, registration, chalk depth, steep fractures); document language set on restore; sheet handle keyboard-operable (arrows, Enter); service worker deletes only its own `kbm-` caches; WebGL creation inside a guarded block; radar panels retry up to four times. | template, `web_bundle.py` (sw.js) | none |
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
3. Velocity calibration against a reflector of known depth (a core through C-2).
4. The calibration behind the statement that the raw files are already time-zero
   corrected.
5. Whether a denser 3D survey with migration is worth running for the steep set.
