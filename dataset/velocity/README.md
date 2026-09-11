# Velocity: what was measured, what was adopted, what is carried as uncertainty

| file | what |
| --- | --- |
| `PARSAN_calibration_table1.csv` | PARSAN's known-depth calibration (their report, Section on field calibration, Table 1): a steel pipe and an iron plate under 0.10 m and 1.00 m dolerite slabs, picked two-way times, velocities 0.1174 to 0.120 m/ns, RDP 6.24 to 6.52; their Zond combined value (Figure 4) 0.1252 m/ns, RDP 5.73; their adopted RDP 6.25 (0.1200 m/ns). Transcribed values; the scans themselves were not supplied. |
| `hyperbola_velocity.csv` | this work: 322 candidate diffraction apices on the survey lines, each fitted for velocity (columns: block, line, trace, sample, apex time, v, RDP, envelope coherence score `semb`, focusing width `vwidth`) |
| `velocity_summary.json` | the one selection rule (vwidth <= 0.012, t0 > 10 ns), 114 fits, median 0.1202 m/ns, spread, per-block medians, depth sensitivity |
| `firstbreak_aic.csv` | AIC first-break time per line and channel, whose scatter (HF 0.27 ns, LF 1.75 ns) is the time-zero term of the uncertainty ladder |

**Status.** The velocity is calibrated: PARSAN measured it on known-depth targets in dolerite slabs and adopted 0.1200 m/ns; the diffraction scan on the benches themselves gives 0.1202. The calibration values spread from 5.73 to 6.52 in permittivity, and that spread, halved about the adopted 6.25, is the velocity term of the uncertainty ladder (`sigma_v/v` = 3.2 %, `tables/uncertainty.json`). What has not been done is a calibration in the benches themselves against a reflector of known depth (a core through C-2 would give one).
