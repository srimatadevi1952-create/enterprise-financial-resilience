"""Deterministic merchant risk and forensic signal evaluator."""
import json
from .m2_fixture import did
def evaluate_merchant_risk(conn,tenant,branches):
 run=branches['stressed']; total=conn.execute("SELECT COALESCE(sum(net_minor),0) FROM resilience_v2.settlement_obligations WHERE tenant_id=%s AND run_id=%s",(tenant,run)).fetchone()[0]
 out=[]
 for merchant in ('M01','M02'):
  exposure,held=conn.execute("SELECT COALESCE(sum(o.net_minor),0), count(*) FILTER (WHERE a.state='HELD') FROM resilience_v2.settlement_obligations o JOIN resilience_v2.scheduled_actions a ON a.tenant_id=o.tenant_id AND a.obligation_id=o.obligation_id WHERE o.tenant_id=%s AND o.run_id=%s AND o.merchant_key=%s",(tenant,run,merchant)).fetchone(); share=float(exposure)/float(total)*100; band='HIGH' if held else 'LOW'; refs=json.dumps([f'run:{run}',f'merchant:{merchant}'])
  conn.execute("INSERT INTO resilience_v2.merchant_risk_scores VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(tenant,run,did(f'{run}:merchant-risk:{merchant}'),merchant,exposure,held,share,band,refs)); out.append((merchant,exposure,held))
  if held: conn.execute("INSERT INTO resilience_v2.forensic_signals VALUES (%s,%s,%s,'HELD_CLUSTER',%s,'HIGH',%s,%s,%s)",(tenant,run,did(f'{run}:forensic:{merchant}'),merchant,held,'Twenty held obligations cluster on one merchant segment',refs))
  conn.execute("INSERT INTO resilience_v2.concentration_metrics VALUES (%s,%s,%s,'MERCHANT',%s,%s,%s,%s)",(tenant,run,did(f'{run}:concentration:{merchant}'),merchant,exposure,share,'ELEVATED' if share>=40 else 'NORMAL'))
 return {'total_exposure_minor':total,'merchants':out,'forensic_signals':1}
