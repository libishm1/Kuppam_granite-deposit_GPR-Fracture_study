# Kuppam dolerite benches: GPR fracture model, verification and block yield

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)

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
| [REPORT.md](REPORT.md) ([PDF](REPORT.pdf)) | the consolidated report: data, the six fracture surfaces, registration, candidate blocks with and without uncertainty, the cut plan and its order, verification, what the radar can and cannot do |
| [AUDIT_RESPONSE.md](AUDIT_RESPONSE.md) | the independent read-only audit of 10 September, item by item, and what was changed in answer |
| [GEOLOGIST_AUDIT.md](GEOLOGIST_AUDIT.md) | frame and conventions, picking methods, dip / dip direction / strike, checks, discrepancies with the contractor's report, open questions |
| [UNCERTAINTY.md](UNCERTAINTY.md) | the uncertainty analysis: tolerance ladder per surface, confidence in the clearances, migration, what the survey cannot see, the cost of an uncertainty-safe clearance, and the Monte Carlo risk of every planned block |
| [ORIENTATION.md](ORIENTATION.md) | where east is and which corner each origin is, proven from the registered photographs and the satellite view |
| [VERIFICATION.md](VERIFICATION.md) | per-line ties to the contractor's report; orientation audit of the interface |
| [MODEL.md](MODEL.md), [AUDIT.md](AUDIT.md) | the working documents: raw-data audit and the block-by-block model |
| [dataset/README.md](dataset/README.md) | the metric dataset: point clouds, surfaces (OBJ, DXF), picks with two-way time, frames, the velocity calibration (contractor's slab table and the diffraction scan) |
| [joint_mapping/STUDY.md](joint_mapping/STUDY.md) | the joint sets visible in the photogrammetry (facets and sawn-face traces) against the radar surfaces; the stereonet of the three benches; the Block A tests |

## The interface

One HTML file, `index.html`, with the data embedded (about 8 MB). Three roles switch
the default layers and tab: **Mason** (the cuts in order, the blocks in removal order),
**Owner** (cubic metres and tonnes in candidate blocks, as drawn and with uncertainty, the four chalk assumptions side by side, and a price per cubic metre by size class that you type in: value per class, blended price, saw cost per square metre of cut, net value and value yield, as in the BoEGE paper), **Geologist** (the raw radar lines stood up in 3D, one line at a time with
the picks on it, dip and strike, spectra and velocity). Every number on the page is read
from the tables in `tables/`. The page states what is checked and what is not.

State can be linked: `index.html#block=B&role=geo&tab=radar&ch=LF&line=5`
(`block`, `role`, `tab`, `lang=ta`, `ch`, `line`, `scen`, `unc`, `sel`).

## What is and is not here

- The raw SEG-Y files, the instrument files, the technician's field sheets, the
  photogrammetric meshes, the photographs and the contractor's report are not in this
  repository. The radargram panels embedded in the interface are rendered from
  the raw survey data.
- The three blocks are not positioned relative to each other; each is in its own
  metric frame tied to its painted grid.
- Depths are at 0.1202 m/ns, the median of 114 diffraction hyperbolae in the data. The
  contractor calibrated 0.1200 m/ns on dolerite slabs over targets of known depth; both
  are in `dataset/velocity/`. Neither is a calibration in the benches themselves.
- "East" in the cutting order is set per block from the registered photographs and the
  satellite view ([ORIENTATION.md](ORIENTATION.md)): every origin is the north-western
  corner, every bench looks east; on Block A east is grid +x, on B and C grid +y (C
  corrected 12 September 2026 from the site photographs; A confirmed 13 September from the
  crew's numbering and the technician's field sheet). The contractor's report reads +x as
  east on B. A compass on site still confirms it.
- The block plan is a model, not a promise: the chalked surface cracks have not been
  measured for depth, the surfaces carry the uncertainty stated on the page, and this
  survey does not reliably constrain steep cracks.

## Reproduce

`scripts/` holds every step in the order the report describes them (audit, picking,
adjustment, registration, DEM, crack maps, packing, guillotine plan, radargram panels,
web bundle). They expect the raw data and meshes at the paths written at the top of each
file. Python 3 with numpy, scipy, scikit-image, Pillow, matplotlib and PyMuPDF.

## Licence

Copyright (C) 2026 Libish Murugesan (ORCID 0009-0004-3238-4202). See [NOTICE.md](NOTICE.md).

This repository (code, documents, tables, figures and the web interface) is licensed
under the **GNU General Public License v3.0** (see `LICENSE`). You may use, study and
share it, and build on it, on the terms of that licence: keep the copyright and licence
notices, state what you changed, and release derived work under the same licence.
Attribute as: *Libish Murugesan, Kuppam dolerite benches: GPR fracture model, verification and
block yield, 2026, https://github.com/libishm1/Kuppam_granite-deposit_GPR-Fracture_study*.
The data, documents and figures are also deposited on figshare under CC BY 4.0:
https://doi.org/10.6084/m9.figshare.33690616 (`deposit/` holds the builder).

The survey data belongs to the client; the contractor's report and the raw survey records are
not redistributed, and the quarry's position is withheld.
