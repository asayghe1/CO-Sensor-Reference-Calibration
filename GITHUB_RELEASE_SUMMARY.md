# GitHub reproducibility release summary

This repository contains the frozen scientific evidence and reproducibility tooling for the CO sensor-array calibration manuscript. The scientific source artifacts, saved predictions, query masks, metrics and confirmation outputs were not altered by the submission-text cleanup.

## Reproducibility scope

The release retains the development and fixed-D10 temporal-confirmation evidence, including saved predictions, causal access records, masks, protocols, numerical tables, figure inputs and verification manifests. The evidence-only workflow recomputes the reported metrics from saved outputs without refitting models or regenerating predictions.

## Submission-text cleanup

The `submission-cleanup-v1` branch updates manuscript-facing text only:
- removes author-review placeholders and internal workflow labels;
- qualifies the confirmation result and states its D11 dependence;
- adds Se et al. (2024) to related work;
- reduces repeated headline values and repeated uncertainty caveats;
- finalizes the CRediT and AI-assistance wording;
- replaces draft title-page, cover-letter and highlights text;
- inserts the repository URL into data/code availability statements.

A fresh LaTeX build and full rendered-page inspection of this updated branch remain required before merge/submission. The repository is currently private and must be made public before the manuscript's repository-access statements are used for submission.
