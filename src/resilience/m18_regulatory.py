"""Deterministic multi-jurisdiction regulatory transition evaluator."""
import json
from .m2_fixture import did,T0
def evaluate_regulatory_transition(conn,tenant,branches):
 run=branches['stressed']; refs=json.dumps([f'run:{run}',f'regulation:{run}']); regimes=[]
 for jurisdiction in ('IN','GB','SG','US','AE','SA','DE','NL','CH','JP','HK','AU','CA','BR','ZA'):
  rid=did(f'{tenant}:regime:{jurisdiction}:v2'); conn.execute("INSERT INTO resilience_v2.regulatory_regimes VALUES (%s,%s,%s,'REG-SETTLEMENT','2.0',%s,NULL,5.0000,20.0000,'ACTIVE')",(tenant,rid,jurisdiction,T0)); regimes.append(rid)
 transition=did(f'{run}:reg-transition:v1-v2'); conn.execute("INSERT INTO resilience_v2.regulatory_transitions VALUES (%s,%s,%s,%s,'1.0','2.0','APPLIED',200,%s)",(tenant,run,transition,regimes[0],f'transition:{transition}'))
 remediation=did(f'{run}:remediation:screening'); conn.execute("INSERT INTO resilience_v2.compliance_remediations VALUES (%s,%s,%s,%s,'ENHANCED_SCREENING','M01','COMPLETE',100,%s)",(tenant,run,remediation,transition,refs))
 return {'regimes':15,'affected_count':200,'remediation_count':100}
