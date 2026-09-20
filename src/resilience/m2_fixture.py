"""Deterministic M2 fixture and materialized branch builder."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import UUID, uuid5
import json
import psycopg

UTC = timezone.utc
FIXTURE_NAMESPACE = UUID("e6c1c7f7-8797-4d2d-93d7-6b1b8f0c4d11")
T0 = datetime(2026, 9, 20, tzinfo=UTC)


def did(label: str) -> UUID:
    return uuid5(FIXTURE_NAMESPACE, label)


def digest(value) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _run(conn, tenant, experiment, run_id, role, parent, seed):
    conn.execute("INSERT INTO resilience_v2.runs(tenant_id,run_id,experiment_id,parent_tenant_id,parent_run_id,branch_role,status,seed,code_hash,model_hash,input_hash,virtual_time) VALUES (%s,%s,%s,%s,%s,%s,'READY',%s,'m2-fixture','m2-fixture','m2-input',%s)", (tenant,run_id,experiment,tenant,parent,role,seed,T0))


def _copy_branch(conn, tenant, experiment, source, child, role, hold_targets=()):
    _run(conn, tenant, experiment, child, role, source, int(child.int & 0x7fffffff))
    rows = conn.execute("SELECT transaction_id,business_key,merchant_key,amount_minor,currency,created_at FROM resilience_v2.transactions WHERE tenant_id=%s AND run_id=%s ORDER BY business_key", (tenant,source)).fetchall()
    for txn_id,business_key,merchant,amount,currency,created in rows:
        new_txn=did(f"{child}:txn:{business_key}")
        conn.execute("INSERT INTO resilience_v2.transactions VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (tenant,child,new_txn,business_key,merchant,amount,currency,created))
        conn.execute("INSERT INTO resilience_v2.lineage_mappings VALUES (%s,%s,%s,'TRANSACTION',%s,%s,%s,%s)", (tenant,child,new_txn,source,txn_id,did(f"{source}:checkpoint:0"),business_key))
        old_ob=conn.execute("SELECT obligation_id,business_key,gross_minor,fee_minor,tax_minor,net_minor,currency,due_at FROM resilience_v2.settlement_obligations WHERE tenant_id=%s AND transaction_id=%s", (tenant,txn_id)).fetchone()
        oid,obkey,gross,fee,tax,net,cur,due=old_ob; new_ob=did(f"{child}:ob:{obkey}")
        conn.execute("INSERT INTO resilience_v2.settlement_obligations VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (tenant,child,new_ob,obkey,new_txn,merchant,gross,fee,tax,net,cur,due))
        conn.execute("INSERT INTO resilience_v2.lineage_mappings VALUES (%s,%s,%s,'OBLIGATION',%s,%s,%s,%s)", (tenant,child,new_ob,source,oid,did(f"{source}:checkpoint:0"),obkey))
        payment=did(f"{child}:payment:{obkey}")
        conn.execute("INSERT INTO resilience_v2.payment_obligations VALUES (%s,%s,%s,%s,%s,%s,%s)", (tenant,child,payment,new_txn,net,cur,due))
        action=did(f"{child}:action:{obkey}"); state='HELD' if obkey in hold_targets else 'PENDING'
        conn.execute("INSERT INTO resilience_v2.scheduled_actions VALUES (%s,%s,%s,%s,'SETTLE',%s,10,%s)", (tenant,child,action,new_ob,due,state))
    target_digest=digest(sorted(hold_targets)); scenario=did(f"{child}:scenario")
    conn.execute("INSERT INTO resilience_v2.scenario_applications VALUES (%s,%s,%s,'SETTLEMENT_DELAY',%s,%s,%s)", (tenant,child,scenario,digest({'targets':list(hold_targets)}),target_digest,T0))
    for obkey in hold_targets:
        ob=conn.execute("SELECT obligation_id FROM resilience_v2.settlement_obligations WHERE tenant_id=%s AND run_id=%s AND business_key=%s", (tenant,child,obkey)).fetchone()[0]
        conn.execute("INSERT INTO resilience_v2.scenario_effects VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (tenant,child,did(f"{child}:effect:{obkey}"),scenario,ob,'PENDING','HELD',f"{child}:hold:{obkey}"))
    return scenario


def build_fixture(conn: psycopg.Connection, tenant: UUID, experiment: UUID, actor: UUID):
    """Build the four M2 branches; caller supplies a transaction connection."""
    baseline=did('run:baseline'); stressed=did('run:stressed'); intervention=did('run:intervention'); control=did('run:control')
    conn.execute("INSERT INTO resilience_v2.experiments(tenant_id,experiment_id,purpose) VALUES (%s,%s,'M2 deterministic settlement recovery') ON CONFLICT DO NOTHING", (tenant,experiment))
    _run(conn,tenant,experiment,baseline,'BASELINE',None,20260920)
    for merchant in ('M01','M02'):
        for i in range(1,101):
            key=f'{merchant}-{i:03d}'; txn=did(f'{baseline}:txn:{key}'); amount=10000
            conn.execute("INSERT INTO resilience_v2.transactions VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (tenant,baseline,txn,key,merchant,amount,'INR',T0))
            ob=did(f'{baseline}:ob:{key}'); due=T0+timedelta(days=1)
            conn.execute("INSERT INTO resilience_v2.settlement_obligations VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (tenant,baseline,ob,key,txn,merchant,amount,0,0,amount,'INR',due))
            pay=did(f'{baseline}:payment:{key}')
            conn.execute("INSERT INTO resilience_v2.payment_obligations VALUES (%s,%s,%s,%s,%s,%s,%s)", (tenant,baseline,pay,txn,amount,'INR',due))
            action=did(f'{baseline}:action:{key}')
            conn.execute("INSERT INTO resilience_v2.scheduled_actions VALUES (%s,%s,%s,%s,'SETTLE',%s,10,'PENDING')", (tenant,baseline,action,ob,due))
    hold=tuple(f'M01-{i:03d}' for i in range(1,21))
    for key in hold: pass
    _copy_branch(conn,tenant,experiment,baseline,stressed,'STRESS',hold)
    _copy_branch(conn,tenant,experiment,stressed,intervention,'INTERVENTION',hold)
    _copy_branch(conn,tenant,experiment,stressed,control,'CONTROL',hold)
    for run, parent in ((baseline,None),(stressed,baseline),(intervention,stressed),(control,stressed)):
        cp=did(f'{run}:checkpoint:0'); seq=0
        conn.execute("INSERT INTO resilience_v2.checkpoints VALUES (%s,%s,%s,%s,%s,%s,false)", (tenant,cp,run,T0,seq,digest({'run':str(run),'fixture':'m2'})))
        conn.execute("INSERT INTO resilience_v2.run_stages VALUES (%s,%s,'fixture',1,'SUCCEEDED','m2-input','m2-output')", (tenant,run))
    return {'baseline':baseline,'stressed':stressed,'intervention':intervention,'control':control,'held':hold}
