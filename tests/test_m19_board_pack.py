from uuid import uuid4
import psycopg,pytest
from resilience.config import load_profile
from resilience.m2_fixture import build_fixture
from resilience.m19_board_pack import generate_board_pack
@pytest.mark.integration
def test_m19_generates_repeatable_board_pack():
 p=load_profile('test');tenant,actor,experiment=uuid4(),uuid4(),uuid4()
 with psycopg.connect(**p.connection_kwargs(migration=True)) as a:
  a.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'m19-test','ACTIVE')",(tenant,));a.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'m19-actor')",(tenant,actor));a.commit()
 with psycopg.connect(**p.connection_kwargs()) as c:
  with c.transaction(): b=build_fixture(c,tenant,experiment,actor);r=generate_board_pack(c,tenant,b)
  assert r=={'pack_id':r['pack_id'],'sections':4,'actions':3,'status':'REVIEW'}
  assert c.execute("SELECT count(*) FROM resilience_v2.board_pack_sections WHERE tenant_id=%s AND severity='HIGH'",(tenant,)).fetchone()[0]==2
  assert c.execute("SELECT count(*) FROM resilience_v2.board_pack_actions WHERE tenant_id=%s",(tenant,)).fetchone()[0]==3
