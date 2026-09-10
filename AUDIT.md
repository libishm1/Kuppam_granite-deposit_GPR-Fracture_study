# Kuppam GPR: audit of the revised report and the raw data

09-09-2026. Everything below was derived from the delivered files. Scripts are in
`scripts/`, tables in `tables/`, figures in `figs/`. Every number here is
reproducible by re-running the named script.

**Headline. The revision fixed most of what was raised, the raw data confirms the
survey geometry and the adopted velocity, and one of my own earlier objections is
now provably wrong and has to be withdrawn. Two questions survive, and only one
of them is worth more than a few centimetres.**

---

## 0. What arrived

| item | detail |
| --- | --- |
| revised report | `Ground Penetrating Radar Survey_Kuppam (09-09-26).pdf`, 51 pp, was 48 |
| authorship | now Dr Sanjay Rana, Ms Ronak Dahiya **and Ms Priya Mohani** |
| raw archive | `GPR Raw data_Kuppam.rar`, 140 MB, 276 files |
| SEG-Y | **178 files**, 89 lines x HF and LF |
| per-line metadata | 89 UTF-16 CSVs, instrument settings and scan length |
| field sketches | `A Block sketch.pdf`, `B Block sketch.pdf`, `C Block Sketch.pdf` |
| slice montages | 6 JPGs, HF and LF per block |
| returned | our own `GPR-Kuppam-R2_Questions.docx` |

Blocks A / B / C hold 24 / 33 / 32 lines. That matches the report exactly.

---

## 1. Raw-data facts, all verified

`scripts/inventory.py`, `scripts/segy.py`

| | HF | LF |
| --- | --- | --- |
| samples per trace | 655 | 664 |
| time window | 40 ns | 81 ns |
| sampling rate | 16.38 GHz | 8.19 GHz |
| **antenna offset** | **7.0 cm** | **24.4 cm** |
| measured spectral peak | **628 MHz** | **358 MHz** |
| measured -6 dB band | 412-888 MHz | 110-658 MHz |

Instrument Proceq GS8000, S/N **GS80-001-0145**, firmware 5.7.6, app 3.8.1.
Trace spacing **2.49 cm** (0.4 scans/cm) on every line. SEG-Y rev 1, IEEE float,
big-endian.

**The measured LF centre frequency is the number the report never states.** It is
358 MHz, not 500. `scripts/spectra.py`

### 1.1 The raw data contains no coordinates at all

- Every trace header coordinate field is **zero**: `sx`, `sy`, `gx`, `gy`,
  `cdpx`, `cdpy`. The scalar `scalco = -1000` is written but never used.
- Every one of the 89 per-line CSVs reports **Start x = 0.000, Start y = 0.000**.

**So the entire x, y coordinate system in the report was assigned at the desk from
the field sketch, by line number.** That is a legitimate way to do it, and the
sketches support it, but it means the grid has never been tied to anything on the
rock. This is still the largest unbounded error in the project and nothing in
this delivery changes it.

### 1.2 Along-line length error is the measurable part of the registration

`tables/GEOMETRY_resolved.csv`. Scan length is the wheel odometer, so the
difference from the nominal grid dimension is the along-line positional error at
the far end of each line.

| block | family | n | median error | worst |
| --- | --- | --- | --- | --- |
| A | Y-lines | 12 | -2.5 cm | -30.0 cm |
| A | X-lines | 12 | -5.0 cm | -25.0 cm |
| B | X-lines | 13 | +10.0 cm | +17.5 cm |
| B | Y-lines | 20 | +3.8 cm | +30.0 cm |
| C | X-lines | 17 | -7.5 cm | -40.0 cm |
| C | Y-lines | 15 | -7.5 cm | +25.0 cm |

**Median 7.5 cm, 90th percentile 25 cm, worst 40 cm.** Half the lines are inside
the 20 cm requirement on this term alone; the tail is not.

### 1.3 A practical note on the SEG-Y files

The binary header writes the sample interval as **61** (HF) and **122** (LF) in
the field SEG-Y defines as **microseconds**. The true intervals are 61 and 122
**picoseconds**. Any standard reader will therefore believe the record is 39.9
milliseconds long instead of 39.9 nanoseconds, a factor of 10^6. This is the
usual GPR-into-SEG-Y convention rather than a mistake, but it has to be
corrected on load or every depth comes out absurd. Our reader handles it.

### 1.4 HF is blind below about a metre

HF trace RMS falls two and a half orders of magnitude by 7 ns. This independently
confirms the report's statement that B-2 and C-2 are LF-only because they sit
below the practical HF range. That decision was correct.

---

## 2. Report claims checked against the raw data

### 2.1 CONFIRMED: depth = TWT x 0.06, with no time-zero subtraction

Re-verified across every published endpoint in the **revised** edition: Table 2
(B-2, 10 endpoints), Table 3 (C-2, 16 endpoints), Figures 5 and 6 (A-1). All
exact. Ronak's own worked example in her covering email, 7.81 ns to 0.47 m and
11.65 ns to 0.70 m, reproduces the same rule.

The new Table 1 justifies this. Solving the two-depth pair algebraically:

| target | 0.10 m | 1.00 m | solved v | solved t0 |
| --- | --- | --- | --- | --- |
| steel pipe | 1.67 ns | 16.80 ns | 0.1190 m/ns | **-0.011 ns** |
| iron plate | 1.70 ns | 17.03 ns | 0.1174 m/ns | **-0.003 ns** |

**Both give time zero of essentially zero.** So the report's choice not to
subtract a t0 is supported by its own new calibration table. My earlier objection
on this point is answered.

### 2.2 OPEN, and the only question worth real money

**Figure 2 and Table 1 give two different numbers for the same measurement.**

- Figure 2 caption: *"Proceq system (HF channel), 0.10 m slab, Line 2 - hyperbola
  apex t0 = 4.74 ns."*
- Table 1, steel pipe, 0.10 m dolerite slab: **picked TWT 1.67 ns.**

Two observations. First, 1.67 is exactly 2 x 0.10 / 0.120, so that cell is the
value implied by the adopted velocity rather than an independent pick. Second,
Section 4.1 says apex picks were *"made below this ringing band"*, and at 1.67 ns
the HF direct wave is still at full amplitude in our own measurement of the block
data, so a pick there would be inside the band, not below it.

**Corrected 09-09, later the same day.** An earlier version of this section said
20 cm, from solving the pipe pair algebraically. That solve also drives velocity
to 0.1493 m/ns, RDP 4.03, which our own hyperbola scan rules out, and it is a
rotation rather than a uniform shift: -10 cm at 10 ns rising to +50 cm at 50 ns.

The sound derivation pins velocity at the measured 0.1202 and asks what time zero
each pick implies: **+0.006 ns for Table 1, +3.076 ns for Figure 2, a difference
of 3.07 ns, which is 18.5 cm on every depth.**

**This one question is worth 18 cm on all three blocks.** It is the only item I
cannot settle at my end, because the calibration SEG-Y was not shipped and the
blocks contain no known-depth target.

Note also that 2 x 0.10 / 0.120 = 1.6667, so Table 1's 1.67 is exactly what the
adopted velocity predicts. "Time-zero corrected" and "back-computed from v" are
indistinguishable from outside the data, so the question must ask for the action,
not propose a mechanism.

Related and minor: Figure 4's Proceq plate bar runs off the top of the axis,
above 11, while Table 1 and Section 4.2 give 6.52 for the same test.

### 2.3 CONFIRMED, and my item 5 is now provably wrong

`figs/C_line21_HF_pick.png`, `scripts/plot_pick.py`

I plotted Block C Line 21 HF from the raw SEG-Y and overlaid the report's own
Table row, y 49 to 294 cm at TWT 2.68 to 11.83 ns. **The pick sits exactly on a
coherent, monotonically deepening reflector.** The reversed alternative sits on
nothing.

My earlier claim that the figure shallowed where the table deepened was wrong.
The likely cause is that Figure 22 is captioned *"line 20 HF, x = 150 cm"* in
this edition, and x = 150 cm is Line 21, so I was comparing a figure against the
wrong table row.

**Item 5 is fully withdrawn, not half withdrawn.** The earlier half-retraction was
itself wrong and must not be sent.

### 2.4 CONFIRMED: C-2 is real

`figs/C_C2_LF_lines22_11.png`

Lines 22 (Y, x=200) and 11 (X, y=500) plotted from raw LF. A strong, laterally
continuous, gently undulating band runs the full length of both lines at 2.9 to
3.3 m, in both orientations, and the report's picked band brackets it correctly.

Two things visible in the raw that are not in the report:

- a **second continuous band at roughly 3.9 to 4.3 m**, below C-2, on both lines
- a **sharp full-depth discontinuity on Line 11 at about x = 315 cm**, where the
  whole section steps sideways. That looks like a stop and restart during
  acquisition, and if so the along-line positions past 315 cm on that line are
  offset.

### 2.5 CONFIRMED: the line-to-coordinate map, for B and C

The field sketches settle it. Block B: lines 1-13 run along the 9.5 m axis
stepped in y, lines 14-33 run along the 6 m axis stepped in x. Block C: lines
1-17 along 7 m stepped in y, lines 18-32 along 8 m stepped in x. Both agree with
the measured scan lengths and with every table in the report.

### 2.6 OPEN: Block A's two line families may be the wrong way round

The Block A sketch numbers **1 to 12 along the top edge**, stepped in x, and
**13 to 24 down the left edge**, stepped in y. Blocks B and C are numbered the
other way, X-family first.

The report treats Block A the way it treats B and C:

| report says | sketch implies |
| --- | --- |
| Figure 5, Line 19, fixed at **x = 300 cm** | Line 19 is an X-line, fixed at **y = 300 cm** |
| Figure 6, Line 10, fixed at **y = 450 cm** | Line 10 is a Y-line, fixed at **x = 450 cm** |

**The magnitudes match exactly. Only the axis letter differs.** That is what a
transposition looks like.

Because Block A is square, the data alone cannot decide this: swapping x and y is
a mirror about the diagonal and is invisible to any internal consistency test. It
needs one sentence from PARSAN or one compass bearing on site.

It matters because a mirror about the NE-SW diagonal leaves a NE-SW trend
unchanged while flipping the dip direction between NW and SE. **That is exactly
the inconsistency in the report's own A-1 description**, which calls it NE-SW
trending and deepening south-west while Figure 10 draws the down-dip arrow to the
north-west.

Blocks B and C are unaffected.

### 2.7 NEW and positive: the grid ties to itself at 5 to 10 cm

`scripts/tie_check.py`, `tables/tie_crossings.csv`

Every X-line crosses every Y-line, and both sample the same rock there. Comparing
the HF envelope trace at all 608 crossings:

| block | crossings | median lateral mismatch |
| --- | --- | --- |
| A | 123 | 10.0 cm |
| B | 255 | 5.0 cm |
| C | 230 | 10.0 cm |

**Internal registration is inside the 20 cm requirement.** A third of crossings
show no coherent match at the nominal position, which is expected when two
orthogonal antenna orientations cross over an anisotropic medium, so this is a
floor on quality rather than a defect count.

This says nothing about where the grid sits on the rock. That is still unmeasured.

### 2.8 NEW and positive: the adopted velocity is confirmed by the block data

`scripts/hyperbola_velocity.py`

Diffraction-hyperbola semblance scan over all 89 HF lines. Restricting to
well-focused apices deeper than 0.6 m, which is where a hyperbola has enough
moveout to constrain velocity and is clear of the direct wave:

| | n | median v | implied RDP |
| --- | --- | --- | --- |
| **measured, this survey** | **114** | **0.1202 m/ns** | **6.22** |
| report adopted | | 0.1200 m/ns | 6.25 |
| Proceq plate at 1.00 m | 1 | 0.1174 m/ns | 6.52 |
| Zond combined, Figure 4 | | 0.1252 m/ns | 5.73 |

**The adopted 6.25 is confirmed to within one per cent by an independent method on
the blocks themselves.** Per-apex scatter is wide, interquartile 0.099 to 0.157,
but the mean is well determined and the choice is right.

This retires the concern that 0.12 was a granite table value carried over. It
also retires the published-mafic-literature disagreement: this rock behaves like
RDP 6.2, not like the 6.9 to 7.9 of published basalt and norite. **Depth
conversion contributes roughly plus or minus 12 cm at 3 m, not 39 cm.**

### 2.9 WITHDRAWN before sending: the HF/LF datum offset

An envelope cross-correlation over 1 to 25 ns showed the LF channel placing
reflectors 2.740 ns behind HF, sd 0.069, on all 89 lines, of which only 0.580 ns
is explained by the antenna offsets. That looked like a 13 cm datum error on the
LF channel, which would have moved B-2 and C-2.

**It does not survive AGC.** Repeating with amplitude-normalised envelopes so the
correlation locks on waveform shape rather than the decay envelope gives a
residual of **-0.33 ns, about 2 cm**. The 2.7 ns was an artefact of comparing a
628 MHz wavelet against a 358 MHz one, whose envelopes have very different
lengths.

The report's own evidence agrees: B-1 appears at 0.52 to 0.59 m in HF slices and
0.47 to 0.61 m in LF slices, which is agreement to a few centimetres.

**No inter-channel datum problem. Claim dropped.**

---

## 3. What the revision fixed

Worth recording, because it is most of the sheet.

| | |
| --- | --- |
| Section 4 | rewritten with a real calibration table; the unsupportable claim that the two-depth design cancels t0 algebraically has been **removed** |
| B-1 | changed from "near-vertical" to "gently east-dipping", and the 3.8 degree plan rotation quantified as about 40 cm across the block |
| apparent dip | now correctly described as a **lower bound** on true dip |
| RDP | 6.2 corrected to 6.25 in two places; the stray 0.11 m/ns corrected to 0.12 |
| Figure 3 | caption corrected from "0.10 m slab" to "1 m slab" |
| block corners | **all three blocks now have their four corner coordinates stated** |
| numbering | Table 1/2 renumbered 2/3; section "9. Recommended Targeted Verification" renumbered 11; cross-references repaired |
| Figure 10 | caption now explains that the red trace is a plan line, not a constant depth |

## 4. Remaining editorial points, no reply needed

- Figure 13 caption says Line 13 at y = 200 cm; the text says lines 1, 5, 9, 13
  sit at y = 0, 200, 400, 600, so Line 13 is y = 600.
- Figure 22 caption now says "line 20 HF, x = 150 cm". x = 150 cm is Line 21, and
  the text says the three lines shown are 21, 24 and 27. **This error is new in
  this edition** and it is what misled me into raising item 5.
- The sketches are dated 19/8/26; the SEG-Y filenames and timestamps are 20/8.
- All three sketches are headed "PROCEQ & ZOND (500 & 300)", but only Proceq
  SEG-Y was supplied. If Zond block data exists it would be a free second opinion
  on every feature.

## 5. Ronak's four answers, checked

| | answer | verdict |
| --- | --- | --- |
| plan positions | no correction indicated, use as reported | accepted, her call; carried as an uncertainty at our end |
| pick range order | lower TWT is the shallow end | **confirmed**, her worked example reproduces exactly |
| permittivity | 6.25 for all three blocks | **independently confirmed at 6.22** |
| Block C clutter | shallow clutter y = 350-750 cm, across much of the width | usable; matches the report's own zone |

The third answer is now backed by our own measurement rather than taken on trust.
The fourth is the one with a consequence for someone else, and it is the one that
matters most on site: **treat y = 350 to 750 cm in the top metre of Block C as
suspect for metal.**

## 6. What is still ours to do

1. **Tape and compass over the three grid origins.** The raw data proved there is
   no positioning in it at all. This is now confirmed as the largest error and it
   costs one afternoon.
2. **One core through C-2 near Line 22 or Line 11.** Sections 8, 9 and 11 all
   recommend it. It would settle the Figure 2 question by measurement rather than
   by correspondence.
3. Build surfaces from `tables/GEOMETRY_resolved.csv`, treating Block A's axes as
   provisional until the transposition question is answered.
4. Decide whether the second band at 3.9 to 4.3 m in Block C is worth picking.


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
