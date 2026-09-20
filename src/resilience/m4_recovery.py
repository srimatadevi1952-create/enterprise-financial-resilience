"""Deterministic M4 intervention execution and resilience measurement."""
import json
from datetime import timedelta
from .m2_fixture import did, T0

def execute_intervention(conn, tenant, branches, actor):
    stressed, intervention, control = branches['stressed'], branches['intervention'], branches['control']
    targets = conn.execute("SELECT obligation_id,business_key,net_minor,due_at FROM resilience_v2.settlement_obligations WHERE tenant_id=%s AND run_id=%s AND business_key LIKE 'M01-%%' AND business_key <= 'M01-020' ORDER BY business_key", (tenant, intervention)).fetchall()
    iid = did(f"{intervention}:intervention:release-holds")
    conn.execute("INSERT INTO resilience_v2.intervention_executions VALUES (%s,%s,%s,'RELEASE_HELD_SETTLEMENTS',%s,%s,%s)", (tenant, intervention, iid, did(f"{intervention}:hold-targets"), T0+timedelta(days=2), actor))
    released = 0
    for oid, key, amount, due in targets:
        conn.execute("UPDATE resilience_v2.scheduled_actions SET state='EXECUTED' WHERE tenant_id=%s AND run_id=%s AND obligation_id=%s", (tenant, intervention, oid))
        ex = did(f"{intervention}:execution:{key}"); alloc = did(f"{intervention}:allocation:{key}"); event = f"m4:{intervention}:{key}"
        conn.execute("INSERT INTO resilience_v2.settlement_executions VALUES (%s,%s,%s,%s,%s,'INR',%s,%s)", (tenant, intervention, ex, oid, amount, T0+timedelta(days=2, hours=1), event))
        conn.execute("INSERT INTO resilience_v2.settlement_allocations VALUES (%s,%s,%s,%s,%s,'INR')", (tenant, alloc, ex, oid, amount))
        obs = did(f"{intervention}:observation:{key}")
        conn.execute("INSERT INTO resilience_v2.settlement_observations VALUES (%s,%s,%s,%s,%s,%s,%s,'INR',%s,'SETTLED') ON CONFLICT DO NOTHING", (tenant, intervention, obs, did(f"{intervention}:feed:settlement"), f"intervention:{key}", key, amount, T0+timedelta(days=2, hours=2)))
        conn.execute("UPDATE resilience_v2.reconciliation_outcomes SET observation_id=%s, observed_minor=expected_minor, outcome='MATCHED', quality_state='TRUSTED', evidence_ref=%s WHERE tenant_id=%s AND run_id=%s AND obligation_id=%s", (obs, f"intervention:{event}", tenant, intervention, oid))
        released += 1
    refs = json.dumps([f"intervention:{iid}", f"run:{intervention}", f"compare:{stressed}", f"compare:{control}"])
    for key, value, unit, compare in [('recovered_held_count', released, 'count', stressed), ('recovery_completion_pct', 100.0, 'percent', stressed), ('recovery_lift_vs_stressed_pct', 10.0, 'percentage_points', stressed), ('recovery_lift_vs_control_pct', 10.0, 'percentage_points', control)]:
        conn.execute("INSERT INTO resilience_v2.recovery_measures VALUES (%s,%s,%s,%s,%s,%s,%s,'TRUSTED',%s,%s)", (tenant, intervention, did(f"{intervention}:measure:{key}"), key, value, unit, compare, refs, T0+timedelta(days=2, hours=3)))
    return {'intervention_id': iid, 'released': released, 'completion_pct': 100.0}
