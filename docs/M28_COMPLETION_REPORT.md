# M28 Completion Report

M28 was built on 30 September 2026.

## Delivered

- Enterprise-specific calibration from governed historical observations.
- Ridge-regularised coefficients for probability, impact and resilience.
- Explicit dependency interaction terms.
- Historical-sensitivity variable weights blended with approved prior weights.
- Beta, Poisson, negative-binomial, lognormal, empirical and normal distribution fitting.
- Chronological holdout testing and recorded validation error.
- Candidate, independent approval and explicit activation boundaries.
- Canonical scenario fingerprints for live and simulated sources.
- Separate occurrence evidence for every repeated live or simulated instance of a scenario.
- Exact, strong, related and distinct scenario matching.
- Deterministic scenario narratives and connected-path explanations.
- Precedent retrieval that always requires current-state validation.
- Validation rules covering simulation outcome, evidence confidence and rollback readiness.
- Draft-lesson creation only after verified recovery.
- Append-only persistence for calibrations, distributions, weights, approvals, activations, scenarios, matches and response validations.
- A post-run console panel showing the scene, results, connected pathways, model version, precedent state and lesson state.

## Safety properties

- No calibration activates itself.
- The calibration creator cannot independently approve it.
- Historical inputs require established evidence and unique lineage.
- A precedent never produces automatic execution authority.
- An exact scenario match still requires current-state validation.
- A simulated outcome alone cannot become a published lesson.
- Every stored model and scenario carries a reproducible digest or fingerprint.
- Existing live monitoring remains unchanged by simulation.

## Current operating boundary

The local console remains on the disclosed `DEFAULT-UAT-V1` model. The M28 calibration facility is ready, but a particular enterprise model cannot honestly be fitted until that enterprise's approved historical records, units, lineage, configuration and prior weights are supplied.

The database migration is prepared as revision `m28_0037`. Database-backed migration tests remain pending while the local Docker/PostgreSQL service is unavailable.
