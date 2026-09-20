from uuid import uuid4
import pytest
import psycopg
from resilience.config import load_profile


@pytest.mark.integration
def test_m1_schema_and_runtime_grants():
    p = load_profile("test")
    with psycopg.connect(**p.connection_kwargs()) as c:
        tables = {r[0] for r in c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='resilience_v2'").fetchall()}
        assert {"environment_identity", "alembic_version", "tenants", "runs", "transactions", "settlement_obligations", "run_events", "commands", "jobs"}.issubset(tables)
        assert c.execute("SELECT version_num FROM resilience_v2.alembic_version").fetchone()[0] == "m15_0018"
        assert c.execute("SELECT has_table_privilege(current_user,'resilience_v2.runs','SELECT')").fetchone()[0]


@pytest.mark.integration
def test_m1_runtime_cannot_create_tenant():
    p = load_profile("test")
    with psycopg.connect(**p.connection_kwargs()) as c:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            c.execute("INSERT INTO resilience_v2.tenants(tenant_id,name,state) VALUES (%s,'x','ACTIVE')", (uuid4(),))
        c.rollback()
