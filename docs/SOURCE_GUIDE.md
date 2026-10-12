# Source, evidence and protocol guide

Paths below are relative to `frozen/`. The same tree is expanded under `build/frozen/` by `python scripts/reproduce.py --prepare-only`. A final `.gz` added by packaging is removed during expansion. Files originally ending in `.gz` remain their original archives. `manifests/SOURCE_MANIFEST.json` identifies the encoding, original byte length/SHA256, packaged byte length/SHA256 and both paths for every item. No original scientific file was edited.

| Function | Frozen source / evidence |
| --- | --- |
| Raw preprocessing, time/quality admission, exposure grouping, heater-phase features | `phase5/resume/audit.py`, `methods.py`; `phase5/resume/evidence/exposure_features.json.gz`, `data_audit.json.gz`, `admission.json` where present |
| RF/OLS/ridge specifications, scaling and fit roles | `phase5/resume/analysis.py`, `phase6/analysis.py`, `phase6/methods.py`; development upstream provenance under `co_revision_execution_v2/work/evidence/UPSTREAM_MODEL_PROVENANCE.json.gz` |
| Saved development upstream predictions and initialization inputs | `phase6/evidence/authentic_packets_predictions.json.gz`, `calibration_packets.json.gz`, `individual_calibration_predictions.json.gz`; `reference_budget_study_v1/evidence/PRIOR_INPUT_MANIFEST.json.gz` |
| Observable construction and shared configurations | `reference_budget_study_v1/data.py` |
| Envelope construction and historical risk | `reference_budget_study_v1/methods.py` |
| Schedules, exact quotas and reference access | `reference_budget_study_v1/replay.py`; `co_revision_execution_v2/work/src/development_replay.py`; `co_submission_finish_v1/src/c5_replay.py` |
| Offset, inverse affine, projection and midpoint | `reference_budget_review_correction_v1/correction.py`; `co_revision_execution_v2/work/src/revision_analyses_checked.py` |
| Development driver, evaluators and reporting | `co_revision_execution_v2/work/src/run_development.py`, `analyze_development.py`, `update_diagnostics.py`, `rebuild_manuscript.py` |
| Development protocol, roles and normalization | `co_revision_execution_v2/work/PROTOCOL.v2.md`, `PROTOCOL_SHA256.txt`, `SOURCE_AND_ROLE_MANIFEST.json.gz`; evidence `B0_NORMALIZATION.json.gz`, `RUN_MANIFEST.json.gz` |
| Development predictions, masks and primary causal records | `co_revision_execution_v2/work/evidence/runs_{bounds}_{model}_{session}.json.gz` (36 archives), `historical_{model}_{session}.json.gz` (9 archives) |
| Development contradiction/raw-intersection evidence | `reference_budget_review_correction_v1/diagnostics/slope95_{model}_{session}.json.gz` (9 archives). These are saved derived diagnostic arrays, not raw sensor data. |
| Frozen development resampling evidence | `co_revision_execution_v2/work/evidence/PAIRED_LOSS_PATHS.json.gz`, `indices_L{5,10,20}_{D6,D8,D10}.npy.gz`, `RESAMPLING_INDEX_MANIFEST.json` |
| C5 preprocessing, frozen model preparation and guarded historical extraction | `co_submission_finish_v1/src/c5_inputs.py`, `prepare_c5.py`, `extract_c5.py` |
| C5 replay and evaluation | `co_submission_finish_v1/src/c5_replay.py`, `execute_c5.py`, `c5_evaluate.py` |
| C5 protocol, model/input hashes and D10 state | `co_submission_finish_v1/C5_FROZEN_PROTOCOL.md`, `C5_CODE_AND_ARTIFACT_HASHES.json`, `C5_INPUT_MANIFEST.json`, `MODEL_MANIFEST.json.gz`, `D10_INITIALIZATION.npz`, `models/*.joblib` |
| Committed C5 predictions, masks, intervals and pre-query records | `co_submission_finish_v1/c5_execution_v1/replays/D{11,12,13}_{policy}_B{budget}_S{seed}.json.gz` and matching `.prequery.jsonl.gz`; `FINAL_REPLAY_COMMIT_MANIFEST.json.gz`, `EXECUTION_LOG.jsonl` |
| C5 saved evaluator reference values | `co_submission_finish_v1/c5_execution_v1/REFERENCES_FOR_EVALUATOR_ONLY.json`; these 300 saved exposure references are numerical evaluation evidence, not reopened raw records. |
| C5 metrics and predeclared primary contrasts | `co_submission_finish_v1/c5_execution_v1/replays/METRICS.json.gz`, `AGGREGATE.json.gz`, `PRIMARY_CONTRASTS.json`; complete CSV exports alongside `replays/` |
| Completed C5 reporting-only audit source | `co_submission_finish_v1/c5_reporting_finish_v1/verify_saved_outputs.py`, `verify_aggregate_and_contrasts.py`, `verify_reporting_exports.py` |
| Actual false-assurance reporting | `co_submission_finish_v1/src/audit_assurance.py`, `aggregate_assurance.py`; `co_submission_finish_v1/paper_with_c5/FALSE_ASSURANCE_AUDIT.csv.gz` and `FALSE_ASSURANCE_POOLED.csv.gz` |

Development protocol SHA256: `6163d54d660beaef501786d5cf3869544f0cd5160feb5092ace5065174ab0300`.

C5 protocol SHA256: `4de22fff8678773f3fb3ba23198431947efe3c54145b8452ddec2ebf036c40bc`.

C5 final replay commit manifest SHA256: `17acc46519ead38977242df56d56c55be773687d8eef01d2d5c9ffc362578c9b`.

The original C5 artifact manifest authenticates 38 files, including twelve RF model binaries. Those binaries are hashed without loading them. Development uses saved upstream predictions and a fit/fold/configuration provenance manifest; it does not claim that serialized development OLS/ridge/RF models were archived when they were not.

## Supported release adapters

The new `scripts/` entry points change paths and reporting destinations only. The development metric scorer is the original evaluator through the existing aggregate/share calculations, terminated before resampling-bank creation. False-assurance and saved-coefficient diagnostics retain the original arithmetic. C5 reporting adapters independently score saved arrays and compare all metric fields. C5 initialization checks compare all saved starts with the common D10-initialized state; they do not refit initialization coefficients. The separate saved-resampling checker uses the archived development index banks and original loss-aggregation order, generating neither new draws nor adaptive paths.

`verify_development_tables.py` uses the original table-row formulas to check completed typesetting while preserving edited captions/prose. `verify_confirmation_tables.py` checks C5 JSON→CSV→TeX values. `manuscript/format_figures.py` reads saved summary cells; the audit records all 412 plotted cells. `prediction_csv.py` exports existing scalars in a compact wide format, with one exposure/configuration row and separate estimator columns. Blank estimator cells mean that estimator was not in the frozen export; they are not zeros or reconstructed predictions. Exposure/configuration IDs are one-based in CSV; the causal JSON event indices are zero-based.

The compact CSVs and causal JSON serve different review uses. They intentionally share prediction values, which are checked exactly. Duplicated long-form historical CSV exports, repeated metric JSON copies, superseded manuscripts, large raw archives and intermediate backups were omitted. The canonical committed C5 `METRICS.json` is used; its redundant `INDEPENDENT_METRICS.json` copy is unnecessary.

## Audit limits

Primary development records contain detailed causal events and saved purchased states. Legacy bound-sensitivity records retain predictions, masks and intervals but not the same detailed event format. RF primary pre-query prediction digests can be reconstructed exactly. Historical OLS/ridge exports retained four of seven internally hashed estimators: their original full prediction digests remain recorded but cannot be independently reconstructed from the reduced export. Older development state records also omit an explicit update-success flag; finite stored state and recorded failure counters are checked, without inventing that missing flag. Confirmation records retain all seven estimators, full pre-query snapshots and update-success fields, so the complete confirmation audit is possible.

The default workflow proves consistency of saved numerical evidence and presentation, not independent raw-to-model retraining. It does not retroactively establish human scientific verification. No raw reserved data were accessed in release preparation. Full rendered-page manuscript inspection, author declarations and all-author approval remain outstanding.
