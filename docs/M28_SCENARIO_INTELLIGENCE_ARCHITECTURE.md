# M28 Scenario Intelligence, Enterprise Calibration and Adaptive Recovery

## Purpose

M28 connects live observations and private simulations to a governed scenario repository. It identifies direct and connected effects, explains each result, finds exact and related precedents, validates any proposed reuse against the current enterprise state, and creates a draft lesson only after actual recovery has been verified.

The model is calibrated separately for each enterprise. No coefficient, variable weight, dependency effect or distribution is assumed to be universally valid.

## Enterprise-specific calibration

An enterprise calibration consumes only established historical observations with unique lineage references. Every observation contains:

- its effective timestamp and source lineage;
- the six broad control states;
- the underlying variable values;
- observed probability, impact and resilience outcomes; and
- an M25 evidence-quality state.

The first model uses ridge-regularised regression with declared control dependency interactions. The regularisation reduces unstable coefficients when variables are correlated. Observations are ordered by time; the latest 20 percent are held out for back-testing so the model is not validated on the same periods used to fit it.

Each calibration records its training window, observation count, feature names, probability coefficients, impact coefficients, resilience coefficients, interaction terms, training error, holdout error, ridge penalty, historical-data digest, model digest and limitations.

The calibration begins as `CANDIDATE`. Its creator cannot approve it. Approval and activation are separate append-only events, and activation is never automatic.

## Variable weights

Weights are calculated independently within each broad control. Historical importance is measured from the absolute relationship between each variable and the observed risk outcome. The empirical weight is blended with the enterprise's approved prior weight:

`final weight = credibility × historical weight + (1 − credibility) × approved prior weight`

Credibility increases with the number of established observations. This prevents a short or abnormal history from immediately overwhelming expert and governance knowledge. Weights are then normalised to total 1.0 within each control and stored with the calibration.

## Distribution fitting

M28 fits distributions according to the declared nature of each variable:

| Variable kind | Fitted family |
|---|---|
| Bounded rate or probability | Beta |
| Event count with ordinary dispersion | Poisson |
| Over-dispersed event count | Negative binomial |
| Strictly positive, skewed value | Lognormal |
| Enterprise history to be preserved directly | Empirical quantiles |
| General continuous value | Normal |

Every distribution stores its sample count, mean, variance, fifth percentile, median, ninety-fifth percentile and family parameters. The historical window is enterprise and configuration specific. Distribution drift must trigger recalibration review rather than silent parameter replacement.

## Scenario identity

A scenario fingerprint is calculated from:

- enterprise configuration and active calibration;
- model version and baseline hash;
- changed variables, directions, magnitudes and weights;
- activated dependency pathways; and
- jurisdictions.

The observation time and evidence record are retained but do not make an otherwise identical scenario different. This permits repeat observations of the same material condition to resolve to one scenario identity while preserving separate evidence events.

Every live or simulated occurrence is retained separately with its own time, result and evidence. A new fingerprint creates a new scenario definition; an existing fingerprint adds another occurrence rather than duplicating the definition.

## Matching and precedent reuse

An exact fingerprint produces an exact match. Non-identical scenarios are ranked using:

- 60 percent variable-state similarity;
- 20 percent dependency-path similarity;
- 10 percent jurisdiction similarity; and
- 10 percent model and configuration context.

The first thresholds are 85 percent for a strong match and 60 percent for a related match. These thresholds are versioned policy values and require calibration during the pilot.

A matched intervention is advisory. It cannot initiate a production action. Before it becomes eligible for a client decision, the current case must pass a validation simulation, reach at least 80 percent evidence confidence, have a ready rollback plan and retain supporting evidence. Implementation still requires the M24 decision and mandate controls.

## Online and simulation scenarios

Both sources use the same scenario contract:

- `LIVE` represents a material condition detected from governed online observations;
- `SIMULATION` represents an authorised private what-if branch.

Routine fluctuations do not create new knowledge cases. Materiality, novelty and case-closure policy determine whether a record proceeds to lesson drafting.

## Lesson lifecycle

Simulation results may inform a lesson, but only a verified actual recovery can produce a lesson draft. The draft records the scenario, response, expected outcome, actual outcome and evidence. M26 independent review and publication remain mandatory. Retrieval remains advisory and tenant bound.

## Console behaviour

The local console now returns a scenario identifier, explanation, connected pathways, results, model version, precedent-search state and lesson eligibility after every private run. Until approved enterprise history is connected, the console visibly uses `DEFAULT-UAT-V1`; it does not claim to be calibrated.

## Production gates

Before activating an enterprise calibration:

1. map the 220 variables to approved source records and units;
2. establish sufficient, representative historical depth;
3. resolve missing values, regime changes and structural breaks;
4. approve dependency definitions and prior weights;
5. back-test probability, impact and resilience errors;
6. perform sensitivity, stability, fairness and tail-risk review;
7. obtain independent model approval;
8. activate through an append-only activation event; and
9. monitor drift and outcome error continuously.
