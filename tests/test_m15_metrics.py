from uuid import uuid4
import psycopg,pytest
from resilience.config import load_profile
from resilience.m2_fixture import build_fixture
from resilience.m15_metrics import evaluate_institutional_metrics
@pytest.mark.integration
def test_m15_records_named_institutional_metrics():
 p=load_profile('test');tenant,actor,experiment=uuid4(),uuid4(),uuid4()
 with psycopg.connect(**p.connection_kwargs(migration=True)) as a:
  a.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'m15-test','ACTIVE')",(tenant,));a.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'m15-actor')",(tenant,actor));a.commit()
 with psycopg.connect(**p.connection_kwargs()) as c:
  with c.transaction(): b=build_fixture(c,tenant,experiment,actor);v=evaluate_institutional_metrics(c,tenant,b)
  assert v['system_stability_grade']==90 and v['fragility_index']==0.1
  assert c.execute("SELECT count(*) FROM resilience_v2.metric_definitions WHERE tenant_id=%s",(tenant,)).fetchone()[0]==4
  assert c.execute("SELECT count(*) FROM resilience_v2.institutional_metrics WHERE tenant_id=%s",(tenant,)).fetchone()[0]==4
