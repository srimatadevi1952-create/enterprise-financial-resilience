from uuid import uuid4
import psycopg,pytest
from resilience.config import load_profile
from resilience.m2_fixture import build_fixture
from resilience.m3_evidence import build_evidence
from resilience.m4_recovery import execute_intervention
from resilience.m5_operations import record_operations
from resilience.m6_pilot import evaluate_pilot
@pytest.mark.integration
def test_m6_pilot_gate_and_alerts():
 p=load_profile('test'); tenant,actor,experiment=uuid4(),uuid4(),uuid4()
 with psycopg.connect(**p.connection_kwargs(migration=True)) as a:
  a.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'m6-test','ACTIVE')",(tenant,));a.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'m6-actor')",(tenant,actor));a.commit()
 with psycopg.connect(**p.connection_kwargs()) as c:
  with c.transaction():
   b=build_fixture(c,tenant,experiment,actor);build_evidence(c,tenant,b);execute_intervention(c,tenant,b,actor);record_operations(c,tenant,b,actor);r=evaluate_pilot(c,tenant,b)
  assert r['gates']==4
  assert c.execute("SELECT count(*) FROM resilience_v2.pilot_gate_results WHERE tenant_id=%s AND result='PASS'",(tenant,)).fetchone()[0]==4
  assert c.execute("SELECT state FROM resilience_v2.alert_events WHERE tenant_id=%s",(tenant,)).fetchone()[0]=='OPEN'
