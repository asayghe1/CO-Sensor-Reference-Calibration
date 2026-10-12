# Fixed-D10 C5 temporal confirmation — frozen preparation v1

Status: prepared and inactive. No final payload or reserved sensor value has been parsed. This protocol becomes executable only after the user explicitly authorizes C5 for its reported SHA256. It is informed by known development findings; it is not independent preregistration. No model, budget, family, policy or seed may be selected by final outcomes.

## Immutable source roles and exact inputs

Eligible channels are R1–R6 and R8–R13, in that fixed order; Figaro is the first six and FIS the last six. R7/R14 are excluded throughout. UCI270 batches 7–10 remain sealed and unused. Original reservations are in FROZEN_PROTOCOL.md, phase5/ADMISSION_PROTOCOL.v1.0.md and phase5/evidence/reservation_rules.json. Their roles are unchanged.

The raw source is data/co_chamber/uci487.zip, nested member gas-sensor-array-temperature-modulation.zip. Original outer/nested/member hashes, exact header and timestamp-to-session mapping are frozen in C5_INPUT_MANIFEST.json, copied from the original development audit without opening an archive. Outer SHA256: cb5ce4a6af1a51b933d1979952d7845f0e9baac54e15a81a1e3599e8b85905d4. Nested SHA256: 4a6b4e3609aeff297dcbed084e7c85f1c88a8c5219417afebe99281c369dcd11. These are reproducibility fingerprints, not publisher signatures.

| Role | Session and exact CSV filename |
|---|---|
| Upstream fit | D1 20160930_203718.csv; D2 20161001_231809.csv; D4 20161004_104124.csv; D5 20161005_140846.csv; D6 20161006_182224.csv; D7 20161007_210049.csv; D8 20161008_234508.csv; D9 20161010_095046.csv |
| Initial correction calibration only | D10 20161011_113032.csv |
| Independent assessment resets | D11 20161013_143355.csv; D12 20161014_184659.csv; D13 20161016_053656.csv |
| Excluded clock failure | D3 20161003_085624.csv |

Upstream fitting uses ONLY phase5/resume/evidence/exposure_features.json (10,800 permitted development rows), with exact unique day/exposure/unit identity checks. Each model uses its own unit's 800 rows from the eight fit days. D10 is never passed to RF fitting or StandardScaler.fit. No global transfer model or alternative upstream model is required for the five-peer median estimand.

## Archived preprocessing and fixed model files

For exposure e=1…100 retain time [900e+600,900(e+1)−60) seconds. Preserve the archived implementation: core rows must exceed 500; each heater phase has at least 10 rows; finite permitted fields; positive resistance; strictly increasing clock; max core gap <5 s; recording starts no later than 900e and ends at least 900(e+1)−10. Released-reference constancy is an isolated grouping check. Missing required groups invalidate evaluation; no substitute exposure/day/unit is allowed.

Predictors, in order: median natural-log resistance in native MΩ at high heater >0.5 V; low heater 0–5 s; low 5–15 s; low ≥15 s since the measured falling edge; median RH%; median temperature °C. Measured heater transitions and timestamps define phase and grouping only. Time/day/exposure identifiers, reference CO, flow, injected concentrations, R7/R14 and final statistics are not predictor inputs. No blank/test normalization or outcome tuning.

Twelve individual pipelines: StandardScaler followed by RandomForestRegressor(random_state=487,n_estimators=100,max_depth=5,min_samples_leaf=5,n_jobs=1); all other sklearn defaults are recorded explicitly in MODEL_MANIFEST.json with software versions, exact fit IDs and scaler statistics. Files are models/RF_R{01,02,03,04,05,06,08,09,10,11,12,13}_fitD1D2D4D5D6D7D8D9.joblib. The manifest freezes every model's exact SHA256. No refitting after final access.

For each omitted unit, use the median of its five same-family peers' individual RF outputs. These twelve outputs overlap and are correlated. D10_INITIALIZATION.npz stores D10-only consensus, residuals, contexts, confidence, q, individual predictions/tree spreads and released historical reference. MODEL_MANIFEST.json freezes context mean/population SD (zero SD→1), affine mean/population SD (below 1e−8→1), confidence historical median floor0.1, and q as the 91st ordered absolute D10 residual floored at0.1. RH/T/consensus context is standardized using D10 only.

## Estimators, schedules, budgets and seeds

Original primary methods remain: unchanged median consensus, contextual midpoint, interval projection, regularized offset, inverse affine λ1. Historical assimilation uses ridge1, θ=0/P=I before all 100 D10 pairs, and λ1. The archived formulas, contradiction/hull fallback, SPD/finite checks, symmetry operation and numerical fallback rules are preserved in hashed sources. Primary bounds: epsilon0.1 ppm, rho0.01 ppm/exposure, gamma0.5 ppm, empirical maximum slope, with no clipping or slope95 substitution.

Declared extensions, never replacements for the original primary contrasts: inverse affine forgetting factors .95 and .90, applied only at purchases, discounting historical information and ridge; and one fixed .95 max-over-twelve unscaled φ′Pφ controller. All seven estimators consume each run's same purchased mask. No affine-specific scheduler and no outcome-chosen “best” comparator.

Schedules: periodic zero-based floor((k+0.5)100/B); random uniform B-subset using every seed487–496; confidence (maximum normalized mean peer tree SD); envelope/radius (maximum radius/q, contradiction score10^12). The original adaptive higher quantile at1−remaining/horizon, strict exceedance and exact-quota forcing rule are unchanged. Envelope history uses archived D10 leave-one-out anchor risk, while slope/normalization use D10. Confidence history uses D10 normalized confidence. The fixed .95 information history evaluates all 100 D10 regressors using the initialized driver P, then appends pre-query scores.

Budgets0/5/10/20 checks per100-exposure session; deterministic seed487. Canonical B0 is one shared numerical baseline per day, not duplicated physical evidence. Positive-budget random seeds are all retained and averaged within day. One shared purchase per exposure, charged even at exposure100. A single seed/arm purchase cannot benefit any other arm.

## Causal access and independent D10 resets

Every policy/budget/seed/day receives new estimator, envelope, provider and scheduler objects. Each of D11, D12 and D13 starts from the SAME D10 initialization; there is no D11→D12→D13 recalibration or acquired-label carry. Upstream models and normalization never update.

Current permitted observables → all predictions/intervals/flags and query decision → exclusive JSONL record flush+fsync → current budget-gated purchase → state update for later exposures. The current prediction cannot use its own label. Only purchased references update the estimators and controller. ReferenceProvider denies future, duplicate and over-budget access. Complete reference arrays are held only in the provider/evaluator layer; inference packets accept exactly z/consensus/confidence. No future-observable ranking or reference-defined evaluation stratum enters inference. The final adapter separates outcomes from observable packets; reference constancy is only a required grouping check.

All paths for a day freeze before its evaluator runs. The next day creates new state. Shared masks apply only among estimators within a single costed arm, not across policies, budgets, seeds or sessions. Persist partial records if any run fails; never overwrite an existing frozen replay.

## Endpoints, denominator rules and aggregation

The original co-primary descriptive contrasts are preserved:

1. Historical inverse affine λ1 B0 minus unchanged consensus B0.
2. Incremental inverse affine λ1 envelope B20 minus its own inverse affine λ1 B0 on identical all-exposure keys.

Primary endpoint is strict pre-query absolute prediction-minus-released-reference error >1 ppm; MAE is the accuracy guardrail. Secondary .5/2 ppm exceedance, RMSE, signed bias, all estimator/schedule/budget/factor results, family and every day/configuration value, width, contradictions, containment, purchased timing and assurance are retained. Relative10% and concentration bands remain evaluation-only development sensitivities; they are not primary C5 endpoints. No reference uncertainty propagation or IID significance test is implied.

Within exposure average all twelve indicators/absolute errors; retain separate six-output Figaro/FIS summaries and all twelve configuration cells. Average seeds within day, then give the three days equal weight. Counts sum day-level seed-mean numerators/denominators; RMSE uses weighted squared errors before square root. Expected physical N=300 exposures and3600 correlated configuration outputs, not replicate counts from seeds/arms.

All/queried/unqueried outputs retain exact counts. Positive-budget subsets report same-subset consensus and own-B0 values. Queried B0 has undefined accuracy/assurance rates, not zero. False assurance is noncontradictory own-radius≤tolerance AND actual absolute error>that tolerance. Report false/assured and false/all ratios from weighted counts; zero denominators are NA. Keep raw/report-hull noncontainment and contradictions separate; RLS assurance is unavailable. Record session effects/directions and fixed-seed ranges; never suppress reversals.

The original draft disallows population bootstrap intervals. The reviewed development draft's conditional block resampling is optional planning context, not part of this C5 executable scope: no new resampling or outcome-based method promotion is authorized here. All existing development resampling files remain preserved. Forgetting and the information controller are the explicitly included C5 extensions.

## Scientific failures versus invalid evaluation

Valid scientific failures remain scored and reported: interval noncontainment, contradictions, sparse/false assurance, adverse MAE or exceedance, endpoint disagreement, family/day reversals and failure to establish incremental benefit. Any raw noncontainment rejects an unconditional hard-bound claim; hull containment does not rescue it. Never tune bounds after failure.

Historical or incremental descriptive benefit requires negative1ppm contrast AND nonpositive MAE change overall AND separately for BOTH families. Otherwise report absent/heterogeneous confirmation. Any adverse day/family cell precludes a uniform improvement claim. Secondary schedule superiority additionally requires negative1ppm and nonpositive MAE against periodic, random-seed mean and confidence atB20 overall and both families; fixed-seed overlap must be reported. It cannot replace either primary comparison or support a population-superiority claim.

Invalid evaluation: hash/role/access violation, current or unpurchased label use, cross-arm/session carry, changed predictions after reveal, budget mismatch, absent/incompatible required group, invalid pairing, nonfinite unscorable endpoint, or unrecorded numerical fallback. Stop and preserve partial evidence, identify the integrity/access failure, and do not reinterpret it as a scientific null. Recorded archived numerical fallbacks retain their prediction and explicit failure record; they neither certify physics nor disappear from reporting. Future raw grouping/quality checks remain required after authorization and may invalidate evaluation.

## Frozen implementation and authorization boundary

C5_INPUT_MANIFEST.json, MODEL_MANIFEST.json, D10_INITIALIZATION.npz and C5_CODE_AND_ARTIFACT_HASHES.json freeze exact input identities, normalization/model bytes, settings, implementation and tests. src/execute_c5.py requires explicit authorization plus the exact authorized protocol SHA256 and verifies the embedded artifact-manifest hash and all its entries before opening final inputs. src/extract_c5.py is a hash-gated opaque extractor for the three exact final members. src/c5_inputs.py is an inactive final adapter; only synthetic fixtures have exercised it. A future authorized extraction must match the original member hashes and copy only the three exact final files into an isolated input directory. Never convert/use R7/R14 or UCI270 reserved payloads.

This preparation does not activate C5. Stop before final payload parsing, present C5_PREFLIGHT.md and this protocol's SHA256, and obtain explicit user authorization. No submission, publication, author declarations, independent-array validation or journal-readiness claim follows.

Artifact-manifest SHA256: `11c1f9a6b3010345ed53413a8236d6139d038b95f5abc06d3c081e8ae9095d8a`
