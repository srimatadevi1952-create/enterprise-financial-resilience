# Enterprise Financial Resilience V2

M0 foundation established 19 September 2026. This is an isolated new codebase; it does not import or run recovered V1 engines.

## Available now

- Python 3.12.14 virtual environment and pinned dependencies.
- PostgreSQL 15.19 container `efrco-v2-postgres-20260919`, bound only to `127.0.0.1:56432`, with persistent volume `efrco-v2-data-20260919`.
- Separate databases `efrco_v2_dev` and `efrco_v2_test`, with separate runtime and migration roles.
- M17 migration `m17_0020`; cash-flow observations, liquidity stress, funding capacity, and liquidity measures are available for isolated tests. No recovered V1 populations are imported.
- Guarded read-only `doctor` command and isolation tests.
- Runtime roles can read the identity/version tables but cannot alter, update or truncate them; test roles cannot connect to development.
- M0 completion evidence is in the parent [M0 Completion Report](../M0_Completion_Report.md).

M5 now records run manifests, intervention approvals, replay keys, decision records, and feed-quality incidents alongside the closed-loop recovery experiment.

## Check the environment

From this directory in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m resilience.cli doctor --profile development
.\.venv\Scripts\python.exe -m resilience.cli doctor --profile test
.\.venv\Scripts\python.exe -m pytest -q
```

The profile must be explicit. Credentials live in ignored `.local/profiles.json`; they are not committed. The command verifies database name, local endpoint, role, instance marker, environment and schema version before use. It fails closed on mismatches.

## Database lifecycle

```powershell
docker stop efrco-v2-postgres-20260919
docker start efrco-v2-postgres-20260919
```

The persistent volume survives stop/start. The container has an `unless-stopped` restart policy. Do not remove the volume as a routine cleanup step. These commands target only V2; the recovered `ledger-recovery-db` remains separate.

## Migrations

Migrations require the migration profile and check a separately provisioned database identity before changing schema:

```powershell
$env:EFR_PROFILE='test'
.\.venv\Scripts\python.exe -m alembic upgrade head
```

M0 created the environment identity; M1 adds the tenant-scoped domain foundation. Runtime credentials cannot migrate. M1 downgrades are deliberately disabled. Test and development migration roles are distinct; production is not configured.

## Recreate dependencies

Use the exact Python version in `.python-version`. Create a new virtual environment at the intended path rather than copying the existing environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-index --find-links .local\wheelhouse --require-hashes -r requirements-hashed.lock
.\.venv\Scripts\python.exe -m pip install --no-build-isolation --no-deps -e .
```

`requirements.lock` and `requirements-hashed.lock` pin all installed tools and transitive dependencies for this Windows/Python environment. `runtime-lock.json` pins the PostgreSQL image digest. The wheelhouse and local credentials are excluded from Git. A different OS/Python version requires a separately tested lock.

`scripts/provision_local.py` is a fresh-install helper. It refuses existing profiles, containers or volumes; it is not a repair/reset command. Re-provisioning a different target must be deliberate and must never point at V1.

## Preservation and scope

The project-level M0 report and manifests in the parent output directory record the V1 archive and restore verification. The full preservation archive, logical backups, and recovery logs remain outside this repository. Neither raw recovery data nor V1 credentials are copied into V2 Git history.

The original logical dump failed PostgreSQL validation because its bytes had been encoded as UTF-16. A separate binary-safe read-only export was successfully restored and compared with the recovered database. The old dump remains preserved as evidence.

## Reference documentation

Implementation choices were checked against the official [Psycopg installation guide](https://www.psycopg.org/psycopg3/docs/basic/install.html), [Python virtual environment guide](https://docs.python.org/3/library/venv.html), and [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html). Successful local compatibility and isolation tests, not the documentation alone, establish this M0 baseline.
