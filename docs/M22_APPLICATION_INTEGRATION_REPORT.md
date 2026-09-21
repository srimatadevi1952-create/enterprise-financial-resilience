# M22 Application Integration Report

**Status:** Working development integration completed  
**Visual foundation:** `m22-globe-concept-v1.9-operating-modes`

## Integrated application slice

The approved editorial console is now implemented as a working Canvas application inside the V2 Python application. The approved 1881 × 1073 artwork is the rendering master, so the full console scales as one coordinated surface without HTML reflow or page scrolling. It is served by `resilience.m22_web`, uses the M22 220-variable register, and delegates authorization, session isolation, scenario calculation and collaboration rules to the testable `resilience.m22_console` service. The earlier DOM implementation remains preserved as `dom-console-v2.html`.

The initial application supports:

- default, immutable **Live Monitor** mode;
- server-side entitlement and step-up checks before a Simulation Lab is created;
- a timestamped baseline hash for every private simulation;
- independent, per-session scenario state;
- all six control groups: Capital, Liquidity, Operations, Regulation, Merchants, and Countries & Corridors;
- draggable parameter decks populated from the authoritative variable register;
- linked Probability × Impact, single-colour enterprise core temperature, BowTie severity, capital trajectory and resilience output;
- return from Simulation Lab to the unchanged Live Monitor;
- owner-controlled Viewer, Co-analyst, Approver and Auditor invitations;
- explicit separation between Meet/Zoom screen presentation and authenticated console participation;
- local-only hosting on `127.0.0.1` under the explicit development profile.
- pixel-matched Canvas rendering with resolution-independent hit testing and high-density display support.
- keyboard access for Live Monitor (`L`), Simulation Lab (`S`), parameter decks (`1`–`6`), Run (`R`) and Close (`Escape`).

## Verification completed

- Simulation creation fails without the required scope or step-up clearance.
- A severe private scenario changed resilience from 87 to 29 and changed the linked visual state.
- Returning to Live Monitor restored the unchanged score of 87 and disabled the Run control.
- A collaborator invitation appeared only in the private session.
- A Viewer cannot edit a simulation; a Co-analyst can be granted edit scope by the owner.
- The application produced no browser errors during the verified flow.
- The Canvas exactly fits the viewport dimensions and introduces no horizontal or vertical document scrolling.
- The automated M22 service checks pass.

## Production adapters still required

The integration is a real application slice running against the V2 package, but it is intentionally development-bound. Before production use, replace these adapters:

1. Connect the identity boundary to the enterprise identity provider with MFA/step-up evidence and centrally administered entitlements.
2. Persist simulation sessions, invitations and audit evidence in the approved database namespace.
3. Replace the stable development live-state adapter with approved read-only enterprise feeds and freshness controls.
4. Route scenario execution through the selected production simulation orchestration layer and retained evidence store.
5. Integrate Meet/Zoom launch links only after organisational security and data-sharing controls are approved.
6. Add deployment security review, observability, recovery procedures and operational acceptance testing.

These items do not change the approved UX. They convert the development adapters behind the same authorization and isolation boundaries into production infrastructure.
