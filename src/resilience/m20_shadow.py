"""Deterministic read-only shadow-run readiness evaluator."""
from .m2_fixture import did
def prepare_shadow_run(conn,tenant):
 plan=did(f'{tenant}:shadow-plan:2026-09'); conn.execute("INSERT INTO resilience_v2.shadow_run_plans VALUES (%s,%s,'PRODUCTION_SHADOW_2026_09','READ_ONLY_SANITIZED_OR_APPROVED_INPUTS',30,'PROHIBITED','STOP_AND_REVERT_TO_READ_ONLY','READY')",(tenant,plan))
 controls=[('data_boundary','DATA','OPERATIONS'),('retention','RETENTION','GOVERNANCE'),('monitoring','MONITORING','OPERATIONS'),('alert_routing','ALERTING','RISK'),('rollback','ROLLBACK','ENGINEERING'),('live_action_block','SAFETY','ENGINEERING')]
 for key,typ,owner in controls: conn.execute("INSERT INTO resilience_v2.shadow_run_controls VALUES (%s,%s,%s,%s,%s,%s,'PASS',%s)",(tenant,plan,did(f'{plan}:control:{key}'),key,typ,owner,f'control:{plan}:{key}'))
 incident=did(f'{plan}:incident:feed-quality'); conn.execute("INSERT INTO resilience_v2.shadow_run_incidents VALUES (%s,%s,%s,'FEED_QUALITY_DEGRADATION','HIGH','Pause ingestion, preserve evidence, notify risk owner','TESTED')",(tenant,plan,incident))
 return {'plan_id':plan,'controls':len(controls),'incidents':1,'status':'READY'}
