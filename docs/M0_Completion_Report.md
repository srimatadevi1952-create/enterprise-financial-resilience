# M0 Completion Report

M0 completed on 20 September 2026.

The recovered working state was inventoried without changing it. A private archive contains 405 files, 29,398,555 source bytes, Git HEAD `d1c8763d242648b175c59c2e4faa35ee6b736c05`, and SHA-256 `c555d8e5189b801560c06eadafca65aa3a49a2fde0f3bcf5ec8ffcb424d7f340`. The archive is outside V2 source control because it includes private recovery evidence and credential-bearing files. The full inventory and hashes are in [M0 Recovery Manifest](M0_Recovery_Manifest.json).

The original recovered logical dump remains preserved, but it is not readable as a PostgreSQL custom archive: its first bytes are a UTF-16 encoding of `PGDMP`. A new read-only binary-safe export was created from `ledger-recovery-db`, with SHA-256 `119875c933e73b50f40b47429c79401400c34eadd4b968879a7a070b018a34c1`, and restored into a disposable network-isolated PostgreSQL target. All 53 user tables, 55,377 rows, row-content fingerprints, and column definitions matched. Details are in [M0 Backup Verification](M0_Backup_Verification.json) and [M0 Restore Comparison](M0_Restore_Comparison.json).

The isolated V2 target is a new PostgreSQL 15.19 container using a new volume, bound only to `127.0.0.1:56432`. It contains separate development and test databases, separate runtime and migration roles, and only the `m0_0001` identity/version migration. No simulation or recovered business data was copied into it.

The V2 Python 3.12.14 environment is installed under `outputs/resilience-v2/.venv`. Dependencies are pinned in `requirements.lock`, hashes and local wheels are recorded for offline recreation, and `pip check` passed. The guarded `doctor` command passed for both environments. The isolation suite passed 15 tests, including wrong-database rejection, environment-marker checks, separation of development and test roles, read-only runtime access, and schema modification rejection.

One warning from the first test run was corrected by registering the `integration` marker. The remaining test warning is a local pytest cache permission warning and does not affect test results: 15 tests pass. The recovered V1 database and source remain unchanged.

## M0 exit decision

M0 is complete. The next work is M1: implement the V2 domain and persistence contracts—tenant/run identity, typed money and time, obligations, observations, allocations, events, jobs, idempotency, checkpoints, and the first relational constraints. M1 will be implemented only in the new V2 workspace and databases.
