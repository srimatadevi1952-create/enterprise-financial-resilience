# M23 to M27 Operational Assurance Roadmap

This roadmap converts the practical recommendations in `Review and Suggestions.docx` into an implementation sequence. It extends the completed M0 to M21 engine foundation and the M22 operating console without weakening the separation between Live Monitor and the private Simulation Lab.

## Existing foundation

The current system already provides tenant isolation, scenario branches, evidence references, data-quality states, intervention approvals, decision records, feed-quality incidents, alert routing, shadow-run controls and an interactive console. The remaining work is to make these controls configurable for each enterprise and usable in everyday advisory and assurance work.

## M23 Enterprise Configuration and Process Risk Model

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

## M24 Change Governance and Impact Simulation

### Objective

Create a governed lifecycle for changes to enterprise processes, controls, configurations and operating assumptions.

### Scope

- Change request containing the original state, proposed state, reason, owner, affected processes and supporting evidence.
- Impact assessment across capital, liquidity, operations, regulation, merchants and corridors.
- Private what-if simulation of the proposed change before approval.
- Segregated request, review, approval, implementation and validation roles.
- Decision history, comments, conditions, implementation evidence and rollback plan.
- Post-implementation comparison between expected and observed effects.

### Deliverables

- Change register and immutable change-event history.
- Impact-analysis service connected to the M22 Simulation Lab.
- Approval workflow and role-entitlement model.
- Change comparison and post-implementation review views.
- Audit export containing the proposal, evidence, approvals, simulation and outcome.

### Acceptance criteria

- A user can trace an approved change from the original state through simulation, approval, implementation evidence and final validation.
- No proposed or simulated change can alter Live Monitor data or initiate a financial action.
- Approval rules prevent self-approval where segregation of duties is required.
- Rejected, withdrawn and rolled-back changes remain preserved and searchable.
- The expected impact can be compared with the observed outcome using the same metrics and evidence lineage.

## M25 Client Information Obligations and Evidence Confidence

### Objective

Manage missing, delayed, incomplete and unreliable client information while showing how evidence quality affects the reliability of each risk assessment.

### Scope

- Information-obligation register for documents, confirmations, filings and recurring data submissions.
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
- Client and adviser work queues plus dashboard indicators.

### Acceptance criteria

- Every required item has an owner, due date, current state, evidence link and escalation history.
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

## M27 Operational Assurance Console and Controlled Pilot

### Objective

Integrate M23 to M26 into the approved M22 visual language and prove the complete workflow with a controlled multi-role pilot.

### Scope

- Draggable panels for enterprise configuration, changes, information obligations and lessons learned.
- Live Monitor indicators for overdue obligations, open changes, evidence confidence and relevant alerts.
- Simulation Lab links from proposed changes and missing-information conditions.
- Role-specific views for client, adviser, analyst, approver, executive and auditor.
- End-to-end notifications, audit evidence and executive reporting.
- Accessibility, performance, security and cross-tenant isolation validation.

### Deliverables

- Integrated Operational Assurance workspace in the M22 console.
- End-to-end pilot fixture covering a process change, delayed evidence, escalation, simulation, approval, implementation review and captured lesson.
- Operator guide, control catalogue and pilot evidence pack.
- Readiness report with defects, decisions and recommended production boundary.

### Acceptance criteria

- The pilot completes the full workflow without changing the immutable live baseline or initiating a financial action.
- Each dashboard state traces to source evidence, configuration version and responsible owner.
- Authorisation and segregation-of-duty checks pass for every role transition.
- Users can distinguish exposure severity, evidence confidence, workflow status and calculated resilience outcome.
- The pilot meets agreed usability, accessibility, performance, retention and audit requirements.
- Business owners approve or reject progression using a complete evidence pack.

## Delivery order and dependencies

M23 comes first because all later workflows require a reliable enterprise and process model. M24 follows so proposed configuration and process changes are governed and can be simulated. M25 then adds client information obligations and confidence-aware risk results. M26 uses the structured context and completed workflow evidence from M23 to M25. M27 integrates the four capabilities and validates them together.

## Cross-cutting controls

All five milestones must preserve:

- tenant isolation and least-privilege access;
- immutable baselines and versioned records;
- explicit actor, time, reason and evidence attribution;
- separation of risk severity, evidence confidence and resilience outcome;
- prohibition of financial actions from the visualization and simulation layers;
- data minimisation, retention, confidentiality and auditability;
- accessible operation without depending on colour alone;
- deterministic tests and replayable pilot evidence.

## Definition of completion

The operational assurance programme is complete when an authorised team can configure an enterprise, identify an information gap, govern and simulate a proposed response, obtain approval, observe the result, capture the lesson and reproduce the complete decision trail without affecting live financial operations.
