# M27 UAT Remediation Report

**Correction build date:** 30 September 2026  
**Scope:** Findings UAT-01 through UAT-09 from the first guided application walkthrough.

## Ready for local retest

| Finding | Correction delivered | Retest evidence |
|---|---|---|
| UAT-01 | Every control deck now exposes its complete variable register in eight-row pages. The selected variable has live and simulated values, unit, 0–100 normalised range, reset, changed-state marker and aggregate contribution. The aggregate uses the disclosed equal-weight normalisation rule V1. | Capital reports 28 variables and four pages; simulation edits remain private. |
| UAT-02 | The severity tint uses an artwork-calibrated ellipse centred at `(941, 452)` with radii `(139, 127)`. Stable state has no tint; adverse states use one uniform yellow-to-orange colour while retaining texture, lettering and dark rim. | Geometry is asserted in the console package test and calibrated against the 1881 × 1073 master artwork. |
| UAT-03 | Role changes now open an explicit local UAT authorization step, retain the existing live session, enforce server-side view scopes and record granted and denied transitions. The selector is visibly labelled as a local UAT role preview. | An enterprise principal is denied the consultant view; the denied event is recorded. |
| UAT-04 | Every assurance summary row opens a read-only detail panel with source, owner, identifiers, evidence and effective context. | Consultant Change Inbox returns five governed detail rows. |
| UAT-05 | Client Approval now shows recommendation, options, simulated effect, authority and evidence panels, plus Approve, Reject and Return for Clarification actions. Decisions require client scope and step-up authorization; final decisions cannot be contradicted. | Clarification was recorded with `live_actions = 0`; final-decision immutability is unit tested. |
| UAT-06 | Assurance measures state their scope, scale, direction, timestamp and case/configuration reference. Consultant and client use the same case values. | API responses expose `measure_context` on all views. |
| UAT-08 | A simulation owner can create an opaque expiring invitation, copy a scoped join URL, admit the named viewer as read-only, inspect status and revoke access. Reuse, identity mismatch, expiry and revoked access fail closed. | A named viewer joined one simulation read-only; revocation and one-use behaviour pass tests. |
| UAT-09 | Base, Adverse, Severe and Recovery are selectable versioned presets. Stop resets the timeline, Play advances eight periods, Pause retains the inspected period, and Run performs the private scenario calculation. | Preset and playback controls are active application state and leave live monitoring unchanged. |

## Production connection gates

UAT-07 is deliberately visible rather than concealed. Enterprise cards now use the current console state, while the M23–M26 consultant and client records remain labelled `SYNTHETIC_UAT`. A live-data pilot still requires approved tenant-scoped repository queries, source feeds and a running PostgreSQL environment.

Google Meet and Zoom buttons open their providers, but governed meeting creation still requires the organisation's approved OAuth connectors and browser permission at presentation time. Local collaboration can be retested now; external meeting integration remains a deployment task.

The local role-preview authorization demonstrates the governed transition and server-side scope checks. Production authentication still requires the organisation's identity provider, directory claims, mandates and durable audit storage.

## Verification

- JavaScript syntax check: passed.
- Python module compilation: passed.
- Focused M22/M27 tests: 10 passed.
- Entire non-database suite: 25 passed, 36 database tests deselected.
- Local HTTP workflow: simulation creation, participant join, assurance detail and client clarification passed.
- Browser load: no console warnings or errors.

Database-backed integration tests were not run because Docker/PostgreSQL is unavailable on this workstation. They remain required before the live-data pilot; this does not prevent the corrected local UAT walkthrough.
