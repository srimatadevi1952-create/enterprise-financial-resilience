from uuid import uuid4
import psycopg,pytest
from resilience.config import load_profile
from resilience.m2_fixture import build_fixture
from resilience.m7_cross_border import build_cross_border
@pytest.mark.integration
def test_m7_models_cross_border_corridors_and_fx():
 p=load_profile('test'); tenant,actor,experiment=uuid4(),uuid4(),uuid4()
 with psycopg.connect(**p.connection_kwargs(migration=True)) as a:
  a.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'m7-test','ACTIVE')",(tenant,));a.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'m7-actor')",(tenant,actor));a.commit()
 with psycopg.connect(**p.connection_kwargs()) as c:
  with c.transaction(): b=build_fixture(c,tenant,experiment,actor); r=build_cross_border(c,tenant,b)
  assert r['cross_border_count']==80 and r['corridors']==['IN-GB','IN-SG']
  assert c.execute("SELECT count(*) FROM resilience_v2.cross_border_obligations WHERE tenant_id=%s AND compliance_state='CLEARED'",(tenant,)).fetchone()[0]==80
  assert c.execute("SELECT count(*) FROM resilience_v2.corridor_scenarios WHERE tenant_id=%s",(tenant,)).fetchone()[0]==8
