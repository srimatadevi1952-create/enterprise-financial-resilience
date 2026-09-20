"""Deterministic M5 governance and replay-safe operation helpers."""
import json
from hashlib import sha256
from datetime import timedelta
from .m2_fixture import did, T0

def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def record_operations(conn, tenant, branches, actor):
    intervention = branches['intervention']; stressed = branches['stressed']
    manifest = did(f'{intervention}:manifest')
    conn.execute("INSERT INTO resilience_v2.run_manifests VALUES (%s,%s,%s,%s,%s,'m5_0008',%s)", (tenant, intervention, manifest, digest({'run':str(intervention),'fixture':'m5'}), 'm5-code', T0))
    approval = did(f'{intervention}:approval')
    conn.execute("INSERT INTO resilience_v2.intervention_approvals VALUES (%s,%s,%s,'RELEASE_HELD_SETTLEMENTS',%s,%s,'APPROVED',%s,'Release approved for controlled recovery experiment')", (tenant, intervention, approval, actor, actor, T0+timedelta(hours=1)))
    replay = 'm5:intervention:release-held-settlements:v1'
    req = digest({'run':str(intervention),'approval':str(approval),'targets':20})
    conn.execute("INSERT INTO resilience_v2.replay_keys VALUES (%s,%s,%s,'INTERVENTION_EXECUTION',%s,%s,%s)", (tenant, intervention, replay, req, T0+timedelta(hours=1), digest({'released':20})))
    decision = did(f'{intervention}:decision')
    refs = json.dumps([f'approval:{approval}', f'replay:{replay}', f'run:{intervention}', f'compare:{stressed}'])
    conn.execute("INSERT INTO resilience_v2.decision_records VALUES (%s,%s,%s,'RECOVERY_GO','APPROVE_INTERVENTION',%s,%s,%s)", (tenant, intervention, decision, actor, refs, T0+timedelta(hours=1)))
    feed = conn.execute("SELECT feed_id FROM resilience_v2.feed_manifests WHERE tenant_id=%s AND run_id=%s", (tenant, stressed)).fetchone()[0]
    incident = did(f'{stressed}:feed-quality:late-arrival')
    conn.execute("INSERT INTO resilience_v2.feed_quality_incidents VALUES (%s,%s,%s,%s,'LOW','DEGRADED','Synthetic late-arrival marker retained for operational quality testing',%s)", (tenant, stressed, incident, feed, T0+timedelta(hours=4)))
    return {'manifest_id': manifest, 'approval_id': approval, 'replay_key': replay, 'decision_id': decision, 'incident_id': incident}
