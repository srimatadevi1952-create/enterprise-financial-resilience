from uuid import uuid4
import psycopg,pytest
from resilience.config import load_profile
from resilience.m20_shadow import prepare_shadow_run
from resilience.m21_shadow_run import execute_shadow_run
@pytest.mark.integration
def test_m21_executes_read_only_shadow_run():
 p=load_profile('test');tenant=uuid4()
 with psycopg.connect(**p.connection_kwargs(migration=True)) as a: a.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'m21-test','ACTIVE')",(tenant,));a.commit()
 with psycopg.connect(**p.connection_kwargs()) as c:
  with c.transaction(): prepare_shadow_run(c,tenant);r=execute_shadow_run(c,tenant,{})
  assert r=={'execution_id':r['execution_id'],'observed':20,'reconciled':20,'live_actions':0,'result':'PASS'}
  assert c.execute("SELECT count(*) FROM resilience_v2.shadow_observations WHERE tenant_id=%s AND observation_state='RECONCILED'",(tenant,)).fetchone()[0]==20
  assert c.execute("SELECT live_actions FROM resilience_v2.shadow_run_executions WHERE tenant_id=%s",(tenant,)).fetchone()[0]==0
