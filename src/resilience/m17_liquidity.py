"""Deterministic liquidity stress evaluator."""
import json
from .m2_fixture import did
def evaluate_liquidity(conn,tenant,branches):
 run=branches['stressed']; sid=did(f'{run}:liquidity:stress')
 conn.execute("INSERT INTO resilience_v2.liquidity_scenarios VALUES (%s,%s,%s,'INFLOW_DELAY_AND_OUTFLOW_SURGE',3000000,-20.0000,15.0000,500000)",(tenant,run,sid))
 flows=[(0,500000,800000,-300000,2700000,'OPERATING'),(1,350000,900000,-550000,2150000,'OPERATING'),(2,400000,700000,-300000,1850000,'OPERATING'),(3,600000,500000,100000,1950000,'RECOVERY'),(4,700000,400000,300000,2250000,'RECOVERY')]
 for period,inf,out,net,balance,source in flows: conn.execute("INSERT INTO resilience_v2.cash_flow_observations VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(tenant,run,did(f'{run}:cash-flow:{period}'),period,inf,out,net,balance,source))
 refs=json.dumps([f'liquidity-scenario:{sid}',f'run:{run}'])
 for key,val,unit,state in [('minimum_liquidity_minor',1850000,'INR_minor','TIGHT'),('liquidity_shortfall_minor',0,'INR_minor','ADEQUATE'),('funding_capacity_used_pct',0,'percent','ADEQUATE')]: conn.execute("INSERT INTO resilience_v2.liquidity_measures VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",(tenant,run,did(f'{run}:liquidity-measure:{key}'),key,val,unit,state,refs))
 return {'scenario_id':sid,'minimum_liquidity_minor':1850000,'shortfall_minor':0}
