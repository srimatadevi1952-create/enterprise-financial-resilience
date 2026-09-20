from uuid import uuid4
import psycopg,pytest
from resilience.config import load_profile
from resilience.m2_fixture import build_fixture
from resilience.m10_systemic import evaluate_systemic
@pytest.mark.integration
def test_m10_models_cascading_enterprise_failure():
 p=load_profile('test');tenant,actor,experiment=uuid4(),uuid4(),uuid4()
 with psycopg.connect(**p.connection_kwargs(migration=True)) as a:
  a.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'m10-test','ACTIVE')",(tenant,));a.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'m10-actor')",(tenant,actor));a.commit()
 with psycopg.connect(**p.connection_kwargs()) as c:
  with c.transaction(): b=build_fixture(c,tenant,experiment,actor);r=evaluate_systemic(c,tenant,b)
  assert r['nodes']==4 and r['capacity_state']=='EXCEEDED' and r['exposure_minor']==2200000
  assert c.execute("SELECT count(*) FROM resilience_v2.cascade_events WHERE tenant_id=%s",(tenant,)).fetchone()[0]==4
  assert c.execute("SELECT count(*) FROM resilience_v2.systemic_impacts WHERE tenant_id=%s AND capacity_state='EXCEEDED'",(tenant,)).fetchone()[0]==3
