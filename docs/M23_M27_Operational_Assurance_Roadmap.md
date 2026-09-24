# M23 to M27 Operational Assurance Roadmap

This roadmap converts the practical recommendations in `Review and Suggestions.docx` into an implementation sequence. It extends the completed M0 to M21 engine foundation and the M22 operating console without weakening the separation between Live Monitor and the private Simulation Lab. The existing enterprise-operated system is preserved as Model 1. M24 onward also introduces Model 2, a consultant-operated managed service, as defined in [Dual Operating Model Architecture](DUAL_OPERATING_MODEL_ARCHITECTURE.md).

## Existing foundation

The current system already provides tenant isolation, scenario branches, evidence references, data-quality states, intervention approvals, decision records, feed-quality incidents, alert routing, shadow-run controls and an interactive console. Model 1 retains these capabilities for direct operation by an enterprise. Model 2 adds a separate consultant control centre, online client-data acquisition, expert assessment, client approval and tightly governed implementation support without altering the Model 1 experience.

## M23 Enterprise Configuration and Process Risk Model

Status: Complete on 24 September 2026. See [M23 Completion Report](M23_Completion_Report.md).

### Objective

Represent how each client enterprise actually operates so that risk analysis, monitoring and simulation use organisation-specific processes, responsibilities, controls and thresholds.

### Scope

- Enterprise profile covering legal entities, business units, products, jurisdictions, currencies, merchants, banks, gateways and corridors.
- Process and sub-process register with owners, dependencies, criticality and service expectations.
- Risk and control mapping for each process, including preventive, detective, corrective and recovery controls.
- Configurable limits, tolerances, reporting thresholds and escalation paths.
- Versioned configuration with effective dates, status and evidence references.
- Import templates and validation rules for controlled onboarding.

### Deliverables

- Tenant-scoped enterprise configuration schema and migration.
- Configuration service and validated import contract.
- Process-risk-control dependency model.
- Enterprise onboarding and configuration interface specification.
- A representative configured enterprise fixture with multiple business units and jurisdictions.

### Acceptance criteria

- Two enterprises can use different process structures, thresholds and control ownership without code changes or cross-tenant exposure.
- Every active configuration has an owner, version, effective date, approval status and evidence reference.
- Simulations resolve the configuration version that was effective at the scenario baseline time.
- Invalid, incomplete or conflicting configurations fail validation before activation.
- Existing M0 to M22 regression checks continue to pass.

## M24 Consultant Workbench, Change Governance and Impact Simulation

Status: Complete on 24 September 2026. See [M24 Completion Report](M24_Completion_Report.md).

### Objective

Preserve the enterprise-operated workflow while adding a consultant workbench that can receive authorised client observations, identify changes, apply expert judgement, simulate responses and submit governed recommendations to the client.

### Scope

- Explicit operating-model and client-tenant context for every case and session.
- Consultant assignment, service mandate, permitted purpose, authority scope and expiry.
- Read-only online source observations with lineage, quality results and reconciliation status.
- Detected-change facts compared with the approved M23 configuration and prior client state.
- Consultant assessment containing the original state, proposed state, reason, affected processes, professional rationale and supporting evidence.
- Impact assessment across capital, liquidity, operations, regulation, merchants and corridors.
- Private what-if simulation of the proposed change before approval.
- Segregated consultant, client reviewer, client approver, implementation and validation roles.
- Decision history, comments, conditions, implementation evidence and rollback plan.
- Advisory, assisted and delegated implementation modes.
- Controlled execution package proven through a sandbox adapter; no production connector is enabled in M24.
- Post-implementation comparison between expected and observed effects.

### Deliverables

- Consultant portfolio work queue and tenant-safe case workspace.
- Source-observation, change register and immutable change-event history.
- Expert assessment and recommendation record.
- Impact-analysis service connected to the M22 Simulation Lab.
- Client approval, mandate and role-entitlement model.
- Execution package, preflight and sandbox-orchestration contract.
- Change comparison and post-implementation review views.
- Audit export containing the proposal, evidence, approvals, simulation and outcome.

### Acceptance criteria

- Model 1 continues to operate without requiring a consultant or exposing consultant-only functions.
- A consultant sees and operates only the client tenants explicitly assigned under a current mandate.
- Every extracted observation is read-only and traceable to its authorised source, collection time and transformation history.
- A detected change requires recorded expert acceptance or dismissal before it becomes a recommendation.
- A user can trace an approved change from the original state through expert assessment, simulation, client approval, implementation evidence and final validation.
- No proposed or simulated change can alter Live Monitor data or initiate a financial action.
- Approval rules prevent self-approval where segregation of duties is required.
- Delegated execution is blocked without an active mandate, approved action scope and successful preflight; M24 execution affects only its sandbox adapter.
- Rejected, withdrawn and rolled-back changes remain preserved and searchable.
- The expected impact can be compared with the observed outcome using the same metrics and evidence lineage.

## M25 Online Client Information Obligations and Evidence Confidence

### Objective

Manage authorised online inputs and missing, delayed, incomplete or unreliable client information while showing how evidence quality affects each consultant and enterprise risk assessment.

### Scope

- Information-obligation register for documents, confirmations, filings and recurring data submissions.
- Connector and source register covering authorisation, purpose, scope, schedule, owner, credentials reference and revocation status.
- Responsible client contact, internal owner, due date, recurrence, jurisdiction and regulatory dependency.
- Request, receipt, validation, rejection, overdue and waiver states.
- Reminder and escalation policies with full communication-event history.
- Evidence completeness, freshness and reliability measures.
- Separate display of risk severity and assessment confidence.
- Rules for cases where an information delay is itself an operational or compliance risk.

### Deliverables

- Information-obligation and evidence-status schema.
- Reminder, escalation and service-level timer service.
- Evidence-confidence calculation with versioned rules.
- Missing-information impact service connected to classifications, alerts and board intelligence.
- Client, enterprise-user and consultant work queues plus dashboard indicators.

### Acceptance criteria

- Every required item and online source has an owner, authority basis, current state, evidence link and escalation history.
- Reminders and escalations are deterministic, configurable and protected from duplicate delivery.
- Risk severity and assessment confidence are stored and displayed as separate measures.
- Missing information reduces confidence only according to explicit rules; it raises risk severity only when a defined exposure or obligation is affected.
- Executive outputs disclose material evidence gaps and do not present low-confidence results as established facts.

## M26 Lessons Learned and Case Intelligence

### Objective

Convert completed cases, simulations, interventions and changes into governed institutional knowledge that can assist future decisions.

### Scope

- Structured case record covering context, issue, approach, decision, intervention, outcome, what worked, what failed and new learning.
- Links to relevant processes, risks, controls, scenarios, changes, evidence and jurisdictions.
- Review, approval, sensitivity, retention and publication states.
- Search and similarity matching using controlled metadata before any advanced semantic capability is introduced.
- User feedback on whether a suggested precedent was relevant and useful.
- Safeguards for confidential, personal, privileged and client-specific information.

### Deliverables

- Case and lesson repository with version history.
- Case-authoring and review workflow.
- Faceted search and related-case service.
- Contextual prior-case panel for the console and change workflow.
- Knowledge-quality and reuse measures.

### Acceptance criteria

- An authorised professional can record, review, approve and retrieve a lesson without exposing restricted client information.
- Each published lesson identifies its source case, reviewer, applicable context, limitations and evidence.
- The system can retrieve relevant prior cases using process, risk, jurisdiction, control and scenario attributes.
- Superseded or withdrawn lessons remain auditable and cannot be presented as current guidance.
- Suggested cases are advisory and never change a simulation or live decision automatically.

## M27 Dual-Model Operational Assurance Console and Controlled Pilot

### Objective

Integrate M23 to M26 into the approved M22 visual language and prove both the preserved enterprise-operated model and the consultant-operated service with controlled multi-role pilots.

### Scope

- Draggable panels for enterprise configuration, changes, information obligations and lessons learned.
- Consultant control centre with assigned-client portfolio, work queue, tenant switch and mandate status.
- Client portal for evidence requests, recommendations, decisions, authority and revocation.
- Live Monitor indicators for overdue obligations, open changes, evidence confidence and relevant alerts.
- Simulation Lab links from proposed changes and missing-information conditions.
- Role-specific views for enterprise user, consultant, client decision-maker, implementation operator, executive and auditor.
- End-to-end notifications, audit evidence and executive reporting.
- Accessibility, performance, security and cross-tenant isolation validation.

### Deliverables

- Integrated Model 1 Operational Assurance workspace in the M22 console.
- Integrated Model 2 consultant control centre and client approval portal.
- Enterprise-operated pilot fixture covering a process change, delayed evidence, escalation, simulation, approval, implementation review and captured lesson.
- Consultant-operated pilot fixture covering authorised online extraction, detected change, expert assessment, simulation, recommendation, client approval, sandbox delegated action, post-change validation and captured lesson.
- Operator guide, control catalogue and pilot evidence pack.
- Readiness report with defects, decisions and recommended production boundary.

### Acceptance criteria

- Model 1 remains usable as a complete standalone enterprise system.
- The consultant pilot completes the full service workflow without cross-client exposure or direct action from the visualization or simulation layers.
- Only the separately governed sandbox execution adapter can receive the pilot's delegated action.
- Each dashboard state traces to source evidence, configuration version and responsible owner.
- Authorisation and segregation-of-duty checks pass for every role transition.
- Users can distinguish exposure severity, evidence confidence, workflow status and calculated resilience outcome.
- The pilot meets agreed usability, accessibility, performance, retention and audit requirements.
- Business owners approve or reject progression using a complete evidence pack.

## Delivery order and dependencies

M23 comes first because both operating models require a reliable enterprise and process model. M24 preserves Model 1 and adds the consultant workbench, mandates and governed change lifecycle. M25 adds authorised online-source governance, client information obligations and confidence-aware risk results. M26 uses the structured context and completed workflow evidence from M23 to M25. M27 integrates the capabilities and validates each model separately and together.

## Cross-cutting controls

All five milestones must preserve:

- tenant isolation and least-privilege access;
- explicit operating-model, tenant, consultant assignment and client-mandate context;
- immutable baselines and versioned records;
- explicit actor, time, reason and evidence attribution;
- separation of risk severity, evidence confidence and resilience outcome;
- prohibition of financial actions from the visualization and simulation layers;
- data minimisation, retention, confidentiality and auditability;
- accessible operation without depending on colour alone;
- deterministic tests and replayable pilot evidence.

## Definition of completion

The operational assurance programme is complete when an enterprise can use Model 1 independently and an authorised consultant can use Model 2 to receive approved client inputs, assess a detected change, simulate and recommend a response, obtain client approval, support or perform an authorised action through the separate execution boundary, validate the result, capture the lesson and reproduce the complete decision trail without allowing the visualization or simulation layers to affect live financial operations.
