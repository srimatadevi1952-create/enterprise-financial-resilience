"""M28 enterprise-specific calibration, scenario matching and governed reuse.

The numerical routines are intentionally dependency-free so a calibration can
be reproduced from its governed observation set.  Calibrations are candidates
until independently approved; precedent responses are always advisory and
must pass a current-state validation simulation before an authorised decision.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from statistics import mean
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


CONTROL_NAMES = (
    "Capital", "Liquidity", "Operations", "Regulation", "Merchants", "Countries & Corridors",
)


class ScenarioIntelligenceError(ValueError):
    pass


def _json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("TIME_MUST_BE_TIMEZONE_AWARE")
    return value.astimezone(timezone.utc)


class VariableDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    variable_id: str = Field(min_length=1, max_length=80)
    control: Literal["Capital", "Liquidity", "Operations", "Regulation", "Merchants", "Countries & Corridors"]
    value_kind: Literal["BOUNDED", "COUNT", "POSITIVE", "CONTINUOUS", "EMPIRICAL"]
    prior_weight: float = Field(gt=0, le=1)
    lower_bound: float | None = None
    upper_bound: float | None = None

    @model_validator(mode="after")
    def valid_bounds(self):
        if self.value_kind == "BOUNDED":
            if self.lower_bound is None or self.upper_bound is None or self.upper_bound <= self.lower_bound:
                raise ValueError("BOUNDED_VARIABLE_RANGE_REQUIRED")
        return self


class DependencyDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    left_control: Literal["Capital", "Liquidity", "Operations", "Regulation", "Merchants", "Countries & Corridors"]
    right_control: Literal["Capital", "Liquidity", "Operations", "Regulation", "Merchants", "Countries & Corridors"]

    @model_validator(mode="after")
    def distinct(self):
        if self.left_control == self.right_control:
            raise ValueError("DEPENDENCY_SELF_LINK_PROHIBITED")
        return self


class HistoricalObservation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    observed_at: datetime
    controls: dict[str, float]
    variables: dict[str, float]
    probability: float = Field(ge=0, le=10)
    impact: float = Field(ge=0, le=10)
    resilience: float = Field(ge=0, le=100)
    quality_status: Literal["ESTABLISHED", "QUALIFIED", "REJECTED"]
    lineage_ref: str = Field(min_length=1, max_length=500)

    @field_validator("observed_at")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        return _utc(value)

    @field_validator("controls")
    @classmethod
    def all_controls(cls, value: dict[str, float]) -> dict[str, float]:
        if set(value) != set(CONTROL_NAMES) or any(v < 0 or v > 100 for v in value.values()):
            raise ValueError("CONTROL_VECTOR_INVALID")
        return value


class CalibrationRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    enterprise_id: UUID
    config_id: UUID
    model_key: str = Field(min_length=1, max_length=160)
    version: str = Field(min_length=1, max_length=40)
    created_by: UUID
    variables: tuple[VariableDefinition, ...] = Field(min_length=1)
    dependencies: tuple[DependencyDefinition, ...] = ()
    observations: tuple[HistoricalObservation, ...] = Field(min_length=12)
    ridge_penalty: float = Field(default=0.05, gt=0, le=10)

    @model_validator(mode="after")
    def valid_history(self):
        ids = [item.variable_id for item in self.variables]
        if len(ids) != len(set(ids)):
            raise ValueError("VARIABLE_DEFINITION_DUPLICATE")
        established = [item for item in self.observations if item.quality_status == "ESTABLISHED"]
        if len(established) < 12:
            raise ValueError("INSUFFICIENT_ESTABLISHED_HISTORY")
        if {item.control for item in self.variables} != set(CONTROL_NAMES):
            raise ValueError("ALL_CONTROL_VARIABLES_REQUIRED")
        if any(set(item.variables) != set(ids) for item in established):
            raise ValueError("HISTORICAL_VARIABLE_VECTOR_INVALID")
        if len({item.lineage_ref for item in established}) != len(established):
            raise ValueError("HISTORICAL_LINEAGE_DUPLICATE")
        return self


class ScenarioChange(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    variable_id: str = Field(min_length=1, max_length=80)
    control: str = Field(min_length=1, max_length=80)
    baseline_value: float
    scenario_value: float
    weight: float = Field(gt=0, le=1)


class ScenarioSignature(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    enterprise_id: UUID
    config_id: UUID
    calibration_id: UUID
    model_version: str = Field(min_length=1, max_length=80)
    baseline_hash: str = Field(min_length=8, max_length=128)
    source: Literal["LIVE", "SIMULATION"]
    changes: tuple[ScenarioChange, ...] = Field(min_length=1)
    dependencies: tuple[str, ...] = ()
    jurisdictions: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    as_of: datetime

    @field_validator("as_of")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        return _utc(value)


def _solve(matrix: list[list[float]], vector: list[float]) -> list[float]:
    n = len(vector)
    augmented = [matrix[i][:] + [vector[i]] for i in range(n)]
    for column in range(n):
        pivot = max(range(column, n), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            augmented[pivot][column] = 1e-12
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        scale = augmented[column][column]
        augmented[column] = [value / scale for value in augmented[column]]
        for row in range(n):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [a - factor * b for a, b in zip(augmented[row], augmented[column])]
    return [augmented[i][-1] for i in range(n)]


def _ridge_fit(rows: list[list[float]], targets: list[float], penalty: float) -> list[float]:
    columns = len(rows[0])
    gram = [[sum(row[i] * row[j] for row in rows) for j in range(columns)] for i in range(columns)]
    rhs = [sum(row[i] * target for row, target in zip(rows, targets)) for i in range(columns)]
    for index in range(1, columns):  # never penalise the intercept
        gram[index][index] += penalty
    return _solve(gram, rhs)


def _predict(row: list[float], coefficients: list[float]) -> float:
    return sum(a * b for a, b in zip(row, coefficients))


def _rmse(rows: list[list[float]], targets: list[float], coefficients: list[float]) -> float:
    return math.sqrt(mean((_predict(row, coefficients) - target) ** 2 for row, target in zip(rows, targets)))


def _correlation(xs: list[float], ys: list[float]) -> float:
    xbar, ybar = mean(xs), mean(ys)
    numerator = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys))
    denominator = math.sqrt(sum((x - xbar) ** 2 for x in xs) * sum((y - ybar) ** 2 for y in ys))
    return 0.0 if denominator == 0 else numerator / denominator


def _quantile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def _distribution(definition: VariableDefinition, values: list[float]) -> dict:
    avg = mean(values)
    variance = mean((value - avg) ** 2 for value in values)
    common = {"sample_count": len(values), "mean": avg, "variance": variance,
              "q05": _quantile(values, .05), "q50": _quantile(values, .5), "q95": _quantile(values, .95)}
    if definition.value_kind == "BOUNDED" and variance > 0:
        low, high = definition.lower_bound, definition.upper_bound
        scaled = [(value - low) / (high - low) for value in values]
        m = min(.999999, max(.000001, mean(scaled)))
        v = mean((value - m) ** 2 for value in scaled)
        concentration = max(.01, m * (1 - m) / max(v, 1e-9) - 1)
        return {**common, "family": "BETA", "parameters": {"alpha": m * concentration, "beta": (1 - m) * concentration, "lower": low, "upper": high}}
    if definition.value_kind == "COUNT":
        dispersion = variance / max(avg, 1e-9)
        if dispersion <= 1.5:
            return {**common, "family": "POISSON", "parameters": {"lambda": avg}}
        size = avg * avg / max(variance - avg, 1e-9)
        return {**common, "family": "NEGATIVE_BINOMIAL", "parameters": {"size": size, "probability": size / (size + avg)}}
    if definition.value_kind == "POSITIVE" and all(value > 0 for value in values):
        logs = [math.log(value) for value in values]
        mu = mean(logs)
        return {**common, "family": "LOGNORMAL", "parameters": {"mu": mu, "sigma": math.sqrt(mean((value - mu) ** 2 for value in logs))}}
    if definition.value_kind == "EMPIRICAL":
        return {**common, "family": "EMPIRICAL", "parameters": {"quantiles": {"p05": common["q05"], "p50": common["q50"], "p95": common["q95"]}}}
    return {**common, "family": "NORMAL", "parameters": {"mean": avg, "standard_deviation": math.sqrt(variance)}}


def calibrate_enterprise(request_value) -> dict:
    request = CalibrationRequest.model_validate(request_value)
    observations = sorted(
        (item for item in request.observations if item.quality_status == "ESTABLISHED"),
        key=lambda item: item.observed_at,
    )
    dependency_pairs = sorted({tuple(sorted((item.left_control, item.right_control))) for item in request.dependencies})
    feature_names = ["intercept"] + [f"control:{name}" for name in CONTROL_NAMES] + [f"interaction:{left}|{right}" for left, right in dependency_pairs]

    def row(item: HistoricalObservation) -> list[float]:
        controls = {name: item.controls[name] / 100 for name in CONTROL_NAMES}
        return [1.0] + [controls[name] for name in CONTROL_NAMES] + [controls[left] * controls[right] for left, right in dependency_pairs]

    rows = [row(item) for item in observations]
    holdout = max(2, len(rows) // 5)
    train_rows, test_rows = rows[:-holdout], rows[-holdout:]
    train_observations = observations[:-holdout]
    targets = {
        "probability": [item.probability / 10 for item in observations],
        "impact": [item.impact / 10 for item in observations],
        "resilience": [item.resilience / 100 for item in observations],
    }
    coefficients, validation = {}, {}
    for target, values in targets.items():
        fitted = _ridge_fit(train_rows, values[:-holdout], request.ridge_penalty)
        coefficients[target] = dict(zip(feature_names, fitted))
        validation[target] = {
            "train_rmse": _rmse(train_rows, values[:-holdout], fitted),
            "holdout_rmse": _rmse(test_rows, values[-holdout:], fitted),
            "scale": "0_TO_1", "fit_sample_count": len(train_rows), "holdout_sample_count": len(test_rows),
            "holdout_from": observations[-holdout].observed_at.isoformat(), "holdout_to": observations[-1].observed_at.isoformat(),
        }

    severity = [item.probability * item.impact + (100 - item.resilience) / 10 for item in train_observations]
    variable_weights, distributions = {}, {}
    credibility = len(train_observations) / (len(train_observations) + 30)
    for control in CONTROL_NAMES:
        definitions = [item for item in request.variables if item.control == control]
        if not definitions:
            continue
        empirical = {item.variable_id: abs(_correlation([row.variables[item.variable_id] for row in train_observations], severity)) + 1e-6 for item in definitions}
        empirical_total = sum(empirical.values())
        prior_total = sum(item.prior_weight for item in definitions)
        blended = {
            item.variable_id: credibility * empirical[item.variable_id] / empirical_total + (1 - credibility) * item.prior_weight / prior_total
            for item in definitions
        }
        total = sum(blended.values())
        variable_weights[control] = {key: value / total for key, value in blended.items()}
    for definition in request.variables:
        historical_values = [item.variables[definition.variable_id] for item in train_observations]
        if definition.value_kind == "BOUNDED" and any(value < definition.lower_bound or value > definition.upper_bound for value in historical_values):
            raise ScenarioIntelligenceError(f"HISTORICAL_VARIABLE_OUT_OF_RANGE:{definition.variable_id}")
        if definition.value_kind == "COUNT" and any(value < 0 or not float(value).is_integer() for value in historical_values):
            raise ScenarioIntelligenceError(f"HISTORICAL_COUNT_INVALID:{definition.variable_id}")
        if definition.value_kind == "POSITIVE" and any(value <= 0 for value in historical_values):
            raise ScenarioIntelligenceError(f"HISTORICAL_POSITIVE_VALUE_INVALID:{definition.variable_id}")
        distributions[definition.variable_id] = _distribution(definition, historical_values)

    history_digest = sha256(_json([item.model_dump(mode="json") for item in observations]).encode()).hexdigest()
    payload = {
        "calibration_id": uuid4(), "enterprise_id": request.enterprise_id, "config_id": request.config_id,
        "model_key": request.model_key, "version": request.version, "status": "CANDIDATE",
        "created_by": request.created_by, "training_from": train_observations[0].observed_at,
        "training_to": train_observations[-1].observed_at, "sample_count": len(observations),
        "feature_names": feature_names, "coefficients": coefficients, "variable_weights": variable_weights,
        "distributions": distributions, "validation": validation, "ridge_penalty": request.ridge_penalty,
        "credibility_factor": credibility, "history_digest": history_digest,
        "approval_required": True, "automatic_activation": False,
        "limitations": "Historical relationships may drift; candidate requires independent approval and continuing back-testing.",
    }
    payload["model_digest"] = sha256(_json(payload).encode()).hexdigest()
    return payload


def approve_calibration(calibration: dict, *, approved_by: UUID, creator_id: UUID, holdout_rmse_limit: float = .20) -> dict:
    if approved_by == creator_id:
        raise ScenarioIntelligenceError("INDEPENDENT_CALIBRATION_APPROVAL_REQUIRED")
    if calibration.get("status") != "CANDIDATE":
        raise ScenarioIntelligenceError("CALIBRATION_CANDIDATE_REQUIRED")
    if any(item["holdout_rmse"] > holdout_rmse_limit for item in calibration["validation"].values()):
        raise ScenarioIntelligenceError("CALIBRATION_VALIDATION_FAILED")
    return {"calibration_id": calibration["calibration_id"], "decision": "APPROVED", "approved_by": approved_by,
            "eligible_for_activation": True, "automatic_activation": False}


def evaluate_calibrated_model(calibration: dict, controls: dict[str, float]) -> dict:
    if set(controls) != set(CONTROL_NAMES) or any(value < 0 or value > 100 for value in controls.values()):
        raise ScenarioIntelligenceError("CONTROL_VECTOR_INVALID")
    scaled = {name: controls[name] / 100 for name in CONTROL_NAMES}
    features = {}
    for name in calibration["feature_names"]:
        if name == "intercept":
            features[name] = 1.0
        elif name.startswith("control:"):
            features[name] = scaled[name.removeprefix("control:")]
        elif name.startswith("interaction:"):
            left, right = name.removeprefix("interaction:").split("|", 1)
            features[name] = scaled[left] * scaled[right]
    predictions = {}
    scales = {"probability": 10, "impact": 10, "resilience": 100}
    for target, coefficients in calibration["coefficients"].items():
        predictions[target] = round(max(0.0, min(1.0, sum(features[name] * coefficients[name] for name in calibration["feature_names"]))) * scales[target], 4)
    predictions["model_digest"] = calibration["model_digest"]
    predictions["calibration_id"] = calibration["calibration_id"]
    return predictions


def scenario_fingerprint(value) -> dict:
    spec = ScenarioSignature.model_validate(value)
    changes = sorted((item.variable_id, item.control, item.baseline_value, item.scenario_value, item.weight) for item in spec.changes)
    canonical = {
        "enterprise_id": str(spec.enterprise_id), "config_id": str(spec.config_id),
        "calibration_id": str(spec.calibration_id), "model_version": spec.model_version,
        "baseline_hash": spec.baseline_hash, "changes": changes,
        "dependencies": sorted(set(spec.dependencies)), "jurisdictions": sorted(set(spec.jurisdictions)),
    }
    fingerprint = sha256(_json(canonical).encode()).hexdigest()
    directions = [f"{item.variable_id} {'increased' if item.scenario_value > item.baseline_value else 'decreased'}" for item in sorted(spec.changes, key=lambda item: item.variable_id)]
    narrative = f"{spec.source.title()} scenario affecting {len(changes)} variables: " + "; ".join(directions)
    if spec.dependencies:
        narrative += ". Connected effects: " + ", ".join(sorted(set(spec.dependencies)))
    return {"fingerprint": fingerprint, "canonical": canonical, "narrative": narrative, "source": spec.source,
            "lesson_state": "DRAFT_ELIGIBLE_AFTER_VALIDATED_OUTCOME", "automatic_response": False}


def compare_scenarios(left_value, right_value) -> dict:
    left, right = ScenarioSignature.model_validate(left_value), ScenarioSignature.model_validate(right_value)
    left_fp, right_fp = scenario_fingerprint(left), scenario_fingerprint(right)
    if left_fp["fingerprint"] == right_fp["fingerprint"]:
        return {"match_type": "EXACT", "similarity_pct": 100.0, "validation_required": True, "automatic_execution": False}
    lmap, rmap = {item.variable_id: item for item in left.changes}, {item.variable_id: item for item in right.changes}
    ids = set(lmap) | set(rmap)
    total_weight, distance = 0.0, 0.0
    for variable_id in ids:
        a, b = lmap.get(variable_id), rmap.get(variable_id)
        weight = ((a.weight if a else 0) + (b.weight if b else 0)) / (2 if a and b else 1)
        total_weight += weight
        distance += weight * (min(1.0, abs(a.scenario_value - b.scenario_value) / 100) if a and b else 1.0)
    variable_similarity = 1 - distance / max(total_weight, 1e-9)

    def jaccard(a, b):
        union = set(a) | set(b)
        return 1.0 if not union else len(set(a) & set(b)) / len(union)

    dependency_similarity = jaccard(left.dependencies, right.dependencies)
    jurisdiction_similarity = jaccard(left.jurisdictions, right.jurisdictions)
    context_similarity = 1.0 if (left.config_id, left.calibration_id, left.model_version) == (right.config_id, right.calibration_id, right.model_version) else 0.0
    similarity = round(100 * (.60 * variable_similarity + .20 * dependency_similarity + .10 * jurisdiction_similarity + .10 * context_similarity), 2)
    return {"match_type": "STRONG" if similarity >= 85 else "RELATED" if similarity >= 60 else "DISTINCT",
            "similarity_pct": similarity, "validation_required": True, "automatic_execution": False,
            "components": {"variables": round(variable_similarity * 100, 2), "dependencies": round(dependency_similarity * 100, 2),
                           "jurisdictions": round(jurisdiction_similarity * 100, 2), "model_context": round(context_similarity * 100, 2)}}


def precedent_candidate(match: dict, *, precedent_ref: str, intervention: str, limitations: str) -> dict:
    return {"precedent_ref": precedent_ref, "match_type": match["match_type"], "similarity_pct": match["similarity_pct"],
            "recommended_response": intervention, "limitations": limitations, "status": "CURRENT_STATE_VALIDATION_REQUIRED",
            "validation_simulation_required": True, "authority_required": True, "automatic_execution": False}


def validate_precedent_response(candidate: dict, *, simulation_passed: bool, evidence_confidence_pct: float,
                                rollback_ready: bool, evidence_refs: tuple[str, ...]) -> dict:
    if not evidence_refs:
        raise ScenarioIntelligenceError("VALIDATION_EVIDENCE_REQUIRED")
    eligible = simulation_passed and evidence_confidence_pct >= 80 and rollback_ready
    return {"precedent_ref": candidate["precedent_ref"],
            "status": "ELIGIBLE_FOR_AUTHORISED_DECISION" if eligible else "FURTHER_ANALYSIS_REQUIRED",
            "simulation_passed": simulation_passed, "evidence_confidence_pct": evidence_confidence_pct,
            "rollback_ready": rollback_ready, "evidence_refs": list(evidence_refs),
            "authority_required": True, "automatic_execution": False}


def draft_lesson_from_outcome(*, scenario_ref: str, response_ref: str, recovery_state: str,
                              expected_outcome: str, actual_outcome: str, evidence_refs: tuple[str, ...]) -> dict:
    if recovery_state != "VERIFIED_RECOVERED":
        raise ScenarioIntelligenceError("VERIFIED_RECOVERY_REQUIRED")
    if not evidence_refs:
        raise ScenarioIntelligenceError("LESSON_EVIDENCE_REQUIRED")
    return {"draft_id": uuid4(), "scenario_ref": scenario_ref, "response_ref": response_ref,
            "expected_outcome": expected_outcome, "actual_outcome": actual_outcome,
            "evidence_refs": list(evidence_refs), "status": "DRAFT_REVIEW_REQUIRED",
            "publish_automatically": False, "advisory_only": True}


def explain_console_scenario(baseline: dict, result: dict, model_version: str = "DEFAULT-UAT-V1") -> dict:
    changes = []
    for control in CONTROL_NAMES:
        before, after = baseline["controls"][control], result["controls"][control]
        if before != after:
            changes.append({"control": control, "before": before, "after": after, "direction": "UP" if after > before else "DOWN"})
    dependency_map = {
        "Capital": ("Liquidity",), "Liquidity": ("Capital", "Operations"),
        "Operations": ("Liquidity", "Merchants"), "Regulation": ("Capital", "Countries & Corridors"),
        "Merchants": ("Operations", "Countries & Corridors"),
        "Countries & Corridors": ("Regulation", "Liquidity", "Merchants"),
    }
    connected = sorted({f"{item['control']}→{target}" for item in changes for target in dependency_map[item["control"]]})
    canonical = {"model_version": model_version, "baseline": baseline["controls"], "changes": changes, "result": {
        "probability": result["probability"], "impact": result["impact"], "resilience": result["resilience"],
        "payment_disruption": result["payment_disruption"],
    }}
    fingerprint = sha256(_json(canonical).encode()).hexdigest()
    drivers = ", ".join(f"{item['control']} {item['before']}→{item['after']}" for item in changes) or "no control changes"
    return {"scenario_id": fingerprint[:16].upper(), "fingerprint": fingerprint, "model_version": model_version,
            "explanation": f"Scenario driven by {drivers}. Connected pathways considered: {', '.join(connected) or 'none'}.",
            "results": canonical["result"], "connected_pathways": connected,
            "precedent_search": "PENDING_PERSISTENT_REPOSITORY", "lesson_state": "DRAFT_ELIGIBLE_AFTER_VALIDATED_OUTCOME",
            "automatic_execution": False}


def record_calibration(conn, tenant: UUID, calibration: dict, *, recorded_at: datetime | None = None) -> dict:
    recorded_at = _utc(recorded_at or datetime.now(timezone.utc))
    if calibration.get("status") != "CANDIDATE" or calibration.get("automatic_activation") is not False:
        raise ScenarioIntelligenceError("GOVERNED_CANDIDATE_REQUIRED")
    if UUID(str(calibration.get("enterprise_id"))) != tenant:
        raise ScenarioIntelligenceError("CALIBRATION_TENANT_MISMATCH")
    conn.execute(
        """INSERT INTO resilience_v2.enterprise_model_calibrations
        VALUES (%s,%s,%s,%s,%s,'CANDIDATE',%s,%s,%s,'RIDGE_LINEAR_WITH_DEPENDENCY_INTERACTIONS',
        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (tenant, calibration["calibration_id"], calibration["config_id"], calibration["model_key"], calibration["version"],
         calibration["training_from"], calibration["training_to"], calibration["sample_count"],
         _json(calibration["feature_names"]), _json(calibration["coefficients"]), _json(calibration["validation"]),
         calibration["ridge_penalty"], calibration["credibility_factor"], calibration["history_digest"],
         calibration["model_digest"], calibration["limitations"], calibration["created_by"], recorded_at),
    )
    for variable_id, distribution in calibration["distributions"].items():
        statistics = {key: value for key, value in distribution.items() if key not in {"family", "parameters"}}
        conn.execute(
            "INSERT INTO resilience_v2.variable_distribution_models VALUES (%s,%s,%s,%s,%s,%s)",
            (tenant, calibration["calibration_id"], variable_id, distribution["family"],
             _json(distribution["parameters"]), _json(statistics)),
        )
    for control, weights in calibration["variable_weights"].items():
        for variable_id, weight in weights.items():
            conn.execute(
                "INSERT INTO resilience_v2.variable_weight_models VALUES (%s,%s,%s,%s,%s,'SHRUNK_HISTORICAL_SENSITIVITY_V1')",
                (tenant, calibration["calibration_id"], control, variable_id, weight),
            )
    return {"calibration_id": calibration["calibration_id"], "status": "CANDIDATE", "automatic_activation": False}


def approve_calibration_record(conn, tenant: UUID, calibration_id: UUID, approved_by: UUID, rationale: str,
                               evidence_refs: tuple[str, ...], *, at: datetime | None = None) -> dict:
    at = _utc(at or datetime.now(timezone.utc))
    if not rationale.strip() or not evidence_refs:
        raise ScenarioIntelligenceError("CALIBRATION_APPROVAL_EVIDENCE_REQUIRED")
    row = conn.execute(
        """SELECT created_by,validation_metrics FROM resilience_v2.enterprise_model_calibrations
        WHERE tenant_id=%s AND calibration_id=%s""", (tenant, calibration_id),
    ).fetchone()
    if row is None:
        raise ScenarioIntelligenceError("CALIBRATION_NOT_FOUND")
    validation = json.loads(row[1]) if isinstance(row[1], str) else row[1]
    approval = approve_calibration(
        {"calibration_id": calibration_id, "status": "CANDIDATE", "validation": validation},
        approved_by=approved_by, creator_id=row[0],
    )
    approval_id = uuid4()
    conn.execute(
        "INSERT INTO resilience_v2.model_calibration_approval_events VALUES (%s,%s,%s,'APPROVED',%s,%s,%s,%s)",
        (tenant, approval_id, calibration_id, approved_by, rationale.strip(), _json(list(evidence_refs)), at),
    )
    return {**approval, "approval_id": approval_id}


def activate_calibration_record(conn, tenant: UUID, calibration_id: UUID, activated_by: UUID,
                                evidence_refs: tuple[str, ...], *, supersedes: UUID | None = None,
                                effective_at: datetime | None = None) -> dict:
    effective_at = _utc(effective_at or datetime.now(timezone.utc))
    if not evidence_refs:
        raise ScenarioIntelligenceError("ACTIVATION_EVIDENCE_REQUIRED")
    approved = conn.execute(
        """SELECT 1 FROM resilience_v2.model_calibration_approval_events
        WHERE tenant_id=%s AND calibration_id=%s AND decision='APPROVED'""", (tenant, calibration_id),
    ).fetchone()
    if approved is None:
        raise ScenarioIntelligenceError("APPROVED_CALIBRATION_REQUIRED")
    activation_id = uuid4()
    conn.execute(
        "INSERT INTO resilience_v2.model_activation_events VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (tenant, activation_id, calibration_id, supersedes, activated_by, effective_at, _json(list(evidence_refs))),
    )
    return {"activation_id": activation_id, "calibration_id": calibration_id, "effective_at": effective_at,
            "active": True, "automatic_activation": False}


def record_scenario(conn, tenant: UUID, signature_value, *, results: dict, created_by: UUID,
                    recorded_at: datetime | None = None) -> dict:
    signature = ScenarioSignature.model_validate(signature_value)
    record = scenario_fingerprint(signature)
    recorded_at = _utc(recorded_at or datetime.now(timezone.utc))
    proposed_id = uuid4()
    inserted = conn.execute(
        """INSERT INTO resilience_v2.scenario_intelligence_records
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (tenant_id,fingerprint) DO NOTHING RETURNING scenario_record_id""",
        (tenant, proposed_id, record["fingerprint"], signature.source, signature.config_id,
         signature.calibration_id, signature.model_version, signature.baseline_hash,
         _json([item.model_dump() for item in signature.changes]), _json(list(signature.dependencies)),
         _json(list(signature.jurisdictions)), _json(results), record["narrative"],
         _json(list(signature.evidence_refs)), created_by, signature.as_of, recorded_at),
    ).fetchone()
    novel = inserted is not None
    scenario_record_id = inserted[0] if novel else conn.execute(
        "SELECT scenario_record_id FROM resilience_v2.scenario_intelligence_records WHERE tenant_id=%s AND fingerprint=%s",
        (tenant, record["fingerprint"]),
    ).fetchone()[0]
    occurrence_id = uuid4()
    conn.execute(
        "INSERT INTO resilience_v2.scenario_occurrence_events VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (tenant, occurrence_id, scenario_record_id, signature.source, _json(results),
         _json(list(signature.evidence_refs)), signature.as_of, recorded_at),
    )
    return {"scenario_record_id": scenario_record_id, "occurrence_id": occurrence_id, **record,
            "novel_scenario": novel, "occurrence_stored": True}


def record_match(conn, tenant: UUID, query_scenario_id: UUID, candidate_scenario_id: UUID, match: dict,
                 searched_by: UUID, *, precedent_ref: str | None = None, at: datetime | None = None) -> dict:
    at = _utc(at or datetime.now(timezone.utc))
    match_id = uuid4()
    conn.execute(
        "INSERT INTO resilience_v2.scenario_match_events VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (tenant, match_id, query_scenario_id, candidate_scenario_id, match["match_type"],
         match["similarity_pct"], _json(match.get("components", {})), precedent_ref, searched_by, at),
    )
    return {"match_id": match_id, **match, "advisory_only": True}


def record_precedent_validation(conn, tenant: UUID, scenario_record_id: UUID, candidate: dict,
                                *, simulation_passed: bool, evidence_confidence_pct: float,
                                rollback_ready: bool, evidence_refs: tuple[str, ...], validated_by: UUID,
                                at: datetime | None = None) -> dict:
    at = _utc(at or datetime.now(timezone.utc))
    validation = validate_precedent_response(
        candidate, simulation_passed=simulation_passed, evidence_confidence_pct=evidence_confidence_pct,
        rollback_ready=rollback_ready, evidence_refs=evidence_refs,
    )
    validation_id = uuid4()
    conn.execute(
        """INSERT INTO resilience_v2.precedent_response_validation_events
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (tenant, validation_id, scenario_record_id, candidate["precedent_ref"], simulation_passed,
         evidence_confidence_pct, rollback_ready, validation["status"], _json(list(evidence_refs)), validated_by, at),
    )
    return {"validation_id": validation_id, **validation}


def find_scenario_matches(conn, tenant: UUID, query_value, *, limit: int = 10) -> list[dict]:
    if not 1 <= limit <= 50:
        raise ScenarioIntelligenceError("SCENARIO_MATCH_LIMIT_INVALID")
    query = ScenarioSignature.model_validate(query_value)
    rows = conn.execute(
        """SELECT scenario_record_id,config_id,calibration_id,model_version,baseline_hash,source,
        changes,dependencies,jurisdictions,evidence_refs,observed_at,fingerprint
        FROM resilience_v2.scenario_intelligence_records WHERE tenant_id=%s""", (tenant,),
    ).fetchall()

    def decoded(value):
        return json.loads(value) if isinstance(value, str) else value

    matches = []
    for row in rows:
        candidate = ScenarioSignature(
            enterprise_id=query.enterprise_id, config_id=row[1], calibration_id=row[2], model_version=row[3],
            baseline_hash=row[4], source=row[5], changes=decoded(row[6]), dependencies=tuple(decoded(row[7])),
            jurisdictions=tuple(decoded(row[8])), evidence_refs=tuple(decoded(row[9])), as_of=row[10],
        )
        comparison = compare_scenarios(query, candidate)
        matches.append({"scenario_record_id": row[0], "fingerprint": row[11], **comparison})
    return sorted(matches, key=lambda item: (-item["similarity_pct"], str(item["scenario_record_id"])))[:limit]
