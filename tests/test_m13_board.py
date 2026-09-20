from uuid import uuid4
import psycopg,pytest
from resilience.config import load_profile
from resilience.m2_fixture import build_fixture
from resilience.m13_board import build_board_readiness
@pytest.mark.integration
def test_m13_builds_board_briefing_and_shadow_gates():
 p=load_profile('test');tenant,actor,experiment=uuid4(),uuid4(),uuid4()
 with psycopg.connect(**p.connection_kwargs(migration=True)) as a:
  a.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'m13-test','ACTIVE')",(tenant,));a.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'m13-actor')",(tenant,actor));a.commit()
 with psycopg.connect(**p.connection_kwargs()) as c:
  with c.transaction(): b=build_fixture(c,tenant,experiment,actor);r=build_board_readiness(c,tenant,b,actor)
  assert r['gates']==4 and c.execute("SELECT condition_class FROM resilience_v2.board_briefings WHERE tenant_id=%s",(tenant,)).fetchone()[0]=='RECOVERY'
  assert c.execute("SELECT count(*) FROM resilience_v2.shadow_run_gates WHERE tenant_id=%s AND result='PASS'",(tenant,)).fetchone()[0]==4
  assert c.execute("SELECT status FROM resilience_v2.executive_actions WHERE tenant_id=%s",(tenant,)).fetchone()[0]=='PROPOSED'
