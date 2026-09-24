"""M24 consultant workbench, change governance and sandbox execution."""

from alembic import op
import sqlalchemy as sa


revision = "m24_0028"
down_revision = "m23_0027"


def upgrade(profile, **kwargs):
    uuid = sa.UUID()

    op.create_table(
        "consultant_assignments",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("assignment_id", uuid, nullable=False),
        sa.Column("consultant_principal_id", uuid, nullable=False),
        sa.Column("consultant_actor_id", uuid, nullable=False),
        sa.Column("service_name", sa.Text, nullable=False),
        sa.Column("permitted_purposes", sa.JSON, nullable=False),
        sa.Column("authority_scope", sa.JSON, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence_ref", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "assignment_id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["resilience_v2.tenants.tenant_id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "consultant_actor_id"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("status IN ('ACTIVE','REVOKED','EXPIRED')"),
        sa.CheckConstraint("expires_at > effective_from"),
        schema="resilience_v2",
    )
    op.create_index(
        "ix_consultant_assignments_principal",
        "consultant_assignments",
        ["consultant_principal_id", "status"],
        schema="resilience_v2",
    )

    op.create_table(
        "client_service_mandates",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("mandate_id", uuid, nullable=False),
        sa.Column("assignment_id", uuid, nullable=False),
        sa.Column("authorized_by", uuid, nullable=False),
        sa.Column("implementation_modes", sa.JSON, nullable=False),
        sa.Column("action_scope", sa.JSON, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence_ref", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "mandate_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "assignment_id"],
            ["resilience_v2.consultant_assignments.tenant_id", "resilience_v2.consultant_assignments.assignment_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "authorized_by"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("status IN ('ACTIVE','REVOKED','EXPIRED')"),
        sa.CheckConstraint("expires_at > effective_from"),
        schema="resilience_v2",
    )

    op.create_table(
        "consultant_source_observations",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("observation_id", uuid, nullable=False),
        sa.Column("assignment_id", uuid, nullable=False),
        sa.Column("source_key", sa.Text, nullable=False),
        sa.Column("source_record_key", sa.Text, nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("schema_version", sa.Text, nullable=False),
        sa.Column("payload_hash", sa.Text, nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column("lineage_ref", sa.Text, nullable=False),
        sa.Column("quality_status", sa.Text, nullable=False),
        sa.Column("reconciliation_status", sa.Text, nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "observation_id"),
        sa.UniqueConstraint("tenant_id", "source_key", "source_record_key", "payload_hash"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "assignment_id"],
            ["resilience_v2.consultant_assignments.tenant_id", "resilience_v2.consultant_assignments.assignment_id"],
        ),
        sa.CheckConstraint("quality_status IN ('VALID','DEGRADED','REJECTED')"),
        sa.CheckConstraint("reconciliation_status IN ('MATCHED','CHANGED','EXCEPTION','PENDING')"),
        schema="resilience_v2",
    )

    op.create_table(
        "consultant_cases",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("case_id", uuid, nullable=False),
        sa.Column("assignment_id", uuid, nullable=False),
        sa.Column("config_id", uuid, nullable=False),
        sa.Column("operating_model", sa.Text, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("change_summary", sa.Text, nullable=False),
        sa.Column("baseline_hash", sa.Text, nullable=False),
        sa.Column("current_hash", sa.Text, nullable=False),
        sa.Column("severity", sa.Integer, nullable=False),
        sa.Column("confidence_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("opened_by", uuid, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "case_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "assignment_id"],
            ["resilience_v2.consultant_assignments.tenant_id", "resilience_v2.consultant_assignments.assignment_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "config_id"],
            ["resilience_v2.enterprise_configuration_versions.tenant_id", "resilience_v2.enterprise_configuration_versions.config_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "opened_by"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("operating_model = 'CONSULTANT'"),
        sa.CheckConstraint("severity BETWEEN 0 AND 10"),
        sa.CheckConstraint("confidence_pct BETWEEN 0 AND 100"),
        sa.CheckConstraint("status IN ('NEW','ASSESSED','PROPOSED','AWAITING_CLIENT_DECISION','APPROVED','REJECTED','RETURNED','IMPLEMENTATION_PENDING','IMPLEMENTED','VALIDATED','CLOSED')"),
        schema="resilience_v2",
    )

    op.create_table(
        "consultant_case_observations",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("case_id", uuid, nullable=False),
        sa.Column("observation_id", uuid, nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "case_id", "observation_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "case_id"],
            ["resilience_v2.consultant_cases.tenant_id", "resilience_v2.consultant_cases.case_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "observation_id"],
            ["resilience_v2.consultant_source_observations.tenant_id", "resilience_v2.consultant_source_observations.observation_id"],
        ),
        schema="resilience_v2",
    )

    op.create_table(
        "consultant_expert_assessments",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("assessment_id", uuid, nullable=False),
        sa.Column("case_id", uuid, nullable=False),
        sa.Column("assessed_by", uuid, nullable=False),
        sa.Column("disposition", sa.Text, nullable=False),
        sa.Column("rationale", sa.Text, nullable=False),
        sa.Column("affected_dimensions", sa.JSON, nullable=False),
        sa.Column("evidence_refs", sa.JSON, nullable=False),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "assessment_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "case_id"],
            ["resilience_v2.consultant_cases.tenant_id", "resilience_v2.consultant_cases.case_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "assessed_by"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("disposition IN ('ACCEPTED','AMENDED','DISMISSED')"),
        schema="resilience_v2",
    )

    op.create_table(
        "consultant_change_proposals",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("proposal_id", uuid, nullable=False),
        sa.Column("case_id", uuid, nullable=False),
        sa.Column("assessment_id", uuid, nullable=False),
        sa.Column("proposed_by", uuid, nullable=False),
        sa.Column("implementation_mode", sa.Text, nullable=False),
        sa.Column("target_dimensions", sa.JSON, nullable=False),
        sa.Column("recommended_change", sa.Text, nullable=False),
        sa.Column("expected_outcome", sa.Text, nullable=False),
        sa.Column("simulation_ref", sa.Text, nullable=False),
        sa.Column("rollback_plan", sa.Text, nullable=False),
        sa.Column("evidence_refs", sa.JSON, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "proposal_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "case_id"],
            ["resilience_v2.consultant_cases.tenant_id", "resilience_v2.consultant_cases.case_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "assessment_id"],
            ["resilience_v2.consultant_expert_assessments.tenant_id", "resilience_v2.consultant_expert_assessments.assessment_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "proposed_by"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("implementation_mode IN ('ADVISORY','ASSISTED','DELEGATED')"),
        sa.CheckConstraint("status IN ('DRAFT','SUBMITTED','APPROVED','REJECTED','RETURNED','IMPLEMENTATION_PENDING','IMPLEMENTED','VALIDATED','WITHDRAWN')"),
        schema="resilience_v2",
    )

    op.create_table(
        "consultant_client_decisions",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("decision_id", uuid, nullable=False),
        sa.Column("proposal_id", uuid, nullable=False),
        sa.Column("decided_by", uuid, nullable=False),
        sa.Column("decision", sa.Text, nullable=False),
        sa.Column("conditions", sa.Text, nullable=False),
        sa.Column("evidence_ref", sa.Text, nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "decision_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "proposal_id"],
            ["resilience_v2.consultant_change_proposals.tenant_id", "resilience_v2.consultant_change_proposals.proposal_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "decided_by"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("decision IN ('APPROVED','REJECTED','RETURNED')"),
        schema="resilience_v2",
    )

    op.create_table(
        "consultant_execution_packages",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("package_id", uuid, nullable=False),
        sa.Column("proposal_id", uuid, nullable=False),
        sa.Column("mandate_id", uuid, nullable=True),
        sa.Column("prepared_by", uuid, nullable=False),
        sa.Column("action_type", sa.Text, nullable=False),
        sa.Column("target_ref", sa.Text, nullable=False),
        sa.Column("payload_hash", sa.Text, nullable=False),
        sa.Column("idempotency_key", sa.Text, nullable=False),
        sa.Column("sandbox_only", sa.Boolean, nullable=False),
        sa.Column("rollback_plan", sa.Text, nullable=False),
        sa.Column("preflight_evidence_ref", sa.Text, nullable=True),
        sa.Column("result_evidence_ref", sa.Text, nullable=True),
        sa.Column("live_actions", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "package_id"),
        sa.UniqueConstraint("tenant_id", "idempotency_key"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "proposal_id"],
            ["resilience_v2.consultant_change_proposals.tenant_id", "resilience_v2.consultant_change_proposals.proposal_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "mandate_id"],
            ["resilience_v2.client_service_mandates.tenant_id", "resilience_v2.client_service_mandates.mandate_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "prepared_by"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("sandbox_only"),
        sa.CheckConstraint("live_actions = 0"),
        sa.CheckConstraint("status IN ('DRAFT','PREFLIGHT_PASSED','EXECUTED','FAILED','CANCELLED')"),
        schema="resilience_v2",
    )

    op.create_table(
        "consultant_case_events",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("event_id", uuid, nullable=False),
        sa.Column("case_id", uuid, nullable=False),
        sa.Column("actor_id", uuid, nullable=False),
        sa.Column("event_type", sa.Text, nullable=False),
        sa.Column("event_payload", sa.JSON, nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "event_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "case_id"],
            ["resilience_v2.consultant_cases.tenant_id", "resilience_v2.consultant_cases.case_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "actor_id"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        schema="resilience_v2",
    )

    op.execute(sa.text("""
        CREATE FUNCTION resilience_v2.guard_m24_append_only()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          RAISE EXCEPTION 'M24_HISTORY_APPEND_ONLY';
        END;
        $$
    """))
    for table in (
        "consultant_source_observations",
        "consultant_case_observations",
        "consultant_expert_assessments",
        "consultant_client_decisions",
        "consultant_case_events",
    ):
        op.execute(sa.text(
            f"CREATE TRIGGER {table}_append_only BEFORE UPDATE OR DELETE ON resilience_v2.{table} "
            "FOR EACH ROW EXECUTE FUNCTION resilience_v2.guard_m24_append_only()"
        ))

    op.execute(sa.text(
        f"REVOKE UPDATE, DELETE ON resilience_v2.consultant_source_observations, "
        f"resilience_v2.consultant_case_observations, resilience_v2.consultant_expert_assessments, "
        f"resilience_v2.consultant_client_decisions, resilience_v2.consultant_case_events "
        f"FROM {profile.runtime_user}"
    ))
    op.execute(sa.text(
        f"REVOKE INSERT, UPDATE, DELETE ON resilience_v2.tenants, resilience_v2.actors, "
        f"resilience_v2.environment_identity, resilience_v2.alembic_version FROM {profile.runtime_user}"
    ))


def downgrade(**kwargs):
    raise RuntimeError("M24 downgrade disabled; rebuild disposable V2 database explicitly")
