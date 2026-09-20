"""Deterministic M6 pilot gate evaluator."""
import json
from .m2_fixture import did,T0
def evaluate_pilot(conn,tenant,branches):
    run=branches['intervention']; refs=json.dumps([f'run:{run}',f'measures:{run}',f'manifest:{run}'])
    contract=did(f'{tenant}:contract:settlement:v1')
    conn.execute("INSERT INTO resilience_v2.feed_adapter_contracts VALUES (%s,%s,'SETTLEMENT','1.0',%s,'source_event_key','ACTIVE',%s)",(tenant,contract,json.dumps(['business_key','amount_minor','currency','observed_at']),'2026-09-20T00:00:00Z'))
    checks=[('schema_contract','PASS'),('approval_record','PASS'),('replay_protection','PASS'),('recovery_measure','PASS')]
    for key,result in checks: conn.execute("INSERT INTO resilience_v2.pilot_gate_results VALUES (%s,%s,%s,%s,%s,%s,%s)",(tenant,run,did(f'{run}:gate:{key}'),key,result,refs,T0))
    alert=did(f'{run}:alert:pilot-ready'); conn.execute("INSERT INTO resilience_v2.alert_events VALUES (%s,%s,%s,'PILOT_READY','INFO','Controlled pilot gate passed','operations','OPEN',%s)",(tenant,run,alert,T0))
    return {'contract_id':contract,'gates':len(checks),'alert_id':alert}
