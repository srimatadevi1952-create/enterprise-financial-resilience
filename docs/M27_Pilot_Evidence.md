# M27 Controlled Pilot Evidence

## Pilot method

Both pilots are deterministic and replayable. Acceptance requires every ordered step and each readiness category to pass. The validator rejects incomplete sequences, duplicate or missing readiness categories, failed steps, invalid timestamps and any non-zero live-action count.

## Enterprise-operated pilot

| Order | Step | Result | Evidence reference pattern |
|---:|---|---|---|
| 1 | Configuration resolved | Pass | `pilot:enterprise:configuration_resolved` |
| 2 | Live state observed | Pass | `pilot:enterprise:live_state_observed` |
| 3 | Private simulation completed | Pass | `pilot:enterprise:private_simulation_completed` |
| 4 | Change approved | Pass | `pilot:enterprise:change_approved` |
| 5 | Information escalated | Pass | `pilot:enterprise:information_escalated` |
| 6 | Outcome reviewed | Pass | `pilot:enterprise:outcome_reviewed` |
| 7 | Lesson published | Pass | `pilot:enterprise:lesson_published` |

This proves that Model 1 remains independently operable through configuration, monitoring, simulation, approval, evidence escalation, review and institutional learning.

## Consultant-operated pilot

| Order | Step | Result | Evidence reference pattern |
|---:|---|---|---|
| 1 | Assignment active | Pass | `pilot:consultant:assignment_active` |
| 2 | Authorised source ingested | Pass | `pilot:consultant:source_ingested` |
| 3 | Change assessed by expert | Pass | `pilot:consultant:change_assessed` |
| 4 | Private simulation completed | Pass | `pilot:consultant:private_simulation_completed` |
| 5 | Client approved | Pass | `pilot:consultant:client_approved` |
| 6 | Sandbox execution completed | Pass | `pilot:consultant:sandbox_executed` |
| 7 | Outcome validated | Pass | `pilot:consultant:outcome_validated` |
| 8 | Lesson published | Pass | `pilot:consultant:lesson_published` |

This proves the full consultant service path while preserving the client decision gate and separate sandbox execution boundary.

## Readiness evidence

Both pilots record passing evidence for usability, accessibility, performance, security, retention, audit and tenant isolation. Each record stores the operator, UTC start and completion times, evidence references and evidence digest.

## Control result

- Enterprise pilot: **Pass**
- Consultant pilot: **Pass**
- Visualization or simulation live actions: **0**
- Production action capability: **Disabled**
- Direct pilot-evidence modification: **Rejected by database**

The automated pilot is a controlled technical proof. Business-owner approval, production identity integration, approved source connectors and a separately accredited execution adapter remain production-entry gates.

