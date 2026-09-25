# M27 Control Catalogue

| ID | Control | Enforcement | Evidence |
|---|---|---|---|
| M27-01 | Separate operating models | Enterprise, consultant and client view models require distinct scopes. | M27 authorisation test |
| M27-02 | Tenant and mandate context | Consultant output identifies active client and mandate; M23–M26 services retain tenant keys and authority checks. | Consultant pilot sequence |
| M27-03 | Read-only visualization boundary | Every assurance response declares `live_actions: 0`; the console exposes no execution endpoint. | Console bootstrap and pilot records |
| M27-04 | Sandbox-only delegated implementation | Consultant mandate is displayed as sandbox-only; M24 remains the only governed action-package boundary. | M24 controls and M27 consultant view |
| M27-05 | Measure separation | Severity, evidence confidence, workflow state and resilience are separate fields and visual cards. | View-model test and console inspection |
| M27-06 | Role-specific disclosure | Enterprise, consultant and client views require `assurance:*:view` scopes. | Denied-scope test |
| M27-07 | Complete pilot sequence | The data model rejects missing, reordered or failed required steps. | Pydantic validation test |
| M27-08 | Complete readiness review | All seven readiness categories must occur exactly once and pass. | Pilot validation test |
| M27-09 | Append-only pilot evidence | Database triggers reject updates and deletes; runtime grants also revoke both operations. | Direct-update rejection test |
| M27-10 | Zero production action | A database check constrains `live_actions` to zero and readiness reports production actions disabled. | Migration constraint and dual-model test |
| M27-11 | Evidence integrity | Each accepted pilot stores a digest over the ordered steps, readiness results and operating model. | Pilot evidence pack |
| M27-12 | Accessible operation | Keyboard entry, visible labels, textual states and non-colour measure labels are provided. | Accessibility readiness check |
| M27-13 | Movable workspace | The assurance title bar supports pointer drag and constrains the panel to the console boundary. | Console package test and visual inspection |
| M27-14 | Cross-tenant isolation | Pilot tables carry tenant keys and existing tenant-isolation controls; no portfolio response contains another client's records. | Tenant-isolation readiness check |
| M27-15 | Retention and audit | Pilot identity, actor, timestamps, ordered evidence and readiness records are retained as immutable audit material. | Schema and retention readiness check |

