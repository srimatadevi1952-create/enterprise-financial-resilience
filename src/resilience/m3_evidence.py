"""Deterministic M3 settlement evidence and reconciliation builder."""
from datetime import timedelta
import json
from .m2_fixture import did, T0


def build_evidence(conn, tenant, branches):
    """Create feed, observation, reconciliation and metric facts for each branch."""
    summary = {}
    for role, run_id in branches.items():
        if role == "held":
            continue
        feed = did(f"{run_id}:feed:settlement")
        rows = conn.execute("SELECT obligation_id,business_key,net_minor,due_at FROM resilience_v2.settlement_obligations WHERE tenant_id=%s AND run_id=%s ORDER BY business_key", (tenant, run_id)).fetchall()
        held = {r[0] for r in conn.execute("SELECT obligation_id FROM resilience_v2.scheduled_actions WHERE tenant_id=%s AND run_id=%s AND state='HELD'", (tenant, run_id)).fetchall()}
        source_uri = f"fixture://m3/{role}"
        content_hash = f"m3-{role}"
        conn.execute("INSERT INTO resilience_v2.feed_manifests VALUES (%s,%s,%s,'SETTLEMENT',%s,%s,%s,%s)", (tenant,run_id,feed,source_uri,content_hash,len(rows),T0+timedelta(hours=2)))
        matched = held_count = missing = 0
        for oid, business_key, expected, due in rows:
            if oid in held:
                held_count += 1; outcome, observed = 'HELD', 0; quality = 'TRUSTED'; obs = None
            else:
                matched += 1; outcome, observed = 'MATCHED', expected; quality = 'TRUSTED'; obs = did(f"{run_id}:observation:{business_key}")
                conn.execute("INSERT INTO resilience_v2.settlement_observations VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'SETTLED')", (tenant,run_id,obs,feed,f"{role}:{business_key}",business_key,observed,'INR',due+timedelta(hours=1)))
            conn.execute("INSERT INTO resilience_v2.reconciliation_outcomes VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (tenant,run_id,did(f"{run_id}:recon:{business_key}"),oid,obs,expected,observed,outcome,quality,f"feed:{feed}:business_key:{business_key}"))
        total = len(rows); completion = (matched / total * 100) if total else 0
        refs = [f"feed:{feed}", f"run:{run_id}"]
        for key, value, unit in [('settlement_completion_pct', completion, 'percent'), ('held_obligation_count', held_count, 'count')]:
            conn.execute("INSERT INTO resilience_v2.metric_observations VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", (tenant,run_id,did(f"{run_id}:metric:{key}"),key,value,unit,'TRUSTED',json.dumps(refs),T0+timedelta(hours=3)))
        summary[role] = {'feed_id': feed, 'observations': matched, 'held': held_count, 'completion_pct': completion}
    return summary
