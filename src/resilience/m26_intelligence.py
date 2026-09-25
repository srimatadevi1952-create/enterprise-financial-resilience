"""M26 governed lessons learned and metadata-based case intelligence."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


LINK_TYPES = {"PROCESS", "RISK", "CONTROL", "SCENARIO", "CHANGE", "EVIDENCE", "JURISDICTION"}
CONTEXT_LINK_TYPES = {"PROCESS", "RISK", "CONTROL", "SCENARIO", "JURISDICTION"}


class CaseIntelligenceError(ValueError):
    pass


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("TIME_MUST_BE_TIMEZONE_AWARE")
    return value.astimezone(timezone.utc)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class LessonLinkSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    link_type: Literal["PROCESS", "RISK", "CONTROL", "SCENARIO", "CHANGE", "EVIDENCE", "JURISDICTION"]
    link_key: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def valid_key(self):
        if self.link_type == "JURISDICTION" and not re.fullmatch(r"[A-Z]{2}", self.link_key):
            raise ValueError("JURISDICTION_LINK_INVALID")
        return self


class LessonContentSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    title: str = Field(min_length=1, max_length=240)
    context: str = Field(min_length=1, max_length=8000)
    issue: str = Field(min_length=1, max_length=8000)
    approach: str = Field(min_length=1, max_length=8000)
    decision_summary: str = Field(min_length=1, max_length=8000)
    intervention: str = Field(min_length=1, max_length=8000)
    outcome: str = Field(min_length=1, max_length=8000)
    what_worked: str = Field(min_length=1, max_length=8000)
    what_failed: str = Field(min_length=1, max_length=8000)
    new_learning: str = Field(min_length=1, max_length=8000)
    applicable_context: str = Field(min_length=1, max_length=8000)
    limitations: str = Field(min_length=1, max_length=8000)
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    links: tuple[LessonLinkSpec, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_evidence_and_links(self):
        if any(not ref.strip() for ref in self.evidence_refs):
            raise ValueError("LESSON_EVIDENCE_REQUIRED")
        pairs = [(item.link_type, item.link_key) for item in self.links]
        if len(pairs) != len(set(pairs)):
            raise ValueError("LESSON_LINK_DUPLICATE")
        if not any(item.link_type == "EVIDENCE" for item in self.links):
            raise ValueError("EVIDENCE_LINK_REQUIRED")
        if not any(item.link_type in CONTEXT_LINK_TYPES for item in self.links):
            raise ValueError("CONTEXT_LINK_REQUIRED")
        return self


class LessonCaseSpec(LessonContentSpec):
    case_key: str = Field(min_length=1, max_length=160)
    source_type: Literal["CONSULTANT_CASE", "ENTERPRISE_CASE", "SIMULATION", "INTERVENTION"]
    source_ref: str = Field(min_length=1, max_length=500)
    source_case_id: UUID | None = None
    config_id: UUID
    operating_model: Literal["ENTERPRISE", "CONSULTANT"]
    sensitivity: Literal["INTERNAL", "CONFIDENTIAL", "RESTRICTED", "PRIVILEGED"]
    contains_personal_data: bool = False
    contains_privileged_information: bool = False
    retention_until: datetime
    author_actor_id: UUID

    @field_validator("retention_until")
    @classmethod
    def retention_aware(cls, value: datetime) -> datetime:
        return _utc(value)

    @model_validator(mode="after")
    def valid_sensitivity(self):
        if (self.source_type == "CONSULTANT_CASE") != (self.source_case_id is not None):
            raise ValueError("CONSULTANT_SOURCE_CASE_REQUIRED")
        if self.contains_privileged_information and self.sensitivity != "PRIVILEGED":
            raise ValueError("PRIVILEGED_SENSITIVITY_REQUIRED")
        if self.contains_personal_data and self.sensitivity not in ("RESTRICTED", "PRIVILEGED"):
            raise ValueError("PERSONAL_DATA_SENSITIVITY_REQUIRED")
        return self


def _require_actor(conn, tenant: UUID, actor_id: UUID):
    if conn.execute(
        "SELECT 1 FROM resilience_v2.actors WHERE tenant_id=%s AND actor_id=%s",
        (tenant, actor_id),
    ).fetchone() is None:
        raise CaseIntelligenceError("TENANT_ACTOR_REQUIRED")


def _require_authority(conn, tenant: UUID, actor_id: UUID, decision: str, at: datetime):
    rows = conn.execute(
        """SELECT authority_scope FROM resilience_v2.client_decision_authorities
        WHERE tenant_id=%s AND actor_id=%s AND status='ACTIVE'
          AND effective_from <= %s AND expires_at > %s""",
        (tenant, actor_id, at, at),
    ).fetchall()
    if not any(decision in row[0].get("decisions", []) for row in rows):
        raise CaseIntelligenceError("CASE_INTELLIGENCE_AUTHORITY_REQUIRED")


def _validate_links(conn, tenant: UUID, config_id: UUID, links: tuple[LessonLinkSpec, ...]):
    tables = {
        "PROCESS": ("enterprise_processes", "process_key"),
        "RISK": ("enterprise_risks", "risk_key"),
        "CONTROL": ("enterprise_controls", "control_key"),
    }
    for link in links:
        if link.link_type in tables:
            table, column = tables[link.link_type]
            if conn.execute(
                f"SELECT 1 FROM resilience_v2.{table} WHERE tenant_id=%s AND config_id=%s AND {column}=%s",
                (tenant, config_id, link.link_key),
            ).fetchone() is None:
                raise CaseIntelligenceError(f"{link.link_type}_LINK_UNKNOWN")


def _event(conn, tenant: UUID, case_id: UUID, version_id: UUID, actor_id: UUID, event_type: str, payload: dict, at: datetime):
    conn.execute(
        "INSERT INTO resilience_v2.knowledge_case_events VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (tenant, uuid4(), case_id, version_id, actor_id, event_type, _json(payload), at),
    )


def _insert_version(
    conn, tenant: UUID, case_id: UUID, version: int, author_actor_id: UUID,
    content: LessonContentSpec, at: datetime,
) -> UUID:
    _validate_links(conn, tenant, _case_config(conn, tenant, case_id), content.links)
    version_id = uuid4()
    conn.execute(
        """INSERT INTO resilience_v2.knowledge_lesson_versions
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL,'DRAFT',%s,%s)""",
        (tenant, version_id, case_id, version, content.title, content.context, content.issue,
         content.approach, content.decision_summary, content.intervention, content.outcome,
         content.what_worked, content.what_failed, content.new_learning,
         content.applicable_context, content.limitations, _json(list(content.evidence_refs)),
         author_actor_id, at, at),
    )
    for link in content.links:
        conn.execute(
            "INSERT INTO resilience_v2.knowledge_lesson_links VALUES (%s,%s,%s,%s)",
            (tenant, version_id, link.link_type, link.link_key),
        )
    return version_id


def _case_config(conn, tenant: UUID, case_id: UUID) -> UUID:
    row = conn.execute(
        "SELECT config_id FROM resilience_v2.knowledge_cases WHERE tenant_id=%s AND knowledge_case_id=%s",
        (tenant, case_id),
    ).fetchone()
    if row is None:
        raise CaseIntelligenceError("KNOWLEDGE_CASE_NOT_FOUND")
    return row[0]


def create_lesson_case(conn, tenant: UUID, value, *, at: datetime | None = None) -> dict:
    spec = LessonCaseSpec.model_validate(value)
    at = _utc(at or _now())
    if spec.retention_until <= at:
        raise CaseIntelligenceError("RETENTION_MUST_BE_FUTURE")
    _require_actor(conn, tenant, spec.author_actor_id)
    config = conn.execute(
        "SELECT status FROM resilience_v2.enterprise_configuration_versions WHERE tenant_id=%s AND config_id=%s",
        (tenant, spec.config_id),
    ).fetchone()
    if config is None or config[0] not in ("ACTIVE", "RETIRED"):
        raise CaseIntelligenceError("EFFECTIVE_CONFIGURATION_REQUIRED")
    if spec.source_case_id is not None:
        source = conn.execute(
            "SELECT 1 FROM resilience_v2.consultant_cases WHERE tenant_id=%s AND case_id=%s",
            (tenant, spec.source_case_id),
        ).fetchone()
        if source is None:
            raise CaseIntelligenceError("CONSULTANT_SOURCE_CASE_NOT_FOUND")
    _validate_links(conn, tenant, spec.config_id, spec.links)
    case_id = uuid4()
    conn.execute(
        """INSERT INTO resilience_v2.knowledge_cases
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (tenant, case_id, spec.case_key, spec.source_type, spec.source_ref, spec.source_case_id,
         spec.config_id, spec.operating_model, spec.sensitivity, spec.contains_personal_data,
         spec.contains_privileged_information, spec.retention_until, spec.author_actor_id, at),
    )
    content = LessonContentSpec.model_validate(spec.model_dump(include=set(LessonContentSpec.model_fields)))
    version_id = _insert_version(conn, tenant, case_id, 1, spec.author_actor_id, content, at)
    _event(conn, tenant, case_id, version_id, spec.author_actor_id, "DRAFT_CREATED", {"version": 1}, at)
    return {"knowledge_case_id": case_id, "version_id": version_id, "version": 1, "status": "DRAFT"}


def create_lesson_revision(
    conn, tenant: UUID, knowledge_case_id: UUID, author_actor_id: UUID, value,
    *, at: datetime | None = None,
) -> dict:
    content = LessonContentSpec.model_validate(value)
    at = _utc(at or _now())
    _require_actor(conn, tenant, author_actor_id)
    case = conn.execute(
        "SELECT retention_until FROM resilience_v2.knowledge_cases WHERE tenant_id=%s AND knowledge_case_id=%s",
        (tenant, knowledge_case_id),
    ).fetchone()
    if case is None or case[0] <= at:
        raise CaseIntelligenceError("ACTIVE_KNOWLEDGE_CASE_REQUIRED")
    latest = conn.execute(
        """SELECT max(version),array_agg(status) FROM resilience_v2.knowledge_lesson_versions
        WHERE tenant_id=%s AND knowledge_case_id=%s""",
        (tenant, knowledge_case_id),
    ).fetchone()
    if any(status in ("DRAFT", "IN_REVIEW", "APPROVED") for status in latest[1]):
        raise CaseIntelligenceError("OPEN_LESSON_VERSION_EXISTS")
    version = latest[0] + 1
    version_id = _insert_version(conn, tenant, knowledge_case_id, version, author_actor_id, content, at)
    _event(conn, tenant, knowledge_case_id, version_id, author_actor_id, "REVISION_CREATED", {"version": version}, at)
    return {"knowledge_case_id": knowledge_case_id, "version_id": version_id, "version": version, "status": "DRAFT"}


def submit_lesson_for_review(conn, tenant: UUID, version_id: UUID, actor_id: UUID, *, at: datetime | None = None) -> dict:
    at = _utc(at or _now())
    row = conn.execute(
        """SELECT knowledge_case_id,author_actor_id,status FROM resilience_v2.knowledge_lesson_versions
        WHERE tenant_id=%s AND version_id=%s FOR UPDATE""",
        (tenant, version_id),
    ).fetchone()
    if row is None or row[1] != actor_id or row[2] != "DRAFT":
        raise CaseIntelligenceError("AUTHOR_DRAFT_REQUIRED")
    conn.execute(
        "UPDATE resilience_v2.knowledge_lesson_versions SET status='IN_REVIEW',updated_at=%s WHERE tenant_id=%s AND version_id=%s",
        (at, tenant, version_id),
    )
    _event(conn, tenant, row[0], version_id, actor_id, "SUBMITTED_FOR_REVIEW", {}, at)
    return {"version_id": version_id, "status": "IN_REVIEW"}


def review_lesson(
    conn, tenant: UUID, version_id: UUID, reviewer_actor_id: UUID,
    decision: Literal["APPROVED", "RETURNED", "REJECTED"], rationale: str,
    *, at: datetime | None = None,
) -> dict:
    at = _utc(at or _now())
    if not rationale.strip():
        raise CaseIntelligenceError("REVIEW_RATIONALE_REQUIRED")
    _require_authority(conn, tenant, reviewer_actor_id, "REVIEW_CASE_INTELLIGENCE", at)
    row = conn.execute(
        """SELECT knowledge_case_id,author_actor_id,status FROM resilience_v2.knowledge_lesson_versions
        WHERE tenant_id=%s AND version_id=%s FOR UPDATE""",
        (tenant, version_id),
    ).fetchone()
    if row is None or row[2] != "IN_REVIEW":
        raise CaseIntelligenceError("LESSON_IN_REVIEW_REQUIRED")
    if row[1] == reviewer_actor_id:
        raise CaseIntelligenceError("INDEPENDENT_REVIEW_REQUIRED")
    conn.execute(
        """UPDATE resilience_v2.knowledge_lesson_versions
        SET status=%s,reviewer_actor_id=%s,updated_at=%s WHERE tenant_id=%s AND version_id=%s""",
        (decision, reviewer_actor_id, at, tenant, version_id),
    )
    review_id = uuid4()
    conn.execute(
        "INSERT INTO resilience_v2.knowledge_lesson_reviews VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (tenant, review_id, version_id, reviewer_actor_id, decision, rationale, at),
    )
    _event(conn, tenant, row[0], version_id, reviewer_actor_id, "REVIEW_RECORDED", {"decision": decision}, at)
    return {"review_id": review_id, "version_id": version_id, "status": decision}


def publish_lesson(conn, tenant: UUID, version_id: UUID, actor_id: UUID, *, at: datetime | None = None) -> dict:
    at = _utc(at or _now())
    _require_authority(conn, tenant, actor_id, "PUBLISH_CASE_INTELLIGENCE", at)
    row = conn.execute(
        """SELECT v.knowledge_case_id,v.status,v.reviewer_actor_id,c.retention_until
        FROM resilience_v2.knowledge_lesson_versions v
        JOIN resilience_v2.knowledge_cases c ON c.tenant_id=v.tenant_id AND c.knowledge_case_id=v.knowledge_case_id
        WHERE v.tenant_id=%s AND v.version_id=%s FOR UPDATE OF v""",
        (tenant, version_id),
    ).fetchone()
    if row is None or row[1] != "APPROVED" or row[2] is None:
        raise CaseIntelligenceError("APPROVED_REVIEWED_LESSON_REQUIRED")
    if row[3] <= at:
        raise CaseIntelligenceError("RETENTION_EXPIRED")
    previous = conn.execute(
        """SELECT version_id FROM resilience_v2.knowledge_lesson_versions
        WHERE tenant_id=%s AND knowledge_case_id=%s AND status='PUBLISHED' FOR UPDATE""",
        (tenant, row[0]),
    ).fetchone()
    if previous is not None:
        conn.execute(
            "UPDATE resilience_v2.knowledge_lesson_versions SET status='SUPERSEDED',updated_at=%s WHERE tenant_id=%s AND version_id=%s",
            (at, tenant, previous[0]),
        )
        _event(conn, tenant, row[0], previous[0], actor_id, "SUPERSEDED", {"replacement_version_id": str(version_id)}, at)
    conn.execute(
        "UPDATE resilience_v2.knowledge_lesson_versions SET status='PUBLISHED',updated_at=%s WHERE tenant_id=%s AND version_id=%s",
        (at, tenant, version_id),
    )
    _event(conn, tenant, row[0], version_id, actor_id, "PUBLISHED", {}, at)
    return {"version_id": version_id, "status": "PUBLISHED", "superseded_version_id": previous[0] if previous else None}


def withdraw_lesson(conn, tenant: UUID, version_id: UUID, actor_id: UUID, reason: str, *, at: datetime | None = None) -> dict:
    at = _utc(at or _now())
    if not reason.strip():
        raise CaseIntelligenceError("WITHDRAWAL_REASON_REQUIRED")
    _require_authority(conn, tenant, actor_id, "PUBLISH_CASE_INTELLIGENCE", at)
    row = conn.execute(
        """UPDATE resilience_v2.knowledge_lesson_versions SET status='WITHDRAWN',updated_at=%s
        WHERE tenant_id=%s AND version_id=%s AND status='PUBLISHED' RETURNING knowledge_case_id""",
        (at, tenant, version_id),
    ).fetchone()
    if row is None:
        raise CaseIntelligenceError("PUBLISHED_LESSON_REQUIRED")
    _event(conn, tenant, row[0], version_id, actor_id, "WITHDRAWN", {"reason": reason}, at)
    return {"version_id": version_id, "status": "WITHDRAWN"}


def grant_lesson_access(
    conn, tenant: UUID, knowledge_case_id: UUID, actor_id: UUID, granted_by: UUID,
    purpose: str, effective_from: datetime, expires_at: datetime, evidence_ref: str,
    *, at: datetime | None = None,
) -> dict:
    at = _utc(at or _now())
    effective_from, expires_at = _utc(effective_from), _utc(expires_at)
    _require_authority(conn, tenant, granted_by, "GRANT_CASE_INTELLIGENCE_ACCESS", at)
    _require_actor(conn, tenant, actor_id)
    if actor_id == granted_by or not purpose.strip() or not evidence_ref.strip():
        raise CaseIntelligenceError("ACCESS_GRANT_INVALID")
    if not (effective_from <= at < expires_at):
        raise CaseIntelligenceError("ACCESS_GRANT_NOT_EFFECTIVE")
    grant_id = uuid4()
    conn.execute(
        """INSERT INTO resilience_v2.knowledge_access_grants
        VALUES (%s,%s,%s,%s,%s,%s,'ACTIVE',%s,%s,%s,%s,%s)""",
        (tenant, grant_id, knowledge_case_id, actor_id, granted_by, purpose,
         effective_from, expires_at, evidence_ref, at, at),
    )
    version_id = conn.execute(
        """SELECT version_id FROM resilience_v2.knowledge_lesson_versions
        WHERE tenant_id=%s AND knowledge_case_id=%s ORDER BY version DESC LIMIT 1""",
        (tenant, knowledge_case_id),
    ).fetchone()[0]
    _event(
        conn, tenant, knowledge_case_id, version_id, granted_by, "ACCESS_GRANTED",
        {"grant_id": str(grant_id), "actor_id": str(actor_id), "purpose": purpose}, at,
    )
    return {"grant_id": grant_id, "status": "ACTIVE"}


def revoke_lesson_access(
    conn, tenant: UUID, grant_id: UUID, revoked_by: UUID, reason: str,
    *, at: datetime | None = None,
) -> dict:
    at = _utc(at or _now())
    if not reason.strip():
        raise CaseIntelligenceError("ACCESS_REVOCATION_REASON_REQUIRED")
    _require_authority(conn, tenant, revoked_by, "GRANT_CASE_INTELLIGENCE_ACCESS", at)
    row = conn.execute(
        """UPDATE resilience_v2.knowledge_access_grants SET status='REVOKED',updated_at=%s
        WHERE tenant_id=%s AND grant_id=%s AND status='ACTIVE'
        RETURNING knowledge_case_id,actor_id""",
        (at, tenant, grant_id),
    ).fetchone()
    if row is None:
        raise CaseIntelligenceError("ACTIVE_ACCESS_GRANT_REQUIRED")
    version_id = conn.execute(
        """SELECT version_id FROM resilience_v2.knowledge_lesson_versions
        WHERE tenant_id=%s AND knowledge_case_id=%s ORDER BY version DESC LIMIT 1""",
        (tenant, row[0]),
    ).fetchone()[0]
    _event(
        conn, tenant, row[0], version_id, revoked_by, "ACCESS_REVOKED",
        {"grant_id": str(grant_id), "actor_id": str(row[1]), "reason": reason}, at,
    )
    return {"grant_id": grant_id, "status": "REVOKED"}


def _can_access(conn, tenant: UUID, case_id: UUID, actor_id: UUID, at: datetime, *, audit: bool = False) -> bool:
    row = conn.execute(
        """SELECT c.sensitivity,c.created_by,v.author_actor_id,v.reviewer_actor_id,c.retention_until
        FROM resilience_v2.knowledge_cases c
        JOIN resilience_v2.knowledge_lesson_versions v
          ON v.tenant_id=c.tenant_id AND v.knowledge_case_id=c.knowledge_case_id
        WHERE c.tenant_id=%s AND c.knowledge_case_id=%s
        ORDER BY v.version DESC LIMIT 1""",
        (tenant, case_id),
    ).fetchone()
    if row is None or (row[4] <= at and not audit):
        return False
    if actor_id in (row[1], row[2], row[3]) or row[0] == "INTERNAL":
        return conn.execute(
            "SELECT 1 FROM resilience_v2.actors WHERE tenant_id=%s AND actor_id=%s",
            (tenant, actor_id),
        ).fetchone() is not None
    grant = conn.execute(
        """SELECT 1 FROM resilience_v2.knowledge_access_grants
        WHERE tenant_id=%s AND knowledge_case_id=%s AND actor_id=%s AND status='ACTIVE'
          AND effective_from <= %s AND expires_at > %s""",
        (tenant, case_id, actor_id, at, at),
    ).fetchone()
    if grant is not None:
        return True
    if audit:
        try:
            _require_authority(conn, tenant, actor_id, "AUDIT_CASE_INTELLIGENCE", at)
            return True
        except CaseIntelligenceError:
            pass
    return False


def _lesson_payload(conn, tenant: UUID, version_id: UUID) -> dict:
    row = conn.execute(
        """SELECT v.knowledge_case_id,v.version,v.title,v.context,v.issue,v.approach,
        v.decision_summary,v.intervention,v.outcome,v.what_worked,v.what_failed,v.new_learning,
        v.applicable_context,v.limitations,v.evidence_refs,v.status,v.reviewer_actor_id,
        c.case_key,c.source_type,c.source_ref,c.operating_model,c.sensitivity,c.retention_until
        FROM resilience_v2.knowledge_lesson_versions v
        JOIN resilience_v2.knowledge_cases c ON c.tenant_id=v.tenant_id AND c.knowledge_case_id=v.knowledge_case_id
        WHERE v.tenant_id=%s AND v.version_id=%s""",
        (tenant, version_id),
    ).fetchone()
    if row is None:
        raise CaseIntelligenceError("LESSON_VERSION_NOT_FOUND")
    links = conn.execute(
        "SELECT link_type,link_key FROM resilience_v2.knowledge_lesson_links WHERE tenant_id=%s AND version_id=%s ORDER BY link_type,link_key",
        (tenant, version_id),
    ).fetchall()
    return {
        "knowledge_case_id": row[0], "version_id": version_id, "version": row[1],
        "title": row[2], "context": row[3], "issue": row[4], "approach": row[5],
        "decision_summary": row[6], "intervention": row[7], "outcome": row[8],
        "what_worked": row[9], "what_failed": row[10], "new_learning": row[11],
        "applicable_context": row[12], "limitations": row[13], "evidence_refs": row[14],
        "status": row[15], "reviewer_actor_id": row[16], "case_key": row[17],
        "source_type": row[18], "source_ref": row[19], "operating_model": row[20],
        "sensitivity": row[21], "retention_until": row[22],
        "links": [{"link_type": item[0], "link_key": item[1]} for item in links],
        "advisory_only": True,
    }


def retrieve_lesson(
    conn, tenant: UUID, version_id: UUID, actor_id: UUID,
    *, purpose: Literal["DIRECT", "SEARCH", "RELATED_CASE", "CONSOLE", "AUDIT"] = "DIRECT",
    include_historical: bool = False, at: datetime | None = None,
) -> dict:
    at = _utc(at or _now())
    payload = _lesson_payload(conn, tenant, version_id)
    audit = include_historical or purpose == "AUDIT"
    if payload["status"] != "PUBLISHED" and not audit:
        raise CaseIntelligenceError("CURRENT_PUBLISHED_LESSON_REQUIRED")
    if not _can_access(conn, tenant, payload["knowledge_case_id"], actor_id, at, audit=audit):
        raise CaseIntelligenceError("LESSON_ACCESS_DENIED")
    conn.execute(
        "INSERT INTO resilience_v2.knowledge_access_events VALUES (%s,%s,%s,%s,%s,%s)",
        (tenant, uuid4(), version_id, actor_id, purpose, at),
    )
    return payload


def search_lessons(
    conn, tenant: UUID, actor_id: UUID, *, filters: dict[str, str] | None = None,
    at: datetime | None = None,
) -> list[dict]:
    at = _utc(at or _now())
    requested = {key.upper(): value for key, value in (filters or {}).items()}
    invalid = set(requested) - LINK_TYPES
    if invalid:
        raise CaseIntelligenceError("SEARCH_FILTER_INVALID")
    rows = conn.execute(
        """SELECT v.version_id,v.knowledge_case_id FROM resilience_v2.knowledge_lesson_versions v
        JOIN resilience_v2.knowledge_cases c ON c.tenant_id=v.tenant_id AND c.knowledge_case_id=v.knowledge_case_id
        WHERE v.tenant_id=%s AND v.status='PUBLISHED' AND c.retention_until > %s
        ORDER BY v.title,v.version_id""",
        (tenant, at),
    ).fetchall()
    results = []
    for version_id, case_id in rows:
        if not _can_access(conn, tenant, case_id, actor_id, at):
            continue
        links = set(conn.execute(
            "SELECT link_type,link_key FROM resilience_v2.knowledge_lesson_links WHERE tenant_id=%s AND version_id=%s",
            (tenant, version_id),
        ).fetchall())
        if not all((key, value) in links for key, value in requested.items()):
            continue
        payload = retrieve_lesson(conn, tenant, version_id, actor_id, purpose="SEARCH", at=at)
        results.append({
            "knowledge_case_id": case_id, "version_id": version_id, "title": payload["title"],
            "applicable_context": payload["applicable_context"], "limitations": payload["limitations"],
            "links": payload["links"], "advisory_only": True,
        })
    return results


def related_lessons(
    conn, tenant: UUID, version_id: UUID, actor_id: UUID,
    *, limit: int = 5, at: datetime | None = None,
) -> list[dict]:
    at = _utc(at or _now())
    if not 1 <= limit <= 20:
        raise CaseIntelligenceError("RELATED_LIMIT_INVALID")
    target = retrieve_lesson(conn, tenant, version_id, actor_id, purpose="RELATED_CASE", at=at)
    target_links = {(item["link_type"], item["link_key"]) for item in target["links"] if item["link_type"] in CONTEXT_LINK_TYPES}
    candidates = search_lessons(conn, tenant, actor_id, at=at)
    scored = []
    for item in candidates:
        if item["version_id"] == version_id:
            continue
        links = {(entry["link_type"], entry["link_key"]) for entry in item["links"]}
        score = len(target_links & links)
        if score:
            scored.append({**item, "metadata_match_score": score})
    return sorted(scored, key=lambda item: (-item["metadata_match_score"], item["title"]))[:limit]


def record_lesson_feedback(
    conn, tenant: UUID, version_id: UUID, actor_id: UUID,
    relevant: bool, useful: bool, comment: str, *, at: datetime | None = None,
) -> dict:
    at = _utc(at or _now())
    payload = _lesson_payload(conn, tenant, version_id)
    if payload["status"] != "PUBLISHED" or not _can_access(conn, tenant, payload["knowledge_case_id"], actor_id, at):
        raise CaseIntelligenceError("PUBLISHED_ACCESSIBLE_LESSON_REQUIRED")
    feedback_id = uuid4()
    row = conn.execute(
        """INSERT INTO resilience_v2.knowledge_lesson_feedback
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (tenant_id,version_id,actor_id) DO NOTHING RETURNING feedback_id""",
        (tenant, feedback_id, version_id, actor_id, relevant, useful, comment, at),
    ).fetchone()
    if row is None:
        raise CaseIntelligenceError("FEEDBACK_ALREADY_RECORDED")
    return {"feedback_id": feedback_id, "recorded": True}


def lesson_history(conn, tenant: UUID, knowledge_case_id: UUID, actor_id: UUID, *, at: datetime | None = None) -> list[dict]:
    at = _utc(at or _now())
    if not _can_access(conn, tenant, knowledge_case_id, actor_id, at, audit=True):
        raise CaseIntelligenceError("LESSON_AUDIT_ACCESS_DENIED")
    rows = conn.execute(
        """SELECT version_id,version,status,author_actor_id,reviewer_actor_id,created_at,updated_at
        FROM resilience_v2.knowledge_lesson_versions
        WHERE tenant_id=%s AND knowledge_case_id=%s ORDER BY version""",
        (tenant, knowledge_case_id),
    ).fetchall()
    return [
        {"version_id": row[0], "version": row[1], "status": row[2], "author_actor_id": row[3],
         "reviewer_actor_id": row[4], "created_at": row[5], "updated_at": row[6]}
        for row in rows
    ]


def knowledge_quality_metrics(conn, tenant: UUID) -> dict:
    versions = conn.execute(
        """SELECT count(*) FILTER (WHERE status='PUBLISHED'),
        count(*) FILTER (WHERE status='SUPERSEDED'),count(*) FILTER (WHERE status='WITHDRAWN')
        FROM resilience_v2.knowledge_lesson_versions WHERE tenant_id=%s""",
        (tenant,),
    ).fetchone()
    accesses = conn.execute(
        "SELECT count(*) FROM resilience_v2.knowledge_access_events WHERE tenant_id=%s",
        (tenant,),
    ).fetchone()[0]
    feedback = conn.execute(
        """SELECT count(*),count(*) FILTER (WHERE relevant),count(*) FILTER (WHERE useful)
        FROM resilience_v2.knowledge_lesson_feedback WHERE tenant_id=%s""",
        (tenant,),
    ).fetchone()
    return {
        "published": versions[0], "superseded": versions[1], "withdrawn": versions[2],
        "retrievals": accesses, "feedback_count": feedback[0],
        "relevance_pct": round(100 * feedback[1] / feedback[0], 2) if feedback[0] else None,
        "usefulness_pct": round(100 * feedback[2] / feedback[0], 2) if feedback[0] else None,
    }
