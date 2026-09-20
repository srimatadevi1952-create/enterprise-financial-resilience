from uuid import uuid4
import psycopg,pytest
from resilience.config import load_profile
from resilience.m2_fixture import build_fixture
from resilience.m11_classification import classify_and_compare
@pytest.mark.integration
def test_m11_classifies_enterprise_and_compares_scenarios():
 p=load_profile('test');tenant,actor,experiment=uuid4(),uuid4(),uuid4()
 with psycopg.connect(**p.connection_kwargs(migration=True)) as a:
  a.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'m11-test','ACTIVE')",(tenant,));a.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'m11-actor')",(tenant,actor));a.commit()
 with psycopg.connect(**p.connection_kwargs()) as c:
  with c.transaction(): b=build_fixture(c,tenant,experiment,actor);r=classify_and_compare(c,tenant,b,experiment)
  assert r['classifications']==4 and r['comparisons']==4 and r['intervention_class']=='RECOVERY'
  assert c.execute("SELECT condition_class FROM resilience_v2.enterprise_classifications WHERE tenant_id=%s AND run_id=%s",(tenant,b['stressed'])).fetchone()[0]=='STRESSED'
  assert c.execute("SELECT count(*) FROM resilience_v2.comparative_resilience_scores WHERE tenant_id=%s AND rank=1",(tenant,)).fetchone()[0]==2
