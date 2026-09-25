from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest
from pydantic import ValidationError

from resilience.config import ROOT, load_profile
from resilience.m22_console import ConsoleAuthorizationError, Principal
from resilience.m27_assurance import (
    CONSULTANT_STEPS,
    ENTERPRISE_STEPS,
    READINESS_CATEGORIES,
    ControlledPilotSpec,
    OperationalAssuranceService,
    dual_model_readiness,
    pilot_evidence_pack,
    record_controlled_pilot,
)


T0 = datetime(2027, 1, 5, 9, tzinfo=timezone.utc)


def _pilot(model, actor, steps):
    return {
        "operating_model": model,
        "pilot_name": f"M27 {model.title()} controlled pilot",
        "executed_by": actor,
        "started_at": T0,
        "completed_at": T0 + timedelta(minutes=20),
        "live_actions": 0,
        "steps": [
            {"step_key": key, "outcome": "PASS", "evidence_ref": f"pilot:{model.lower()}:{key.lower()}"}
            for key in steps
        ],
        "readiness_checks": [
            {"category": category, "outcome": "PASS", "evidence_ref": f"readiness:{model.lower()}:{category.lower()}"}
            for category in READINESS_CATEGORIES
        ],
    }


def test_m27_view_authorization_and_measure_separation():
    service = OperationalAssuranceService()
    analyst = Principal("analyst", "Enterprise Analyst", frozenset({"assurance:enterprise:view"}))
    consultant = Principal("consultant", "Risk Consultant", frozenset({"assurance:consultant:view"}))
    enterprise = service.bootstrap(analyst, "enterprise")
    assert enterprise["draggable_panels"] is True
    assert enterprise["severity_confidence_resilience_separate"] is True
    assert enterprise["live_actions"] == 0
    consultant_view = service.bootstrap(consultant, "consultant")
    assert consultant_view["mandate"]["sandbox_only"] is True
    with pytest.raises(ConsoleAuthorizationError, match="ASSURANCE_VIEW_DENIED"):
        service.bootstrap(analyst, "consultant")


def test_m27_rejects_incomplete_pilot_sequence():
    value = _pilot("ENTERPRISE", uuid4(), ENTERPRISE_STEPS[:-1])
    with pytest.raises(ValidationError, match="PILOT_STEP_SEQUENCE_INCOMPLETE"):
        ControlledPilotSpec.model_validate(value)


@pytest.mark.integration
def test_m27_records_immutable_dual_model_pilot_evidence():
    profile = load_profile("test")
    tenant, enterprise_actor, consultant_actor = uuid4(), uuid4(), uuid4()
    with psycopg.connect(**profile.connection_kwargs(migration=True)) as admin:
        admin.execute("INSERT INTO resilience_v2.tenants VALUES (%s,'M27 Dual Model Pilot','ACTIVE')", (tenant,))
        admin.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'Enterprise pilot operator')", (tenant, enterprise_actor))
        admin.execute("INSERT INTO resilience_v2.actors VALUES (%s,%s,'Consultant pilot operator')", (tenant, consultant_actor))
        admin.commit()
    with psycopg.connect(**profile.connection_kwargs()) as conn:
        with conn.transaction():
            enterprise = record_controlled_pilot(conn, tenant, _pilot("ENTERPRISE", enterprise_actor, ENTERPRISE_STEPS))
            consultant = record_controlled_pilot(conn, tenant, _pilot("CONSULTANT", consultant_actor, CONSULTANT_STEPS))
            enterprise_pack = pilot_evidence_pack(conn, tenant, enterprise["pilot_id"])
            consultant_pack = pilot_evidence_pack(conn, tenant, consultant["pilot_id"])
            readiness = dual_model_readiness(conn, tenant)
            assert enterprise_pack["status"] == "PASS"
            assert [step["step_key"] for step in enterprise_pack["steps"]] == list(ENTERPRISE_STEPS)
            assert [step["step_key"] for step in consultant_pack["steps"]] == list(CONSULTANT_STEPS)
            assert len(enterprise_pack["readiness_checks"]) == 7
            assert readiness["ready"] is True
            assert readiness["production_actions_enabled"] is False
            assert pilot_evidence_pack(conn, tenant, consultant["pilot_id"])["live_actions"] == 0
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute(
                "UPDATE resilience_v2.operational_assurance_pilots SET live_actions=1 WHERE tenant_id=%s AND pilot_id=%s",
                (tenant, enterprise["pilot_id"]),
            )
        conn.rollback()


def test_m27_console_packages_operational_assurance_workspace():
    web = ROOT / "src" / "resilience" / "web" / "index.html"
    source = web.read_text(encoding="utf-8")
    assert "/api/operational-assurance/bootstrap" in source
    assert "OPERATIONAL ASSURANCE" in source
    assert "draggable" in source.lower()
    server = (ROOT / "src" / "resilience" / "m22_web.py").read_text(encoding="utf-8")
    assert '"/api/operational-assurance/bootstrap"' in server
