# Dual Operating Model Architecture

## Decision

The Enterprise Financial Resilience and Control Operating System supports two complementary operating models. The existing enterprise-operated application is preserved as built. A consultant-operated managed service is added as a separate layer over the same governed risk, simulation and intelligence engines.

The models must never be blended implicitly. Every session, case, simulation, recommendation, approval and implementation action identifies its operating model, client tenant, actor, authority and evidence lineage.

## Model 1: Enterprise-Operated System

The client enterprise operates the system for its own organisation.

- Authorised enterprise users monitor the live business state.
- Entitled users create private simulation branches without changing the live baseline.
- Internal analysts assess scenarios and recommend responses.
- Internal approvers govern changes under the enterprise's own authority structure.
- The enterprise implements approved actions through its existing operational processes.
- Executives, board members and auditors receive role-appropriate intelligence and evidence.

All M0 to M23 capabilities and the approved M22 console remain part of this model without replacement or loss.

## Model 2: Consultant-Operated Managed Service

An authorised risk consultant operates the system for one or more client enterprises from a consultant control centre.

- Client data is obtained online through explicitly authorised, tenant-specific connections.
- The system validates, reconciles and compares observations with the client's approved enterprise configuration and prior state.
- The consultant reviews detected changes, explains their risk significance and records professional judgement.
- The consultant creates private simulations, compares remedies and issues a recommendation.
- The client reviews and approves, rejects or returns the recommendation.
- Following approval, the client may implement it, work with the consultant, or delegate a defined implementation action to the consultant.
- The system monitors the observed result and compares it with the expected effect.

The consultant is the expert operator. Automated detection and analytics support professional judgement; they do not replace it.

## Shared Platform and Separate Experience

Both models use the same controlled platform services:

- enterprise configuration and process-risk-control model;
- live monitoring and data-quality controls;
- stress, regulatory, systemic, recovery and capital simulations;
- reconciliation, merchant risk, forensic intelligence and classification;
- board intelligence, comparative resilience and reporting;
- evidence, audit, retention and tenant isolation.

Each model has its own application experience:

| Area | Model 1: Enterprise-operated | Model 2: Consultant-operated |
|---|---|---|
| Entry point | Enterprise console | Consultant control centre |
| Primary scope | One enterprise | Assigned portfolio of client tenants |
| Live view | Enterprise's authorised operational view | Read-only client view under mandate |
| Simulation | Enterprise user's private branch | Consultant case workspace and private branch |
| Recommendation | Internal decision workflow | Consultant recommendation delivered to client portal |
| Approval | Enterprise approval chain | Client approval under recorded mandate |
| Implementation | Enterprise operational team | Client, assisted, or delegated execution |
| Oversight | Enterprise audit and board | Client audit plus consultant service oversight |

Tenant context is explicit and visually persistent. A consultant cannot combine client data, switch tenant context silently or expose one client's information in another client's case.

## Consultant-Led Workflow

### 1. Onboarding and mandate

The client approves the service scope, source systems, data categories, named consultant team, permitted purposes, retention period, geographic restrictions and authority limits. The mandate has effective and expiry dates and can be revoked.

### 2. Online data acquisition

The Data Acquisition Gateway obtains approved input through APIs, secure file transfer, bank and payment feeds, ERP or accounting connectors, document repositories, or a client-side agent for private systems. Connections are read-only by default.

Every observation records the client tenant, source, source record identity, extraction time, effective time, schema version, transformation history and quality result. Credentials remain in a managed secret store and are not copied to the consultant's workstation.

### 3. Reconciliation and change detection

Inputs are normalised into canonical records and reconciled against expected balances, prior observations and the M23 configuration. The system produces change facts and exceptions, including missing or stale evidence. It does not declare the business meaning of a change without the consultant's assessment.

### 4. Expert assessment

The consultant accepts, amends or dismisses a detected change; identifies affected processes, risks, controls, obligations and dependencies; records reasoning and confidence; and requests further evidence where required.

### 5. Simulation and recommendation

The consultant creates an isolated simulation branch, tests response options and records expected effects on capital, liquidity, operations, regulation, merchants and corridors. Resilience remains the calculated outcome. A recommendation includes assumptions, evidence, limitations, implementation steps, success measures and a rollback plan.

### 6. Client decision

The client portal presents the current state, detected change, consultant assessment, proposed response, alternatives, simulated effects and authority requested. An authorised client decision-maker approves, rejects or returns it. Segregation-of-duty rules prevent prohibited self-approval.

### 7. Implementation

The client selects one of three modes:

1. **Advisory:** the consultant recommends; the client implements.
2. **Assisted:** the consultant prepares the action; the client confirms or performs the final step.
3. **Delegated:** the consultant executes a specifically approved action from the consultant station within a current mandate.

The visualization and simulation layers cannot issue production actions. Delegated actions pass through a separate Execution Orchestrator with allowlisted operations, step-up authentication, approval verification, preflight checks, idempotency, live status, rollback controls and an emergency stop. The client can revoke authority at any time.

### 8. Validation and closure

The system re-collects the relevant observations, reconciles the actual result, compares it with the simulation and reports exceptions. The consultant records the conclusion, the client accepts the outcome, and an approved lesson may enter the case-intelligence repository.

## Consultant Control Centre

The consultant experience adds:

- a portfolio view containing only assigned client tenants;
- a work queue for detected changes, missing evidence, expiring mandates, pending decisions and implementation tasks;
- an explicit tenant switch with client identity and authority status fixed in the interface;
- a case workspace showing baseline, current observation and proposed state side by side;
- expert assessment, evidence request, simulation and recommendation tools;
- a client approval and mandate panel;
- a separate implementation console with stronger visual warnings and action-level controls;
- post-change validation and outcome reporting.

The existing M22 enterprise console remains the foundation for each client's risk state and simulation. The consultant control centre surrounds it with portfolio, case, mandate and service-delivery capabilities.

## Authority and Safety Rules

- Client data ownership and decision authority remain with the client.
- Consultant access is least-privilege, client-specific, time-bounded and revocable.
- Data extraction is limited to approved sources and purposes.
- Live monitoring, simulation, approval and execution are separate capabilities.
- A simulation can never alter the live state or initiate an action.
- A recommendation is not an approval.
- Delegated execution requires an active mandate, an approved change, an authorised operator and successful preflight checks.
- High-impact actions can require a second person and a final client confirmation.
- Every access, decision and action is attributable and auditable.
- Cross-client analytics use only approved, appropriately anonymised or aggregated data.

## M24 Boundary

M24 will build the consultant workbench and governed change lifecycle while preserving Model 1. It will include consultant assignments, online observation records, change detection, expert assessment, simulation-linked recommendations, client decisions, mandates and controlled execution packages. Execution will first be proven against a sandbox adapter. Production connectors remain disabled until a named pilot connector, client mandate and operational control set are approved and validated in M27.

