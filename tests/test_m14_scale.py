from uuid import uuid4
import psycopg,pytest
from resilience.config import load_profile
from resilience.m14_scale import run_scale_benchmark
@pytest.mark.integration
def test_m14_validates_production_shaped_scale_profile():
 p=load_profile('test');tenant=uuid4()
 with psycopg.connect(**p.connection_kwargs(migration=True)) as a: a.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'m14-test','ACTIVE')",(tenant,));a.commit()
 with psycopg.connect(**p.connection_kwargs()) as c:
  with c.transaction(): r=run_scale_benchmark(c,tenant)
  assert r['records']==10000 and r['throughput_per_sec']>0
  assert c.execute("SELECT status FROM resilience_v2.population_profiles WHERE tenant_id=%s",(tenant,)).fetchone()[0]=='VALIDATED'
  assert c.execute("SELECT result_state FROM resilience_v2.benchmark_runs WHERE tenant_id=%s",(tenant,)).fetchone()[0]=='PASS'
