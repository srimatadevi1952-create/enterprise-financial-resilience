# M27 User Acceptance Testing Findings

Testing started on 29 September 2026.

**Remediation update — 30 September 2026:** The local correction build for UAT-01 through UAT-09 is complete and ready for a second guided walkthrough. See [M27_UAT_REMEDIATION_REPORT.md](M27_UAT_REMEDIATION_REPORT.md) for delivered behaviour, verification and the production connection gates that remain outside local UAT.

## UAT-01 — Parameter deck exposes only an aggregate control

**Screen:** Simulation Lab → Capital Parameter Deck

**Observed:** The deck reports 28 Capital variables but displays only the first 10. The single percentage slider changes the aggregate Capital control level and does not identify or edit an individual variable.

**Assessment:** Confirmed functional and UX gap. A qualified user cannot see which source variables produced the aggregate level or manipulate the 28 variables independently.

**Required correction:**

- display all 28 Capital variables through a searchable, internally scrollable or paginated variable list;
- give every manipulable variable its own current value, simulation value, unit, permitted range and reset control;
- distinguish state variables, shocks, behaviours and interventions;
- calculate the aggregate Capital control level from the variable values using an explicit versioned rule;
- show which variables changed and their contribution to the aggregate result;
- keep the Live Monitor values read-only and all Simulation Lab edits private;
- apply the same pattern to all six control groups.

**Priority:** High

**Status:** Open

## UAT-09 — Scenario cues and playback controls are static artwork

**Screen:** Main console → Scenario Cues and timeline controls

**Observed:** `Base`, `Adverse`, `Severe` and `Recovery`, together with the stop, play and pause symbols, appear selectable but do not respond. The current orange Base indicator is part of the master artwork rather than application state.

**Assessment:** Confirmed functional and affordance defect. The controls communicate capabilities that have not yet been connected to scenario presets or timeline execution.

**Required correction:**

- make Base, Adverse, Severe and Recovery selectable scenario presets;
- define a versioned variable set, assumptions and evidence for every preset;
- load presets only inside an authorised private Simulation Lab;
- show the selected preset as application state rather than fixed artwork;
- connect stop/reset, play/run and pause to the simulation timeline;
- display current period, progress, paused state and completion state;
- allow inspection of each period without changing the live business state;
- ensure the separate orange Run control and playback controls have clear, non-duplicative purposes;
- provide keyboard and screen-reader labels and do not rely on colour alone.

**Priority:** High

**Status:** Open

## UAT-08 — Simulation sharing dialog does not create a usable collaboration session

**Screen:** Simulation Lab → Share Private Simulation

**Observed:** `Present with Meet / Zoom` displays only a status message. `Copy Secure Session Link` copies a local URL that does not complete an authenticated join flow. `Invite Viewer-1` updates only the temporary in-memory session and does not notify or admit another person. There is no participant list, join screen or shared-session workspace.

**Assessment:** Confirmed functional gap. The screen represents the intended sharing model but is not yet an end-to-end collaboration facility.

**Required correction:**

- provide an authenticated participant invitation flow using the organisation's user directory;
- issue opaque, signed, purpose-bound invitation tokens with expiry, revocation and single-session scope;
- provide a join page that verifies identity and entitlement before opening the shared simulation;
- add participant presence, role, invitation state, expiry and revoke/remove controls;
- keep viewer access read-only and prevent access to other simulations or tenants;
- persist invitations and collaboration events in the audit store;
- integrate approved Google Meet and Zoom meeting creation or joining through their governed connectors;
- require the user to approve browser screen-sharing permissions at the point of presentation;
- show clear failure, expiry and revoked-access states instead of status-message-only responses.

**Priority:** High; mandatory before multi-user pilot

**Status:** Open

## UAT-07 — Assurance values are demonstration fixtures rather than live governed records

**Screen:** All three Operational Assurance views

**Observed:** Names, counts and measures such as `Example Payments Group`, severity 7, confidence 92/94 and resilience 87/82 are supplied by the local M27 demonstration view model.

**Assessment:** Confirmed integration gap. The visual workflow is testable, but the displayed values are not yet resolved dynamically from the M23 configuration, M24 change, M25 evidence and M26 case repositories.

**Required correction:**

- replace demonstration fixtures with tenant-scoped service queries;
- derive every card and count from governed M23 to M26 records;
- attach source evidence, owner, effective time and configuration version;
- refresh the console after authorised record changes without creating a live action path;
- retain explicit synthetic-data labelling for demonstration and training environments;
- add end-to-end tests proving that a governed record change appears only in the entitled tenant's view.

**Priority:** Critical before a live-data pilot

**Status:** Open

## UAT-03 — Workspace tabs can appear to bypass role authorization

**Screen:** Operational Assurance → Enterprise Model, Consultant Centre and Client Approval

**Observed:** The local demonstration permits the operator to move between all three role views by selecting a tab. The displayed identity changes with the selected view.

**Assessment:** Confirmed production-control gap. The tabs are useful for demonstrating the three experiences, but a production user must not acquire another role merely by changing a tab.

**Required correction:**

- bind identity, organisation, tenant, role and mandate to the authenticated session;
- show only views authorised for that identity;
- require step-up authorization for a permitted role or tenant change;
- preserve the previous live session while a private role-specific workspace is opened;
- record every successful and rejected view transition in the audit trail;
- label any demonstration-only role selector explicitly as a demonstration control.

**Priority:** Critical before production

**Status:** Open

## UAT-04 — Assurance summaries have no operational drill-down

**Screen:** All three Operational Assurance views

**Observed:** Counts and the `AVAILABLE PANELS` entries are displayed as text but cannot be opened. The user cannot inspect the overdue obligation, governed change, prior case, client assignment or supporting audit record.

**Assessment:** Confirmed functional gap. The summaries communicate status but do not yet support the operational work represented by M23 to M26.

**Required correction:**

- make summary counts and available-panel entries selectable;
- open draggable detail panels for configuration, obligations, changes, evidence, cases and audit history;
- carry source evidence, owner, configuration version, case identifier and timestamps into every detail panel;
- support return to the same dashboard state after closing a detail panel;
- retain read-only behaviour unless the user's specific workflow authority permits an action.

**Priority:** High

**Status:** Open

## UAT-05 — Client decision view lacks a complete approval package

**Screen:** Operational Assurance → Client Approval

**Observed:** The screen shows that a recommendation is awaiting decision, but it does not show the recommendation, available options, before-and-after simulated effect, requested authority or decision controls.

**Assessment:** Confirmed functional and governance gap. The client cannot make an informed, attributable approval or rejection from the current screen.

**Required correction:**

- show the consultant's recommendation, rationale, limitations and attestation;
- present alternative options and the simulated impact of each option;
- disclose evidence gaps and confidence basis;
- state the exact action, scope, duration and execution boundary for which authority is requested;
- provide Approve, Reject and Return for Clarification actions;
- require step-up authentication and segregation-of-duty checks before decision submission;
- show expiry, revocation and complete decision evidence.

**Priority:** High

**Status:** Open

## UAT-06 — Measure scope and time context are ambiguous

**Screen:** All three Operational Assurance views

**Observed:** Enterprise shows severity 7, confidence 92% and resilience 87, while Consultant and Client show severity 7, confidence 94% and resilience 82. No scale, as-of time, case reference or scope explains the differences.

**Assessment:** Confirmed interpretation risk. The values may legitimately represent enterprise-wide live state and a client-specific proposed-change case, but the screen does not establish that distinction.

**Required correction:**

- label every measure with its scope: enterprise, client, process, case or scenario;
- show scale and direction, including whether a higher value is better or worse;
- show effective time, data timestamp and configuration version;
- display the scenario, change or recommendation identifier when applicable;
- explain material differences between the live baseline and simulated or proposed state;
- use the same case values in Consultant and Client views when both refer to the same decision package.

**Priority:** High

**Status:** Open

## UAT-02 — Enterprise Core severity mask is misregistered

**Screen:** Simulation Lab → completed scenario

**Observed:** The core changes to the correct severity colour after a scenario run, but the colour mask does not align with the Enterprise Core artwork. The dark rim remains exposed unevenly and the colour extends too far near the lower edge.

**Assessment:** Confirmed visual defect. The implementation uses an approximate circular mask centred at design coordinate `(941, 460)` with radius `134`. The master artwork's core is centred higher and its visible boundary is slightly elliptical, so the approximation cannot align on every edge.

**Required correction:**

- replace the approximate circle with an artwork-calibrated elliptical clipping path;
- align the mask to the actual core centre and horizontal and vertical radii;
- preserve the original core texture, lettering and intended dark boundary;
- apply one uniform severity colour to the complete core state;
- verify pale-yellow, amber and deep-orange states at the master design size and scaled window sizes;
- keep the original monochrome core with no mask under stable conditions.

**Priority:** High

**Status:** Open
