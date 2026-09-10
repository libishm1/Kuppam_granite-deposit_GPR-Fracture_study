# Kuppam dolerite benches: GPR fracture model, verification and block yield

**Interactive model (English and Tamil, phone and desktop):**
https://libishm1.github.io/Kuppam_granite-deposit_GPR-Fracture_study/

Three dimension-stone benches (Block A 5.5 × 5.5 m, Block B 9.5 × 6.0 m, Block C
7.0 × 8.0 m) at a dolerite quarry near Kuppam, Chittoor district, Andhra Pradesh,
surveyed 18 to 20 August 2026 with a Proceq GS8000 dual-frequency ground-penetrating
radar on a painted 0.5 m grid by PARSAN Overseas. This repository holds the independent
re-processing of the raw SEG-Y data, its registration onto photogrammetry of the same
benches, the surface-crack map, a straight-cut (guillotine) block plan with an order of
cutting, the verification of every stage, and the web interface that shows all of it.

## Read first

| file | for whom |
| --- | --- |
| [REPORT.md](REPORT.md) ([PDF](REPORT.pdf)) | the consolidated report: data, the six fracture surfaces, registration, block yield, the cut plan, verification, what the radar can and cannot do |
| [GEOLOGIST_AUDIT.md](GEOLOGIST_AUDIT.md) | frame and conventions, picking methods, dip / dip direction / strike, checks, discrepancies with the contractor's report, open questions |
| [VERIFICATION.md](VERIFICATION.md) | per-line ties to the contractor's report; orientation audit of the interface |
| [MODEL.md](MODEL.md), [AUDIT.md](AUDIT.md) | the working documents: raw-data audit and the block-by-block model |
| [dataset/README.md](dataset/README.md) | the metric dataset: point clouds, surfaces (OBJ, DXF), picks with two-way time, frames |

## The interface

One HTML file, `index.html`, with the data embedded (about 8 MB). Three roles switch
the default layers and tab: **Mason** (the cuts in order, the blocks in removal order),
**Owner** (tonnes in blocks the saw can free, the four assumptions side by side, a blank
price field), **Geologist** (the raw radar lines stood up in 3D, one line at a time with
the picks on it, dip and strike, spectra and velocity). Every number on the page is read
from the tables in `tables/`. The page states what is checked and what is not.

State can be linked: `index.html#block=B&role=geo&tab=radar&ch=LF&line=5`
(`block`, `role`, `tab`, `lang=ta`, `ch`, `line`, `scen`).

## What is and is not here

- The raw SEG-Y files, the photogrammetric meshes and the contractor's report are not
  in this repository. The radargram panels embedded in the interface are rendered from
  the raw survey data.
- The three blocks are not positioned relative to each other; each is in its own
  metric frame tied to its painted grid.
- Depths are at 0.1202 m/ns, from 114 diffraction hyperbolae in the data. The contractor
  used 0.1200 m/ns.
- "East" in the cutting order is taken as grid +x, the sense the contractor's report uses
  on Block B. It has not been checked with a compass.
- The block plan is a model, not a promise: the chalked surface cracks have not been
  measured for depth, and the radar does not see steep cracks.

## Reproduce

`scripts/` holds every step in the order the report describes them (audit, picking,
adjustment, registration, DEM, crack maps, packing, guillotine plan, radargram panels,
web bundle). They expect the raw data and meshes at the paths written at the top of each
file. Python 3 with numpy, scipy, scikit-image, Pillow, matplotlib and PyMuPDF.

## Licence

MIT for the code and the documents in this repository. The survey data belongs to the
client; the contractor's report is not redistributed.
