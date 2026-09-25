from datetime import datetime, timedelta, timezone
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
from resilience.m24_consultant import create_assignment, grant_client_decision_authority
from resilience.m25_information import (
    ConfidenceRuleSpec,
    InformationGovernanceError,
    assess_evidence_confidence,
    consultant_information_queue,
    executive_evidence_summary,
    information_work_queue,
    ingest_authorized_observation,
    process_obligation_timers,
    receive_information,
    register_confidence_rule,
    register_data_source,
    register_information_obligation,
    revoke_data_source,
    validate_information,
    waive_information_obligation,
)


T0 = datetime(2026, 11, 1, 9, tzinfo=timezone.utc)
T1 = datetime(2027, 10, 1, tzinfo=timezone.utc)


def test_m25_confidence_weights_must_total_100():
    with pytest.raises(ValidationError, match="CONFIDENCE_WEIGHTS_MUST_TOTAL_100"):
        ConfidenceRuleSpec(
            rule_key="DEFAULT",
            version=1,
            completeness_weight_pct=40,
            freshness_weight_pct=40,
            reliability_weight_pct=40,
            established_threshold_pct=80,
            effective_from=T0,
            evidence_ref="policy:invalid",
        )


@pytest.mark.integration
def test_m25_governs_sources_obligations_confidence_and_risk_separately():
    profile = load_profile("test")
    tenant = uuid4()
    principal = uuid4()
    consultant, approver, authority_owner, contact, internal_owner = (
        uuid4(), uuid4(), uuid4(), uuid4(), uuid4()
    )
    with psycopg.connect(**profile.connection_kwargs(migration=True)) as admin:
        admin.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'M25 Information Client','ACTIVE')", (tenant,))
        for actor, name in (
            (consultant, "Risk consultant"),
            (approver, "Client information approver"),
            (authority_owner, "Client authority owner"),
            (contact, "Client information contact"),
            (internal_owner, "Information obligation owner"),
        ):
            admin.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,%s)", (tenant, actor, name))
        admin.commit()

    with psycopg.connect(**profile.connection_kwargs()) as conn:
        with conn.transaction():
            config = register_enterprise_configuration(conn, tenant, example_enterprise_spec(internal_owner))
            activate_enterprise_configuration(conn, tenant, config["config_id"])
            assignment = create_assignment(
                conn,
                tenant,
                {
                    "consultant_principal_id": principal,
                    "consultant_actor_id": consultant,
                    "service_name": "Managed information assurance",
                    "permitted_purposes": ["continuous-monitoring"],
                    "authority_scope": {"sources": ["payments-api"], "jurisdictions": ["IN"]},
                    "effective_from": datetime(2026, 10, 1, tzinfo=timezone.utc),
                    "expires_at": T1,
                    "evidence_ref": "agreement:m25:v1",
                },
                at=T0,
            )
            grant_client_decision_authority(
                conn,
                tenant,
                {
                    "actor_id": approver,
                    "granted_by": authority_owner,
                    "authority_scope": {
                        "decisions": ["AUTHORIZE_DATA_SOURCE", "WAIVE_INFORMATION_OBLIGATION"],
                        "implementation_modes": ["ADVISORY"],
                    },
                    "effective_from": datetime(2026, 10, 1, tzinfo=timezone.utc),
                    "expires_at": T1,
                    "evidence_ref": "authority:information-sources:v1",
                },
                at=T0,
            )
            consultant_source = register_data_source(
                conn,
                tenant,
                {
                    "assignment_id": assignment["assignment_id"],
                    "operating_model": "CONSULTANT",
                    "source_key": "payments-api",
                    "source_type": "API",
                    "purpose": "continuous-monitoring",
                    "data_scope": {"fields": ["settlement_delay", "failed_payments"]},
                    "collection_schedule": "hourly",
                    "owner_actor_id": consultant,
                    "authorized_by": approver,
                    "credential_ref": "vault:client/payments-api/read-only",
                    "jurisdiction": "IN",
                    "effective_from": T0,
                    "expires_at": T1,
                    "evidence_ref": "source-approval:payments-api:v1",
                },
                at=T0,
            )
            enterprise_source = register_data_source(
                conn,
                tenant,
                {
                    "operating_model": "ENTERPRISE",
                    "source_key": "finance-erp",
                    "source_type": "ERP",
                    "purpose": "financial-close-evidence",
                    "data_scope": {"fields": ["trial_balance"]},
                    "collection_schedule": "monthly",
                    "owner_actor_id": internal_owner,
                    "authorized_by": approver,
                    "credential_ref": "secret-ref:enterprise/finance-erp/read-only",
                    "jurisdiction": "IN",
                    "effective_from": T0,
                    "expires_at": T1,
                    "evidence_ref": "source-approval:finance-erp:v1",
                },
                at=T0,
            )
            observation = ingest_authorized_observation(
                conn,
                tenant,
                consultant_source["source_id"],
                "window:2026-11-01T09",
                {"settlement_delay": 38, "failed_payments": 12},
                observed_at=T0,
                effective_at=T0,
                schema_version="payments-v1",
                lineage_ref="api:payments:batch-001",
                quality_status="VALID",
                reconciliation_status="CHANGED",
            )
            assert observation["authorized"] is True

            rule = register_confidence_rule(
                conn,
                tenant,
                {
                    "rule_key": "DEFAULT-EVIDENCE",
                    "version": 1,
                    "completeness_weight_pct": 40,
                    "freshness_weight_pct": 30,
                    "reliability_weight_pct": 30,
                    "established_threshold_pct": 80,
                    "effective_from": T0,
                    "evidence_ref": "policy:evidence-confidence:v1",
                },
                at=T0,
            )
            exposed = register_information_obligation(
                conn,
                tenant,
                {
                    "config_id": config["config_id"],
                    "source_id": consultant_source["source_id"],
                    "obligation_key": "DAILY-SETTLEMENT-CONFIRMATION",
                    "version": 1,
                    "title": "Daily settlement confirmation",
                    "item_type": "CONFIRMATION",
                    "operating_model": "CONSULTANT",
                    "responsible_contact_actor_id": contact,
                    "internal_owner_actor_id": consultant,
                    "first_due_at": T0 + timedelta(days=1),
                    "recurrence_days": 30,
                    "reminder_lead_hours": 24,
                    "escalation_after_hours": 1,
                    "freshness_limit_hours": 48,
                    "jurisdiction": "IN",
                    "regulatory_dependency": True,
                    "exposure_linked": True,
                    "affected_dimension": "LIQUIDITY",
                    "risk_increment": 3,
                    "effective_from": T0,
                    "evidence_ref": "obligation-policy:settlement:v1",
                },
                at=T0,
            )
            non_exposed = register_information_obligation(
                conn,
                tenant,
                {
                    "config_id": config["config_id"],
                    "source_id": enterprise_source["source_id"],
                    "obligation_key": "MONTHLY-NARRATIVE",
                    "version": 1,
                    "title": "Monthly management narrative",
                    "item_type": "DOCUMENT",
                    "operating_model": "ENTERPRISE",
                    "responsible_contact_actor_id": contact,
                    "internal_owner_actor_id": internal_owner,
                    "first_due_at": T0 + timedelta(days=1),
                    "reminder_lead_hours": 24,
                    "escalation_after_hours": 1,
                    "freshness_limit_hours": 720,
                    "jurisdiction": "IN",
                    "regulatory_dependency": False,
                    "exposure_linked": False,
                    "risk_increment": 0,
                    "effective_from": T0,
                    "evidence_ref": "obligation-policy:narrative:v1",
                },
                at=T0,
            )

            first_timer = process_obligation_timers(conn, tenant, as_of=T0)
            repeated_timer = process_obligation_timers(conn, tenant, as_of=T0)
            assert first_timer == {"reminders": 2, "new_overdue": 0, "escalations": 0}
            assert repeated_timer == {"reminders": 0, "new_overdue": 0, "escalations": 0}

            late_time = T0 + timedelta(days=1, hours=2)
            overdue_timer = process_obligation_timers(conn, tenant, as_of=late_time)
            repeated_overdue = process_obligation_timers(conn, tenant, as_of=late_time)
            assert overdue_timer == {"reminders": 0, "new_overdue": 2, "escalations": 2}
            assert repeated_overdue == {"reminders": 0, "new_overdue": 0, "escalations": 0}

            missing = assess_evidence_confidence(
                conn, tenant, exposed["obligation_id"], rule["rule_id"], 4, as_of=late_time
            )
            unrelated = assess_evidence_confidence(
                conn, tenant, non_exposed["obligation_id"], rule["rule_id"], 6, as_of=late_time
            )
            assert missing["confidence_pct"] == 0
            assert missing["risk_severity"] == 7
            assert missing["exposure_affected"] is True
            assert unrelated["confidence_pct"] == 0
            assert unrelated["risk_severity"] == 6
            assert unrelated["exposure_affected"] is False
            summary_with_gap = executive_evidence_summary(conn, tenant)
            assert summary_with_gap["material_exposure_gaps"] == 1
            assert summary_with_gap["established_facts_only"] is False

            receipt = receive_information(
                conn,
                tenant,
                exposed["obligation_id"],
                contact,
                "evidence:settlement-confirmation:2026-11-02",
                {"confirmed": True, "amount_minor": 2500000},
                90,
                90,
                received_at=late_time + timedelta(hours=1),
            )
            validation = validate_information(
                conn,
                tenant,
                exposed["obligation_id"],
                internal_owner,
                "VALIDATED",
                "Settlement confirmation reconciled to the source observation.",
                at=late_time + timedelta(hours=1),
            )
            assert validation["next_obligation_id"] is not None
            established = assess_evidence_confidence(
                conn,
                tenant,
                exposed["obligation_id"],
                rule["rule_id"],
                4,
                as_of=late_time + timedelta(hours=2),
            )
            assert established["confidence_pct"] > 90
            assert established["risk_severity"] == 4
            assert established["facts_status"] == "ESTABLISHED"
            assert len(consultant_information_queue(conn, principal, as_of=late_time)) == 1
            assert information_work_queue(conn, tenant, contact)[0]["status"] == "OVERDUE"
            waiver = waive_information_obligation(
                conn,
                tenant,
                non_exposed["obligation_id"],
                approver,
                "Narrative deferred to the next reporting cycle.",
                "waiver:management-narrative:approved",
                at=late_time,
            )
            assert waiver["status"] == "WAIVED"
            assert conn.execute(
                "SELECT count(*) FROM resilience_v2.information_communications WHERE tenant_id=%s",
                (tenant,),
            ).fetchone()[0] == 4

            with pytest.raises(InformationGovernanceError, match="ACTIVE_SOURCE_REQUIRED"):
                ingest_authorized_observation(
                    conn,
                    uuid4(),
                    consultant_source["source_id"],
                    "cross-tenant",
                    {"value": 1},
                    observed_at=T0,
                    effective_at=T0,
                    schema_version="v1",
                    lineage_ref="invalid",
                    quality_status="VALID",
                    reconciliation_status="CHANGED",
                )

        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute(
                "UPDATE resilience_v2.information_receipts SET evidence_ref='tampered' WHERE tenant_id=%s AND receipt_id=%s",
                (tenant, receipt["receipt_id"]),
            )
        conn.rollback()

        with conn.transaction():
            revoked = revoke_data_source(
                conn, tenant, consultant_source["source_id"], approver, "Client revoked connector access", at=late_time
            )
            assert revoked["status"] == "REVOKED"
            with pytest.raises(InformationGovernanceError, match="ACTIVE_SOURCE_REQUIRED"):
                ingest_authorized_observation(
                    conn,
                    tenant,
                    consultant_source["source_id"],
                    "after-revocation",
                    {"value": 1},
                    observed_at=late_time,
                    effective_at=late_time,
                    schema_version="v1",
                    lineage_ref="revoked",
                    quality_status="VALID",
                    reconciliation_status="CHANGED",
                )
