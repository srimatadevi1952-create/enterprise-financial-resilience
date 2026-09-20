from uuid import uuid4
import psycopg
import pytest
from resilience.config import load_profile
from resilience.m2_fixture import build_fixture
from resilience.m3_evidence import build_evidence
from resilience.m4_recovery import execute_intervention
from resilience.m5_operations import record_operations

@pytest.mark.integration
def test_m5_records_governance_replay_and_quality_facts():
    p=load_profile('test'); tenant, actor, experiment=uuid4(),uuid4(),uuid4()
    with psycopg.connect(**p.connection_kwargs(migration=True)) as a:
        a.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'m5-test','ACTIVE')",(tenant,)); a.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'m5-actor')",(tenant,actor)); a.commit()
    with psycopg.connect(**p.connection_kwargs()) as c:
        with c.transaction():
            b=build_fixture(c,tenant,experiment,actor); build_evidence(c,tenant,b); execute_intervention(c,tenant,b,actor); r=record_operations(c,tenant,b,actor)
        assert c.execute("SELECT status FROM resilience_v2.intervention_approvals WHERE tenant_id=%s",(tenant,)).fetchone()[0]=='APPROVED'
        assert c.execute("SELECT count(*) FROM resilience_v2.replay_keys WHERE tenant_id=%s",(tenant,)).fetchone()[0]==1
        assert c.execute("SELECT count(*) FROM resilience_v2.decision_records WHERE tenant_id=%s",(tenant,)).fetchone()[0]==1
        assert c.execute("SELECT quality_state FROM resilience_v2.feed_quality_incidents WHERE tenant_id=%s",(tenant,)).fetchone()[0]=='DEGRADED'
        assert r['replay_key'].startswith('m5:')
