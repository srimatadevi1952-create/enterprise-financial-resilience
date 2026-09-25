# M27 Operator Guide

## Purpose

M27 brings enterprise-operated Model 1 and consultant-operated Model 2 into the approved M22 console. The dashboard remains a full-screen, no-scroll instrument panel. The new Operational Assurance workspace is read-only and cannot initiate a financial or production action.

## Opening the workspace

Open the local console at `http://127.0.0.1:8766/` and select **Operational Assurance**, or press **A**. Drag the dark title bar to move the panel. Press **Escape** or select the close control to dismiss it.

The local demonstration exposes three governed views:

1. **Enterprise Model** — configuration, information obligations, governed changes and case intelligence for the enterprise's own operating team.
2. **Consultant Centre** — assigned-client portfolio, change review, client decisions and current mandate for an authorised risk consultant.
3. **Client Approval** — the recommendation, simulated effect, requested authority and decision evidence presented to the client decision-maker.

Production must derive these views from the organisation's identity provider and active tenant/mandate context. The local role selector is demonstration scaffolding.

## Reading the four measures

- **Risk severity** is the assessed exposure. It does not represent evidence quality.
- **Evidence confidence** measures completeness, freshness and reliability of the supporting information.
- **Workflow status** shows where the governed case or decision currently sits.
- **Resilience outcome** is the calculated result after applying the relevant enterprise and scenario state.

These measures remain separate in storage, services and display. A low-confidence result must be described as uncertain; it is not converted into lower risk.

## Model 1 operating sequence

1. Resolve the current enterprise configuration.
2. Observe the live state without changing it.
3. Open a private Simulation Lab and test the proposed response.
4. Obtain the required business approval.
5. Escalate delayed or missing information through M25.
6. Review the observed outcome.
7. Publish the approved lesson through M26.

Model 1 remains usable without a consultant mandate or consultant service.

## Model 2 operating sequence

1. Confirm the consultant assignment and active client mandate.
2. Ingest only an authorised online source and preserve its lineage.
3. Record the consultant's qualified assessment of the detected change.
4. Run an isolated private simulation.
5. Present the recommendation and evidence to the client decision-maker.
6. Proceed only after the client's explicit decision.
7. Send any delegated action only to the separately governed sandbox execution adapter.
8. Validate the post-change outcome and publish the approved lesson.

Revocation, expiry or insufficient authority stops the workflow. The dashboard and Simulation Lab never send live actions.

## Evidence and audit

Every pilot step has a stable evidence reference. The recorded pilot pack contains the operating model, operator, ordered steps, readiness checks, timestamps, zero-live-action assertion and a SHA-256 evidence digest. Pilot records are append-only and tenant-bound.

