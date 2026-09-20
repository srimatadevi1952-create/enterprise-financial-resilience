from uuid import uuid4
import psycopg
import pytest
from resilience.config import load_profile
from resilience.m2_fixture import build_fixture


@pytest.mark.integration
def test_m2_builds_deterministic_branches_and_twenty_holds():
    p = load_profile("test")
    tenant, actor, experiment = uuid4(), uuid4(), uuid4()
    with psycopg.connect(**p.connection_kwargs(migration=True)) as admin:
        admin.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'m2-test','ACTIVE')", (tenant,))
        admin.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'m2-test-actor')", (tenant,actor))
        admin.commit()
    with psycopg.connect(**p.connection_kwargs()) as conn:
        with conn.transaction():
            result = build_fixture(conn, tenant, experiment, actor)
        assert result['held'] == tuple(f'M01-{i:03d}' for i in range(1,21))
        for role, run in result.items():
            if role in ('held',): continue
            assert conn.execute("SELECT count(*) FROM resilience_v2.transactions WHERE tenant_id=%s AND run_id=%s", (tenant,run)).fetchone()[0] == 200
            assert conn.execute("SELECT count(*) FROM resilience_v2.settlement_obligations WHERE tenant_id=%s AND run_id=%s", (tenant,run)).fetchone()[0] == 200
            assert conn.execute("SELECT count(*) FROM resilience_v2.scheduled_actions WHERE tenant_id=%s AND run_id=%s AND state='HELD'", (tenant,run)).fetchone()[0] == (20 if role != 'baseline' else 0)
        assert conn.execute("SELECT count(*) FROM resilience_v2.scenario_effects WHERE tenant_id=%s AND run_id=%s", (tenant,result['stressed'])).fetchone()[0] == 20
        assert conn.execute("SELECT count(*) FROM resilience_v2.lineage_mappings WHERE tenant_id=%s", (tenant,)).fetchone()[0] == 1200
        assert conn.execute("SELECT count(*) FROM resilience_v2.transactions t JOIN resilience_v2.runs r ON r.tenant_id=t.tenant_id AND r.run_id=t.run_id WHERE t.tenant_id=%s AND r.parent_run_id IS NOT NULL AND t.run_id<>r.parent_run_id", (tenant,)).fetchone()[0] == 600
