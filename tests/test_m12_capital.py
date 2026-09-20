from uuid import uuid4
import psycopg,pytest
from resilience.config import load_profile
from resilience.m2_fixture import build_fixture
from resilience.m12_capital import evaluate_capital
@pytest.mark.integration
def test_m12_models_capital_depletion_and_regeneration():
 p=load_profile('test');tenant,actor,experiment=uuid4(),uuid4(),uuid4()
 with psycopg.connect(**p.connection_kwargs(migration=True)) as a:
  a.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'m12-test','ACTIVE')",(tenant,));a.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'m12-actor')",(tenant,actor));a.commit()
 with psycopg.connect(**p.connection_kwargs()) as c:
  with c.transaction(): b=build_fixture(c,tenant,experiment,actor);r=evaluate_capital(c,tenant,b)
  assert r['starting_capital_minor']==5000000 and r['restored_month']==5 and r['minimum_buffer_pct']==54
  assert c.execute("SELECT count(*) FROM resilience_v2.capital_trajectories WHERE tenant_id=%s",(tenant,)).fetchone()[0]==6
  assert c.execute("SELECT count(*) FROM resilience_v2.capital_trajectories WHERE tenant_id=%s AND capital_state='RESTORED'",(tenant,)).fetchone()[0]==1
