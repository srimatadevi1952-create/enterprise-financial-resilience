"""M24 consultant-led cases, change governance and sandbox execution."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


DIMENSIONS = {"CAPITAL", "LIQUIDITY", "OPERATIONS", "REGULATION", "MERCHANTS", "CORRIDORS"}


class ConsultantWorkflowError(ValueError):
    pass


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("TIME_MUST_BE_TIMEZONE_AWARE")
    return value.astimezone(timezone.utc)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _digest(value) -> str:
    return sha256(_json(value).encode()).hexdigest()


class AssignmentSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    consultant_principal_id: UUID
    consultant_actor_id: UUID
    service_name: str = Field(min_length=1, max_length=160)
    permitted_purposes: tuple[str, ...] = Field(min_length=1)
    authority_scope: dict
    effective_from: datetime
    expires_at: datetime
    evidence_ref: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def valid_period(self):
        start, end = _utc(self.effective_from), _utc(self.expires_at)
        if end <= start:
            raise ValueError("ASSIGNMENT_PERIOD_INVALID")
        if any(not value.strip() for value in self.permitted_purposes):
            raise ValueError("PERMITTED_PURPOSE_REQUIRED")
        return self


class MandateSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    assignment_id: UUID
    authorized_by: UUID
    implementation_modes: tuple[Literal["ADVISORY", "ASSISTED", "DELEGATED"], ...] = Field(min_length=1)
    action_scope: dict
    effective_from: datetime
    expires_at: datetime
    evidence_ref: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def valid_period(self):
        if _utc(self.expires_at) <= _utc(self.effective_from):
            raise ValueError("MANDATE_PERIOD_INVALID")
        if len(set(self.implementation_modes)) != len(self.implementation_modes):
            raise ValueError("IMPLEMENTATION_MODE_DUPLICATE")
        return self


class ClientDecisionAuthoritySpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    actor_id: UUID
    granted_by: UUID
    authority_scope: dict
    effective_from: datetime
    expires_at: datetime
    evidence_ref: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def valid_authority(self):
        if self.actor_id == self.granted_by:
            raise ValueError("AUTHORITY_SELF_GRANT_PROHIBITED")
        if _utc(self.expires_at) <= _utc(self.effective_from):
            raise ValueError("AUTHORITY_PERIOD_INVALID")
        decisions = self.authority_scope.get("decisions", [])
        modes = self.authority_scope.get("implementation_modes", [])
        if not decisions or not modes:
            raise ValueError("AUTHORITY_SCOPE_REQUIRED")
        return self


class ObservationSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    assignment_id: UUID
    source_key: str = Field(min_length=1, max_length=160)
    source_record_key: str = Field(min_length=1, max_length=240)
    observed_at: datetime
    effective_at: datetime
    schema_version: str = Field(min_length=1, max_length=80)
    payload: dict
    lineage_ref: str = Field(min_length=1, max_length=500)
    quality_status: Literal["VALID", "DEGRADED", "REJECTED"]
    reconciliation_status: Literal["MATCHED", "CHANGED", "EXCEPTION", "PENDING"]

    @field_validator("observed_at", "effective_at")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        return _utc(value)


class CaseSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    assignment_id: UUID
    config_id: UUID
    observation_ids: tuple[UUID, ...] = Field(min_length=1)
    title: str = Field(min_length=1, max_length=240)
    change_summary: str = Field(min_length=1, max_length=4000)
    baseline_hash: str = Field(min_length=1, max_length=128)
    current_hash: str = Field(min_length=1, max_length=128)
    severity: int = Field(ge=0, le=10)
    confidence_pct: float = Field(ge=0, le=100)
    opened_by: UUID


class AssessmentSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    case_id: UUID
    assessed_by: UUID
    disposition: Literal["ACCEPTED", "AMENDED", "DISMISSED"]
    rationale: str = Field(min_length=1, max_length=8000)
    affected_dimensions: tuple[str, ...] = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(min_length=1)

    @field_validator("affected_dimensions")
    @classmethod
    def dimensions_valid(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value) or not set(value).issubset(DIMENSIONS):
            raise ValueError("AFFECTED_DIMENSIONS_INVALID")
        return value


class ProposalSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    case_id: UUID
    assessment_id: UUID
    proposed_by: UUID
    implementation_mode: Literal["ADVISORY", "ASSISTED", "DELEGATED"]
    target_dimensions: tuple[str, ...] = Field(min_length=1)
    recommended_change: str = Field(min_length=1, max_length=8000)
    expected_outcome: str = Field(min_length=1, max_length=8000)
    simulation_ref: str = Field(min_length=1, max_length=500)
    rollback_plan: str = Field(min_length=1, max_length=8000)
    evidence_refs: tuple[str, ...] = Field(min_length=1)

    @field_validator("target_dimensions")
    @classmethod
    def dimensions_valid(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value) or not set(value).issubset(DIMENSIONS):
            raise ValueError("TARGET_DIMENSIONS_INVALID")
        return value


def _event(conn, tenant: UUID, case_id: UUID, actor_id: UUID, event_type: str, payload: dict, at: datetime):
    event_id = uuid4()
    conn.execute(
        "INSERT INTO resilience_v2.consultant_case_events VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (tenant, event_id, case_id, actor_id, event_type, _json(payload), at),
    )
    return event_id


def _active_assignment(conn, tenant: UUID, assignment_id: UUID, actor_id: UUID | None, at: datetime):
    row = conn.execute(
        """SELECT consultant_actor_id FROM resilience_v2.consultant_assignments
        WHERE tenant_id=%s AND assignment_id=%s AND status='ACTIVE'
          AND effective_from <= %s AND expires_at > %s""",
        (tenant, assignment_id, at, at),
    ).fetchone()
    if row is None:
        raise ConsultantWorkflowError("ACTIVE_ASSIGNMENT_REQUIRED")
    if actor_id is not None and row[0] != actor_id:
        raise ConsultantWorkflowError("CONSULTANT_NOT_ASSIGNED")
    return row[0]


def create_assignment(conn, tenant: UUID, value, *, at: datetime | None = None) -> dict:
    spec = AssignmentSpec.model_validate(value)
    at = _utc(at or _now())
    if not (spec.effective_from <= at < spec.expires_at):
        raise ConsultantWorkflowError("ASSIGNMENT_NOT_EFFECTIVE")
    assignment_id = uuid4()
    conn.execute(
        """INSERT INTO resilience_v2.consultant_assignments
        VALUES (%s,%s,%s,%s,%s,%s,%s,'ACTIVE',%s,%s,%s,%s,%s)""",
        (tenant, assignment_id, spec.consultant_principal_id, spec.consultant_actor_id,
         spec.service_name, _json(list(spec.permitted_purposes)), _json(spec.authority_scope),
         spec.effective_from, spec.expires_at, spec.evidence_ref, at, at),
    )
    return {"assignment_id": assignment_id, "status": "ACTIVE", "operating_model": "CONSULTANT"}


def grant_client_decision_authority(conn, tenant: UUID, value, *, at: datetime | None = None) -> dict:
    spec = ClientDecisionAuthoritySpec.model_validate(value)
    at = _utc(at or _now())
    if not (spec.effective_from <= at < spec.expires_at):
        raise ConsultantWorkflowError("CLIENT_AUTHORITY_NOT_EFFECTIVE")
    authority_id = uuid4()
    conn.execute(
        """INSERT INTO resilience_v2.client_decision_authorities
        VALUES (%s,%s,%s,%s,%s,'ACTIVE',%s,%s,%s,%s,%s)""",
        (tenant, authority_id, spec.actor_id, spec.granted_by, _json(spec.authority_scope),
         spec.effective_from, spec.expires_at, spec.evidence_ref, at, at),
    )
    return {"authority_id": authority_id, "status": "ACTIVE"}


def _require_client_authority(
    conn, tenant: UUID, actor_id: UUID, decision: str, implementation_mode: str, at: datetime,
) -> UUID:
    rows = conn.execute(
        """SELECT authority_id,authority_scope FROM resilience_v2.client_decision_authorities
        WHERE tenant_id=%s AND actor_id=%s AND status='ACTIVE'
          AND effective_from <= %s AND expires_at > %s""",
        (tenant, actor_id, at, at),
    ).fetchall()
    for authority_id, scope in rows:
        if (decision in scope.get("decisions", [])
                and implementation_mode in scope.get("implementation_modes", [])):
            return authority_id
    raise ConsultantWorkflowError("CLIENT_DECISION_AUTHORITY_REQUIRED")


def revoke_assignment(conn, tenant: UUID, assignment_id: UUID, *, at: datetime | None = None) -> dict:
    at = _utc(at or _now())
    row = conn.execute(
        """UPDATE resilience_v2.consultant_assignments SET status='REVOKED',updated_at=%s
        WHERE tenant_id=%s AND assignment_id=%s AND status='ACTIVE' RETURNING assignment_id""",
        (at, tenant, assignment_id),
    ).fetchone()
    if row is None:
        raise ConsultantWorkflowError("ACTIVE_ASSIGNMENT_REQUIRED")
    return {"assignment_id": assignment_id, "status": "REVOKED"}


def create_mandate(conn, tenant: UUID, value, *, at: datetime | None = None) -> dict:
    spec = MandateSpec.model_validate(value)
    at = _utc(at or _now())
    _active_assignment(conn, tenant, spec.assignment_id, None, at)
    if not (spec.effective_from <= at < spec.expires_at):
        raise ConsultantWorkflowError("MANDATE_NOT_EFFECTIVE")
    assignment_actor, assignment_start, assignment_end = conn.execute(
        """SELECT consultant_actor_id,effective_from,expires_at
        FROM resilience_v2.consultant_assignments WHERE tenant_id=%s AND assignment_id=%s""",
        (tenant, spec.assignment_id),
    ).fetchone()
    if assignment_actor == spec.authorized_by:
        raise ConsultantWorkflowError("CLIENT_AUTHORIZER_MUST_BE_INDEPENDENT")
    if spec.effective_from < assignment_start or spec.expires_at > assignment_end:
        raise ConsultantWorkflowError("MANDATE_EXCEEDS_ASSIGNMENT_PERIOD")
    for mode in spec.implementation_modes:
        _require_client_authority(conn, tenant, spec.authorized_by, "ISSUE_SERVICE_MANDATE", mode, at)
    mandate_id = uuid4()
    conn.execute(
        """INSERT INTO resilience_v2.client_service_mandates
        VALUES (%s,%s,%s,%s,%s,%s,'ACTIVE',%s,%s,%s,%s,%s)""",
        (tenant, mandate_id, spec.assignment_id, spec.authorized_by,
         _json(list(spec.implementation_modes)), _json(spec.action_scope), spec.effective_from,
         spec.expires_at, spec.evidence_ref, at, at),
    )
    return {"mandate_id": mandate_id, "status": "ACTIVE"}


def record_source_observation(conn, tenant: UUID, value) -> dict:
    spec = ObservationSpec.model_validate(value)
    _active_assignment(conn, tenant, spec.assignment_id, None, spec.observed_at)
    payload_hash = _digest(spec.payload)
    observation_id = uuid4()
    inserted = conn.execute(
        """INSERT INTO resilience_v2.consultant_source_observations
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (tenant_id,source_key,source_record_key,payload_hash) DO NOTHING
        RETURNING observation_id""",
        (tenant, observation_id, spec.assignment_id, spec.source_key, spec.source_record_key,
         spec.observed_at, spec.effective_at, spec.schema_version, payload_hash,
         _json(spec.payload), spec.lineage_ref, spec.quality_status, spec.reconciliation_status),
    ).fetchone()
    if inserted is None:
        raise ConsultantWorkflowError("OBSERVATION_ALREADY_RECORDED")
    return {"observation_id": observation_id, "payload_hash": payload_hash, "read_only": True}


def open_consultant_case(conn, tenant: UUID, value, *, at: datetime | None = None) -> dict:
    spec = CaseSpec.model_validate(value)
    at = _utc(at or _now())
    _active_assignment(conn, tenant, spec.assignment_id, spec.opened_by, at)
    if spec.baseline_hash == spec.current_hash:
        raise ConsultantWorkflowError("CHANGE_REQUIRED")
    config = conn.execute(
        """SELECT status FROM resilience_v2.enterprise_configuration_versions
        WHERE tenant_id=%s AND config_id=%s""",
        (tenant, spec.config_id),
    ).fetchone()
    if config is None or config[0] not in ("ACTIVE", "RETIRED"):
        raise ConsultantWorkflowError("EFFECTIVE_CONFIGURATION_REQUIRED")
    rows = conn.execute(
        """SELECT observation_id,assignment_id FROM resilience_v2.consultant_source_observations
        WHERE tenant_id=%s AND observation_id = ANY(%s)""",
        (tenant, list(spec.observation_ids)),
    ).fetchall()
    if len(rows) != len(set(spec.observation_ids)) or any(row[1] != spec.assignment_id for row in rows):
        raise ConsultantWorkflowError("CASE_OBSERVATION_SCOPE_INVALID")
    case_id = uuid4()
    conn.execute(
        """INSERT INTO resilience_v2.consultant_cases
        VALUES (%s,%s,%s,%s,'CONSULTANT',%s,%s,%s,%s,%s,%s,%s,'NEW',%s,%s)""",
        (tenant, case_id, spec.assignment_id, spec.config_id, spec.title, spec.change_summary,
         spec.baseline_hash, spec.current_hash, spec.severity, spec.confidence_pct,
         spec.opened_by, at, at),
    )
    for observation_id in dict.fromkeys(spec.observation_ids):
        conn.execute(
            "INSERT INTO resilience_v2.consultant_case_observations VALUES (%s,%s,%s)",
            (tenant, case_id, observation_id),
        )
    _event(conn, tenant, case_id, spec.opened_by, "CASE_OPENED", {"observations": len(set(spec.observation_ids))}, at)
    return {"case_id": case_id, "status": "NEW", "operating_model": "CONSULTANT"}


def record_expert_assessment(conn, tenant: UUID, value, *, at: datetime | None = None) -> dict:
    spec = AssessmentSpec.model_validate(value)
    at = _utc(at or _now())
    case = conn.execute(
        """SELECT assignment_id,status FROM resilience_v2.consultant_cases
        WHERE tenant_id=%s AND case_id=%s FOR UPDATE""",
        (tenant, spec.case_id),
    ).fetchone()
    if case is None or case[1] not in ("NEW", "RETURNED"):
        raise ConsultantWorkflowError("CASE_NOT_ASSESSABLE")
    _active_assignment(conn, tenant, case[0], spec.assessed_by, at)
    assessment_id = uuid4()
    conn.execute(
        """INSERT INTO resilience_v2.consultant_expert_assessments
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (tenant, assessment_id, spec.case_id, spec.assessed_by, spec.disposition, spec.rationale,
         _json(list(spec.affected_dimensions)), _json(list(spec.evidence_refs)), at),
    )
    next_status = "CLOSED" if spec.disposition == "DISMISSED" else "ASSESSED"
    conn.execute(
        "UPDATE resilience_v2.consultant_cases SET status=%s,updated_at=%s WHERE tenant_id=%s AND case_id=%s",
        (next_status, at, tenant, spec.case_id),
    )
    _event(conn, tenant, spec.case_id, spec.assessed_by, "EXPERT_ASSESSMENT_RECORDED", {"disposition": spec.disposition}, at)
    return {"assessment_id": assessment_id, "status": next_status, "disposition": spec.disposition}


def create_change_proposal(conn, tenant: UUID, value, *, at: datetime | None = None) -> dict:
    spec = ProposalSpec.model_validate(value)
    at = _utc(at or _now())
    case = conn.execute(
        """SELECT assignment_id,status FROM resilience_v2.consultant_cases
        WHERE tenant_id=%s AND case_id=%s FOR UPDATE""",
        (tenant, spec.case_id),
    ).fetchone()
    if case is None or case[1] != "ASSESSED":
        raise ConsultantWorkflowError("ASSESSED_CASE_REQUIRED")
    _active_assignment(conn, tenant, case[0], spec.proposed_by, at)
    assessment = conn.execute(
        """SELECT disposition FROM resilience_v2.consultant_expert_assessments
        WHERE tenant_id=%s AND assessment_id=%s AND case_id=%s""",
        (tenant, spec.assessment_id, spec.case_id),
    ).fetchone()
    if assessment is None or assessment[0] == "DISMISSED":
        raise ConsultantWorkflowError("ACCEPTED_ASSESSMENT_REQUIRED")
    proposal_id = uuid4()
    conn.execute(
        """INSERT INTO resilience_v2.consultant_change_proposals
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'SUBMITTED',%s,%s)""",
        (tenant, proposal_id, spec.case_id, spec.assessment_id, spec.proposed_by,
         spec.implementation_mode, _json(list(spec.target_dimensions)), spec.recommended_change,
         spec.expected_outcome, spec.simulation_ref, spec.rollback_plan,
         _json(list(spec.evidence_refs)), at, at),
    )
    conn.execute(
        "UPDATE resilience_v2.consultant_cases SET status='AWAITING_CLIENT_DECISION',updated_at=%s WHERE tenant_id=%s AND case_id=%s",
        (at, tenant, spec.case_id),
    )
    _event(conn, tenant, spec.case_id, spec.proposed_by, "PROPOSAL_SUBMITTED", {"proposal_id": str(proposal_id), "mode": spec.implementation_mode}, at)
    return {"proposal_id": proposal_id, "status": "SUBMITTED", "client_decision_required": True}


def record_client_decision(
    conn, tenant: UUID, proposal_id: UUID, decided_by: UUID,
    decision: Literal["APPROVED", "REJECTED", "RETURNED"], evidence_ref: str,
    *, conditions: str = "None", at: datetime | None = None,
) -> dict:
    if not evidence_ref.strip():
        raise ConsultantWorkflowError("DECISION_EVIDENCE_REQUIRED")
    at = _utc(at or _now())
    proposal = conn.execute(
        """SELECT p.case_id,p.proposed_by,p.status,p.implementation_mode FROM resilience_v2.consultant_change_proposals p
        WHERE p.tenant_id=%s AND p.proposal_id=%s FOR UPDATE""",
        (tenant, proposal_id),
    ).fetchone()
    if proposal is None or proposal[2] != "SUBMITTED":
        raise ConsultantWorkflowError("SUBMITTED_PROPOSAL_REQUIRED")
    if proposal[1] == decided_by:
        raise ConsultantWorkflowError("CLIENT_DECISION_MUST_BE_INDEPENDENT")
    _require_client_authority(conn, tenant, decided_by, "CHANGE_PROPOSAL_DECISION", proposal[3], at)
    decision_id = uuid4()
    conn.execute(
        "INSERT INTO resilience_v2.consultant_client_decisions VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (tenant, decision_id, proposal_id, decided_by, decision, conditions, evidence_ref, at),
    )
    conn.execute(
        "UPDATE resilience_v2.consultant_change_proposals SET status=%s,updated_at=%s WHERE tenant_id=%s AND proposal_id=%s",
        (decision, at, tenant, proposal_id),
    )
    conn.execute(
        "UPDATE resilience_v2.consultant_cases SET status=%s,updated_at=%s WHERE tenant_id=%s AND case_id=%s",
        (decision, at, tenant, proposal[0]),
    )
    _event(conn, tenant, proposal[0], decided_by, "CLIENT_DECISION_RECORDED", {"decision": decision, "proposal_id": str(proposal_id)}, at)
    return {"decision_id": decision_id, "decision": decision, "proposal_status": decision}


def prepare_sandbox_execution(
    conn, tenant: UUID, proposal_id: UUID, prepared_by: UUID, action_type: str,
    target_ref: str, payload: dict, idempotency_key: str, *, mandate_id: UUID | None = None,
    at: datetime | None = None,
) -> dict:
    at = _utc(at or _now())
    if not all(value.strip() for value in (action_type, target_ref, idempotency_key)):
        raise ConsultantWorkflowError("EXECUTION_PACKAGE_FIELDS_REQUIRED")
    proposal = conn.execute(
        """SELECT p.case_id,p.implementation_mode,p.rollback_plan,p.status,c.assignment_id
        FROM resilience_v2.consultant_change_proposals p
        JOIN resilience_v2.consultant_cases c ON c.tenant_id=p.tenant_id AND c.case_id=p.case_id
        WHERE p.tenant_id=%s AND p.proposal_id=%s FOR UPDATE OF p,c""",
        (tenant, proposal_id),
    ).fetchone()
    if proposal is None or proposal[3] != "APPROVED":
        raise ConsultantWorkflowError("APPROVED_PROPOSAL_REQUIRED")
    _active_assignment(conn, tenant, proposal[4], prepared_by, at)
    if proposal[1] == "DELEGATED":
        if mandate_id is None:
            raise ConsultantWorkflowError("ACTIVE_DELEGATED_MANDATE_REQUIRED")
        mandate = conn.execute(
            """SELECT implementation_modes,action_scope FROM resilience_v2.client_service_mandates
            WHERE tenant_id=%s AND mandate_id=%s AND assignment_id=%s AND status='ACTIVE'
              AND effective_from <= %s AND expires_at > %s""",
            (tenant, mandate_id, proposal[4], at, at),
        ).fetchone()
        if (mandate is None or "DELEGATED" not in mandate[0]
                or action_type not in mandate[1].get("action_types", [])
                or target_ref not in mandate[1].get("targets", [])):
            raise ConsultantWorkflowError("ACTIVE_DELEGATED_MANDATE_REQUIRED")
    package_id = uuid4()
    inserted = conn.execute(
        """INSERT INTO resilience_v2.consultant_execution_packages
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,true,%s,NULL,NULL,0,'DRAFT',%s,%s)
        ON CONFLICT (tenant_id,idempotency_key) DO NOTHING RETURNING package_id""",
        (tenant, package_id, proposal_id, mandate_id, prepared_by, action_type, target_ref,
         _digest(payload), idempotency_key, proposal[2], at, at),
    ).fetchone()
    if inserted is None:
        raise ConsultantWorkflowError("EXECUTION_IDEMPOTENCY_CONFLICT")
    conn.execute(
        "UPDATE resilience_v2.consultant_change_proposals SET status='IMPLEMENTATION_PENDING',updated_at=%s WHERE tenant_id=%s AND proposal_id=%s",
        (at, tenant, proposal_id),
    )
    conn.execute(
        "UPDATE resilience_v2.consultant_cases SET status='IMPLEMENTATION_PENDING',updated_at=%s WHERE tenant_id=%s AND case_id=%s",
        (at, tenant, proposal[0]),
    )
    _event(conn, tenant, proposal[0], prepared_by, "SANDBOX_EXECUTION_PREPARED", {"package_id": str(package_id), "action_type": action_type}, at)
    return {"package_id": package_id, "status": "DRAFT", "sandbox_only": True, "live_actions": 0}


def preflight_sandbox_execution(
    conn, tenant: UUID, package_id: UUID, actor_id: UUID, evidence_ref: str,
    *, step_up_verified: bool, at: datetime | None = None,
) -> dict:
    if not evidence_ref.strip():
        raise ConsultantWorkflowError("PREFLIGHT_EVIDENCE_REQUIRED")
    at = _utc(at or _now())
    if not step_up_verified:
        raise ConsultantWorkflowError("STEP_UP_AUTHENTICATION_REQUIRED")
    row = conn.execute(
        """SELECT x.status,x.sandbox_only,x.live_actions,p.case_id,c.assignment_id
        FROM resilience_v2.consultant_execution_packages x
        JOIN resilience_v2.consultant_change_proposals p ON p.tenant_id=x.tenant_id AND p.proposal_id=x.proposal_id
        JOIN resilience_v2.consultant_cases c ON c.tenant_id=p.tenant_id AND c.case_id=p.case_id
        WHERE x.tenant_id=%s AND x.package_id=%s FOR UPDATE OF x""",
        (tenant, package_id),
    ).fetchone()
    if row is None or row[0] != "DRAFT" or not row[1] or row[2] != 0:
        raise ConsultantWorkflowError("SANDBOX_PREFLIGHT_REJECTED")
    _active_assignment(conn, tenant, row[4], actor_id, at)
    conn.execute(
        """UPDATE resilience_v2.consultant_execution_packages
        SET status='PREFLIGHT_PASSED',preflight_evidence_ref=%s,updated_at=%s
        WHERE tenant_id=%s AND package_id=%s""",
        (evidence_ref, at, tenant, package_id),
    )
    _event(conn, tenant, row[3], actor_id, "SANDBOX_PREFLIGHT_PASSED", {"package_id": str(package_id)}, at)
    return {"package_id": package_id, "status": "PREFLIGHT_PASSED", "live_actions": 0}


def execute_sandbox_package(conn, tenant: UUID, package_id: UUID, actor_id: UUID, result_evidence_ref: str, *, at: datetime | None = None) -> dict:
    if not result_evidence_ref.strip():
        raise ConsultantWorkflowError("EXECUTION_EVIDENCE_REQUIRED")
    at = _utc(at or _now())
    row = conn.execute(
        """SELECT x.status,x.sandbox_only,x.live_actions,x.proposal_id,p.case_id,c.assignment_id
        FROM resilience_v2.consultant_execution_packages x
        JOIN resilience_v2.consultant_change_proposals p ON p.tenant_id=x.tenant_id AND p.proposal_id=x.proposal_id
        JOIN resilience_v2.consultant_cases c ON c.tenant_id=p.tenant_id AND c.case_id=p.case_id
        WHERE x.tenant_id=%s AND x.package_id=%s FOR UPDATE OF x""",
        (tenant, package_id),
    ).fetchone()
    if row is None or row[0] != "PREFLIGHT_PASSED" or not row[1] or row[2] != 0:
        raise ConsultantWorkflowError("SANDBOX_EXECUTION_REJECTED")
    _active_assignment(conn, tenant, row[5], actor_id, at)
    conn.execute(
        """UPDATE resilience_v2.consultant_execution_packages
        SET status='EXECUTED',result_evidence_ref=%s,updated_at=%s
        WHERE tenant_id=%s AND package_id=%s""",
        (result_evidence_ref, at, tenant, package_id),
    )
    conn.execute(
        "UPDATE resilience_v2.consultant_change_proposals SET status='IMPLEMENTED',updated_at=%s WHERE tenant_id=%s AND proposal_id=%s",
        (at, tenant, row[3]),
    )
    conn.execute(
        "UPDATE resilience_v2.consultant_cases SET status='IMPLEMENTED',updated_at=%s WHERE tenant_id=%s AND case_id=%s",
        (at, tenant, row[4]),
    )
    _event(conn, tenant, row[4], actor_id, "SANDBOX_EXECUTED", {"package_id": str(package_id), "live_actions": 0}, at)
    return {"package_id": package_id, "status": "EXECUTED", "sandbox_only": True, "live_actions": 0}


def validate_implementation_outcome(
    conn, tenant: UUID, proposal_id: UUID, reviewed_by: UUID,
    outcome: Literal["MATCHED", "PARTIAL", "FAILED"], expected_metrics: dict,
    observed_metrics: dict, conclusion: str, evidence_refs: tuple[str, ...],
    *, at: datetime | None = None,
) -> dict:
    if not conclusion.strip() or not evidence_refs or any(not ref.strip() for ref in evidence_refs):
        raise ConsultantWorkflowError("REVIEW_EVIDENCE_REQUIRED")
    at = _utc(at or _now())
    proposal = conn.execute(
        """SELECT p.case_id,p.status,c.assignment_id FROM resilience_v2.consultant_change_proposals p
        JOIN resilience_v2.consultant_cases c ON c.tenant_id=p.tenant_id AND c.case_id=p.case_id
        WHERE p.tenant_id=%s AND p.proposal_id=%s FOR UPDATE OF p,c""",
        (tenant, proposal_id),
    ).fetchone()
    if proposal is None or proposal[1] != "IMPLEMENTED":
        raise ConsultantWorkflowError("IMPLEMENTED_PROPOSAL_REQUIRED")
    _active_assignment(conn, tenant, proposal[2], None, at)
    review_id = uuid4()
    conn.execute(
        """INSERT INTO resilience_v2.consultant_post_implementation_reviews
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (tenant, review_id, proposal[0], proposal_id, reviewed_by, outcome,
         _json(expected_metrics), _json(observed_metrics), conclusion, _json(list(evidence_refs)), at),
    )
    conn.execute(
        "UPDATE resilience_v2.consultant_change_proposals SET status='VALIDATED',updated_at=%s WHERE tenant_id=%s AND proposal_id=%s",
        (at, tenant, proposal_id),
    )
    conn.execute(
        "UPDATE resilience_v2.consultant_cases SET status='VALIDATED',updated_at=%s WHERE tenant_id=%s AND case_id=%s",
        (at, tenant, proposal[0]),
    )
    _event(conn, tenant, proposal[0], reviewed_by, "IMPLEMENTATION_OUTCOME_VALIDATED", {"review_id": str(review_id), "outcome": outcome}, at)
    return {"review_id": review_id, "outcome": outcome, "status": "VALIDATED"}


def consultant_work_queue(conn, consultant_principal_id: UUID, *, at: datetime | None = None) -> list[dict]:
    at = _utc(at or _now())
    rows = conn.execute(
        """SELECT a.tenant_id,a.assignment_id,t.name,count(c.case_id) FILTER
        (WHERE c.status NOT IN ('VALIDATED','CLOSED','REJECTED')) AS open_cases
        FROM resilience_v2.consultant_assignments a
        JOIN resilience_v2.tenants t ON t.tenant_id=a.tenant_id
        LEFT JOIN resilience_v2.consultant_cases c ON c.tenant_id=a.tenant_id AND c.assignment_id=a.assignment_id
        WHERE a.consultant_principal_id=%s AND a.status='ACTIVE'
          AND a.effective_from <= %s AND a.expires_at > %s
        GROUP BY a.tenant_id,a.assignment_id,t.name ORDER BY t.name""",
        (consultant_principal_id, at, at),
    ).fetchall()
    return [
        {"tenant_id": row[0], "assignment_id": row[1], "client_name": row[2], "open_cases": row[3]}
        for row in rows
    ]
