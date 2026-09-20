from uuid import uuid4
import psycopg
import pytest
from resilience.config import load_profile
from resilience.m2_fixture import build_fixture
from resilience.m3_evidence import build_evidence


@pytest.mark.integration
def test_m3_evidence_is_complete_and_evidence_linked():
    p = load_profile("test")
    tenant, actor, experiment = uuid4(), uuid4(), uuid4()
    with psycopg.connect(**p.connection_kwargs(migration=True)) as admin:
        admin.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'m3-test','ACTIVE')", (tenant,))
        admin.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'m3-test-actor')", (tenant, actor)); admin.commit()
    with psycopg.connect(**p.connection_kwargs()) as conn:
        with conn.transaction():
            branches = build_fixture(conn, tenant, experiment, actor)
            result = build_evidence(conn, tenant, branches)
        assert result['baseline']['observations'] == 200 and result['baseline']['held'] == 0
        assert result['stressed']['observations'] == 180 and result['stressed']['held'] == 20
        assert result['intervention']['completion_pct'] == 90
        assert conn.execute("SELECT count(*) FROM resilience_v2.feed_manifests WHERE tenant_id=%s", (tenant,)).fetchone()[0] == 4
        assert conn.execute("SELECT count(*) FROM resilience_v2.reconciliation_outcomes WHERE tenant_id=%s AND outcome='HELD'", (tenant,)).fetchone()[0] == 60
        assert conn.execute("SELECT count(*) FROM resilience_v2.metric_observations WHERE tenant_id=%s", (tenant,)).fetchone()[0] == 8
        assert conn.execute("SELECT count(*) FROM resilience_v2.reconciliation_outcomes WHERE tenant_id=%s AND evidence_ref LIKE 'feed:%%'", (tenant,)).fetchone()[0] == 800
