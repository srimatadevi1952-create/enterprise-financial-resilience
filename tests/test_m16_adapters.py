from uuid import uuid4
import psycopg,pytest
from resilience.config import load_profile
from resilience.m2_fixture import build_fixture
from resilience.m16_adapters import exercise_sandbox_adapter
@pytest.mark.integration
def test_m16_maps_sandbox_gateway_batch_to_obligations():
 p=load_profile('test');tenant,actor,experiment=uuid4(),uuid4(),uuid4()
 with psycopg.connect(**p.connection_kwargs(migration=True)) as a:
  a.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'m16-test','ACTIVE')",(tenant,));a.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'m16-actor')",(tenant,actor));a.commit()
 with psycopg.connect(**p.connection_kwargs()) as c:
  with c.transaction(): b=build_fixture(c,tenant,experiment,actor);r=exercise_sandbox_adapter(c,tenant,b)
  assert r['mapped_records']==20 and r['retry_count']==1
  assert c.execute("SELECT mode FROM resilience_v2.gateway_adapters WHERE tenant_id=%s",(tenant,)).fetchone()[0]=='SANDBOX'
  assert c.execute("SELECT count(*) FROM resilience_v2.adapter_records WHERE tenant_id=%s AND mapping_state='MAPPED'",(tenant,)).fetchone()[0]==20
