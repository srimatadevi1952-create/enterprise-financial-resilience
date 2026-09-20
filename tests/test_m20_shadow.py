from uuid import uuid4
import psycopg,pytest
from resilience.config import load_profile
from resilience.m20_shadow import prepare_shadow_run
@pytest.mark.integration
def test_m20_prepares_read_only_shadow_run_controls():
 p=load_profile('test');tenant=uuid4()
 with psycopg.connect(**p.connection_kwargs(migration=True)) as a: a.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'m20-test','ACTIVE')",(tenant,));a.commit()
 with psycopg.connect(**p.connection_kwargs()) as c:
  with c.transaction(): r=prepare_shadow_run(c,tenant)
  assert r['controls']==6 and r['status']=='READY'
  assert c.execute("SELECT live_action_policy FROM resilience_v2.shadow_run_plans WHERE tenant_id=%s",(tenant,)).fetchone()[0]=='PROHIBITED'
  assert c.execute("SELECT count(*) FROM resilience_v2.shadow_run_controls WHERE tenant_id=%s AND status='PASS'",(tenant,)).fetchone()[0]==6
  assert c.execute("SELECT status FROM resilience_v2.shadow_run_incidents WHERE tenant_id=%s",(tenant,)).fetchone()[0]=='TESTED'
