from uuid import uuid4
import psycopg,pytest
from resilience.config import load_profile
from resilience.m2_fixture import build_fixture
from resilience.m17_liquidity import evaluate_liquidity
@pytest.mark.integration
def test_m17_models_cash_flows_and_liquidity_stress():
 p=load_profile('test');tenant,actor,experiment=uuid4(),uuid4(),uuid4()
 with psycopg.connect(**p.connection_kwargs(migration=True)) as a:
  a.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'m17-test','ACTIVE')",(tenant,));a.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'m17-actor')",(tenant,actor));a.commit()
 with psycopg.connect(**p.connection_kwargs()) as c:
  with c.transaction(): b=build_fixture(c,tenant,experiment,actor);r=evaluate_liquidity(c,tenant,b)
  assert r['minimum_liquidity_minor']==1850000 and r['shortfall_minor']==0
  assert c.execute("SELECT count(*) FROM resilience_v2.cash_flow_observations WHERE tenant_id=%s",(tenant,)).fetchone()[0]==5
  assert c.execute("SELECT liquidity_state FROM resilience_v2.liquidity_measures WHERE tenant_id=%s AND measure_key='minimum_liquidity_minor'",(tenant,)).fetchone()[0]=='TIGHT'
