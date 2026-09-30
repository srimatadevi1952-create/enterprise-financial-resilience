"""M28 calibrated scenario intelligence and governed precedent reuse."""

from alembic import op
import sqlalchemy as sa


revision = "m28_0037"
down_revision = "m27_0036"


def upgrade(profile, **kwargs):
    uuid = sa.UUID()
    op.create_table(
        "enterprise_model_calibrations",
        sa.Column("tenant_id", uuid, nullable=False), sa.Column("calibration_id", uuid, nullable=False),
        sa.Column("config_id", uuid, nullable=False), sa.Column("model_key", sa.Text, nullable=False),
        sa.Column("model_version", sa.Text, nullable=False), sa.Column("status", sa.Text, nullable=False),
        sa.Column("training_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("training_to", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sample_count", sa.Integer, nullable=False), sa.Column("algorithm", sa.Text, nullable=False),
        sa.Column("feature_names", sa.JSON, nullable=False), sa.Column("coefficients", sa.JSON, nullable=False),
        sa.Column("validation_metrics", sa.JSON, nullable=False), sa.Column("ridge_penalty", sa.Numeric(12, 8), nullable=False),
        sa.Column("credibility_factor", sa.Numeric(12, 8), nullable=False),
        sa.Column("history_digest", sa.Text, nullable=False), sa.Column("model_digest", sa.Text, nullable=False),
        sa.Column("limitations", sa.Text, nullable=False), sa.Column("created_by", uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "calibration_id"),
        sa.UniqueConstraint("tenant_id", "model_key", "model_version"),
        sa.ForeignKeyConstraint(["tenant_id", "config_id"], ["resilience_v2.enterprise_configuration_versions.tenant_id", "resilience_v2.enterprise_configuration_versions.config_id"]),
        sa.ForeignKeyConstraint(["tenant_id", "created_by"], ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"]),
        sa.CheckConstraint("status='CANDIDATE'"), sa.CheckConstraint("sample_count >= 12"),
        sa.CheckConstraint("training_to >= training_from"), sa.CheckConstraint("credibility_factor > 0 AND credibility_factor <= 1"),
        schema="resilience_v2",
    )
    op.create_table(
        "variable_distribution_models",
        sa.Column("tenant_id", uuid, nullable=False), sa.Column("calibration_id", uuid, nullable=False),
        sa.Column("variable_id", sa.Text, nullable=False), sa.Column("family", sa.Text, nullable=False),
        sa.Column("parameters", sa.JSON, nullable=False), sa.Column("summary_statistics", sa.JSON, nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "calibration_id", "variable_id"),
        sa.ForeignKeyConstraint(["tenant_id", "calibration_id"], ["resilience_v2.enterprise_model_calibrations.tenant_id", "resilience_v2.enterprise_model_calibrations.calibration_id"]),
        sa.CheckConstraint("family IN ('BETA','POISSON','NEGATIVE_BINOMIAL','LOGNORMAL','EMPIRICAL','NORMAL')"),
        schema="resilience_v2",
    )
    op.create_table(
        "variable_weight_models",
        sa.Column("tenant_id", uuid, nullable=False), sa.Column("calibration_id", uuid, nullable=False),
        sa.Column("control_name", sa.Text, nullable=False), sa.Column("variable_id", sa.Text, nullable=False),
        sa.Column("weight", sa.Numeric(14, 10), nullable=False), sa.Column("method", sa.Text, nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "calibration_id", "control_name", "variable_id"),
        sa.ForeignKeyConstraint(["tenant_id", "calibration_id"], ["resilience_v2.enterprise_model_calibrations.tenant_id", "resilience_v2.enterprise_model_calibrations.calibration_id"]),
        sa.CheckConstraint("weight > 0 AND weight <= 1"), schema="resilience_v2",
    )
    op.create_table(
        "model_calibration_approval_events",
        sa.Column("tenant_id", uuid, nullable=False), sa.Column("approval_id", uuid, nullable=False),
        sa.Column("calibration_id", uuid, nullable=False), sa.Column("decision", sa.Text, nullable=False),
        sa.Column("approved_by", uuid, nullable=False), sa.Column("rationale", sa.Text, nullable=False),
        sa.Column("evidence_refs", sa.JSON, nullable=False), sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "approval_id"), sa.UniqueConstraint("tenant_id", "calibration_id"),
        sa.ForeignKeyConstraint(["tenant_id", "calibration_id"], ["resilience_v2.enterprise_model_calibrations.tenant_id", "resilience_v2.enterprise_model_calibrations.calibration_id"]),
        sa.ForeignKeyConstraint(["tenant_id", "approved_by"], ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"]),
        sa.CheckConstraint("decision IN ('APPROVED','REJECTED')"), schema="resilience_v2",
    )
    op.create_table(
        "model_activation_events",
        sa.Column("tenant_id", uuid, nullable=False), sa.Column("activation_id", uuid, nullable=False),
        sa.Column("calibration_id", uuid, nullable=False), sa.Column("supersedes_calibration_id", uuid, nullable=True),
        sa.Column("activated_by", uuid, nullable=False), sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence_refs", sa.JSON, nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "activation_id"),
        sa.ForeignKeyConstraint(["tenant_id", "calibration_id"], ["resilience_v2.enterprise_model_calibrations.tenant_id", "resilience_v2.enterprise_model_calibrations.calibration_id"]),
        sa.ForeignKeyConstraint(["tenant_id", "supersedes_calibration_id"], ["resilience_v2.enterprise_model_calibrations.tenant_id", "resilience_v2.enterprise_model_calibrations.calibration_id"]),
        sa.ForeignKeyConstraint(["tenant_id", "activated_by"], ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"]),
        schema="resilience_v2",
    )
    op.create_table(
        "scenario_intelligence_records",
        sa.Column("tenant_id", uuid, nullable=False), sa.Column("scenario_record_id", uuid, nullable=False),
        sa.Column("fingerprint", sa.Text, nullable=False), sa.Column("source", sa.Text, nullable=False),
        sa.Column("config_id", uuid, nullable=False), sa.Column("calibration_id", uuid, nullable=False),
        sa.Column("model_version", sa.Text, nullable=False), sa.Column("baseline_hash", sa.Text, nullable=False),
        sa.Column("changes", sa.JSON, nullable=False), sa.Column("dependencies", sa.JSON, nullable=False),
        sa.Column("jurisdictions", sa.JSON, nullable=False), sa.Column("results", sa.JSON, nullable=False),
        sa.Column("narrative", sa.Text, nullable=False), sa.Column("evidence_refs", sa.JSON, nullable=False),
        sa.Column("created_by", uuid, nullable=False), sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "scenario_record_id"), sa.UniqueConstraint("tenant_id", "fingerprint"),
        sa.ForeignKeyConstraint(["tenant_id", "config_id"], ["resilience_v2.enterprise_configuration_versions.tenant_id", "resilience_v2.enterprise_configuration_versions.config_id"]),
        sa.ForeignKeyConstraint(["tenant_id", "calibration_id"], ["resilience_v2.enterprise_model_calibrations.tenant_id", "resilience_v2.enterprise_model_calibrations.calibration_id"]),
        sa.ForeignKeyConstraint(["tenant_id", "created_by"], ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"]),
        sa.CheckConstraint("source IN ('LIVE','SIMULATION')"), schema="resilience_v2",
    )
    op.create_table(
        "scenario_match_events",
        sa.Column("tenant_id", uuid, nullable=False), sa.Column("match_id", uuid, nullable=False),
        sa.Column("query_scenario_id", uuid, nullable=False), sa.Column("candidate_scenario_id", uuid, nullable=False),
        sa.Column("match_type", sa.Text, nullable=False), sa.Column("similarity_pct", sa.Numeric(8, 4), nullable=False),
        sa.Column("components", sa.JSON, nullable=False), sa.Column("precedent_ref", sa.Text, nullable=True),
        sa.Column("searched_by", uuid, nullable=False), sa.Column("searched_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "match_id"),
        sa.ForeignKeyConstraint(["tenant_id", "query_scenario_id"], ["resilience_v2.scenario_intelligence_records.tenant_id", "resilience_v2.scenario_intelligence_records.scenario_record_id"]),
        sa.ForeignKeyConstraint(["tenant_id", "candidate_scenario_id"], ["resilience_v2.scenario_intelligence_records.tenant_id", "resilience_v2.scenario_intelligence_records.scenario_record_id"]),
        sa.ForeignKeyConstraint(["tenant_id", "searched_by"], ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"]),
        sa.CheckConstraint("match_type IN ('EXACT','STRONG','RELATED','DISTINCT')"),
        sa.CheckConstraint("similarity_pct >= 0 AND similarity_pct <= 100"), schema="resilience_v2",
    )
    op.create_table(
        "scenario_occurrence_events",
        sa.Column("tenant_id", uuid, nullable=False), sa.Column("occurrence_id", uuid, nullable=False),
        sa.Column("scenario_record_id", uuid, nullable=False), sa.Column("source", sa.Text, nullable=False),
        sa.Column("results", sa.JSON, nullable=False), sa.Column("evidence_refs", sa.JSON, nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "occurrence_id"),
        sa.ForeignKeyConstraint(["tenant_id", "scenario_record_id"], ["resilience_v2.scenario_intelligence_records.tenant_id", "resilience_v2.scenario_intelligence_records.scenario_record_id"]),
        sa.CheckConstraint("source IN ('LIVE','SIMULATION')"), schema="resilience_v2",
    )
    op.create_table(
        "precedent_response_validation_events",
        sa.Column("tenant_id", uuid, nullable=False), sa.Column("validation_id", uuid, nullable=False),
        sa.Column("scenario_record_id", uuid, nullable=False), sa.Column("precedent_ref", sa.Text, nullable=False),
        sa.Column("simulation_passed", sa.Boolean, nullable=False),
        sa.Column("evidence_confidence_pct", sa.Numeric(8, 4), nullable=False),
        sa.Column("rollback_ready", sa.Boolean, nullable=False), sa.Column("decision_state", sa.Text, nullable=False),
        sa.Column("evidence_refs", sa.JSON, nullable=False), sa.Column("validated_by", uuid, nullable=False),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "validation_id"),
        sa.ForeignKeyConstraint(["tenant_id", "scenario_record_id"], ["resilience_v2.scenario_intelligence_records.tenant_id", "resilience_v2.scenario_intelligence_records.scenario_record_id"]),
        sa.ForeignKeyConstraint(["tenant_id", "validated_by"], ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"]),
        sa.CheckConstraint("evidence_confidence_pct >= 0 AND evidence_confidence_pct <= 100"),
        sa.CheckConstraint("decision_state IN ('ELIGIBLE_FOR_AUTHORISED_DECISION','FURTHER_ANALYSIS_REQUIRED')"),
        schema="resilience_v2",
    )
    for table in (
        "enterprise_model_calibrations", "variable_distribution_models", "variable_weight_models",
        "model_calibration_approval_events", "model_activation_events", "scenario_intelligence_records",
        "scenario_match_events", "scenario_occurrence_events", "precedent_response_validation_events",
    ):
        op.execute(sa.text(
            f"CREATE TRIGGER {table}_append_only BEFORE UPDATE OR DELETE ON resilience_v2.{table} "
            "FOR EACH ROW EXECUTE FUNCTION resilience_v2.guard_m24_append_only()"
        ))
        op.execute(sa.text(f"REVOKE UPDATE, DELETE ON resilience_v2.{table} FROM {profile.runtime_user}"))


def downgrade(**kwargs):
    raise RuntimeError("M28 downgrade disabled; rebuild disposable V2 database explicitly")
