from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from resilience.config import ROOT, REVISION
from resilience.m28_scenario_intelligence import (
    ScenarioIntelligenceError,
    approve_calibration,
    calibrate_enterprise,
    compare_scenarios,
    draft_lesson_from_outcome,
    evaluate_calibrated_model,
    explain_console_scenario,
    precedent_candidate,
    scenario_fingerprint,
    validate_precedent_response,
)


T0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
CONTROLS = ("Capital", "Liquidity", "Operations", "Regulation", "Merchants", "Countries & Corridors")


def _request(multiplier=1.0):
    definitions = [
        {"variable_id": "CAP-A", "control": "Capital", "value_kind": "POSITIVE", "prior_weight": .6},
        {"variable_id": "CAP-B", "control": "Capital", "value_kind": "POSITIVE", "prior_weight": .4},
        {"variable_id": "LIQ-A", "control": "Liquidity", "value_kind": "POSITIVE", "prior_weight": 1},
        {"variable_id": "OPS-A", "control": "Operations", "value_kind": "BOUNDED", "prior_weight": .5, "lower_bound": 0, "upper_bound": 100},
        {"variable_id": "OPS-B", "control": "Operations", "value_kind": "COUNT", "prior_weight": .5},
        {"variable_id": "REG-A", "control": "Regulation", "value_kind": "CONTINUOUS", "prior_weight": 1},
        {"variable_id": "MER-A", "control": "Merchants", "value_kind": "EMPIRICAL", "prior_weight": 1},
        {"variable_id": "COR-A", "control": "Countries & Corridors", "value_kind": "BOUNDED", "prior_weight": 1, "lower_bound": 0, "upper_bound": 100},
    ]
    observations = []
    for i in range(40):
        controls = {
            "Capital": 35 + (i * 7) % 60,
            "Liquidity": 30 + (i * 11) % 65,
            "Operations": 25 + (i * 13) % 70,
            "Regulation": 10 + (i * 17) % 80,
            "Merchants": 15 + (i * 19) % 75,
            "Countries & Corridors": 5 + (i * 23) % 90,
        }
        probability = min(10, multiplier * (.02 * (100 - controls["Operations"]) + .018 * controls["Regulation"] + .012 * controls["Merchants"] + .009 * controls["Countries & Corridors"]))
        impact = min(10, multiplier * (.025 * (100 - controls["Capital"]) + .022 * (100 - controls["Liquidity"]) + .01 * controls["Countries & Corridors"]))
        resilience = max(0, 100 - 3.8 * probability - 4.1 * impact)
        variables = {
            "CAP-A": controls["Capital"] * 1000 + 1,
            "CAP-B": controls["Capital"] ** 1.4 + 1,
            "LIQ-A": controls["Liquidity"] * 900 + 1,
            "OPS-A": controls["Operations"],
            "OPS-B": int((100 - controls["Operations"]) / 8),
            "REG-A": controls["Regulation"] - 40,
            "MER-A": controls["Merchants"],
            "COR-A": controls["Countries & Corridors"],
        }
        observations.append({"observed_at": T0 + timedelta(days=i), "controls": controls, "variables": variables,
                             "probability": probability, "impact": impact, "resilience": resilience,
                             "quality_status": "ESTABLISHED", "lineage_ref": f"feed:{i}"})
    return {"enterprise_id": uuid4(), "config_id": uuid4(), "model_key": "ENTERPRISE-RISK", "version": "1.0",
            "created_by": uuid4(), "variables": definitions,
            "dependencies": [{"left_control": "Operations", "right_control": "Liquidity"},
                             {"left_control": "Merchants", "right_control": "Countries & Corridors"}],
            "observations": observations, "ridge_penalty": .01}


def test_enterprise_calibration_learns_versioned_weights_coefficients_and_distributions():
    request = _request()
    result = calibrate_enterprise(request)
    assert result["status"] == "CANDIDATE"
    assert result["approval_required"] is True
    assert result["automatic_activation"] is False
    assert result["sample_count"] == 40
    assert "interaction:Liquidity|Operations" in result["feature_names"]
    assert sum(result["variable_weights"]["Capital"].values()) == pytest.approx(1)
    assert result["distributions"]["OPS-A"]["family"] == "BETA"
    assert result["distributions"]["CAP-A"]["family"] == "LOGNORMAL"
    assert result["validation"]["resilience"]["holdout_rmse"] < .20

    approver = uuid4()
    approval = approve_calibration(result, approved_by=approver, creator_id=request["created_by"])
    assert approval["eligible_for_activation"] is True
    assert approval["automatic_activation"] is False
    with pytest.raises(ScenarioIntelligenceError, match="INDEPENDENT_CALIBRATION_APPROVAL_REQUIRED"):
        approve_calibration(result, approved_by=request["created_by"], creator_id=request["created_by"])


def test_different_enterprise_history_produces_different_coefficients():
    first = calibrate_enterprise(_request(1.0))
    second = calibrate_enterprise(_request(.62))
    assert first["coefficients"]["probability"] != second["coefficients"]["probability"]
    assert first["model_digest"] != second["model_digest"]
    controls = _request()["observations"][-1]["controls"]
    first_result = evaluate_calibrated_model(first, controls)
    second_result = evaluate_calibrated_model(second, controls)
    assert first_result["probability"] != second_result["probability"]
    assert first_result["calibration_id"] == first["calibration_id"]


def _scenario(*, change=65, dependencies=("Operations→Liquidity",), jurisdiction=("IN",)):
    return {"enterprise_id": uuid4(), "config_id": uuid4(), "calibration_id": uuid4(), "model_version": "1.0",
            "baseline_hash": "baseline-001", "source": "SIMULATION",
            "changes": [{"variable_id": "OPS-A", "control": "Operations", "baseline_value": 80,
                         "scenario_value": change, "weight": 1}],
            "dependencies": dependencies, "jurisdictions": jurisdiction,
            "evidence_refs": ("simulation:001",), "as_of": T0}


def test_scenario_fingerprint_matching_and_precedent_reuse_remain_governed():
    left = _scenario()
    right = {**left, "as_of": T0 + timedelta(days=1), "evidence_refs": ("simulation:002",)}
    assert scenario_fingerprint(left)["fingerprint"] == scenario_fingerprint(right)["fingerprint"]
    exact = compare_scenarios(left, right)
    assert exact == {"match_type": "EXACT", "similarity_pct": 100.0, "validation_required": True, "automatic_execution": False}

    related = {**right, "changes": [{**right["changes"][0], "scenario_value": 58}]}
    match = compare_scenarios(left, related)
    candidate = precedent_candidate(match, precedent_ref="lesson:gateway-01", intervention="Activate alternate route", limitations="Valid only for approved corridors")
    assert candidate["status"] == "CURRENT_STATE_VALIDATION_REQUIRED"
    assert candidate["automatic_execution"] is False
    validation = validate_precedent_response(candidate, simulation_passed=True, evidence_confidence_pct=93,
                                             rollback_ready=True, evidence_refs=("validation:001",))
    assert validation["status"] == "ELIGIBLE_FOR_AUTHORISED_DECISION"
    assert validation["authority_required"] is True


def test_lesson_requires_verified_actual_recovery_and_review():
    with pytest.raises(ScenarioIntelligenceError, match="VERIFIED_RECOVERY_REQUIRED"):
        draft_lesson_from_outcome(scenario_ref="scenario:1", response_ref="response:1", recovery_state="EXPECTED",
                                  expected_outcome="Stable", actual_outcome="Unknown", evidence_refs=("evidence:1",))
    draft = draft_lesson_from_outcome(scenario_ref="scenario:1", response_ref="response:1",
                                      recovery_state="VERIFIED_RECOVERED", expected_outcome="Stable",
                                      actual_outcome="Stable after 18 minutes", evidence_refs=("evidence:1",))
    assert draft["status"] == "DRAFT_REVIEW_REQUIRED"
    assert draft["publish_automatically"] is False


def test_console_run_explains_changed_controls_connected_pathways_and_lesson_boundary():
    baseline = {"controls": dict(zip(CONTROLS, (76, 72, 82, 28, 31, 24)))}
    result = {"controls": dict(zip(CONTROLS, (65, 72, 60, 28, 48, 24))),
              "probability": 4.2, "impact": 3.1, "resilience": 67, "payment_disruption": "watch"}
    explanation = explain_console_scenario(baseline, result)
    assert "Capital 76→65" in explanation["explanation"]
    assert "Operations→Merchants" in explanation["connected_pathways"]
    assert explanation["lesson_state"] == "DRAFT_ELIGIBLE_AFTER_VALIDATED_OUTCOME"
    assert explanation["automatic_execution"] is False


def test_m28_migration_contains_append_only_calibration_scenario_and_occurrence_evidence():
    source = (ROOT / "migrations" / "versions" / "m28_0037_scenario_intelligence.py").read_text(encoding="utf-8")
    assert REVISION == "m28_0037"
    for table in (
        "enterprise_model_calibrations", "variable_distribution_models", "variable_weight_models",
        "model_calibration_approval_events", "model_activation_events", "scenario_intelligence_records",
        "scenario_occurrence_events", "scenario_match_events", "precedent_response_validation_events",
    ):
        assert table in source
    assert "append_only" in source
