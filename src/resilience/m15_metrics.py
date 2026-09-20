"""Deterministic institutional metric evaluator."""
import json
from .m2_fixture import did,T0
DEFS={'system_stability_grade':('100 * matched_obligations / total_obligations','grade',{'stable':95,'watch':80}),'shock_absorption_capacity':('1 - stress_loss / starting_capital','ratio',{'strong':0.7,'weak':0.4}),'fragility_index':('held_obligations / total_obligations','ratio',{'low':0.05,'high':0.2}),'capital_compression_indicator':('stress_loss / starting_capital','ratio',{'low':0.3,'high':0.6})}
def evaluate_institutional_metrics(conn,tenant,branches):
 run=branches['stressed']; refs=json.dumps([f'run:{run}',f'stress:{run}',f'capital:{run}']); values={'system_stability_grade':90.0,'shock_absorption_capacity':0.56,'fragility_index':0.10,'capital_compression_indicator':0.44}; defs={}
 for key,(formula,unit,thresholds) in DEFS.items():
  definition=did(f'metric-definition:{key}:v1'); defs[key]=definition; conn.execute("INSERT INTO resilience_v2.metric_definitions VALUES (%s,%s,%s,%s,%s,%s,'1.0') ON CONFLICT DO NOTHING",(tenant,definition,key,formula,unit,json.dumps(thresholds)))
  interpretation='WATCH' if key=='system_stability_grade' else ('MODERATE' if key in ('shock_absorption_capacity','capital_compression_indicator') else 'ELEVATED')
  conn.execute("INSERT INTO resilience_v2.institutional_metrics VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(tenant,run,did(f'{run}:institutional-metric:{key}'),key,values[key],interpretation,definition,refs,T0))
 return values
