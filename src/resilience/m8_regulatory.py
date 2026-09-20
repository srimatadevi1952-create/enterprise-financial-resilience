"""Deterministic regulatory shock evaluator."""
import json
from .m2_fixture import did,T0
def apply_regulatory_shock(conn,tenant,branches):
 run=branches['stressed']; shock=did(f'{run}:regulatory:reserve-screening')
 conn.execute("INSERT INTO resilience_v2.regulatory_shocks VALUES (%s,%s,%s,'REG-RESERVE-2026','RESERVE_AND_SCREENING',%s,5.0000,20.0000,'ACTIVE')",(tenant,run,shock,T0))
 rows=conn.execute("SELECT obligation_id,business_key,net_minor FROM resilience_v2.settlement_obligations WHERE tenant_id=%s AND run_id=%s ORDER BY business_key LIMIT 200",(tenant,run)).fetchall()
 for oid,key,amount in rows:
  state='REVIEW' if key.startswith('M01-') else 'RESERVED'; reserve=round(amount*0.05); review=key.startswith('M01-')
  conn.execute("INSERT INTO resilience_v2.regulatory_impacts VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(tenant,run,did(f'{run}:reg-impact:{key}'),shock,oid,state,reserve,review,f'regulatory:{shock}:{key}'))
 refs=json.dumps([f'shock:{shock}',f'run:{run}'])
 for key,val,unit in [('reserve_requirement_minor',100000, 'INR_minor'),('review_required_count',100,'count'),('restricted_obligation_count',0,'count')]: conn.execute("INSERT INTO resilience_v2.regulatory_measures VALUES (%s,%s,%s,%s,%s,%s,%s)",(tenant,run,did(f'{run}:reg-measure:{key}'),key,val,unit,refs))
 return {'shock_id':shock,'impacts':len(rows),'review_required':100,'reserve_minor':100000}
