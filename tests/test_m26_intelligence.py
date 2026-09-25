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
from resilience.m24_consultant import grant_client_decision_authority
from resilience.m26_intelligence import (
    CaseIntelligenceError,
    LessonCaseSpec,
    create_lesson_case,
    create_lesson_revision,
    grant_lesson_access,
    knowledge_quality_metrics,
    lesson_history,
    publish_lesson,
    record_lesson_feedback,
    related_lessons,
    retrieve_lesson,
    review_lesson,
    revoke_lesson_access,
    search_lessons,
    submit_lesson_for_review,
    withdraw_lesson,
)


T0 = datetime(2026, 12, 1, 9, tzinfo=timezone.utc)
T1 = datetime(2028, 12, 1, 9, tzinfo=timezone.utc)


def _content(title: str, *, learning: str = "Pre-authorise the alternate route before a disruption."):
    return {
        "title": title,
        "context": "A cross-border payment operation experienced a gateway interruption during settlement.",
        "issue": "Settlement delay exceeded the approved service target and created a liquidity exposure.",
        "approach": "The team reconciled the source evidence and simulated the approved alternate route.",
        "decision_summary": "Use the alternate route under the approved recovery conditions.",
        "intervention": "The alternate route was enabled in the controlled execution environment.",
        "outcome": "Settlement completion recovered without an increase in failed payments.",
        "what_worked": "Preflight checks and reconciliation prevented duplicate settlement instructions.",
        "what_failed": "The original route did not recover within its expected service window.",
        "new_learning": learning,
        "applicable_context": "Payment gateways with an approved alternate settlement route and equivalent controls.",
        "limitations": "The result is not established for corridors without equivalent banking and regulatory arrangements.",
        "evidence_refs": ["case-evidence:gateway-incident", "simulation:alternate-route:v1"],
        "links": [
            {"link_type": "PROCESS", "link_key": "PAYMENT"},
            {"link_type": "RISK", "link_key": "GATEWAY-OUTAGE"},
            {"link_type": "CONTROL", "link_key": "GATEWAY-FAILOVER"},
            {"link_type": "SCENARIO", "link_key": "PAYMENT-DISRUPTION"},
            {"link_type": "JURISDICTION", "link_key": "IN"},
            {"link_type": "EVIDENCE", "link_key": "case-evidence:gateway-incident"},
        ],
    }


def test_m26_requires_protected_sensitivity_for_personal_data():
    value = {
        **_content("Invalid sensitivity"),
        "case_key": "INVALID",
        "source_type": "ENTERPRISE_CASE",
        "source_ref": "enterprise-case:invalid",
        "config_id": uuid4(),
        "operating_model": "ENTERPRISE",
        "sensitivity": "INTERNAL",
        "contains_personal_data": True,
        "retention_until": T1,
        "author_actor_id": uuid4(),
    }
    with pytest.raises(ValidationError, match="PERSONAL_DATA_SENSITIVITY_REQUIRED"):
        LessonCaseSpec.model_validate(value)


@pytest.mark.integration
def test_m26_reviews_searches_supersedes_and_protects_case_intelligence():
    profile = load_profile("test")
    tenant = uuid4()
    author, reviewer, publisher, viewer, authority_owner = uuid4(), uuid4(), uuid4(), uuid4(), uuid4()
    with psycopg.connect(**profile.connection_kwargs(migration=True)) as admin:
        admin.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'M26 Knowledge Client','ACTIVE')", (tenant,))
        for actor, name in (
            (author, "Lesson author"),
            (reviewer, "Independent reviewer"),
            (publisher, "Knowledge publisher"),
            (viewer, "Operations viewer"),
            (authority_owner, "Knowledge authority owner"),
        ):
            admin.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,%s)", (tenant, actor, name))
        admin.commit()

    with psycopg.connect(**profile.connection_kwargs()) as conn:
        with conn.transaction():
            config = register_enterprise_configuration(conn, tenant, example_enterprise_spec(author))
            activate_enterprise_configuration(conn, tenant, config["config_id"])
            grant_client_decision_authority(
                conn,
                tenant,
                {
                    "actor_id": reviewer,
                    "granted_by": authority_owner,
                    "authority_scope": {
                        "decisions": ["REVIEW_CASE_INTELLIGENCE"],
                        "implementation_modes": ["ADVISORY"],
                    },
                    "effective_from": T0,
                    "expires_at": T1,
                    "evidence_ref": "authority:knowledge-review:v1",
                },
                at=T0,
            )
            grant_client_decision_authority(
                conn,
                tenant,
                {
                    "actor_id": publisher,
                    "granted_by": authority_owner,
                    "authority_scope": {
                        "decisions": [
                            "PUBLISH_CASE_INTELLIGENCE",
                            "GRANT_CASE_INTELLIGENCE_ACCESS",
                            "AUDIT_CASE_INTELLIGENCE",
                        ],
                        "implementation_modes": ["ADVISORY"],
                    },
                    "effective_from": T0,
                    "expires_at": T1,
                    "evidence_ref": "authority:knowledge-publish:v1",
                },
                at=T0,
            )

            first = create_lesson_case(
                conn,
                tenant,
                {
                    **_content("Gateway interruption recovery"),
                    "case_key": "GATEWAY-RECOVERY-001",
                    "source_type": "ENTERPRISE_CASE",
                    "source_ref": "enterprise-case:gateway-001",
                    "config_id": config["config_id"],
                    "operating_model": "ENTERPRISE",
                    "sensitivity": "RESTRICTED",
                    "retention_until": T1,
                    "author_actor_id": author,
                },
                at=T0,
            )
            submit_lesson_for_review(conn, tenant, first["version_id"], author, at=T0)
            with pytest.raises(CaseIntelligenceError, match="CASE_INTELLIGENCE_AUTHORITY_REQUIRED"):
                review_lesson(
                    conn, tenant, first["version_id"], viewer, "APPROVED", "Viewer cannot review.", at=T0
                )
            review_lesson(
                conn, tenant, first["version_id"], reviewer, "APPROVED",
                "The source, limitations and evidence support publication.", at=T0,
            )
            publish_lesson(conn, tenant, first["version_id"], publisher, at=T0)

            with pytest.raises(CaseIntelligenceError, match="LESSON_ACCESS_DENIED"):
                retrieve_lesson(conn, tenant, first["version_id"], viewer, at=T0)
            access_grant = grant_lesson_access(
                conn, tenant, first["knowledge_case_id"], viewer, publisher,
                "Operational resilience analysis", T0, T1, "access:operations-viewer:v1", at=T0,
            )
            retrieved = retrieve_lesson(conn, tenant, first["version_id"], viewer, purpose="CONSOLE", at=T0)
            assert retrieved["advisory_only"] is True
            assert retrieved["source_ref"] == "enterprise-case:gateway-001"
            assert retrieved["reviewer_actor_id"] == reviewer
            assert search_lessons(
                conn, tenant, viewer, filters={"process": "PAYMENT", "jurisdiction": "IN"}, at=T0
            )[0]["version_id"] == first["version_id"]

            second = create_lesson_case(
                conn,
                tenant,
                {
                    **_content("Payment route readiness", learning="Test recovery routes every quarter."),
                    "case_key": "ROUTE-READINESS-002",
                    "source_type": "SIMULATION",
                    "source_ref": "simulation:route-readiness:002",
                    "config_id": config["config_id"],
                    "operating_model": "ENTERPRISE",
                    "sensitivity": "INTERNAL",
                    "retention_until": T1,
                    "author_actor_id": author,
                },
                at=T0,
            )
            submit_lesson_for_review(conn, tenant, second["version_id"], author, at=T0)
            review_lesson(
                conn, tenant, second["version_id"], reviewer, "APPROVED", "Suitable for internal reuse.", at=T0
            )
            publish_lesson(conn, tenant, second["version_id"], publisher, at=T0)
            related = related_lessons(conn, tenant, first["version_id"], viewer, at=T0)
            assert related[0]["version_id"] == second["version_id"]
            assert related[0]["metadata_match_score"] >= 4
            record_lesson_feedback(
                conn, tenant, first["version_id"], viewer, True, True,
                "The precedent helped evaluate the recovery option.", at=T0,
            )

            revision = create_lesson_revision(
                conn,
                tenant,
                first["knowledge_case_id"],
                author,
                _content(
                    "Gateway interruption recovery — revised",
                    learning="Pre-authorise and quarterly-test the alternate route before a disruption.",
                ),
                at=T0,
            )
            submit_lesson_for_review(conn, tenant, revision["version_id"], author, at=T0)
            review_lesson(
                conn, tenant, revision["version_id"], reviewer, "APPROVED",
                "Revision adds the validated testing frequency.", at=T0,
            )
            publication = publish_lesson(conn, tenant, revision["version_id"], publisher, at=T0)
            assert publication["superseded_version_id"] == first["version_id"]
            current = search_lessons(
                conn, tenant, viewer, filters={"risk": "GATEWAY-OUTAGE"}, at=T0
            )
            assert {item["version_id"] for item in current} == {revision["version_id"], second["version_id"]}
            history = lesson_history(conn, tenant, first["knowledge_case_id"], publisher, at=T0)
            assert [(item["version"], item["status"]) for item in history] == [
                (1, "SUPERSEDED"),
                (2, "PUBLISHED"),
            ]
            withdraw_lesson(
                conn, tenant, revision["version_id"], publisher,
                "The control design changed and requires a new validation.", at=T0,
            )
            assert search_lessons(
                conn, tenant, viewer, filters={"risk": "GATEWAY-OUTAGE"}, at=T0
            )[0]["version_id"] == second["version_id"]
            metrics = knowledge_quality_metrics(conn, tenant)
            assert metrics["published"] == 1
            assert metrics["superseded"] == 1
            assert metrics["withdrawn"] == 1
            assert metrics["feedback_count"] == 1
            assert metrics["relevance_pct"] == 100
            assert revoke_lesson_access(
                conn, tenant, access_grant["grant_id"], publisher,
                "The viewer no longer participates in this review.", at=T0,
            )["status"] == "REVOKED"
            with pytest.raises(CaseIntelligenceError, match="LESSON_AUDIT_ACCESS_DENIED"):
                lesson_history(conn, tenant, first["knowledge_case_id"], viewer, at=T0)
            with pytest.raises(CaseIntelligenceError, match="LESSON_VERSION_NOT_FOUND"):
                retrieve_lesson(conn, uuid4(), second["version_id"], viewer, at=T0)

        with pytest.raises(psycopg.errors.RaiseException, match="LESSON_VERSION_PAYLOAD_IMMUTABLE"):
            conn.execute(
                "UPDATE resilience_v2.knowledge_lesson_versions SET title='Tampered' WHERE tenant_id=%s AND version_id=%s",
                (tenant, second["version_id"]),
            )
        conn.rollback()
