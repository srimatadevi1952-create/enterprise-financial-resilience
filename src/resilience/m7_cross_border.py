"""Deterministic M7 cross-border corridor fixture."""
from .m2_fixture import did,T0
def build_cross_border(conn,tenant,branches):
 rows=[]
 for role in ('baseline','stressed','intervention','control'):
  run=branches[role]
  obligations=conn.execute("SELECT obligation_id,business_key FROM resilience_v2.settlement_obligations WHERE tenant_id=%s AND run_id=%s AND business_key LIKE 'M02-%%' ORDER BY business_key LIMIT 20",(tenant,run)).fetchall()
  for i,(oid,key) in enumerate(obligations):
   corridor='IN-GB' if i%2==0 else 'IN-SG'; origin='IN'; dest='GB' if i%2==0 else 'SG'; settlement='GBP' if i%2==0 else 'SGD'; fx='0.00950000' if i%2==0 else '0.01680000'; local=10000; reporting=round(local*float(fx)); state='CLEARED'
   cb=did(f'{run}:cross-border:{key}')
   conn.execute("INSERT INTO resilience_v2.cross_border_obligations VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'INR',%s,%s,%s,%s,%s)",(tenant,run,cb,oid,corridor,origin,dest,settlement,local,reporting,fx,T0,state))
   rows.append(cb)
  for corridor in ('IN-GB','IN-SG'):
   conn.execute("INSERT INTO resilience_v2.corridor_scenarios VALUES (%s,%s,%s,%s,'CORRIDOR_DISRUPTION',-8.0000,24,15.0000,'MEDIUM')",(tenant,run,did(f'{run}:corridor-scenario:{corridor}'),corridor))
 return {'cross_border_count':len(rows),'corridors':['IN-GB','IN-SG']}
