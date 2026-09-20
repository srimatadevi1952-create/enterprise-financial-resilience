from uuid import uuid4
import psycopg,pytest
from resilience.config import load_profile
from resilience.m2_fixture import build_fixture
from resilience.m18_regulatory import evaluate_regulatory_transition
@pytest.mark.integration
def test_m18_models_versioned_regulatory_transition_and_remediation():
 p=load_profile('test');tenant,actor,experiment=uuid4(),uuid4(),uuid4()
 with psycopg.connect(**p.connection_kwargs(migration=True)) as a:
  a.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'m18-test','ACTIVE')",(tenant,));a.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'m18-actor')",(tenant,actor));a.commit()
 with psycopg.connect(**p.connection_kwargs()) as c:
  with c.transaction(): b=build_fixture(c,tenant,experiment,actor);r=evaluate_regulatory_transition(c,tenant,b)
  assert r=={'regimes':4,'affected_count':200,'remediation_count':100}
  assert c.execute("SELECT count(*) FROM resilience_v2.regulatory_regimes WHERE tenant_id=%s",(tenant,)).fetchone()[0]==4
  assert c.execute("SELECT status FROM resilience_v2.compliance_remediations WHERE tenant_id=%s",(tenant,)).fetchone()[0]=='COMPLETE'
