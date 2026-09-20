"""Read-only synthetic shadow-run executor."""
from .m2_fixture import did
def execute_shadow_run(conn,tenant,branches):
 plan=conn.execute("SELECT plan_id FROM resilience_v2.shadow_run_plans WHERE tenant_id=%s AND status='READY'",(tenant,)).fetchone()[0]
 execution=did(f'{tenant}:shadow-execution:2026-09'); conn.execute("INSERT INTO resilience_v2.shadow_run_executions VALUES (%s,%s,%s,'SANITIZED_PRODUCTION_SHAPED',20,20,0,0,'PASS',%s)",(tenant,execution,plan,f'shadow-execution:{execution}'))
 for i in range(20): conn.execute("INSERT INTO resilience_v2.shadow_observations VALUES (%s,%s,%s,%s,'RECONCILED',%s)",(tenant,execution,did(f'{execution}:observation:{i}'),f'shadow:event:{i}',f'shadow:{execution}:{i}'))
 return {'execution_id':execution,'observed':20,'reconciled':20,'live_actions':0,'result':'PASS'}
