"""M23 enterprise configuration contracts and persistence service."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .m2_fixture import did


class EnterpriseConfigurationError(ValueError):
    pass


class EntitySpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    key: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    entity_type: Literal["GROUP", "LEGAL_ENTITY", "BUSINESS_UNIT", "OPERATING_UNIT"]
    jurisdiction: str = Field(pattern=r"^[A-Z]{2}$")
    parent_key: str | None = None


class ProcessSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    key: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    owner_actor_id: UUID
    criticality: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    service_target_minutes: int = Field(gt=0, le=525_600)
    parent_key: str | None = None


class RiskSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    key: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=80)
    owner_actor_id: UUID
    inherent_likelihood: int = Field(ge=1, le=5)
    inherent_impact: int = Field(ge=1, le=5)
    tolerance_score: int = Field(ge=1, le=25)


class ControlSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    key: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    control_type: Literal["PREVENTIVE", "DETECTIVE", "CORRECTIVE", "RECOVERY"]
    owner_actor_id: UUID
    frequency: str = Field(min_length=1, max_length=80)
    status: Literal["DESIGNED", "ACTIVE", "SUSPENDED", "RETIRED"] = "ACTIVE"


class ProcessRiskSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    process_key: str
    risk_key: str
    exposure_weight_pct: float = Field(gt=0, le=100)


class RiskControlSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    risk_key: str
    control_key: str
    effectiveness_pct: float = Field(ge=0, le=100)


class DependencySpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    upstream_process_key: str
    downstream_process_key: str
    dependency_type: Literal["DATA", "FUNDING", "SERVICE", "CONTROL", "REGULATORY"]
    criticality: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class EnterpriseConfigurationSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    profile_key: str = Field(min_length=1, max_length=80)
    version: int = Field(gt=0)
    legal_name: str = Field(min_length=1, max_length=200)
    industry: str = Field(min_length=1, max_length=120)
    base_currency: str = Field(pattern=r"^[A-Z]{3}$")
    owner_actor_id: UUID
    effective_from: datetime
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    entities: tuple[EntitySpec, ...] = Field(min_length=1)
    processes: tuple[ProcessSpec, ...] = Field(min_length=1)
    risks: tuple[RiskSpec, ...] = Field(min_length=1)
    controls: tuple[ControlSpec, ...] = Field(min_length=1)
    process_risks: tuple[ProcessRiskSpec, ...] = Field(min_length=1)
    risk_controls: tuple[RiskControlSpec, ...] = Field(min_length=1)
    dependencies: tuple[DependencySpec, ...] = ()

    @field_validator("effective_from")
    @classmethod
    def timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("EFFECTIVE_FROM_MUST_BE_TIMEZONE_AWARE")
        return value.astimezone(timezone.utc)

    @field_validator("evidence_refs")
    @classmethod
    def nonempty_evidence(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not item.strip() for item in value):
            raise ValueError("EVIDENCE_REFERENCE_REQUIRED")
        return value

    @model_validator(mode="after")
    def coherent_graph(self):
        entity_keys = _unique_keys(self.entities, "entity")
        process_keys = _unique_keys(self.processes, "process")
        risk_keys = _unique_keys(self.risks, "risk")
        control_keys = _unique_keys(self.controls, "control")

        _validate_parents(self.entities, entity_keys, "entity")
        _validate_parents(self.processes, process_keys, "process")

        for mapping in self.process_risks:
            _require(mapping.process_key, process_keys, "PROCESS_REFERENCE_UNKNOWN")
            _require(mapping.risk_key, risk_keys, "RISK_REFERENCE_UNKNOWN")
        for mapping in self.risk_controls:
            _require(mapping.risk_key, risk_keys, "RISK_REFERENCE_UNKNOWN")
            _require(mapping.control_key, control_keys, "CONTROL_REFERENCE_UNKNOWN")
        for dependency in self.dependencies:
            _require(dependency.upstream_process_key, process_keys, "PROCESS_REFERENCE_UNKNOWN")
            _require(dependency.downstream_process_key, process_keys, "PROCESS_REFERENCE_UNKNOWN")
            if dependency.upstream_process_key == dependency.downstream_process_key:
                raise ValueError("PROCESS_SELF_DEPENDENCY")

        _unique_pairs(
            ((item.process_key, item.risk_key) for item in self.process_risks),
            "PROCESS_RISK_MAPPING_DUPLICATE",
        )
        _unique_pairs(
            ((item.risk_key, item.control_key) for item in self.risk_controls),
            "RISK_CONTROL_MAPPING_DUPLICATE",
        )
        _unique_pairs(
            ((item.upstream_process_key, item.downstream_process_key) for item in self.dependencies),
            "PROCESS_DEPENDENCY_DUPLICATE",
        )
        return self


def _unique_keys(items, label: str) -> set[str]:
    keys = [item.key for item in items]
    if len(keys) != len(set(keys)):
        raise ValueError(f"{label.upper()}_KEY_DUPLICATE")
    return set(keys)


def _validate_parents(items, keys: set[str], label: str):
    parent_by_key = {item.key: item.parent_key for item in items}
    for key, parent in parent_by_key.items():
        if parent is not None:
            _require(parent, keys, f"{label.upper()}_PARENT_UNKNOWN")
            if parent == key:
                raise ValueError(f"{label.upper()}_SELF_PARENT")
    for start in parent_by_key:
        seen: set[str] = set()
        current: str | None = start
        while current is not None:
            if current in seen:
                raise ValueError(f"{label.upper()}_PARENT_CYCLE")
            seen.add(current)
            current = parent_by_key[current]


def _require(value: str, allowed: set[str], message: str):
    if value not in allowed:
        raise ValueError(message)


def _unique_pairs(pairs, message: str):
    values = list(pairs)
    if len(values) != len(set(values)):
        raise ValueError(message)


def _parent_order(items):
    pending = {item.key: item for item in items}
    emitted: set[str] = set()
    ordered = []
    while pending:
        available = sorted(
            (item for item in pending.values() if item.parent_key is None or item.parent_key in emitted),
            key=lambda item: item.key,
        )
        if not available:
            raise EnterpriseConfigurationError("PARENT_GRAPH_UNRESOLVED")
        for item in available:
            ordered.append(item)
            emitted.add(item.key)
            del pending[item.key]
    return ordered


def register_enterprise_configuration(conn, tenant: UUID, value) -> dict:
    spec = EnterpriseConfigurationSpec.model_validate(value)
    config_id = did(f"{tenant}:enterprise-config:{spec.profile_key}:v{spec.version}")
    created_at = datetime.now(timezone.utc)
    evidence = json.dumps(list(spec.evidence_refs))

    conn.execute(
        """INSERT INTO resilience_v2.enterprise_configuration_versions
        (tenant_id,config_id,profile_key,version,legal_name,industry,base_currency,owner_actor_id,
         effective_from,effective_to,status,evidence_refs,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL,'DRAFT',%s,%s)""",
        (
            tenant,
            config_id,
            spec.profile_key,
            spec.version,
            spec.legal_name,
            spec.industry,
            spec.base_currency,
            spec.owner_actor_id,
            spec.effective_from,
            evidence,
            created_at,
        ),
    )

    entity_ids = {item.key: did(f"{config_id}:entity:{item.key}") for item in spec.entities}
    for item in _parent_order(spec.entities):
        conn.execute(
            "INSERT INTO resilience_v2.enterprise_entities VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                tenant,
                config_id,
                entity_ids[item.key],
                item.key,
                item.name,
                item.entity_type,
                item.jurisdiction,
                entity_ids.get(item.parent_key),
            ),
        )

    process_ids = {item.key: did(f"{config_id}:process:{item.key}") for item in spec.processes}
    for item in _parent_order(spec.processes):
        conn.execute(
            "INSERT INTO resilience_v2.enterprise_processes VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                tenant,
                config_id,
                process_ids[item.key],
                item.key,
                item.name,
                item.owner_actor_id,
                item.criticality,
                item.service_target_minutes,
                process_ids.get(item.parent_key),
            ),
        )

    risk_ids = {item.key: did(f"{config_id}:risk:{item.key}") for item in spec.risks}
    for item in spec.risks:
        conn.execute(
            "INSERT INTO resilience_v2.enterprise_risks VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                tenant,
                config_id,
                risk_ids[item.key],
                item.key,
                item.name,
                item.category,
                item.owner_actor_id,
                item.inherent_likelihood,
                item.inherent_impact,
                item.tolerance_score,
            ),
        )

    control_ids = {item.key: did(f"{config_id}:control:{item.key}") for item in spec.controls}
    for item in spec.controls:
        conn.execute(
            "INSERT INTO resilience_v2.enterprise_controls VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                tenant,
                config_id,
                control_ids[item.key],
                item.key,
                item.name,
                item.control_type,
                item.owner_actor_id,
                item.frequency,
                item.status,
            ),
        )

    for item in spec.process_risks:
        mapping_id = did(f"{config_id}:process-risk:{item.process_key}:{item.risk_key}")
        conn.execute(
            "INSERT INTO resilience_v2.process_risk_mappings VALUES (%s,%s,%s,%s,%s,%s)",
            (tenant, config_id, mapping_id, process_ids[item.process_key], risk_ids[item.risk_key], item.exposure_weight_pct),
        )

    for item in spec.risk_controls:
        mapping_id = did(f"{config_id}:risk-control:{item.risk_key}:{item.control_key}")
        conn.execute(
            "INSERT INTO resilience_v2.risk_control_mappings VALUES (%s,%s,%s,%s,%s,%s)",
            (tenant, config_id, mapping_id, risk_ids[item.risk_key], control_ids[item.control_key], item.effectiveness_pct),
        )

    for item in spec.dependencies:
        dependency_id = did(
            f"{config_id}:dependency:{item.upstream_process_key}:{item.downstream_process_key}"
        )
        conn.execute(
            "INSERT INTO resilience_v2.process_dependencies VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (
                tenant,
                config_id,
                dependency_id,
                process_ids[item.upstream_process_key],
                process_ids[item.downstream_process_key],
                item.dependency_type,
                item.criticality,
            ),
        )

    conn.execute(
        "UPDATE resilience_v2.enterprise_configuration_versions SET status='VALIDATED' WHERE tenant_id=%s AND config_id=%s",
        (tenant, config_id),
    )
    return {
        "config_id": config_id,
        "profile_key": spec.profile_key,
        "version": spec.version,
        "status": "VALIDATED",
        "entities": len(spec.entities),
        "processes": len(spec.processes),
        "risks": len(spec.risks),
        "controls": len(spec.controls),
        "dependencies": len(spec.dependencies),
    }


def activate_enterprise_configuration(conn, tenant: UUID, config_id: UUID) -> dict:
    candidate = conn.execute(
        """SELECT profile_key,version,effective_from,status
        FROM resilience_v2.enterprise_configuration_versions
        WHERE tenant_id=%s AND config_id=%s FOR UPDATE""",
        (tenant, config_id),
    ).fetchone()
    if candidate is None:
        raise EnterpriseConfigurationError("CONFIGURATION_NOT_FOUND")
    profile_key, version, effective_from, status = candidate
    if status != "VALIDATED":
        raise EnterpriseConfigurationError("CONFIGURATION_NOT_VALIDATED")

    active = conn.execute(
        """SELECT config_id,version,effective_from FROM resilience_v2.enterprise_configuration_versions
        WHERE tenant_id=%s AND profile_key=%s AND status='ACTIVE' FOR UPDATE""",
        (tenant, profile_key),
    ).fetchone()
    if active is not None:
        active_id, active_version, active_from = active
        if version <= active_version:
            raise EnterpriseConfigurationError("VERSION_NOT_AFTER_ACTIVE_VERSION")
        if effective_from <= active_from:
            raise EnterpriseConfigurationError("EFFECTIVE_DATE_NOT_AFTER_ACTIVE_VERSION")
        conn.execute(
            """UPDATE resilience_v2.enterprise_configuration_versions
            SET status='RETIRED',effective_to=%s WHERE tenant_id=%s AND config_id=%s""",
            (effective_from, tenant, active_id),
        )

    conn.execute(
        "UPDATE resilience_v2.enterprise_configuration_versions SET status='ACTIVE' WHERE tenant_id=%s AND config_id=%s",
        (tenant, config_id),
    )
    return {"config_id": config_id, "profile_key": profile_key, "version": version, "status": "ACTIVE"}


def resolve_enterprise_configuration(conn, tenant: UUID, profile_key: str, as_of: datetime) -> dict:
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise EnterpriseConfigurationError("AS_OF_MUST_BE_TIMEZONE_AWARE")
    row = conn.execute(
        """SELECT config_id,version,status,effective_from,effective_to
        FROM resilience_v2.enterprise_configuration_versions
        WHERE tenant_id=%s AND profile_key=%s
          AND status IN ('ACTIVE','RETIRED')
          AND effective_from <= %s
          AND (effective_to IS NULL OR effective_to > %s)
        ORDER BY version DESC LIMIT 1""",
        (tenant, profile_key, as_of, as_of),
    ).fetchone()
    if row is None:
        raise EnterpriseConfigurationError("NO_EFFECTIVE_CONFIGURATION")
    return {
        "config_id": row[0],
        "version": row[1],
        "status": row[2],
        "effective_from": row[3],
        "effective_to": row[4],
    }


def example_enterprise_spec(actor_id: UUID, *, variant: Literal["payments", "advisory"] = "payments"):
    effective = datetime(2026, 10, 1, tzinfo=timezone.utc)
    if variant == "advisory":
        return EnterpriseConfigurationSpec(
            profile_key="ADVISORY-GROUP",
            version=1,
            legal_name="Example Advisory Group",
            industry="Professional Services",
            base_currency="GBP",
            owner_actor_id=actor_id,
            effective_from=effective,
            evidence_refs=("onboarding:advisory:approved",),
            entities=(
                EntitySpec(key="GROUP", name="Advisory Group", entity_type="GROUP", jurisdiction="GB"),
                EntitySpec(key="SG-UNIT", name="Singapore Advisory Unit", entity_type="BUSINESS_UNIT", jurisdiction="SG", parent_key="GROUP"),
            ),
            processes=(
                ProcessSpec(key="CLIENT-ONBOARDING", name="Client onboarding", owner_actor_id=actor_id, criticality="HIGH", service_target_minutes=2880),
                ProcessSpec(key="REGULATORY-FILING", name="Regulatory filing", owner_actor_id=actor_id, criticality="CRITICAL", service_target_minutes=1440),
            ),
            risks=(
                RiskSpec(key="MISSING-EVIDENCE", name="Missing client evidence", category="COMPLIANCE", owner_actor_id=actor_id, inherent_likelihood=4, inherent_impact=4, tolerance_score=6),
            ),
            controls=(
                ControlSpec(key="EVIDENCE-CHECK", name="Mandatory evidence completeness check", control_type="PREVENTIVE", owner_actor_id=actor_id, frequency="PER_CASE"),
            ),
            process_risks=(
                ProcessRiskSpec(process_key="REGULATORY-FILING", risk_key="MISSING-EVIDENCE", exposure_weight_pct=100),
            ),
            risk_controls=(
                RiskControlSpec(risk_key="MISSING-EVIDENCE", control_key="EVIDENCE-CHECK", effectiveness_pct=70),
            ),
            dependencies=(
                DependencySpec(upstream_process_key="CLIENT-ONBOARDING", downstream_process_key="REGULATORY-FILING", dependency_type="DATA", criticality="HIGH"),
            ),
        )

    return EnterpriseConfigurationSpec(
        profile_key="PAYMENTS-GROUP",
        version=1,
        legal_name="Example Payments Group",
        industry="Payments",
        base_currency="INR",
        owner_actor_id=actor_id,
        effective_from=effective,
        evidence_refs=("onboarding:payments:approved", "process-register:v1"),
        entities=(
            EntitySpec(key="GROUP", name="Payments Group", entity_type="GROUP", jurisdiction="IN"),
            EntitySpec(key="UK-PAY", name="UK Payments", entity_type="LEGAL_ENTITY", jurisdiction="GB", parent_key="GROUP"),
            EntitySpec(key="SG-TREASURY", name="Singapore Treasury", entity_type="BUSINESS_UNIT", jurisdiction="SG", parent_key="GROUP"),
        ),
        processes=(
            ProcessSpec(key="PAYMENT", name="Payment processing", owner_actor_id=actor_id, criticality="CRITICAL", service_target_minutes=5),
            ProcessSpec(key="SETTLEMENT", name="Merchant settlement", owner_actor_id=actor_id, criticality="CRITICAL", service_target_minutes=1440, parent_key="PAYMENT"),
            ProcessSpec(key="LIQUIDITY", name="Liquidity management", owner_actor_id=actor_id, criticality="CRITICAL", service_target_minutes=60),
            ProcessSpec(key="FILING", name="Regulatory filing", owner_actor_id=actor_id, criticality="HIGH", service_target_minutes=2880),
        ),
        risks=(
            RiskSpec(key="GATEWAY-OUTAGE", name="Payment gateway outage", category="OPERATIONS", owner_actor_id=actor_id, inherent_likelihood=3, inherent_impact=5, tolerance_score=6),
            RiskSpec(key="LIQUIDITY-SHORTFALL", name="Intraday liquidity shortfall", category="LIQUIDITY", owner_actor_id=actor_id, inherent_likelihood=3, inherent_impact=5, tolerance_score=5),
            RiskSpec(key="FILING-DELAY", name="Regulatory filing delay", category="REGULATION", owner_actor_id=actor_id, inherent_likelihood=2, inherent_impact=4, tolerance_score=4),
            RiskSpec(key="FX-DISLOCATION", name="FX market dislocation", category="CORRIDOR", owner_actor_id=actor_id, inherent_likelihood=3, inherent_impact=4, tolerance_score=6),
        ),
        controls=(
            ControlSpec(key="GATEWAY-FAILOVER", name="Gateway failover", control_type="RECOVERY", owner_actor_id=actor_id, frequency="CONTINUOUS"),
            ControlSpec(key="SETTLEMENT-RECON", name="Settlement reconciliation", control_type="DETECTIVE", owner_actor_id=actor_id, frequency="DAILY"),
            ControlSpec(key="LIQUIDITY-BUFFER", name="Minimum liquidity buffer", control_type="PREVENTIVE", owner_actor_id=actor_id, frequency="CONTINUOUS"),
            ControlSpec(key="FILING-CALENDAR", name="Regulatory filing calendar", control_type="PREVENTIVE", owner_actor_id=actor_id, frequency="DAILY"),
            ControlSpec(key="FX-LIMIT", name="Currency exposure limit", control_type="PREVENTIVE", owner_actor_id=actor_id, frequency="CONTINUOUS"),
        ),
        process_risks=(
            ProcessRiskSpec(process_key="PAYMENT", risk_key="GATEWAY-OUTAGE", exposure_weight_pct=100),
            ProcessRiskSpec(process_key="SETTLEMENT", risk_key="LIQUIDITY-SHORTFALL", exposure_weight_pct=80),
            ProcessRiskSpec(process_key="LIQUIDITY", risk_key="FX-DISLOCATION", exposure_weight_pct=75),
            ProcessRiskSpec(process_key="FILING", risk_key="FILING-DELAY", exposure_weight_pct=100),
        ),
        risk_controls=(
            RiskControlSpec(risk_key="GATEWAY-OUTAGE", control_key="GATEWAY-FAILOVER", effectiveness_pct=75),
            RiskControlSpec(risk_key="LIQUIDITY-SHORTFALL", control_key="LIQUIDITY-BUFFER", effectiveness_pct=80),
            RiskControlSpec(risk_key="LIQUIDITY-SHORTFALL", control_key="SETTLEMENT-RECON", effectiveness_pct=55),
            RiskControlSpec(risk_key="FILING-DELAY", control_key="FILING-CALENDAR", effectiveness_pct=85),
            RiskControlSpec(risk_key="FX-DISLOCATION", control_key="FX-LIMIT", effectiveness_pct=70),
        ),
        dependencies=(
            DependencySpec(upstream_process_key="PAYMENT", downstream_process_key="SETTLEMENT", dependency_type="DATA", criticality="CRITICAL"),
            DependencySpec(upstream_process_key="LIQUIDITY", downstream_process_key="SETTLEMENT", dependency_type="FUNDING", criticality="CRITICAL"),
            DependencySpec(upstream_process_key="SETTLEMENT", downstream_process_key="FILING", dependency_type="REGULATORY", criticality="HIGH"),
        ),
    )
