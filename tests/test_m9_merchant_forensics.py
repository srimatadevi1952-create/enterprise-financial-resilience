from uuid import uuid4
import psycopg,pytest
from resilience.config import load_profile
from resilience.m2_fixture import build_fixture
from resilience.m9_merchant_forensics import evaluate_merchant_risk
@pytest.mark.integration
def test_m9_scores_merchant_exposure_and_forensic_cluster():
 p=load_profile('test');tenant,actor,experiment=uuid4(),uuid4(),uuid4()
 with psycopg.connect(**p.connection_kwargs(migration=True)) as a:
  a.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'m9-test','ACTIVE')",(tenant,));a.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'m9-actor')",(tenant,actor));a.commit()
 with psycopg.connect(**p.connection_kwargs()) as c:
  with c.transaction(): b=build_fixture(c,tenant,experiment,actor);r=evaluate_merchant_risk(c,tenant,b)
  assert r['total_exposure_minor']==2000000 and r['forensic_signals']==1
  assert c.execute("SELECT risk_band FROM resilience_v2.merchant_risk_scores WHERE tenant_id=%s AND merchant_key='M01'",(tenant,)).fetchone()[0]=='HIGH'
  assert c.execute("SELECT count(*) FROM resilience_v2.forensic_signals WHERE tenant_id=%s AND severity='HIGH'",(tenant,)).fetchone()[0]==1
