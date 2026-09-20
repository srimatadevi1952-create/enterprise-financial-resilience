"""Deterministic systemic cascade evaluator."""
import json
from .m2_fixture import did
def evaluate_systemic(conn,tenant,branches):
 run=branches['stressed']; sid=did(f'{run}:systemic:collapse')
 conn.execute("INSERT INTO resilience_v2.systemic_scenarios VALUES (%s,%s,%s,'MULTI_CORRIDOR_CASCADE',4,50.0000,1500000,'CRITICAL')",(tenant,run,sid))
 nodes=[('MERCHANT','M01',1000000),('MERCHANT','M02',1000000),('CORRIDOR','IN-GB',100000),('CORRIDOR','IN-SG',100000)]
 for wave,(typ,key,exposure) in enumerate(nodes,1): conn.execute("INSERT INTO resilience_v2.cascade_events VALUES (%s,%s,%s,%s,%s,%s,%s,'ACTIVE',%s)",(tenant,run,did(f'{run}:cascade:{key}'),sid,typ,key,wave,exposure))
 refs=json.dumps([f'scenario:{sid}',f'run:{run}'])
 for key,val,unit,state in [('affected_node_count',4,'count','EXCEEDED'),('cascading_exposure_minor',2200000,'INR_minor','EXCEEDED'),('recovery_capacity_pct',45,'percent','EXCEEDED')]: conn.execute("INSERT INTO resilience_v2.systemic_impacts VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",(tenant,run,did(f'{run}:systemic-impact:{key}'),key,val,unit,state,refs))
 return {'scenario_id':sid,'nodes':4,'exposure_minor':2200000,'capacity_state':'EXCEEDED'}
