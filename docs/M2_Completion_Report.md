# M2 Completion Report

M2 completed on 20 September 2026.

The isolated V2 workspace now has the first deterministic experiment fixture and branch foundation. It creates four materialized branches:

- Baseline
- Stressed
- Intervention
- Control

Each branch contains exactly 200 transactions and 200 settlement obligations, with one payment obligation and one settlement schedule per transaction. Amounts are 10,000 INR minor units per transaction, two merchants, and a fixed UTC virtual time of 20 September 2026. Stable UUIDv5 business identifiers and fixed fixture inputs make normalized business outcomes repeatable.

The stressed branch holds exactly 20 M01 obligations (`M01-001` through `M01-020`) and records 20 scenario effects. Intervention and control branches fork from the same stressed source state and preserve those 20 holds. Every child transaction and obligation has an explicit lineage mapping to its source branch/checkpoint. The parent and child rows remain tenant- and run-scoped.

The M2 migration is revision `m2_0005` in both isolated databases. It adds lineage mappings, payment obligations, scheduled actions, scenario applications/effects, settlement executions, and settlement allocations. No recovered V1 source or database is used by the fixture.

Verification passed:

- 22 tests passed.
- Exact 200-transaction and 200-obligation counts per branch.
- Exact 20 held obligations per stressed/intervention/control branch.
- 20 scenario effects recorded for the stressed branch.
- 1,200 lineage mappings recorded across three child branches and two entity types.
- Tenant/run-scoped schema and prior isolation checks continue to pass.

M2 does not yet execute settlements, create independent observation feeds, reconcile expected versus observed evidence, or measure intervention recovery. Those are M3 and M4 responsibilities. The next milestone is M3: add deterministic settlement observations, feed manifests, reconciliation outcomes, quality states, and the first evidence-linked metrics.
