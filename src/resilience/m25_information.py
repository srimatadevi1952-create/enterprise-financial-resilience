"""M25 authorised sources, information obligations and evidence confidence."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .m24_consultant import record_source_observation


DIMENSIONS = {"CAPITAL", "LIQUIDITY", "OPERATIONS", "REGULATION", "MERCHANTS", "CORRIDORS"}


class InformationGovernanceError(ValueError):
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


class DataSourceSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    assignment_id: UUID | None = None
    operating_model: Literal["ENTERPRISE", "CONSULTANT"]
    source_key: str = Field(min_length=1, max_length=160)
    source_type: Literal["API", "SFTP", "BANK_FEED", "ERP", "DOCUMENT_REPOSITORY", "CLIENT_AGENT", "MANUAL"]
    purpose: str = Field(min_length=1, max_length=240)
    data_scope: dict
    collection_schedule: str = Field(min_length=1, max_length=240)
    owner_actor_id: UUID
    authorized_by: UUID
    credential_ref: str = Field(min_length=1, max_length=500)
    jurisdiction: str = Field(pattern=r"^[A-Z]{2}$")
    effective_from: datetime
    expires_at: datetime
    evidence_ref: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def valid_source(self):
        if (self.operating_model == "CONSULTANT") != (self.assignment_id is not None):
            raise ValueError("SOURCE_ASSIGNMENT_MODEL_MISMATCH")
        if _utc(self.expires_at) <= _utc(self.effective_from):
            raise ValueError("SOURCE_PERIOD_INVALID")
        if not self.credential_ref.startswith(("vault:", "secret-ref:", "none:")):
            raise ValueError("MANAGED_CREDENTIAL_REFERENCE_REQUIRED")
        if not self.data_scope:
            raise ValueError("DATA_SCOPE_REQUIRED")
        return self


class ObligationDefinitionSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    config_id: UUID
    source_id: UUID | None = None
    obligation_key: str = Field(min_length=1, max_length=160)
    version: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=240)
    item_type: Literal["DOCUMENT", "CONFIRMATION", "FILING", "DATA_SUBMISSION"]
    operating_model: Literal["ENTERPRISE", "CONSULTANT"]
    responsible_contact_actor_id: UUID
    internal_owner_actor_id: UUID
    first_due_at: datetime
    recurrence_days: int | None = Field(default=None, gt=0, le=3650)
    reminder_lead_hours: int = Field(ge=0, le=8760)
    escalation_after_hours: int = Field(ge=0, le=8760)
    freshness_limit_hours: int = Field(gt=0, le=87600)
    jurisdiction: str = Field(pattern=r"^[A-Z]{2}$")
    regulatory_dependency: bool
    exposure_linked: bool
    affected_dimension: str | None = None
    risk_increment: int = Field(ge=0, le=10)
    effective_from: datetime
    evidence_ref: str = Field(min_length=1, max_length=500)

    @field_validator("first_due_at", "effective_from")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        return _utc(value)

    @model_validator(mode="after")
    def valid_exposure(self):
        if self.exposure_linked:
            if self.affected_dimension not in DIMENSIONS or self.risk_increment <= 0:
                raise ValueError("EXPOSURE_LINK_REQUIRED")
        elif self.affected_dimension is not None or self.risk_increment != 0:
            raise ValueError("NON_EXPOSURE_CANNOT_RAISE_RISK")
        if self.operating_model == "CONSULTANT" and self.source_id is None:
            raise ValueError("CONSULTANT_OBLIGATION_SOURCE_REQUIRED")
        return self


class ConfidenceRuleSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    rule_key: str = Field(min_length=1, max_length=160)
    version: int = Field(gt=0)
    completeness_weight_pct: float = Field(ge=0, le=100)
    freshness_weight_pct: float = Field(ge=0, le=100)
    reliability_weight_pct: float = Field(ge=0, le=100)
    established_threshold_pct: float = Field(ge=0, le=100)
    effective_from: datetime
    evidence_ref: str = Field(min_length=1, max_length=500)

    @field_validator("effective_from")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        return _utc(value)

    @model_validator(mode="after")
    def weights_total(self):
        total = self.completeness_weight_pct + self.freshness_weight_pct + self.reliability_weight_pct
        if abs(total - 100.0) > 0.0001:
            raise ValueError("CONFIDENCE_WEIGHTS_MUST_TOTAL_100")
        return self


def _require_client_authority(conn, tenant: UUID, actor_id: UUID, decision: str, at: datetime):
    rows = conn.execute(
        """SELECT authority_id,authority_scope FROM resilience_v2.client_decision_authorities
        WHERE tenant_id=%s AND actor_id=%s AND status='ACTIVE'
          AND effective_from <= %s AND expires_at > %s""",
        (tenant, actor_id, at, at),
    ).fetchall()
    for authority_id, scope in rows:
        if decision in scope.get("decisions", []):
            return authority_id
    raise InformationGovernanceError("CLIENT_INFORMATION_AUTHORITY_REQUIRED")


def _source_event(conn, tenant: UUID, source_id: UUID, actor_id: UUID, event_type: str, payload: dict, at: datetime):
    event_id = uuid4()
    conn.execute(
        "INSERT INTO resilience_v2.data_source_events VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (tenant, event_id, source_id, actor_id, event_type, _json(payload), at),
    )
    return event_id


def register_data_source(conn, tenant: UUID, value, *, at: datetime | None = None) -> dict:
    spec = DataSourceSpec.model_validate(value)
    at = _utc(at or _now())
    if not (spec.effective_from <= at < spec.expires_at):
        raise InformationGovernanceError("SOURCE_NOT_EFFECTIVE")
    _require_client_authority(conn, tenant, spec.authorized_by, "AUTHORIZE_DATA_SOURCE", at)
    if spec.operating_model == "CONSULTANT":
        assignment = conn.execute(
            """SELECT consultant_actor_id,permitted_purposes,authority_scope,effective_from,expires_at
            FROM resilience_v2.consultant_assignments
            WHERE tenant_id=%s AND assignment_id=%s AND status='ACTIVE'
              AND effective_from <= %s AND expires_at > %s""",
            (tenant, spec.assignment_id, at, at),
        ).fetchone()
        if assignment is None:
            raise InformationGovernanceError("ACTIVE_CONSULTANT_ASSIGNMENT_REQUIRED")
        if spec.purpose not in assignment[1] or spec.source_key not in assignment[2].get("sources", []):
            raise InformationGovernanceError("SOURCE_OUTSIDE_ASSIGNMENT_SCOPE")
        if spec.effective_from < assignment[3] or spec.expires_at > assignment[4]:
            raise InformationGovernanceError("SOURCE_EXCEEDS_ASSIGNMENT_PERIOD")
    source_id = uuid4()
    conn.execute(
        """INSERT INTO resilience_v2.authorized_data_sources
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'ACTIVE',%s,%s,%s,NULL,%s,%s)""",
        (tenant, source_id, spec.assignment_id, spec.operating_model, spec.source_key,
         spec.source_type, spec.purpose, _json(spec.data_scope), spec.collection_schedule,
         spec.owner_actor_id, spec.authorized_by, spec.credential_ref, spec.jurisdiction,
         spec.effective_from, spec.expires_at, spec.evidence_ref, at, at),
    )
    _source_event(conn, tenant, source_id, spec.authorized_by, "SOURCE_AUTHORIZED", {"operating_model": spec.operating_model}, at)
    return {"source_id": source_id, "source_key": spec.source_key, "status": "ACTIVE", "operating_model": spec.operating_model}


def revoke_data_source(conn, tenant: UUID, source_id: UUID, actor_id: UUID, reason: str, *, at: datetime | None = None) -> dict:
    at = _utc(at or _now())
    if not reason.strip():
        raise InformationGovernanceError("REVOCATION_REASON_REQUIRED")
    _require_client_authority(conn, tenant, actor_id, "AUTHORIZE_DATA_SOURCE", at)
    row = conn.execute(
        """UPDATE resilience_v2.authorized_data_sources SET status='REVOKED',updated_at=%s
        WHERE tenant_id=%s AND source_id=%s AND status IN ('ACTIVE','SUSPENDED') RETURNING source_id""",
        (at, tenant, source_id),
    ).fetchone()
    if row is None:
        raise InformationGovernanceError("ACTIVE_SOURCE_REQUIRED")
    _source_event(conn, tenant, source_id, actor_id, "SOURCE_REVOKED", {"reason": reason}, at)
    return {"source_id": source_id, "status": "REVOKED"}


def ingest_authorized_observation(
    conn, tenant: UUID, source_id: UUID, source_record_key: str, payload: dict,
    *, observed_at: datetime, effective_at: datetime, schema_version: str,
    lineage_ref: str, quality_status: str, reconciliation_status: str,
) -> dict:
    observed_at = _utc(observed_at)
    source = conn.execute(
        """SELECT assignment_id,operating_model,source_key FROM resilience_v2.authorized_data_sources
        WHERE tenant_id=%s AND source_id=%s AND status='ACTIVE'
          AND effective_from <= %s AND expires_at > %s""",
        (tenant, source_id, observed_at, observed_at),
    ).fetchone()
    if source is None:
        raise InformationGovernanceError("ACTIVE_SOURCE_REQUIRED")
    if source[1] != "CONSULTANT":
        raise InformationGovernanceError("CONSULTANT_OBSERVATION_SOURCE_REQUIRED")
    result = record_source_observation(
        conn,
        tenant,
        {
            "assignment_id": source[0],
            "source_key": source[2],
            "source_record_key": source_record_key,
            "observed_at": observed_at,
            "effective_at": effective_at,
            "schema_version": schema_version,
            "payload": payload,
            "lineage_ref": lineage_ref,
            "quality_status": quality_status,
            "reconciliation_status": reconciliation_status,
        },
    )
    conn.execute(
        "INSERT INTO resilience_v2.source_observation_links VALUES (%s,%s,%s,%s)",
        (tenant, source_id, result["observation_id"], observed_at),
    )
    conn.execute(
        "UPDATE resilience_v2.authorized_data_sources SET last_successful_at=%s,updated_at=%s WHERE tenant_id=%s AND source_id=%s",
        (observed_at, observed_at, tenant, source_id),
    )
    owner = conn.execute(
        "SELECT owner_actor_id FROM resilience_v2.authorized_data_sources WHERE tenant_id=%s AND source_id=%s",
        (tenant, source_id),
    ).fetchone()[0]
    _source_event(conn, tenant, source_id, owner, "COLLECTION_SUCCEEDED", {"observation_id": str(result["observation_id"])}, observed_at)
    return {**result, "source_id": source_id, "authorized": True}


def _obligation_event(conn, tenant: UUID, obligation_id: UUID, actor_id: UUID, event_type: str, payload: dict, at: datetime):
    event_id = uuid4()
    conn.execute(
        "INSERT INTO resilience_v2.information_obligation_events VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (tenant, event_id, obligation_id, actor_id, event_type, _json(payload), at),
    )
    return event_id


def register_information_obligation(conn, tenant: UUID, value, *, at: datetime | None = None) -> dict:
    spec = ObligationDefinitionSpec.model_validate(value)
    at = _utc(at or _now())
    config = conn.execute(
        "SELECT status FROM resilience_v2.enterprise_configuration_versions WHERE tenant_id=%s AND config_id=%s",
        (tenant, spec.config_id),
    ).fetchone()
    if config is None or config[0] not in ("ACTIVE", "RETIRED"):
        raise InformationGovernanceError("EFFECTIVE_CONFIGURATION_REQUIRED")
    if spec.source_id is not None:
        source = conn.execute(
            """SELECT operating_model,status FROM resilience_v2.authorized_data_sources
            WHERE tenant_id=%s AND source_id=%s""",
            (tenant, spec.source_id),
        ).fetchone()
        if source is None or source != (spec.operating_model, "ACTIVE"):
            raise InformationGovernanceError("OBLIGATION_SOURCE_INVALID")
    active = conn.execute(
        """SELECT definition_id,version,effective_from FROM resilience_v2.information_obligation_definitions
        WHERE tenant_id=%s AND obligation_key=%s AND status='ACTIVE' FOR UPDATE""",
        (tenant, spec.obligation_key),
    ).fetchone()
    if active is not None:
        if spec.version <= active[1] or spec.effective_from <= active[2]:
            raise InformationGovernanceError("OBLIGATION_VERSION_NOT_AFTER_ACTIVE")
        conn.execute(
            "UPDATE resilience_v2.information_obligation_definitions SET status='RETIRED',updated_at=%s WHERE tenant_id=%s AND definition_id=%s",
            (at, tenant, active[0]),
        )
    definition_id, obligation_id = uuid4(), uuid4()
    conn.execute(
        """INSERT INTO resilience_v2.information_obligation_definitions
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'ACTIVE',%s,%s,%s,%s)""",
        (tenant, definition_id, spec.config_id, spec.source_id, spec.obligation_key, spec.version,
         spec.title, spec.item_type, spec.operating_model, spec.responsible_contact_actor_id,
         spec.internal_owner_actor_id, spec.recurrence_days, spec.reminder_lead_hours,
         spec.escalation_after_hours, spec.freshness_limit_hours, spec.jurisdiction,
         spec.regulatory_dependency, spec.exposure_linked, spec.affected_dimension,
         spec.risk_increment, spec.effective_from, spec.evidence_ref, at, at),
    )
    conn.execute(
        """INSERT INTO resilience_v2.information_obligations
        VALUES (%s,%s,%s,1,%s,'REQUESTED',NULL,%s,%s)""",
        (tenant, obligation_id, definition_id, spec.first_due_at, at, at),
    )
    _obligation_event(conn, tenant, obligation_id, spec.internal_owner_actor_id, "REQUESTED", {"due_at": spec.first_due_at.isoformat()}, at)
    return {"definition_id": definition_id, "obligation_id": obligation_id, "occurrence": 1, "status": "REQUESTED"}


def _communication(
    conn, tenant: UUID, obligation_id: UUID, recipient: UUID, communication_type: str,
    template_key: str, idempotency_key: str, scheduled_for: datetime, at: datetime,
) -> bool:
    row = conn.execute(
        """INSERT INTO resilience_v2.information_communications
        VALUES (%s,%s,%s,%s,%s,'IN_APP',%s,%s,%s,%s)
        ON CONFLICT (tenant_id,idempotency_key) DO NOTHING RETURNING communication_id""",
        (tenant, uuid4(), obligation_id, recipient, communication_type, template_key,
         idempotency_key, scheduled_for, at),
    ).fetchone()
    return row is not None


def process_obligation_timers(conn, tenant: UUID, *, as_of: datetime) -> dict:
    as_of = _utc(as_of)
    rows = conn.execute(
        """SELECT o.obligation_id,o.due_at,o.status,d.responsible_contact_actor_id,
        d.internal_owner_actor_id,d.reminder_lead_hours,d.escalation_after_hours
        FROM resilience_v2.information_obligations o
        JOIN resilience_v2.information_obligation_definitions d
          ON d.tenant_id=o.tenant_id AND d.definition_id=o.definition_id
        WHERE o.tenant_id=%s AND o.status IN ('REQUESTED','OVERDUE')
        ORDER BY o.due_at,o.obligation_id FOR UPDATE OF o""",
        (tenant,),
    ).fetchall()
    reminders = escalations = overdue = 0
    for obligation_id, due_at, status, contact, owner, lead_hours, escalation_hours in rows:
        reminder_at = due_at - timedelta(hours=lead_hours)
        if status == "REQUESTED" and reminder_at <= as_of <= due_at:
            reminders += int(_communication(
                conn, tenant, obligation_id, contact, "REMINDER", "information-due",
                f"{obligation_id}:REMINDER:{due_at.isoformat()}", reminder_at, as_of,
            ))
        if status == "REQUESTED" and as_of > due_at:
            conn.execute(
                "UPDATE resilience_v2.information_obligations SET status='OVERDUE',updated_at=%s WHERE tenant_id=%s AND obligation_id=%s",
                (as_of, tenant, obligation_id),
            )
            _obligation_event(conn, tenant, obligation_id, owner, "OVERDUE", {"due_at": due_at.isoformat()}, as_of)
            status = "OVERDUE"
            overdue += 1
        escalation_at = due_at + timedelta(hours=escalation_hours)
        if status == "OVERDUE" and as_of >= escalation_at:
            escalations += int(_communication(
                conn, tenant, obligation_id, owner, "ESCALATION", "information-overdue",
                f"{obligation_id}:ESCALATION:{due_at.isoformat()}", escalation_at, as_of,
            ))
    return {"reminders": reminders, "new_overdue": overdue, "escalations": escalations}


def receive_information(
    conn, tenant: UUID, obligation_id: UUID, submitted_by: UUID, evidence_ref: str,
    content: dict, completeness_pct: float, reliability_pct: float, *, received_at: datetime,
) -> dict:
    received_at = _utc(received_at)
    if not evidence_ref.strip() or not 0 <= completeness_pct <= 100 or not 0 <= reliability_pct <= 100:
        raise InformationGovernanceError("RECEIPT_INVALID")
    row = conn.execute(
        """SELECT status FROM resilience_v2.information_obligations
        WHERE tenant_id=%s AND obligation_id=%s FOR UPDATE""",
        (tenant, obligation_id),
    ).fetchone()
    if row is None or row[0] not in ("REQUESTED", "OVERDUE", "REJECTED"):
        raise InformationGovernanceError("OBLIGATION_NOT_RECEIVABLE")
    receipt_id = uuid4()
    conn.execute(
        "INSERT INTO resilience_v2.information_receipts VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (tenant, receipt_id, obligation_id, submitted_by, received_at, evidence_ref,
         _digest(content), completeness_pct, reliability_pct),
    )
    conn.execute(
        """UPDATE resilience_v2.information_obligations
        SET status='RECEIVED',current_receipt_id=%s,updated_at=%s
        WHERE tenant_id=%s AND obligation_id=%s""",
        (receipt_id, received_at, tenant, obligation_id),
    )
    _obligation_event(conn, tenant, obligation_id, submitted_by, "RECEIVED", {"receipt_id": str(receipt_id)}, received_at)
    return {"receipt_id": receipt_id, "obligation_id": obligation_id, "status": "RECEIVED"}


def validate_information(
    conn, tenant: UUID, obligation_id: UUID, validator_actor_id: UUID,
    decision: Literal["VALIDATED", "REJECTED"], reason: str, *, at: datetime | None = None,
) -> dict:
    at = _utc(at or _now())
    if not reason.strip():
        raise InformationGovernanceError("VALIDATION_REASON_REQUIRED")
    row = conn.execute(
        """SELECT o.status,o.definition_id,o.occurrence,o.due_at,d.recurrence_days
        FROM resilience_v2.information_obligations o
        JOIN resilience_v2.information_obligation_definitions d
          ON d.tenant_id=o.tenant_id AND d.definition_id=o.definition_id
        WHERE o.tenant_id=%s AND o.obligation_id=%s FOR UPDATE OF o""",
        (tenant, obligation_id),
    ).fetchone()
    if row is None or row[0] != "RECEIVED":
        raise InformationGovernanceError("RECEIVED_OBLIGATION_REQUIRED")
    conn.execute(
        "UPDATE resilience_v2.information_obligations SET status=%s,updated_at=%s WHERE tenant_id=%s AND obligation_id=%s",
        (decision, at, tenant, obligation_id),
    )
    _obligation_event(conn, tenant, obligation_id, validator_actor_id, decision, {"reason": reason}, at)
    next_obligation_id = None
    if decision == "VALIDATED" and row[4] is not None:
        next_obligation_id = uuid4()
        next_due = row[3] + timedelta(days=row[4])
        conn.execute(
            """INSERT INTO resilience_v2.information_obligations
            VALUES (%s,%s,%s,%s,%s,'REQUESTED',NULL,%s,%s)""",
            (tenant, next_obligation_id, row[1], row[2] + 1, next_due, at, at),
        )
        _obligation_event(conn, tenant, next_obligation_id, validator_actor_id, "REQUESTED", {"due_at": next_due.isoformat(), "recurring": True}, at)
    return {"obligation_id": obligation_id, "status": decision, "next_obligation_id": next_obligation_id}


def waive_information_obligation(
    conn, tenant: UUID, obligation_id: UUID, authorized_by: UUID,
    reason: str, evidence_ref: str, *, at: datetime | None = None,
) -> dict:
    at = _utc(at or _now())
    if not reason.strip() or not evidence_ref.strip():
        raise InformationGovernanceError("WAIVER_REASON_AND_EVIDENCE_REQUIRED")
    _require_client_authority(conn, tenant, authorized_by, "WAIVE_INFORMATION_OBLIGATION", at)
    row = conn.execute(
        """UPDATE resilience_v2.information_obligations SET status='WAIVED',updated_at=%s
        WHERE tenant_id=%s AND obligation_id=%s AND status IN ('REQUESTED','OVERDUE','REJECTED')
        RETURNING obligation_id""",
        (at, tenant, obligation_id),
    ).fetchone()
    if row is None:
        raise InformationGovernanceError("OBLIGATION_NOT_WAIVABLE")
    _obligation_event(
        conn, tenant, obligation_id, authorized_by, "WAIVED",
        {"reason": reason, "evidence_ref": evidence_ref}, at,
    )
    return {"obligation_id": obligation_id, "status": "WAIVED"}


def register_confidence_rule(conn, tenant: UUID, value, *, at: datetime | None = None) -> dict:
    spec = ConfidenceRuleSpec.model_validate(value)
    at = _utc(at or _now())
    active = conn.execute(
        """SELECT rule_id,version,effective_from FROM resilience_v2.evidence_confidence_rules
        WHERE tenant_id=%s AND rule_key=%s AND status='ACTIVE' FOR UPDATE""",
        (tenant, spec.rule_key),
    ).fetchone()
    if active is not None:
        if spec.version <= active[1] or spec.effective_from <= active[2]:
            raise InformationGovernanceError("CONFIDENCE_RULE_VERSION_NOT_AFTER_ACTIVE")
        conn.execute(
            "UPDATE resilience_v2.evidence_confidence_rules SET status='RETIRED' WHERE tenant_id=%s AND rule_id=%s",
            (tenant, active[0]),
        )
    rule_id = uuid4()
    conn.execute(
        """INSERT INTO resilience_v2.evidence_confidence_rules
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'ACTIVE',%s,%s,%s)""",
        (tenant, rule_id, spec.rule_key, spec.version, spec.completeness_weight_pct,
         spec.freshness_weight_pct, spec.reliability_weight_pct,
         spec.established_threshold_pct, spec.effective_from, spec.evidence_ref, at),
    )
    return {"rule_id": rule_id, "version": spec.version, "status": "ACTIVE"}


def assess_evidence_confidence(
    conn, tenant: UUID, obligation_id: UUID, rule_id: UUID,
    risk_severity_before: int, *, as_of: datetime,
) -> dict:
    as_of = _utc(as_of)
    if not 0 <= risk_severity_before <= 10:
        raise InformationGovernanceError("RISK_SEVERITY_INVALID")
    row = conn.execute(
        """SELECT o.status,o.due_at,o.current_receipt_id,d.freshness_limit_hours,
        d.exposure_linked,d.risk_increment,d.affected_dimension
        FROM resilience_v2.information_obligations o
        JOIN resilience_v2.information_obligation_definitions d
          ON d.tenant_id=o.tenant_id AND d.definition_id=o.definition_id
        WHERE o.tenant_id=%s AND o.obligation_id=%s""",
        (tenant, obligation_id),
    ).fetchone()
    rule = conn.execute(
        """SELECT completeness_weight_pct,freshness_weight_pct,reliability_weight_pct,
        established_threshold_pct,status FROM resilience_v2.evidence_confidence_rules
        WHERE tenant_id=%s AND rule_id=%s""",
        (tenant, rule_id),
    ).fetchone()
    if row is None or rule is None or rule[4] != "ACTIVE":
        raise InformationGovernanceError("ACTIVE_OBLIGATION_AND_RULE_REQUIRED")
    completeness = reliability = freshness = 0.0
    evidence_refs: list[str] = []
    if row[2] is not None:
        receipt = conn.execute(
            """SELECT received_at,evidence_ref,completeness_pct,reliability_pct
            FROM resilience_v2.information_receipts
            WHERE tenant_id=%s AND receipt_id=%s""",
            (tenant, row[2]),
        ).fetchone()
        age_hours = max(0.0, (as_of - receipt[0]).total_seconds() / 3600)
        freshness = max(0.0, 100.0 * (1.0 - age_hours / row[3]))
        completeness, reliability = float(receipt[2]), float(receipt[3])
        evidence_refs.append(receipt[1])
    confidence = round(
        completeness * float(rule[0]) / 100
        + freshness * float(rule[1]) / 100
        + reliability * float(rule[2]) / 100,
        2,
    )
    material_gap = row[0] in ("OVERDUE", "REJECTED") or (row[0] != "VALIDATED" and as_of > row[1])
    exposure_affected = bool(row[4] and material_gap)
    risk_after = min(10, risk_severity_before + row[5]) if exposure_affected else risk_severity_before
    if row[0] == "VALIDATED" and confidence >= float(rule[3]):
        facts_status = "ESTABLISHED"
    elif confidence > 0:
        facts_status = "QUALIFIED"
    else:
        facts_status = "INSUFFICIENT"
    rationale = (
        "A defined exposure is affected by overdue or rejected information."
        if exposure_affected
        else "Evidence confidence changed without an automatic risk-severity increase."
    )
    assessment_id = uuid4()
    conn.execute(
        """INSERT INTO resilience_v2.evidence_confidence_assessments
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (tenant, assessment_id, obligation_id, rule_id, completeness, freshness, reliability,
         confidence, risk_severity_before, risk_after, exposure_affected, facts_status,
         rationale, _json(evidence_refs), as_of),
    )
    return {
        "assessment_id": assessment_id,
        "risk_severity": risk_after,
        "confidence_pct": confidence,
        "facts_status": facts_status,
        "exposure_affected": exposure_affected,
        "affected_dimension": row[6],
    }


def information_work_queue(conn, tenant: UUID, actor_id: UUID) -> list[dict]:
    rows = conn.execute(
        """SELECT o.obligation_id,d.title,o.due_at,o.status,d.operating_model,d.regulatory_dependency
        FROM resilience_v2.information_obligations o
        JOIN resilience_v2.information_obligation_definitions d
          ON d.tenant_id=o.tenant_id AND d.definition_id=o.definition_id
        WHERE o.tenant_id=%s AND o.status NOT IN ('VALIDATED','WAIVED')
          AND (d.responsible_contact_actor_id=%s OR d.internal_owner_actor_id=%s)
        ORDER BY o.due_at,o.obligation_id""",
        (tenant, actor_id, actor_id),
    ).fetchall()
    return [
        {"obligation_id": row[0], "title": row[1], "due_at": row[2], "status": row[3],
         "operating_model": row[4], "regulatory_dependency": row[5]}
        for row in rows
    ]


def consultant_information_queue(conn, consultant_principal_id: UUID, *, as_of: datetime) -> list[dict]:
    as_of = _utc(as_of)
    rows = conn.execute(
        """SELECT s.tenant_id,t.name,o.obligation_id,d.title,o.due_at,o.status
        FROM resilience_v2.consultant_assignments a
        JOIN resilience_v2.authorized_data_sources s
          ON s.tenant_id=a.tenant_id AND s.assignment_id=a.assignment_id
        JOIN resilience_v2.information_obligation_definitions d
          ON d.tenant_id=s.tenant_id AND d.source_id=s.source_id AND d.status='ACTIVE'
        JOIN resilience_v2.information_obligations o
          ON o.tenant_id=d.tenant_id AND o.definition_id=d.definition_id
        JOIN resilience_v2.tenants t ON t.tenant_id=s.tenant_id
        WHERE a.consultant_principal_id=%s AND a.status='ACTIVE'
          AND a.effective_from <= %s AND a.expires_at > %s
          AND s.status='ACTIVE' AND o.status NOT IN ('VALIDATED','WAIVED')
        ORDER BY o.due_at,t.name""",
        (consultant_principal_id, as_of, as_of),
    ).fetchall()
    return [
        {"tenant_id": row[0], "client_name": row[1], "obligation_id": row[2],
         "title": row[3], "due_at": row[4], "status": row[5]}
        for row in rows
    ]


def executive_evidence_summary(conn, tenant: UUID) -> dict:
    counts = conn.execute(
        """SELECT count(*) FILTER (WHERE status='OVERDUE'),
        count(*) FILTER (WHERE status='REJECTED'),
        count(*) FILTER (WHERE status NOT IN ('VALIDATED','WAIVED'))
        FROM resilience_v2.information_obligations WHERE tenant_id=%s""",
        (tenant,),
    ).fetchone()
    latest = conn.execute(
        """SELECT DISTINCT ON (obligation_id) confidence_pct,facts_status,exposure_affected
        FROM resilience_v2.evidence_confidence_assessments WHERE tenant_id=%s
        ORDER BY obligation_id,calculated_at DESC,assessment_id DESC""",
        (tenant,),
    ).fetchall()
    low_confidence = sum(1 for row in latest if row[1] != "ESTABLISHED")
    material_gaps = sum(1 for row in latest if row[2])
    disclosures = []
    if low_confidence:
        disclosures.append(f"{low_confidence} assessment(s) are qualified or have insufficient evidence.")
    if material_gaps:
        disclosures.append(f"{material_gaps} evidence gap(s) affect a defined risk exposure.")
    return {
        "overdue": counts[0],
        "rejected": counts[1],
        "open_obligations": counts[2],
        "low_confidence_assessments": low_confidence,
        "material_exposure_gaps": material_gaps,
        "disclosures": disclosures,
        "established_facts_only": low_confidence == 0,
    }
