# M24 Completion Report

M24 completed on 24 September 2026.

## Outcome

The platform now supports the consultant-operated service defined in the dual operating model while preserving the enterprise-operated system. The consultant workflow is implemented as a tenant-scoped, evidence-backed lifecycle:

1. establish a client-specific consultant assignment;
2. record a time-bounded client service mandate;
3. receive an authorised, read-only source observation;
4. open a detected-change case against an effective M23 configuration;
5. record the consultant's professional assessment;
6. submit a simulation-backed recommendation;
7. obtain an independent client decision;
8. prepare and preflight a controlled sandbox action;
9. execute the sandbox package with zero live actions; and
10. compare expected and observed metrics and validate the outcome.

Model 1 remains independent. Existing enterprise users can continue to use Live Monitor, private Simulation Lab and the M0 to M23 services without a consultant assignment or consultant workflow.

## Implementation

Migration `m24_0028` adds:

- consultant assignments and portfolio identity;
- client service mandates;
- append-only source observations with lineage, payload hash, quality and reconciliation state;
- consultant cases linked to the effective enterprise configuration and supporting observations;
- append-only expert assessments and client decisions;
- simulation-linked change proposals;
- sandbox-only execution packages with idempotency, preflight evidence, rollback plan and a database-enforced zero-live-action rule; and
- append-only case events for the complete decision trail.

Migration `m24_0029` adds immutable post-implementation reviews that store expected metrics, observed metrics, evidence and the final outcome.

Migration `m24_0030` restores and verifies the M23 immutable-configuration privilege boundary. This prevents a later migration from accidentally restoring update access to validated configuration children.

Migration `m24_0031` adds time-bounded client decision authority. Proposal decisions and service mandates require an active authority record whose scope includes both the decision type and implementation mode.

The `m24_consultant` service validates time-bound authority, consultant assignment, tenant scope, evidence, independent client approval, implementation mode, delegated-action type and target, idempotency, step-up authentication, sandbox preflight and outcome validation.

## Control Results

- A consultant can view only assignments bearing the authenticated consultant principal identifier.
- Every case is fixed to one tenant, assignment and effective M23 configuration.
- An observation from one client cannot be attached to another client's case.
- Source observations, assessments, client decisions, case events and outcome reviews are append-only.
- Replayed source observations are rejected without aborting the surrounding transaction.
- The consultant cannot approve the consultant's own proposal.
- Proposal decisions and mandate issuance require explicit, time-bound client authority.
- Delegated preparation is rejected without an active client mandate.
- The action type and target must both fall within the mandate.
- Revoking the assignment blocks further observations and actions.
- Execution packages are constrained to `sandbox_only = true` and `live_actions = 0` by the database.
- Expected and observed effects are retained in the same review record with evidence lineage.

## Verification

- 51 tests passed.
- M24 unit and integration tests passed.
- Both development and test databases migrated to `m24_0031`.
- The full M0 to M23 regression suite passed, demonstrating that Model 1 remains operational.
- Cross-tenant observation attachment was rejected.
- Self-approval, missing mandates, unauthorised targets and post-revocation collection were rejected.
- The complete delegated sandbox path finished with zero live actions and an immutable validation record.

## Deliberate Production Boundary

M24 does not connect to a client's production systems. Online connector registration, recurring information obligations and evidence-confidence management belong to M25. The M24 execution adapter is deliberately sandbox-only. A production action connector cannot be enabled merely by changing application input because the database requires every M24 package to remain sandbox-only with zero live actions.

The visual consultant control centre and client portal will be integrated with the approved M22 visual language in M27. M24 supplies their governed data, authority and workflow foundation.

## Next Milestone

M25 will implement Online Client Information Obligations and Evidence Confidence, including the authorised connector/source register, recurring submissions, missing-information workflow, reminders, escalations and separate risk-severity and assessment-confidence measures.
