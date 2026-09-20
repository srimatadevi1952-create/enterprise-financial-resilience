"""Deterministic sandbox gateway adapter evaluator."""
from .m2_fixture import did
def exercise_sandbox_adapter(conn,tenant,branches):
 run=branches['baseline']; aid=did(f'{tenant}:adapter:psp-sandbox')
 conn.execute("INSERT INTO resilience_v2.gateway_adapters VALUES (%s,%s,'PSP_SANDBOX','PAYMENT_SERVICE_PROVIDER','1.0','SANDBOX','ACTIVE')",(tenant,aid))
 batch=did(f'{run}:batch:2026-09-20T00'); conn.execute("INSERT INTO resilience_v2.settlement_batches VALUES (%s,%s,%s,%s,'2026-09-20T00Z',20,1,'REPLAY_SAFE','MATCHED')",(tenant,run,batch,aid))
 rows=conn.execute("SELECT obligation_id,business_key FROM resilience_v2.settlement_obligations WHERE tenant_id=%s AND run_id=%s ORDER BY business_key LIMIT 20",(tenant,run)).fetchall()
 for i,(oid,key) in enumerate(rows): conn.execute("INSERT INTO resilience_v2.adapter_records VALUES (%s,%s,%s,%s,%s,'MAPPED',%s,%s)",(tenant,batch,did(f'{batch}:{key}'),f'psp:{key}',oid,'psp:2026-09-20:'+key,f'adapter:{aid}:{key}'))
 return {'adapter_id':aid,'batch_id':batch,'mapped_records':len(rows),'retry_count':1}
