"""Deterministic enterprise classification and scenario comparison."""
import json
from .m2_fixture import did,T0
def classify_and_compare(conn,tenant,branches,experiment):
 refs=json.dumps([f'run:{branches["intervention"]}',f'run:{branches["stressed"]}',f'run:{branches["control"]}'])
 classes=[('baseline','RESILIENT',100,'normal-operations'),('stressed','STRESSED',90,'settlement-disruption'),('intervention','RECOVERY',100,'approved-intervention'),('control','STRESSED',90,'no-intervention')]
 for role,condition,score,driver in classes: conn.execute("INSERT INTO resilience_v2.enterprise_classifications VALUES (%s,%s,%s,%s,%s,95,%s,%s,%s)",(tenant,branches[role],did(f'{branches[role]}:classification'),condition,score,driver,refs,T0))
 ordered=[('baseline',100,100,0,1),('intervention',100,100,0,1),('stressed',90,45,-10,3),('control',90,45,-10,3)]
 for role,completion,recovery,delta,rank in ordered: conn.execute("INSERT INTO resilience_v2.comparative_resilience_scores VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(tenant,experiment,did(f'{experiment}:compare:{role}'),role,completion,recovery,delta,rank,refs))
 return {'classifications':4,'comparisons':4,'intervention_class':'RECOVERY'}
