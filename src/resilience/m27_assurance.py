"""M27 role-aware console view models and controlled pilot evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .m22_console import ConsoleAuthorizationError, Principal


ENTERPRISE_STEPS = (
    "CONFIGURATION_RESOLVED",
    "LIVE_STATE_OBSERVED",
    "PRIVATE_SIMULATION_COMPLETED",
    "CHANGE_APPROVED",
    "INFORMATION_ESCALATED",
    "OUTCOME_REVIEWED",
    "LESSON_PUBLISHED",
)
CONSULTANT_STEPS = (
    "ASSIGNMENT_ACTIVE",
    "SOURCE_INGESTED",
    "CHANGE_ASSESSED",
    "PRIVATE_SIMULATION_COMPLETED",
    "CLIENT_APPROVED",
    "SANDBOX_EXECUTED",
    "OUTCOME_VALIDATED",
    "LESSON_PUBLISHED",
)
READINESS_CATEGORIES = (
    "USABILITY",
    "ACCESSIBILITY",
    "PERFORMANCE",
    "SECURITY",
    "RETENTION",
    "AUDIT",
    "TENANT_ISOLATION",
)


class PilotEvidenceError(ValueError):
    pass


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("TIME_MUST_BE_TIMEZONE_AWARE")
    return value.astimezone(timezone.utc)


def _json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class PilotStepSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    step_key: str = Field(min_length=1, max_length=160)
    outcome: Literal["PASS", "FAIL"]
    evidence_ref: str = Field(min_length=1, max_length=500)


class ReadinessCheckSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    category: Literal["USABILITY", "ACCESSIBILITY", "PERFORMANCE", "SECURITY", "RETENTION", "AUDIT", "TENANT_ISOLATION"]
    outcome: Literal["PASS", "FAIL"]
    evidence_ref: str = Field(min_length=1, max_length=500)


class ControlledPilotSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    operating_model: Literal["ENTERPRISE", "CONSULTANT"]
    pilot_name: str = Field(min_length=1, max_length=240)
    executed_by: UUID
    started_at: datetime
    completed_at: datetime
    live_actions: int = Field(ge=0, le=0)
    steps: tuple[PilotStepSpec, ...]
    readiness_checks: tuple[ReadinessCheckSpec, ...]

    @field_validator("started_at", "completed_at")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        return _utc(value)

    @model_validator(mode="after")
    def complete_evidence(self):
        if self.completed_at < self.started_at:
            raise ValueError("PILOT_TIME_RANGE_INVALID")
        required = ENTERPRISE_STEPS if self.operating_model == "ENTERPRISE" else CONSULTANT_STEPS
        keys = [step.step_key for step in self.steps]
        if tuple(keys) != required:
            raise ValueError("PILOT_STEP_SEQUENCE_INCOMPLETE")
        if any(step.outcome != "PASS" for step in self.steps):
            raise ValueError("PILOT_STEP_FAILED")
        categories = [check.category for check in self.readiness_checks]
        if set(categories) != set(READINESS_CATEGORIES) or len(categories) != len(READINESS_CATEGORIES):
            raise ValueError("READINESS_CHECKS_INCOMPLETE")
        if any(check.outcome != "PASS" for check in self.readiness_checks):
            raise ValueError("READINESS_CHECK_FAILED")
        return self


class OperationalAssuranceService:
    """Role-aware M27 view model with no live-action capability."""

    def __init__(self):
        self._enterprise = {
            "operating_model": "ENTERPRISE",
            "workspace_title": "Enterprise Operational Assurance",
            "tenant_context": "Example Payments Group",
            "configuration": {"version": 2, "status": "ACTIVE", "processes": 4, "controls": 5},
            "risk_state": {"severity": 7, "confidence_pct": 92, "resilience": 87, "workflow_status": "MONITORED"},
            "obligations": {"open": 3, "overdue": 1, "qualified_assessments": 1},
            "changes": {"open": 1, "awaiting_approval": 0},
            "knowledge": {"current_lessons": 2, "related_precedents": 1},
            "panels": ["Configuration", "Changes", "Information", "Evidence Confidence", "Prior Cases", "Audit Trail"],
        }
        self._consultant = {
            "operating_model": "CONSULTANT",
            "workspace_title": "Consultant Control Centre",
            "tenant_context": "Assigned Client Portfolio",
            "portfolio": {"assigned_clients": 2, "changes_to_review": 1, "pending_client_decisions": 1, "expiring_mandates": 0},
            "risk_state": {"severity": 7, "confidence_pct": 94, "resilience": 82, "workflow_status": "CLIENT_DECISION"},
            "active_client": "Example Payments Group",
            "mandate": {"status": "ACTIVE", "mode": "DELEGATED", "sandbox_only": True},
            "panels": ["Client Portfolio", "Change Inbox", "Expert Assessment", "Simulation", "Client Decision", "Implementation", "Outcome Review"],
        }
        self._client = {
            "operating_model": "CLIENT_APPROVAL",
            "workspace_title": "Client Decision Portal",
            "tenant_context": "Example Payments Group",
            "recommendation": {"status": "AWAITING_DECISION", "implementation_mode": "DELEGATED", "simulation_ref": "simulation:m27:pilot"},
            "risk_state": {"severity": 7, "confidence_pct": 94, "resilience": 82, "workflow_status": "AWAITING_CLIENT_DECISION"},
            "panels": ["Current State", "Consultant Assessment", "Options", "Simulated Effect", "Authority Requested", "Decision Evidence"],
        }

    def bootstrap(self, principal: Principal, view: str) -> dict:
        scope = {
            "enterprise": "assurance:enterprise:view",
            "consultant": "assurance:consultant:view",
            "client": "assurance:client:view",
        }.get(view)
        if scope is None:
            raise ValueError("ASSURANCE_VIEW_INVALID")
        if scope not in principal.scopes:
            raise ConsoleAuthorizationError("ASSURANCE_VIEW_DENIED")
        source = {"enterprise": self._enterprise, "consultant": self._consultant, "client": self._client}[view]
        return {
            **json.loads(json.dumps(source)),
            "principal": {"actor_id": principal.actor_id, "display_name": principal.display_name},
            "draggable_panels": True,
            "live_actions": 0,
            "severity_confidence_resilience_separate": True,
        }


def record_controlled_pilot(conn, tenant: UUID, value) -> dict:
    spec = ControlledPilotSpec.model_validate(value)
    evidence = {
        "operating_model": spec.operating_model,
        "steps": [step.model_dump() for step in spec.steps],
        "readiness": [check.model_dump() for check in spec.readiness_checks],
        "live_actions": spec.live_actions,
    }
    digest = sha256(_json(evidence).encode()).hexdigest()
    pilot_id = uuid4()
    conn.execute(
        """INSERT INTO resilience_v2.operational_assurance_pilots
        VALUES (%s,%s,%s,%s,%s,'PASS',0,%s,%s,%s)""",
        (tenant, pilot_id, spec.operating_model, spec.pilot_name, spec.executed_by,
         spec.started_at, spec.completed_at, digest),
    )
    for order, step in enumerate(spec.steps, 1):
        conn.execute(
            "INSERT INTO resilience_v2.operational_assurance_pilot_steps VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (tenant, pilot_id, order, step.step_key, step.outcome, step.evidence_ref, spec.completed_at),
        )
    for check in spec.readiness_checks:
        conn.execute(
            "INSERT INTO resilience_v2.operational_assurance_readiness_checks VALUES (%s,%s,%s,%s,%s,%s)",
            (tenant, pilot_id, check.category, check.outcome, check.evidence_ref, spec.completed_at),
        )
    return {"pilot_id": pilot_id, "operating_model": spec.operating_model, "status": "PASS", "live_actions": 0, "evidence_digest": digest}


def pilot_evidence_pack(conn, tenant: UUID, pilot_id: UUID) -> dict:
    pilot = conn.execute(
        """SELECT operating_model,pilot_name,executed_by,status,live_actions,started_at,completed_at,evidence_digest
        FROM resilience_v2.operational_assurance_pilots WHERE tenant_id=%s AND pilot_id=%s""",
        (tenant, pilot_id),
    ).fetchone()
    if pilot is None:
        raise PilotEvidenceError("PILOT_NOT_FOUND")
    steps = conn.execute(
        """SELECT step_order,step_key,outcome,evidence_ref FROM resilience_v2.operational_assurance_pilot_steps
        WHERE tenant_id=%s AND pilot_id=%s ORDER BY step_order""",
        (tenant, pilot_id),
    ).fetchall()
    checks = conn.execute(
        """SELECT category,outcome,evidence_ref FROM resilience_v2.operational_assurance_readiness_checks
        WHERE tenant_id=%s AND pilot_id=%s ORDER BY category""",
        (tenant, pilot_id),
    ).fetchall()
    return {
        "pilot_id": pilot_id, "operating_model": pilot[0], "pilot_name": pilot[1],
        "executed_by": pilot[2], "status": pilot[3], "live_actions": pilot[4],
        "started_at": pilot[5], "completed_at": pilot[6], "evidence_digest": pilot[7],
        "steps": [{"order": row[0], "step_key": row[1], "outcome": row[2], "evidence_ref": row[3]} for row in steps],
        "readiness_checks": [{"category": row[0], "outcome": row[1], "evidence_ref": row[2]} for row in checks],
    }


def dual_model_readiness(conn, tenant: UUID) -> dict:
    rows = conn.execute(
        """SELECT operating_model,count(*),bool_and(status='PASS' AND live_actions=0)
        FROM resilience_v2.operational_assurance_pilots WHERE tenant_id=%s GROUP BY operating_model""",
        (tenant,),
    ).fetchall()
    models = {row[0]: {"pilots": row[1], "ready": row[2]} for row in rows}
    ready = all(model in models and models[model]["ready"] for model in ("ENTERPRISE", "CONSULTANT"))
    return {"ready": ready, "models": models, "production_actions_enabled": False}
