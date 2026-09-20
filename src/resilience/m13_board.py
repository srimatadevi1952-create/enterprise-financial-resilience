"""Deterministic Board Intelligence and shadow-run gate evaluator."""
import json
from .m2_fixture import did,T0
def build_board_readiness(conn,tenant,branches,actor):
 run=branches['intervention']; refs=json.dumps([f'run:{run}',f'classification:{run}',f'capital:{branches["stressed"]}',f'recovery:{run}'])
 conn.execute("INSERT INTO resilience_v2.board_briefings VALUES (%s,%s,%s,%s,'RECOVERY','Approve read-only production shadow run',100,95,%s,%s)",(tenant,run,did(f'{run}:board-briefing'),'Stress contained; intervention restores modeled completion',refs,T0))
 for key,boundary in [('identity_isolation','Read-only shadow tenant'),('feed_contracts','Observe feeds; no writes'),('intervention_controls','No live financial actions'),('audit_evidence','Retain evidence and decisions')]: conn.execute("INSERT INTO resilience_v2.shadow_run_gates VALUES (%s,%s,%s,'PASS',%s,%s,%s)",(tenant,did(f'{tenant}:shadow-gate:{key}'),key,boundary,refs,T0))
 action=did(f'{run}:executive-action:shadow'); conn.execute("INSERT INTO resilience_v2.executive_actions VALUES (%s,%s,%s,'AUTHORIZE_SHADOW_RUN','BOARD','PROPOSED','Validate live-shaped inputs without initiating financial actions',%s,%s)",(tenant,run,action,refs,T0))
 return {'briefing_id':did(f'{run}:board-briefing'),'gates':4,'action_id':action}
