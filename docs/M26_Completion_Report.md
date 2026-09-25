# M26 Completion Report

M26 completed on 25 September 2026.

## Outcome

The platform now converts completed enterprise cases, consultant cases, simulations and interventions into governed institutional knowledge. Each lesson records its source, context, issue, approach, decision, intervention, outcome, successes, failures, new learning, applicable context, limitations and supporting evidence.

Lessons are advisory precedents. Retrieving or displaying a lesson cannot alter a simulation, recommendation, enterprise configuration or live operating state.

## Versioned Lesson Repository

Each knowledge case records:

- tenant and operating model;
- unique case key;
- source type and source reference;
- exact M23 enterprise configuration;
- sensitivity classification;
- personal-data and privileged-information indicators;
- retention deadline; and
- originating author.

Lesson content is immutable. A correction or improvement creates a new numbered version. Publishing a new version automatically supersedes the previous published version while preserving the complete history.

Superseded and withdrawn versions remain available to authorised auditors but are excluded from search results, related-case suggestions and current console guidance.

## Review and Publication Workflow

The governed lifecycle is:

1. draft;
2. submit for review;
3. approve, return or reject through independent review;
4. publish under separate publication authority;
5. supersede through a reviewed replacement or withdraw with a reason.

Review, publication, audit and access-grant operations require separate, time-bound client authority. An author cannot perform the independent review of the author's own lesson.

Every transition produces an append-only case event. Review decisions and rationales are retained separately from the lesson content.

## Context and Evidence Links

Each version has controlled links to one or more of:

- enterprise processes;
- risks;
- controls;
- scenarios;
- changes;
- evidence; and
- jurisdictions.

Process, risk and control links are validated against the exact M23 configuration attached to the knowledge case. Every lesson requires an evidence link and at least one contextual link before it can be created.

Published output always identifies the source reference, reviewer, applicable context, limitations, evidence and current version.

## Search and Related Cases

M26 provides:

- faceted search by process, risk, control, scenario, change, evidence or jurisdiction;
- related-case suggestions ranked by the number of matching controlled metadata attributes;
- a retrieval service suitable for the M27 contextual prior-case panel; and
- an explicit `advisory_only` indicator in every retrieved lesson.

Matching is deterministic. M26 does not use semantic embeddings, generative summarisation or autonomous recommendations.

## Confidentiality and Access

Supported sensitivity levels are internal, confidential, restricted and privileged.

- Internal lessons remain tenant-bound and are available to tenant actors.
- Confidential, restricted and privileged lessons require authorship, review responsibility or an active case-specific access grant.
- Personal-data cases must be restricted or privileged.
- Privileged-information cases must use privileged sensitivity.
- Access grants are purpose-bound, time-limited, auditable and revocable.
- Every retrieval is recorded with actor, purpose and time.
- Retention expiry blocks ordinary retrieval and publication.
- Cross-tenant retrieval fails closed.

No client lesson is shared across clients in M26. Any future comparative knowledge service must use an independently approved anonymisation and aggregation process.

## Quality and Reuse Measures

Users can record whether a suggested precedent was relevant and useful. The quality service reports:

- current published lessons;
- superseded and withdrawn versions;
- retrieval volume;
- feedback volume;
- relevance percentage; and
- usefulness percentage.

Feedback is append-only and limited to one response per actor and lesson version.

## Database Controls

Migration `m26_0034` adds knowledge cases, lesson versions, controlled links, independent reviews, access grants, access events, feedback and case events.

Migration `m26_0035` enforces immutable lesson payloads, approved publication-state transitions, immutable reviewer attribution and controlled access-grant transitions. Runtime deletion is prohibited.

## Verification

- 55 tests passed.
- M26 unit and integration tests passed.
- The complete M0 to M25 regression suite passed.
- Development and test databases migrated to `m26_0035`.
- Independent review and publication authority were enforced.
- Unauthorised access to a restricted lesson was rejected.
- Granted access permitted retrieval and revocation removed it.
- Process, risk, control, scenario, jurisdiction and evidence searches returned current approved lessons.
- Related-case ranking used controlled metadata overlap.
- Publishing version 2 superseded version 1.
- Withdrawing version 2 removed it from current guidance while both versions remained auditable.
- Direct modification of immutable lesson content was rejected by the database.
- Cross-tenant retrieval was rejected.

## Next Milestone

M27 will integrate M23 to M26 into the approved M22 visual language and run controlled pilots for both the enterprise-operated and consultant-operated models.
