"""Deterministic capital regeneration evaluator."""
import json
from .m2_fixture import did
def evaluate_capital(conn,tenant,branches):
 run=branches['stressed']; sid=did(f'{run}:capital:regeneration')
 conn.execute("INSERT INTO resilience_v2.capital_scenarios VALUES (%s,%s,%s,'STRESS_RECOVERY',5000000,2200000,100000,6)",(tenant,run,sid))
 balances=[(0,2700000,0,54,'DEPLETED'),(1,3000000,300000,60,'STABILIZING'),(2,3500000,500000,70,'REGENERATING'),(3,4000000,500000,80,'REGENERATING'),(4,4500000,500000,90,'REGENERATING'),(5,5000000,500000,100,'RESTORED')]
 for period,balance,inflow,ratio,state in balances: conn.execute("INSERT INTO resilience_v2.capital_trajectories VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(tenant,run,did(f'{run}:capital-period:{period}'),sid,period,balance,inflow,ratio,state))
 refs=json.dumps([f'capital-scenario:{sid}',f'run:{run}'])
 for key,val,unit in [('capital_depletion_minor',2300000,'INR_minor'),('capital_restoration_months',6,'months'),('minimum_buffer_ratio_pct',54,'percent')]: conn.execute("INSERT INTO resilience_v2.capital_measures VALUES (%s,%s,%s,%s,%s,%s,%s)",(tenant,run,did(f'{run}:capital-measure:{key}'),key,val,unit,refs))
 return {'scenario_id':sid,'starting_capital_minor':5000000,'restored_month':5,'minimum_buffer_pct':54}
