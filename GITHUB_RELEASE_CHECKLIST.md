# GitHub release checklist

Technical reproducibility results are recorded in `verification/`.

- [x] Sensitive-file scan completed for the distributable tree.
- [x] File-size scan completed; ordinary tracked files remain below GitHub's large-file limits.
- [x] License and attribution files are present for original code, dataset-derived materials and third-party components.
- [x] Numerical reproduction and clean-clone checks passed for the frozen scientific package before the submission-text cleanup.
- [x] Manuscript-number reproduction passed for the frozen development and temporal-confirmation evidence.
- [x] Repository URL inserted in README, CITATION.cff, data/code availability text and submission manuscript.
- [ ] Repository visibility: change `asayghe1/CO-Sensor-Reference-Calibration` from private to public before manuscript submission.
- [ ] Rebuild the updated submission branch with `cd manuscript && bash build.sh` and confirm zero LaTeX errors, unresolved citations/references and overfull boxes.
- [ ] Complete full rendered-page inspection of the updated main manuscript, supplement, title page, cover letter and highlights.
- [ ] Optional: perform a fresh online dependency installation/cross-platform reproduction and archive a public release with Zenodo after publication-ready review.
