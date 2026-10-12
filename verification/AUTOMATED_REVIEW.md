# Automated release-tooling review

A fresh assistant review checked the release runner, reporting adapters, tests, documentation and relevant frozen source. It independently compared all 417 frozen files and 50 copied manuscript files against their manifests and the original workspace bytes; all matched. The reviewer did not rerun C5, fit models, read raw reserved data or provide human scientific approval.

Two findings were addressed:

1. A failed retry could leave a previous `REPRODUCIBILITY.json` marked PASS. The runner now removes prior generated reports, writes timestamped RUNNING, writes FAIL on exceptions, and labels preparation-only runs PREPARED. A regression test first reproduced the failure and then passed after the fix.
2. The initial README virtual-environment command used an unavailable unversioned Python name. It now starts with `python3` and documents the tested Python version.

An additional guard refuses optimized Python (`-O` or `PYTHONOPTIMIZE`) so assertion-based checks cannot be silently disabled. The eight release-tool tests pass. A narrow review recheck confirmed failed-run status, preparation status and both optimization paths, with no regression found.

Review limits: raw-to-model retraining, absent legacy digest components, full PDF visual inspection, online dependency installation, cross-platform behavior, legal release authority, human scientific verification and all-author approval were outside the automated review. The parent workflow separately performs clean-clone and archive checks. No scientific-result or source-provenance discrepancy was found by this tooling review.
