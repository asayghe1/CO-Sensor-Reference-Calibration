# Completed manuscript source — author review

This folder contains the completed development and fixed-D10 confirmation manuscript with user-confirmed author details, derived from the author-finalization package. Scientific results and table values are unchanged from `co_submission_finish_v1/paper_with_c5/`; the existing final editorial corrections are retained. Exact source hashes are in `../manifests/MANUSCRIPT_SOURCE_MANIFEST.json`.

Run `bash build.sh` here for a document-only build using the included tables, four static figures, bibliography and bibliography style. All project-specific TeX dependencies are present. Standard TeX Live packages are external software dependencies; see the root README. The main manuscript, supplement and title-page PDFs are supplied for reading.

The root evidence-only workflow builds in `build/manuscript/` and makes all accompanying numerical CSVs available there by lossless expansion. They are stored once under `frozen/`, not duplicated in this source folder. `format_figures.py` reads saved summary cells only; `FIGURE_VALUE_AUDIT.json` specifies every plotted source value. The root workflow checks all table cells against the numerical files before generating figures.

Funding, conflicts, individual CRediT contributions, final access arrangements, AI-use disclosure and all-author approval remain unresolved. Cover-letter and highlights sources remain drafts. The existing manuscript truthfully describes current access; separate availability-text drafts at the repository root contain the future GitHub URL placeholder. No repository or DOI has been invented. Full rendered-page inspection remains outstanding.
