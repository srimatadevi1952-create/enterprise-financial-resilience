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
    """Role-aware UAT workspace with explicit synthetic-data labelling.

    The state provider binds the enterprise cards to the current console state.
    M23-M26 records below are controlled UAT fixtures until an approved database
    and client feed are connected; the API always discloses that boundary.
    """

    def __init__(self, state_provider=None, *, decision_loader=None, event_recorder=None):
        self._state_provider = state_provider
        self._decision_loader = decision_loader
        self._event_recorder = event_recorder
        self._decision = "AWAITING_DECISION"
        self._decision_events: list[dict] = []
        self._view_events: list[dict] = []

    def _sync_decision(self) -> None:
        if self._decision_loader:
            self._decision = self._decision_loader()

    def _record_external(self, event_type: str, event: dict) -> None:
        if self._event_recorder:
            self._event_recorder(event_type, event)

    def _enterprise(self) -> dict:
        state = self._state_provider().as_dict() if self._state_provider else {
            "as_of": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "probability": 0.0, "impact": 0.0, "resilience": 87,
        }
        severity = round(state["probability"] * state["impact"], 1)
        return {
            "operating_model": "ENTERPRISE",
            "workspace_title": "Enterprise Operational Assurance",
            "tenant_context": "Example Payments Group",
            "configuration": {"version": 2, "status": "ACTIVE", "processes": 4, "controls": 5, "owner": "Asha Iyer"},
            "risk_state": {"severity": severity, "confidence_pct": 92, "resilience": state["resilience"], "workflow_status": "MONITORED"},
            "measure_context": {"scope": "ENTERPRISE LIVE", "scale": "SEVERITY 0-100 HIGHER WORSE · RESILIENCE 0-100 HIGHER BETTER", "as_of": state["as_of"], "reference": "PAYMENTS-GROUP/CONFIG-V2"},
            "obligations": {"open": 3, "overdue": 1, "qualified_assessments": 1},
            "changes": {"open": 1, "awaiting_approval": 0},
            "knowledge": {"current_lessons": 2, "related_precedents": 1},
            "panels": ["Configuration", "Changes", "Information", "Evidence Confidence", "Prior Cases", "Audit Trail"],
        }

    def _consultant(self) -> dict:
        return {
            "operating_model": "CONSULTANT",
            "workspace_title": "Consultant Control Centre",
            "tenant_context": "Assigned Client Portfolio",
            "portfolio": {"assigned_clients": 2, "changes_to_review": 1, "pending_client_decisions": 1 if self._decision == "AWAITING_DECISION" else 0, "expiring_mandates": 0},
            "risk_state": {"severity": 7, "confidence_pct": 94, "resilience": 82, "workflow_status": "CLIENT_DECISION" if self._decision == "AWAITING_DECISION" else self._decision},
            "measure_context": {"scope": "CLIENT CASE", "scale": "SEVERITY 0-10 HIGHER WORSE · RESILIENCE 0-100 HIGHER BETTER", "as_of": "2026-09-29T09:00:00+00:00", "reference": "CASE-CHANGE-001 / SIM-M27-001"},
            "active_client": "Example Payments Group",
            "mandate": {"status": "ACTIVE", "mode": "DELEGATED", "sandbox_only": True, "expires_at": "2026-12-31T23:59:59+00:00"},
            "panels": ["Client Portfolio", "Change Inbox", "Expert Assessment", "Simulation", "Client Decision", "Implementation", "Outcome Review"],
        }

    def _client(self) -> dict:
        return {
            "operating_model": "CLIENT_APPROVAL",
            "workspace_title": "Client Decision Portal",
            "tenant_context": "Example Payments Group",
            "recommendation": {
                "status": self._decision,
                "implementation_mode": "DELEGATED",
                "simulation_ref": "SIM-M27-001",
                "summary": "Activate the approved alternate settlement route for the affected window.",
                "rationale": "The simulated route restores settlement delay below ten minutes without increasing failed payments.",
                "authority": "One sandbox route switch; expires after this case; revocable before execution.",
            },
            "risk_state": {"severity": 7, "confidence_pct": 94, "resilience": 82, "workflow_status": "AWAITING_CLIENT_DECISION" if self._decision == "AWAITING_DECISION" else self._decision},
            "measure_context": {"scope": "CLIENT DECISION PACKAGE", "scale": "SEVERITY 0-10 HIGHER WORSE · RESILIENCE 0-100 HIGHER BETTER", "as_of": "2026-09-29T09:00:00+00:00", "reference": "CHANGE-001 / SIM-M27-001"},
            "options": [
                {"key": "RECOMMENDED", "label": "Alternate settlement route", "resilience": 82, "residual_severity": 3},
                {"key": "DEFER", "label": "Continue current route", "resilience": 68, "residual_severity": 7},
            ],
            "panels": ["Current State", "Consultant Assessment", "Options", "Simulated Effect", "Authority Requested", "Decision Evidence"],
        }

    def bootstrap(self, principal: Principal, view: str) -> dict:
        self._sync_decision()
        scope = {
            "enterprise": "assurance:enterprise:view",
            "consultant": "assurance:consultant:view",
            "client": "assurance:client:view",
        }.get(view)
        if scope is None:
            raise ValueError("ASSURANCE_VIEW_INVALID")
        if scope not in principal.scopes:
            self._view_events.append({
                "at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                "actor_id": principal.actor_id,
                "view": view,
                "outcome": "DENIED",
            })
            self._record_external("VIEW", self._view_events[-1])
            raise ConsoleAuthorizationError("ASSURANCE_VIEW_DENIED")
        source = {"enterprise": self._enterprise, "consultant": self._consultant, "client": self._client}[view]()
        self._view_events.append({
            "at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "actor_id": principal.actor_id,
            "view": view,
            "outcome": "GRANTED",
        })
        self._record_external("VIEW", self._view_events[-1])
        return {
            **json.loads(json.dumps(source)),
            "principal": {"actor_id": principal.actor_id, "display_name": principal.display_name},
            "draggable_panels": True,
            "live_actions": 0,
            "severity_confidence_resilience_separate": True,
            "data_mode": "SYNTHETIC_UAT",
            "data_notice": "Controlled synthetic records; connect approved M23-M26 tenant data before live-data pilot.",
        }

    def detail(self, principal: Principal, view: str, panel: str) -> dict:
        workspace = self.bootstrap(principal, view)
        if panel not in workspace["panels"]:
            raise ValueError("ASSURANCE_PANEL_INVALID")
        common = {
            "Configuration": [("Version", "V2 ACTIVE"), ("Owner", "Asha Iyer"), ("Processes", "4"), ("Controls", "5"), ("Evidence", "process-register:v2")],
            "Changes": [("Change", "CHANGE-001"), ("Status", "OPEN"), ("Owner", "Maya Sen"), ("Simulation", "SIM-M27-001"), ("Evidence", "assessment:accepted")],
            "Information": [("Open", "3"), ("Overdue", "1"), ("Owner", "Client finance contact"), ("Escalation", "ACTIVE"), ("Evidence", "obligation:settlement-confirmation")],
            "Evidence Confidence": [("Confidence", "92%"), ("Completeness", "90%"), ("Freshness", "94%"), ("Rule", "CONF-V1"), ("Gap", "1 material item")],
            "Prior Cases": [("Published", "2"), ("Related", "1"), ("Top case", "Gateway interruption recovery"), ("Status", "ADVISORY ONLY"), ("Evidence", "case:GATEWAY-RECOVERY-001")],
            "Audit Trail": [("View events", str(len(self._view_events))), ("Decision events", str(len(self._decision_events))), ("Live actions", "0"), ("Retention", "7 years"), ("Export", "Controlled evidence pack")],
            "Client Portfolio": [("Assigned clients", "2"), ("Active client", "Example Payments Group"), ("Assignment", "ACTIVE"), ("Tenant", "TENANT-UAT-001"), ("Isolation", "PASS")],
            "Change Inbox": [("Change", "CHANGE-001"), ("Status", "CLIENT DECISION"), ("Severity", "7/10"), ("Confidence", "94%"), ("Owner", "Maya Sen")],
            "Expert Assessment": [("Assessor", "Maya Sen"), ("Disposition", "ACCEPTED"), ("Rationale", "Settlement delay breaches approved target"), ("Limit", "Synthetic UAT evidence"), ("Attestation", "RECORDED")],
            "Simulation": [("Reference", "SIM-M27-001"), ("Baseline resilience", "68"), ("Expected resilience", "82"), ("Live actions", "0"), ("Boundary", "PRIVATE SANDBOX")],
            "Client Decision": [("Status", self._decision), ("Decision maker", "Arun Mehta"), ("Step-up", "REQUIRED"), ("SoD", "CONSULTANT CANNOT SELF-APPROVE"), ("Evidence", "decision:pending")],
            "Implementation": [("Mode", "DELEGATED"), ("Target", "gateway:alternate"), ("Boundary", "SANDBOX ONLY"), ("Mandate expiry", "2026-12-31"), ("Live actions", "0")],
            "Outcome Review": [("Status", "PENDING DECISION"), ("Success measure", "Delay below 10 minutes"), ("Owner", "Client approver"), ("Evidence", "post-change observation required"), ("Lesson", "Publish after validation")],
            "Current State": [("Severity", "7/10"), ("Confidence", "94%"), ("Resilience", "68 baseline"), ("Case", "CASE-CHANGE-001"), ("As of", "2026-09-29 09:00 UTC")],
            "Consultant Assessment": [("Consultant", "Maya Sen"), ("Recommendation", "Alternate settlement route"), ("Rationale", "Restore delay below target"), ("Limitations", "Controlled synthetic evidence"), ("Attestation", "RECORDED")],
            "Options": [("Recommended", "Alternate route → resilience 82"), ("Defer", "Current route → resilience 68"), ("Rollback", "Restore original route"), ("Residual severity", "3 vs 7"), ("Decision", self._decision)],
            "Simulated Effect": [("Baseline resilience", "68"), ("Expected resilience", "82"), ("Settlement delay", "8 minutes"), ("Failed payments", "16 max"), ("Simulation", "SIM-M27-001")],
            "Authority Requested": [("Action", "SWITCH_SETTLEMENT_ROUTE"), ("Target", "gateway:alternate"), ("Scope", "One sandbox execution"), ("Expiry", "After this case"), ("Revocable", "Until execution")],
            "Decision Evidence": [("Status", self._decision), ("Approver", "Arun Mehta"), ("Step-up", "REQUIRED"), ("Evidence pack", "COMPLETE FOR UAT"), ("Live actions", "0")],
        }
        return {"title": panel, "rows": [{"label": a, "value": b} for a, b in common[panel]], "source": workspace["measure_context"], "read_only": True}

    def record_client_decision(self, principal: Principal, decision: str, *, step_up_verified: bool, rationale: str = "") -> dict:
        self._sync_decision()
        if "assurance:client:decide" not in principal.scopes:
            raise ConsoleAuthorizationError("CLIENT_DECISION_DENIED")
        if not step_up_verified:
            raise ConsoleAuthorizationError("STEP_UP_REQUIRED")
        if decision not in {"APPROVED", "REJECTED", "CLARIFICATION_REQUESTED"}:
            raise ValueError("CLIENT_DECISION_INVALID")
        if self._decision in {"APPROVED", "REJECTED"}:
            raise ConsoleAuthorizationError("CLIENT_DECISION_ALREADY_FINAL")
        self._decision = decision
        event = {"at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(), "actor_id": principal.actor_id, "decision": decision, "rationale": rationale, "live_actions": 0}
        self._decision_events.append(event)
        self._record_external("DECISION", event)
        return {**event, "status": decision, "sandbox_execution_enabled": decision == "APPROVED", "live_actions": 0}


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
