from uuid import uuid4
import psycopg
import pytest
from resilience.config import load_profile
from resilience.m2_fixture import build_fixture
from resilience.m3_evidence import build_evidence
from resilience.m4_recovery import execute_intervention

@pytest.mark.integration
def test_m4_releases_holds_and_measures_recovery():
    p = load_profile('test'); tenant, actor, experiment = uuid4(), uuid4(), uuid4()
    with psycopg.connect(**p.connection_kwargs(migration=True)) as admin:
        admin.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'m4-test','ACTIVE')", (tenant,)); admin.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'m4-test-actor')", (tenant, actor)); admin.commit()
    with psycopg.connect(**p.connection_kwargs()) as conn:
        with conn.transaction():
            branches = build_fixture(conn, tenant, experiment, actor); build_evidence(conn, tenant, branches); result = execute_intervention(conn, tenant, branches, actor)
        assert result['released'] == 20
        assert conn.execute("SELECT count(*) FROM resilience_v2.scheduled_actions WHERE tenant_id=%s AND run_id=%s AND state='EXECUTED'", (tenant, branches['intervention'])).fetchone()[0] == 20
        assert conn.execute("SELECT count(*) FROM resilience_v2.settlement_executions WHERE tenant_id=%s AND run_id=%s", (tenant, branches['intervention'])).fetchone()[0] == 20
        assert conn.execute("SELECT count(*) FROM resilience_v2.reconciliation_outcomes WHERE tenant_id=%s AND run_id=%s AND outcome='MATCHED'", (tenant, branches['intervention'])).fetchone()[0] == 200
        assert conn.execute("SELECT measure_value FROM resilience_v2.recovery_measures WHERE tenant_id=%s AND run_id=%s AND measure_key='recovery_completion_pct'", (tenant, branches['intervention'])).fetchone()[0] == 100
