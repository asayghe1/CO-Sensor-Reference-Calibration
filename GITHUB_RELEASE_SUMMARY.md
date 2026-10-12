# GitHub reproducibility release summary

The local **GitHub-ready author-review candidate** is complete. Nothing was published, submitted or sent to anyone. Scientific source and outputs remain frozen; all 730 pre-existing files in the preservation baseline are unchanged. Packaging performed no model fitting, prediction generation, C5 replay, new resampling-index generation, confirmation bootstrap or raw reserved-data access.

## Output paths

Paths below are relative to the project root, so the public repository contains no private absolute filesystem paths.

| Output | Project-relative path |
| --- | --- |
| Repository folder | `github_release_v1/` |
| This summary | `github_release_v1/GITHUB_RELEASE_SUMMARY.md` |
| Reproduction instructions | `github_release_v1/README.md` |
| Authors and citation | `github_release_v1/AUTHORS.md`, `github_release_v1/CITATION.cff` |
| Complete manuscript source and reading PDFs | `github_release_v1/manuscript/` (`main.pdf`, `supplement.pdf`, `title_page.pdf`; all editable TeX and draft ancillary sources) |
| Original frozen source/numerical evidence | `github_release_v1/frozen/` |
| Compact prediction CSVs | `github_release_v1/predictions/` |
| Exact table/figure mapping | `github_release_v1/docs/MANUSCRIPT_MAP.md` |
| Source and protocol guide | `github_release_v1/docs/SOURCE_GUIDE.md` |
| Dataset download/provenance/hash guide | `github_release_v1/data/README.md`, `github_release_v1/data/DATASET_MANIFEST.json` |
| Publication-ready availability drafts | `github_release_v1/DATA_AVAILABILITY_TEXT.md`, `github_release_v1/CODE_AVAILABILITY_TEXT.md` |
| Review and release checklist | `github_release_v1/AUTHOR_CONFIRMATIONS.md`, `github_release_v1/GITHUB_RELEASE_CHECKLIST.md` |
| Original/new hash manifests | `github_release_v1/manifests/`, `github_release_v1/RELEASE_FILES_SHA256.txt` |
| Verification evidence | `github_release_v1/verification/` |
| Versioned ZIP | `CO_Measurement_GitHub_Reproducibility_v1.zip` |
| ZIP SHA256 sidecar | `CO_Measurement_GitHub_Reproducibility_v1.zip.sha256` |
| Final ZIP extraction/build verification | `CO_Measurement_GitHub_Reproducibility_v1.ARCHIVE_VERIFICATION.json` |

The exact ZIP SHA256 is recorded in the external sidecar and the final archive-verification JSON. It is intentionally not embedded in the ZIP itself, which would create a circular checksum. `RELEASE_FILES_SHA256.txt` covers every other distributable repository file; original scientific hashes remain separate and unchanged.

## Reproduction checks completed

- **417 frozen inputs:** every copied/wrapped file restores the original byte length and SHA256; original protocols, twelve frozen C5 RF models, 261 committed C5 outputs, source, feature records and development evidence are preserved. Model binaries are hashed, not loaded.
- **Development:** 1,455 saved runs; 4,482,000 prediction scalars; 134,460 family/band/subset rows and 134,460 configuration rows. Aggregate/session metrics, query timing, contradiction cross-tabs, update diagnostics and false-assurance CSVs reproduce with maximum numerical difference zero. 21,900 causal events and 113,400 saved purchase states are checked, with the legacy limitations below stated explicitly.
- **Existing development conditional bounds:** all 37,620 effect rows and 3,135 paired loss paths reproduce exactly using nine original index banks. No new bank or confirmation resampling was generated.
- **Confirmation:** all 129 committed paths, 12,900 pre-query snapshots, 52,920 saved purchase states, 40,635 metric rows and 5,040 aggregates pass. Maximum per-run metric difference is zero. Every session resets to the same saved D10 initialization.
- **CSV interchange:** all 1,900,800 compact rows match saved prediction/reference/mask/interval scalars exactly. Missing estimator columns remain blank; no predictions are inferred.
- **Manuscript:** all 950 numerical table rows, 36 confirmation presentation CSV rows, and 412 plotted source cells are checked. All unfavorable tables remain. Main/supplement have the same 17 numbered references; all five PDFs build without unresolved citations/references, overfull or underfull warnings. Main/supplement/title-page text matches the supplied PDFs; their page counts are 20/23/1.
- **Portability:** complete reproduction and five document builds passed from a fresh temporary local Git clone with only release files and installed declared software dependencies. No remote was contacted; the clone remained clean afterward. Fresh archive extraction rebuilt all five PDFs after deleting the precompiled document PDFs. Tested code, scientific evidence and manuscript build inputs remain byte-identical to those checks.
- **Release hygiene:** no flagged credential files, token patterns or private absolute paths were found, including in expanded compressed text and PDF text/metadata. The largest tracked file is 10,881,929 bytes (about 10.4 MiB), below the conservative 50 MiB threshold. No raw UCI archive, raw time-series CSV, R7/R14 raw data, UCI270 sealed batch, cache, environment or Git metadata is distributed. Duplicate long-form prediction exports and redundant large metric copies were omitted.
- **Tooling review:** a fresh automated review checked source provenance and release logic. Its stale-success-report and Python-bootstrap findings were fixed; all eight regression/integrity tests pass. This is automated tooling review, not human scientific verification.

## Scientific conclusions retained

The prespecified pooled affine envelope 20-check confirmation changes MAE **1.3553 → 1.3257 ppm** and strict 1 ppm exceedance **43.06% → 42.14%**. FIS improves **0.9471 → 0.9033 ppm** against affine B0 while remaining worse than unchanged consensus (**0.8820 ppm**). Historical benefit is heterogeneous; incremental aggregate benefit is supported. Uniform-session improvement and envelope-schedule superiority remain unsupported. The development/confirmation reversal and all adverse session/family cells remain visible. Midpoint false assurance is **38/74 flagged** and **38/3,600 total**, separately from interval noncontainment; no affine uncertainty claim is made.

## Review limits and remaining author actions

Funding, competing interests, individual CRediT roles, final access/license authority, AI-use disclosure and all-author approval remain unresolved. MIT code-license text, CC BY 4.0 data attribution and the separate LPPL notice are present; this technical packaging does not establish author/legal approval. The repository URL stays **[GITHUB_REPOSITORY_URL]** in availability drafts until a real public repository exists. No repository DOI, release tag, Zenodo record or submission declaration was invented.

Legacy OLS/ridge exports omit three internally hashed estimators; their full original prediction digests cannot be reconstructed from that reduced export. Legacy development state records omit explicit update-success flags. These limitations are documented rather than filled with invented evidence. Confirmation has the complete recorded audit fields. Existing loss temporal-structure summaries are retained with hashes and original calculation code; no new temporal-structure analysis was added.

Full rendered-page PDF inspection, a fresh online dependency installation and cross-platform execution remain uncompleted. Compiler/text checks and the passing local clean-clone test do not substitute for those checks. The evidence-only workflow establishes consistency and reproducibility of the released numerical results; raw-to-model retraining was intentionally not performed.
