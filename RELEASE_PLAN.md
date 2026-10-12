# Release preparation plan

This is a local author-review release candidate. Nothing will be published or submitted.

The release will preserve the completed development and fixed-D10 confirmation evidence. Its default reproduction command will verify and score saved numerical outputs, regenerate presentation assets from saved cells, and optionally compile the manuscript. It will not fit models, generate predictions, run C5, access reserved raw data, or generate new resampling indices.

1. Curate frozen source, protocols, model manifests, saved predictions, query/access records, numerical tables, and the completed author-finalized manuscript. Record source hashes and any packaging transformations.
2. Provide portable evidence-only checks, compact prediction CSV exports, figure/table reproduction, and an external UCI download/hash guide.
3. Document authors, licenses, citation, table/figure provenance, commands, and unresolved release approvals without inventing a repository URL.
4. Run integrity, numerical, sensitive-file, size, manuscript, fresh-extraction, and local clean-clone checks. Obtain a fresh review of the release tooling and address findings.
5. Preserve the original scientific artifacts; record release hashes separately and produce a versioned ZIP with an external checksum.

Implementation choices: compressed frozen evidence retains its original relative tree, with lossless expansion verified against original SHA256 values. Build output is ignored and separate. Historical experimental entry points are archival source only; the release runner does not import them. The official raw archive is an optional external dependency for source inspection, not required for the evidence-only reproduction.

## Completion ledger

Curation, portable numerical checks, documentation, automated tooling review, local clean-clone reproduction and fresh-extraction builds are complete. Original scientific inputs remain unchanged. Final packaging adds only release-summary/checklist/verification metadata around the tested scientific/build payload. Publication and author approvals remain pending.
