from datetime import datetime, timezone
from uuid import uuid4

import psycopg
import pytest
from pydantic import ValidationError

from resilience.config import load_profile
from resilience.m23_enterprise import (
    activate_enterprise_configuration,
    example_enterprise_spec,
    register_enterprise_configuration,
)
from resilience.m24_consultant import (
    AssignmentSpec,
    ConsultantWorkflowError,
    consultant_work_queue,
    create_assignment,
    create_change_proposal,
    create_mandate,
    execute_sandbox_package,
    grant_client_decision_authority,
    open_consultant_case,
    preflight_sandbox_execution,
    prepare_sandbox_execution,
    record_client_decision,
    record_expert_assessment,
    record_source_observation,
    revoke_assignment,
    validate_implementation_outcome,
)


T0 = datetime(2026, 10, 2, 9, tzinfo=timezone.utc)
T1 = datetime(2027, 10, 1, tzinfo=timezone.utc)


def _assignment(actor_id, principal_id):
    return {
        "consultant_principal_id": principal_id,
        "consultant_actor_id": actor_id,
        "service_name": "Managed financial resilience service",
        "permitted_purposes": ["continuous-monitoring", "risk-assessment", "simulation"],
        "authority_scope": {"sources": ["payments-api"], "jurisdictions": ["IN", "GB"]},
        "effective_from": datetime(2026, 10, 1, tzinfo=timezone.utc),
        "expires_at": T1,
        "evidence_ref": "agreement:managed-service:v1",
    }


def test_m24_contracts_reject_naive_assignment_time():
    value = _assignment(uuid4(), uuid4())
    value["effective_from"] = datetime(2026, 10, 1)
    with pytest.raises(ValidationError, match="TIME_MUST_BE_TIMEZONE_AWARE"):
        AssignmentSpec.model_validate(value)


@pytest.mark.integration
def test_m24_dual_model_consultant_workflow_is_tenant_safe_and_sandbox_only():
    profile = load_profile("test")
    principal = uuid4()
    tenant_a, consultant_a, approver_a, owner_a = uuid4(), uuid4(), uuid4(), uuid4()
    tenant_b, consultant_b, approver_b, owner_b = uuid4(), uuid4(), uuid4(), uuid4()

    with psycopg.connect(**profile.connection_kwargs(migration=True)) as admin:
        for tenant, name, consultant, approver, owner in (
            (tenant_a, "M24 Payments Client", consultant_a, approver_a, owner_a),
            (tenant_b, "M24 Advisory Client", consultant_b, approver_b, owner_b),
        ):
            admin.execute("INSERT INTO resilience_v2.tenants VALUES (%s,%s,'ACTIVE')", (tenant, name))
            admin.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'Assigned risk consultant')", (tenant, consultant))
            admin.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'Client approver')", (tenant, approver))
            admin.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'Client authority owner')", (tenant, owner))
        admin.commit()

    with psycopg.connect(**profile.connection_kwargs()) as conn:
        with conn.transaction():
            config_a = register_enterprise_configuration(conn, tenant_a, example_enterprise_spec(consultant_a))
            activate_enterprise_configuration(conn, tenant_a, config_a["config_id"])
            config_b = register_enterprise_configuration(
                conn, tenant_b, example_enterprise_spec(consultant_b, variant="advisory")
            )
            activate_enterprise_configuration(conn, tenant_b, config_b["config_id"])

            assignment_a = create_assignment(conn, tenant_a, _assignment(consultant_a, principal), at=T0)
            assignment_b = create_assignment(conn, tenant_b, _assignment(consultant_b, principal), at=T0)
            for tenant, approver, owner in (
                (tenant_a, approver_a, owner_a),
                (tenant_b, approver_b, owner_b),
            ):
                grant_client_decision_authority(
                    conn,
                    tenant,
                    {
                        "actor_id": approver,
                        "granted_by": owner,
                        "authority_scope": {
                            "decisions": ["CHANGE_PROPOSAL_DECISION", "ISSUE_SERVICE_MANDATE"],
                            "implementation_modes": ["ADVISORY", "ASSISTED", "DELEGATED"],
                        },
                        "effective_from": datetime(2026, 10, 1, tzinfo=timezone.utc),
                        "expires_at": T1,
                        "evidence_ref": "client-authority-register:v1",
                    },
                    at=T0,
                )

            observation = record_source_observation(
                conn,
                tenant_a,
                {
                    "assignment_id": assignment_a["assignment_id"],
                    "source_key": "payments-api",
                    "source_record_key": "settlement-window:2026-10-02T09",
                    "observed_at": T0,
                    "effective_at": T0,
                    "schema_version": "payments-v1",
                    "payload": {"settlement_delay_minutes": 47, "failed_payments": 18},
                    "lineage_ref": "connector:payments-api:batch-001",
                    "quality_status": "VALID",
                    "reconciliation_status": "CHANGED",
                },
            )
            assert observation["read_only"] is True
            with pytest.raises(ConsultantWorkflowError, match="OBSERVATION_ALREADY_RECORDED"):
                record_source_observation(
                    conn,
                    tenant_a,
                    {
                        "assignment_id": assignment_a["assignment_id"],
                        "source_key": "payments-api",
                        "source_record_key": "settlement-window:2026-10-02T09",
                        "observed_at": T0,
                        "effective_at": T0,
                        "schema_version": "payments-v1",
                        "payload": {"settlement_delay_minutes": 47, "failed_payments": 18},
                        "lineage_ref": "connector:payments-api:batch-001-replay",
                        "quality_status": "VALID",
                        "reconciliation_status": "CHANGED",
                    },
                )

            with pytest.raises(ConsultantWorkflowError, match="CASE_OBSERVATION_SCOPE_INVALID"):
                open_consultant_case(
                    conn,
                    tenant_b,
                    {
                        "assignment_id": assignment_b["assignment_id"],
                        "config_id": config_b["config_id"],
                        "observation_ids": [observation["observation_id"]],
                        "title": "Cross-client observation attempt",
                        "change_summary": "Must fail tenant isolation",
                        "baseline_hash": "baseline-b",
                        "current_hash": "changed-b",
                        "severity": 7,
                        "confidence_pct": 90,
                        "opened_by": consultant_b,
                    },
                    at=T0,
                )

            case = open_consultant_case(
                conn,
                tenant_a,
                {
                    "assignment_id": assignment_a["assignment_id"],
                    "config_id": config_a["config_id"],
                    "observation_ids": [observation["observation_id"]],
                    "title": "Settlement delay change",
                    "change_summary": "Settlement delay increased from 4 to 47 minutes",
                    "baseline_hash": "baseline-4-minutes",
                    "current_hash": "current-47-minutes",
                    "severity": 7,
                    "confidence_pct": 94,
                    "opened_by": consultant_a,
                },
                at=T0,
            )
            assessment = record_expert_assessment(
                conn,
                tenant_a,
                {
                    "case_id": case["case_id"],
                    "assessed_by": consultant_a,
                    "disposition": "ACCEPTED",
                    "rationale": "The reconciled delay breaches the approved settlement service target.",
                    "affected_dimensions": ["LIQUIDITY", "OPERATIONS", "MERCHANTS"],
                    "evidence_refs": ["observation:batch-001", "control:settlement-sla"],
                },
                at=T0,
            )
            proposal = create_change_proposal(
                conn,
                tenant_a,
                {
                    "case_id": case["case_id"],
                    "assessment_id": assessment["assessment_id"],
                    "proposed_by": consultant_a,
                    "implementation_mode": "DELEGATED",
                    "target_dimensions": ["LIQUIDITY", "OPERATIONS", "MERCHANTS"],
                    "recommended_change": "Enable the approved alternate settlement route for the affected window.",
                    "expected_outcome": "Restore settlement delay below ten minutes without increasing failed payments.",
                    "simulation_ref": "simulation:m24:settlement-route:v1",
                    "rollback_plan": "Disable the alternate route and restore the original routing profile.",
                    "evidence_refs": ["simulation:m24:settlement-route:v1", "assessment:accepted"],
                },
                at=T0,
            )

            with pytest.raises(ConsultantWorkflowError, match="CLIENT_DECISION_MUST_BE_INDEPENDENT"):
                record_client_decision(
                    conn, tenant_a, proposal["proposal_id"], consultant_a,
                    "APPROVED", "approval:self-invalid", at=T0,
                )

            decision = record_client_decision(
                conn, tenant_a, proposal["proposal_id"], approver_a,
                "APPROVED", "approval:client:change-001", conditions="Sandbox proof required", at=T0,
            )
            assert decision["decision"] == "APPROVED"

            with pytest.raises(ConsultantWorkflowError, match="ACTIVE_DELEGATED_MANDATE_REQUIRED"):
                prepare_sandbox_execution(
                    conn, tenant_a, proposal["proposal_id"], consultant_a,
                    "SWITCH_SETTLEMENT_ROUTE", "gateway:alternate", {"enabled": True}, "change-001:v1", at=T0,
                )

            mandate = create_mandate(
                conn,
                tenant_a,
                {
                    "assignment_id": assignment_a["assignment_id"],
                    "authorized_by": approver_a,
                    "implementation_modes": ["ADVISORY", "ASSISTED", "DELEGATED"],
                    "action_scope": {"action_types": ["SWITCH_SETTLEMENT_ROUTE"], "targets": ["gateway:alternate"]},
                    "effective_from": datetime(2026, 10, 1, tzinfo=timezone.utc),
                    "expires_at": T1,
                    "evidence_ref": "mandate:client:managed-actions:v1",
                },
                at=T0,
            )
            with pytest.raises(ConsultantWorkflowError, match="ACTIVE_DELEGATED_MANDATE_REQUIRED"):
                prepare_sandbox_execution(
                    conn, tenant_a, proposal["proposal_id"], consultant_a,
                    "SWITCH_SETTLEMENT_ROUTE", "gateway:not-authorised", {"enabled": True},
                    "change-001:wrong-target", mandate_id=mandate["mandate_id"], at=T0,
                )
            package = prepare_sandbox_execution(
                conn, tenant_a, proposal["proposal_id"], consultant_a,
                "SWITCH_SETTLEMENT_ROUTE", "gateway:alternate", {"enabled": True}, "change-001:v1",
                mandate_id=mandate["mandate_id"], at=T0,
            )
            with pytest.raises(ConsultantWorkflowError, match="STEP_UP_AUTHENTICATION_REQUIRED"):
                preflight_sandbox_execution(
                    conn, tenant_a, package["package_id"], consultant_a, "preflight:not-verified",
                    step_up_verified=False, at=T0,
                )
            preflight = preflight_sandbox_execution(
                conn, tenant_a, package["package_id"], consultant_a, "preflight:sandbox:passed",
                step_up_verified=True, at=T0,
            )
            result = execute_sandbox_package(
                conn, tenant_a, package["package_id"], consultant_a, "result:sandbox:success", at=T0,
            )

            assert preflight["status"] == "PREFLIGHT_PASSED"
            assert result == {
                "package_id": package["package_id"],
                "status": "EXECUTED",
                "sandbox_only": True,
                "live_actions": 0,
            }
            queue = consultant_work_queue(conn, principal, at=T0)
            assert [item["client_name"] for item in queue] == ["M24 Advisory Client", "M24 Payments Client"]
            assert queue[1]["open_cases"] == 1
            review = validate_implementation_outcome(
                conn,
                tenant_a,
                proposal["proposal_id"],
                approver_a,
                "MATCHED",
                {"settlement_delay_minutes_max": 10, "failed_payments_max": 18},
                {"settlement_delay_minutes": 8, "failed_payments": 16},
                "The sandbox result met the approved success measures.",
                ("result:sandbox:success", "observation:post-change:001"),
                at=T0,
            )
            assert review["status"] == "VALIDATED"
            assert consultant_work_queue(conn, principal, at=T0)[1]["open_cases"] == 0
            assert conn.execute(
                "SELECT count(*) FROM resilience_v2.consultant_case_events WHERE tenant_id=%s AND case_id=%s",
                (tenant_a, case["case_id"]),
            ).fetchone()[0] == 8

        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute(
                "UPDATE resilience_v2.consultant_source_observations SET source_key='tampered' WHERE tenant_id=%s AND observation_id=%s",
                (tenant_a, observation["observation_id"]),
            )
        conn.rollback()

        with conn.transaction():
            revoked = revoke_assignment(conn, tenant_a, assignment_a["assignment_id"], at=T0)
            assert revoked["status"] == "REVOKED"
            with pytest.raises(ConsultantWorkflowError, match="ACTIVE_ASSIGNMENT_REQUIRED"):
                record_source_observation(
                    conn,
                    tenant_a,
                    {
                        "assignment_id": assignment_a["assignment_id"],
                        "source_key": "payments-api",
                        "source_record_key": "after-revocation",
                        "observed_at": T0,
                        "effective_at": T0,
                        "schema_version": "payments-v1",
                        "payload": {"value": 1},
                        "lineage_ref": "connector:revoked",
                        "quality_status": "VALID",
                        "reconciliation_status": "CHANGED",
                    },
                )
