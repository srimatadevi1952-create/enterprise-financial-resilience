# M25 Completion Report

M25 completed on 25 September 2026.

## Outcome

The platform now governs authorised online data sources and recurring client information obligations for both operating models. It records what information is required, who is responsible, when it is due, where it came from, whether it is reliable and how any evidence gap affects confidence and risk.

Risk severity and evidence confidence remain separate measures. Missing or weak information lowers confidence under a versioned calculation rule. It raises risk severity only when the obligation is explicitly linked to a defined exposure and the information is overdue or rejected.

## Authorised Source Governance

Each source records:

- enterprise or consultant operating model;
- consultant assignment where applicable;
- source type and unique source key;
- approved purpose and data scope;
- collection schedule;
- owner and client authoriser;
- managed credential reference rather than a credential value;
- jurisdiction, effective period and approval evidence;
- current status and last successful collection time.

Consultant-operated sources must remain within the source, purpose, jurisdiction and time limits of the consultant assignment. Source authorisation and revocation require active client information authority. Revocation immediately blocks further ingestion.

The authorised-ingestion service links every M24 source observation to its M25 source registration. The source observation retains the source record key, schema version, payload hash, collection time, effective time, lineage reference, quality result and reconciliation result.

## Information Obligations

The obligation model supports documents, confirmations, filings and data submissions. Each versioned definition records:

- the applicable enterprise configuration;
- source and operating model;
- client contact and internal owner;
- first due date and optional recurrence;
- reminder and escalation timing;
- evidence freshness limit;
- jurisdiction and regulatory dependency;
- whether a delay affects a defined exposure;
- affected risk dimension and permitted risk increment; and
- policy evidence and effective date.

Each occurrence has its own state and evidence history. Supported states are requested, received, validated, rejected, overdue and waived. Successful validation of a recurring obligation creates the next occurrence deterministically.

Reminders and escalations use stable idempotency keys. Reprocessing the same timer window cannot create duplicate communication events.

Waivers require time-bound client authority, a reason and an evidence reference. A waiver remains visible in the append-only obligation history.

## Evidence Confidence

Versioned confidence rules assign explicit weights to:

- completeness;
- freshness; and
- reliability.

The weights must total 100 percent. Freshness is calculated from the evidence receipt time and the obligation's freshness limit. Each assessment stores the component scores, final confidence, risk severity before and after, whether a defined exposure was affected, evidence references and one of three fact states:

- **Established:** validated evidence meets the configured confidence threshold.
- **Qualified:** some evidence exists, but the result is below the established threshold or has not been validated.
- **Insufficient:** no usable evidence supports the assessment.

Executive summaries disclose qualified and insufficient assessments explicitly and identify material evidence gaps affecting defined exposures.

## Database Controls

Migration `m25_0032` adds:

- authorised data sources and source event history;
- source-to-observation lineage;
- versioned obligation definitions and recurring obligation occurrences;
- immutable receipts, obligation events and communication events;
- versioned confidence rules and immutable confidence assessments; and
- tenant, actor, configuration, assignment and evidence relationships.

Migration `m25_0033` adds database-enforced payload immutability and permitted state transitions for sources, definitions, obligations and confidence rules. It also verifies that an obligation's current receipt belongs to that same obligation.

Append-only receipts, events, communications, source links and confidence assessments cannot be updated or deleted by the runtime role.

## Work Queues and Executive Disclosure

M25 supplies:

- a tenant-scoped information queue for client contacts and internal owners;
- a consultant portfolio queue limited to active consultant assignments and authorised sources; and
- an executive evidence summary covering overdue, rejected and open obligations, low-confidence assessments, material exposure gaps and required disclosures.

The M27 visual integration can present these services without recalculating governance logic in the interface.

## Verification

- 53 tests passed.
- M25 unit and integration tests passed.
- The complete M0 to M24 regression suite passed.
- Development and test databases migrated to `m25_0033`.
- Enterprise-operated and consultant-operated sources were registered independently.
- Cross-tenant and revoked-source ingestion were rejected.
- Duplicate reminders and escalations were prevented.
- Recurring validation generated the next obligation occurrence.
- An overdue exposure-linked gap increased risk severity from 4 to 7 while confidence remained 0.
- An overdue non-exposure item left risk severity unchanged at 6 while confidence remained 0.
- Validated evidence restored an established confidence state without an automatic risk adjustment.
- Runtime modification of immutable receipt evidence was rejected.

## Production Boundary

M25 provides the governed source registry and ingestion contract. It stores only managed secret references and does not place client credentials in the application database or consultant workstation. Enabling a specific production API, bank feed, SFTP endpoint, ERP connection or client-side agent still requires the client's connector configuration, secret-store integration, network approval and pilot validation.

## Next Milestone

M26 will implement Lessons Learned and Case Intelligence. It will turn completed cases, changes, interventions and evidence into reviewed, searchable institutional knowledge while preserving client confidentiality and tenant isolation.
