# CO sensor-array manuscript: frozen reproducibility package

This repository contains the reproducibility materials for *Historical recalibration versus additional reference checks in CO sensor arrays: a chronological evaluation*. It reproduces the reported development and fixed-D10 temporal-confirmation analyses from saved numerical evidence.

Ali Sayghe; Husam A. Bakhsh; Olugbenga Moses Anubi. Correspondence: **sayghea@rcjy.edu.sa**. Full affiliations and order are in [AUTHORS.md](AUTHORS.md).

The main workflow reads committed predictions, references, masks and access records. It recomputes their reported metrics, checks the existing development conditional bounds with the original saved index banks, and reproduces tables and figures. It does not fit models, generate predictions, execute C5, create new resampling indices, or read raw sensor data. The raw UCI archive is unnecessary for this workflow.

## Reproduce the reported evidence

Use Python 3.12 (tested with 3.12.3) and the pinned packages. The `python3` bootstrap command below must select that version; use `python3.12` explicitly if needed. Run checks without `-O` or `PYTHONOPTIMIZE`:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/reproduce.py
python scripts/scan_release.py
```

Run from the repository root. The command verifies the source manifest, expands compressed artifacts into `build/frozen/`, checks every development reporting table and every C5 metric/aggregate export, verifies the compact prediction CSVs, and regenerates four figures in `build/manuscript/`. Results appear in `build/reports/REPRODUCIBILITY.json` and the detailed reports beside it. A nonzero exit means a check failed. Repeated runs replace generated files only inside ignored `build/`. Allow several minutes and approximately 2 GB of temporary disk space; runtime depends on the machine.

To include the LaTeX build, install a standard TeX Live distribution with pdfLaTeX, BibTeX, natbib, caption, booktabs, tabularx, longtable, amsmath/amssymb, microtype, float, geometry, hyperref and Computer Modern fonts:

```sh
python scripts/reproduce.py --latex
```

This builds `main.pdf`, `supplement.pdf`, `title_page.pdf`, `cover_letter.pdf`, and `highlights.pdf` in `build/manuscript/`. It checks references, author metadata, warnings, and text equality against the supplied main/supplement/title-page PDFs. A document-only build needs no Python:

```sh
cd manuscript
bash build.sh
```

For inspection without scoring:

```sh
python scripts/reproduce.py --prepare-only
```

To regenerate the CSV interchange files from the saved arrays, without inference:

```sh
python scripts/reproduce.py --prepare-only
python scripts/prediction_csv.py --write
```

These new CSVs are written to `build/predictions/`; packaged `predictions/` files remain unchanged. The default reproduction command compares every exported row against its saved source.

## What is included

| Location | Contents |
| --- | --- |
| `frozen/` | Exact original scientific source, protocols, manifests, frozen models, feature records, development arrays, confirmation outputs, masks, causal records, metrics and archived resampling banks; large text/array files are losslessly gzip-wrapped. |
| `predictions/` | Compact gzip CSVs containing all released development/confirmation predictions, references, masks, error-envelope endpoints and configuration identities. |
| `manuscript/` | Manuscript and supplement, title page, static figures, all tables, bibliography, editable LaTeX, cover letter and highlights. |
| `scripts/` | Portable evidence-only scoring, verification and reporting adapters. |
| `manifests/` | Source-to-release paths, original and packaged hashes, document provenance and release file hashes. |
| `docs/MANUSCRIPT_MAP.md` | Exact table/figure-to-file mappings, row selectors and calculation rules. |
| `data/` | Official dataset provenance, historical archive hashes and download/directory instructions; no raw archive. |
| `verification/` | Results of local preparation, fresh-extraction and clean-clone checks. |

The original code covers preprocessing and heater-phase features (`phase5/resume/audit.py`), RF/OLS/ridge (`phase5/resume/analysis.py`, `phase6/analysis.py`), offset/inverse affine correction, envelope/projection/midpoint calculations, all reference schedules, development analyses and frozen C5 extraction/replay/evaluation. See [SOURCE_GUIDE.md](docs/SOURCE_GUIDE.md). Original experimental entry points are retained as archival source; some execute work on import. **Do not run or import those entry points as part of this evidence-only reproduction.** The release runner imports only the pure metric helper from the frozen development module and never instantiates its learning classes. Historical commands need their original preparation sequence and are not presented as the supported release workflow.

## Scientific interpretation retained

Development uses D5/D7/D9 initialization for D6/D8/D10. Confirmation resets D11/D12/D13 independently to the same D10 initialization. It is not rolling recalibration. R7/R14 and UCI270 sealed batches are excluded.

The frozen descriptive benefit criterion requires lower strict 1 ppm exceedance and nonpositive MAE change pooled and in both families. The prespecified cumulative affine envelope-driven 20-check confirmation changes pooled MAE **1.3553 → 1.3257 ppm** and exceedance **43.06% → 42.14%**. FIS improves **0.9471 → 0.9033 ppm** relative to affine B0 but remains worse than unchanged consensus (**0.8820 ppm**).

Historical benefit is heterogeneous; the full historical criterion is unsupported. Incremental aggregate benefit is supported. Adverse D12 and FIS D13 cells preclude uniform-session improvement. Envelope-schedule superiority is unsupported, and no different final-data winner is selected. All 15 pooled affine B20 MAE changes were adverse in development; 14 are favorable and one adverse in confirmation.

Confirmation midpoint-envelope diagnostics include **38 false assurances / 74 flagged outputs** and **38 / 3,600 total outputs**, separate from 284 raw and 276 reported-set noncontainments and eight contradictions. These are not affine uncertainty intervals. Conditional resampling is development-only; there is no confirmation bootstrap, certified uncertainty, independent-array validation or newly invented calibration algorithm.

## Dataset, licensing and review status

The public source is UCI dataset 487, DOI [10.24432/C5S302](https://doi.org/10.24432/C5S302), *Gas sensor array temperature modulation*. The [official UCI record](https://archive.ics.uci.edu/dataset/487/gas+sensor+array+temperature+modulation) lists CC BY 4.0. [Dataset instructions](data/README.md) give the official download route and historically verified archive hashes. No download is performed by the reproduction command.

Original project code and release tooling carry the [MIT license](LICENSE). Dataset-derived numerical evidence is attributed under [DATA_LICENSE.md](DATA_LICENSE.md). `unsrtnat.bst` retains its separate LPPL terms. Manuscript prose is excluded from the code license; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). [GITHUB_RELEASE_CHECKLIST.md](GITHUB_RELEASE_CHECKLIST.md) records the reproducibility checks used for this release. Full rendered PDF-page inspection and fresh online dependency installation remain separate checks from the numerical reproduction.
