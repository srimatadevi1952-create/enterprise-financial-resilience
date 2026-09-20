# M1 Completion Report

M1 foundation slice completed on 20 September 2026.

The isolated V2 workspace now contains pure domain contracts for exact INR minor-unit money, timezone-aware UTC clocks, run provenance, settlement obligations, and idempotent command envelopes. These models are immutable and reject negative money, naive timestamps, negative seeds, and negative net obligations.

The V2 database now runs through revision `m1_0004` in both `efrco_v2_dev` and `efrco_v2_test`. The schema includes tenant and actor identity, experiments, runs and parent lineage, stages, checkpoints, transactions, settlement obligations, append-only run events, commands, jobs, and audit events. Composite tenant/run keys and foreign keys prevent cross-scope references; monetary and lifecycle checks reject invalid rows.

Runtime roles can read and update operational domain tables needed by later services, but cannot modify tenant administration, environment identity, or migration metadata. Migration roles are separate. The guarded connection still uses read-only transactions for inspection commands and rejects the recovered database, the wrong V2 environment, privileged runtime roles, and schema-version mismatches.

Verification passed:

- 21 tests passed.
- Domain validation tests passed.
- Development and test environment checks passed.
- Tenant-scoped schema and privilege tests passed.
- Wrong-environment and wrong-database rejection tests passed.
- Runtime modification of identity and migration metadata was rejected.

No V1 code or recovered database contents were changed. M1 does not yet implement scenario generation, branching, settlement execution, reconciliation, metrics, or recovery. The next milestone is M2: deterministic 200-transaction generation, complete obligation chains, checkpoints, branch materialization, and the controlled 20-obligation delay.
