from uuid import uuid4
import psycopg,pytest
from resilience.config import load_profile
from resilience.m2_fixture import build_fixture
from resilience.m8_regulatory import apply_regulatory_shock
@pytest.mark.integration
def test_m8_regulatory_shock_records_reserve_and_screening_impacts():
 p=load_profile('test');tenant,actor,experiment=uuid4(),uuid4(),uuid4()
 with psycopg.connect(**p.connection_kwargs(migration=True)) as a:
  a.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'m8-test','ACTIVE')",(tenant,));a.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'m8-actor')",(tenant,actor));a.commit()
 with psycopg.connect(**p.connection_kwargs()) as c:
  with c.transaction(): b=build_fixture(c,tenant,experiment,actor);r=apply_regulatory_shock(c,tenant,b)
  assert r['impacts']==200 and r['review_required']==100 and r['reserve_minor']==100000
  assert c.execute("SELECT count(*) FROM resilience_v2.regulatory_impacts WHERE tenant_id=%s AND impact_state='REVIEW'",(tenant,)).fetchone()[0]==100
  assert c.execute("SELECT count(*) FROM resilience_v2.regulatory_shocks WHERE tenant_id=%s",(tenant,)).fetchone()[0]==1
