"""M25 authorised sources, information obligations and evidence confidence."""

from alembic import op
import sqlalchemy as sa


revision = "m25_0032"
down_revision = "m24_0031"


def upgrade(profile, **kwargs):
    uuid = sa.UUID()

    op.create_table(
        "authorized_data_sources",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("source_id", uuid, nullable=False),
        sa.Column("assignment_id", uuid, nullable=True),
        sa.Column("operating_model", sa.Text, nullable=False),
        sa.Column("source_key", sa.Text, nullable=False),
        sa.Column("source_type", sa.Text, nullable=False),
        sa.Column("purpose", sa.Text, nullable=False),
        sa.Column("data_scope", sa.JSON, nullable=False),
        sa.Column("collection_schedule", sa.Text, nullable=False),
        sa.Column("owner_actor_id", uuid, nullable=False),
        sa.Column("authorized_by", uuid, nullable=False),
        sa.Column("credential_ref", sa.Text, nullable=False),
        sa.Column("jurisdiction", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence_ref", sa.Text, nullable=False),
        sa.Column("last_successful_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "source_id"),
        sa.UniqueConstraint("tenant_id", "source_key"),
        sa.ForeignKeyConstraint(["tenant_id"], ["resilience_v2.tenants.tenant_id"]),
        sa.ForeignKeyConstraint(
            ["tenant_id", "assignment_id"],
            ["resilience_v2.consultant_assignments.tenant_id", "resilience_v2.consultant_assignments.assignment_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "owner_actor_id"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "authorized_by"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("operating_model IN ('ENTERPRISE','CONSULTANT')"),
        sa.CheckConstraint("source_type IN ('API','SFTP','BANK_FEED','ERP','DOCUMENT_REPOSITORY','CLIENT_AGENT','MANUAL')"),
        sa.CheckConstraint("status IN ('ACTIVE','SUSPENDED','REVOKED','EXPIRED')"),
        sa.CheckConstraint("jurisdiction ~ '^[A-Z]{2}$'"),
        sa.CheckConstraint("expires_at > effective_from"),
        sa.CheckConstraint("(operating_model='CONSULTANT' AND assignment_id IS NOT NULL) OR (operating_model='ENTERPRISE' AND assignment_id IS NULL)"),
        schema="resilience_v2",
    )

    op.create_table(
        "data_source_events",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("event_id", uuid, nullable=False),
        sa.Column("source_id", uuid, nullable=False),
        sa.Column("actor_id", uuid, nullable=False),
        sa.Column("event_type", sa.Text, nullable=False),
        sa.Column("event_payload", sa.JSON, nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "event_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_id"],
            ["resilience_v2.authorized_data_sources.tenant_id", "resilience_v2.authorized_data_sources.source_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "actor_id"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        schema="resilience_v2",
    )

    op.create_table(
        "source_observation_links",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("source_id", uuid, nullable=False),
        sa.Column("observation_id", uuid, nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "source_id", "observation_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_id"],
            ["resilience_v2.authorized_data_sources.tenant_id", "resilience_v2.authorized_data_sources.source_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "observation_id"],
            ["resilience_v2.consultant_source_observations.tenant_id", "resilience_v2.consultant_source_observations.observation_id"],
        ),
        schema="resilience_v2",
    )

    op.create_table(
        "information_obligation_definitions",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("definition_id", uuid, nullable=False),
        sa.Column("config_id", uuid, nullable=False),
        sa.Column("source_id", uuid, nullable=True),
        sa.Column("obligation_key", sa.Text, nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("item_type", sa.Text, nullable=False),
        sa.Column("operating_model", sa.Text, nullable=False),
        sa.Column("responsible_contact_actor_id", uuid, nullable=False),
        sa.Column("internal_owner_actor_id", uuid, nullable=False),
        sa.Column("recurrence_days", sa.Integer, nullable=True),
        sa.Column("reminder_lead_hours", sa.Integer, nullable=False),
        sa.Column("escalation_after_hours", sa.Integer, nullable=False),
        sa.Column("freshness_limit_hours", sa.Integer, nullable=False),
        sa.Column("jurisdiction", sa.Text, nullable=False),
        sa.Column("regulatory_dependency", sa.Boolean, nullable=False),
        sa.Column("exposure_linked", sa.Boolean, nullable=False),
        sa.Column("affected_dimension", sa.Text, nullable=True),
        sa.Column("risk_increment", sa.Integer, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence_ref", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "definition_id"),
        sa.UniqueConstraint("tenant_id", "obligation_key", "version"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "config_id"],
            ["resilience_v2.enterprise_configuration_versions.tenant_id", "resilience_v2.enterprise_configuration_versions.config_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_id"],
            ["resilience_v2.authorized_data_sources.tenant_id", "resilience_v2.authorized_data_sources.source_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "responsible_contact_actor_id"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "internal_owner_actor_id"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("version > 0"),
        sa.CheckConstraint("item_type IN ('DOCUMENT','CONFIRMATION','FILING','DATA_SUBMISSION')"),
        sa.CheckConstraint("operating_model IN ('ENTERPRISE','CONSULTANT')"),
        sa.CheckConstraint("recurrence_days IS NULL OR recurrence_days > 0"),
        sa.CheckConstraint("reminder_lead_hours >= 0 AND escalation_after_hours >= 0 AND freshness_limit_hours > 0"),
        sa.CheckConstraint("jurisdiction ~ '^[A-Z]{2}$'"),
        sa.CheckConstraint("affected_dimension IS NULL OR affected_dimension IN ('CAPITAL','LIQUIDITY','OPERATIONS','REGULATION','MERCHANTS','CORRIDORS')"),
        sa.CheckConstraint("risk_increment BETWEEN 0 AND 10"),
        sa.CheckConstraint("(exposure_linked AND affected_dimension IS NOT NULL AND risk_increment > 0) OR (NOT exposure_linked AND affected_dimension IS NULL AND risk_increment = 0)"),
        sa.CheckConstraint("status IN ('ACTIVE','RETIRED')"),
        schema="resilience_v2",
    )
    op.create_index(
        "uq_information_obligation_definition_active",
        "information_obligation_definitions",
        ["tenant_id", "obligation_key"],
        unique=True,
        schema="resilience_v2",
        postgresql_where=sa.text("status='ACTIVE'"),
    )

    op.create_table(
        "information_obligations",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("obligation_id", uuid, nullable=False),
        sa.Column("definition_id", uuid, nullable=False),
        sa.Column("occurrence", sa.Integer, nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("current_receipt_id", uuid, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "obligation_id"),
        sa.UniqueConstraint("tenant_id", "definition_id", "occurrence"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "definition_id"],
            ["resilience_v2.information_obligation_definitions.tenant_id", "resilience_v2.information_obligation_definitions.definition_id"],
        ),
        sa.CheckConstraint("occurrence > 0"),
        sa.CheckConstraint("status IN ('REQUESTED','RECEIVED','VALIDATED','REJECTED','OVERDUE','WAIVED')"),
        schema="resilience_v2",
    )

    op.create_table(
        "information_receipts",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("receipt_id", uuid, nullable=False),
        sa.Column("obligation_id", uuid, nullable=False),
        sa.Column("submitted_by", uuid, nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence_ref", sa.Text, nullable=False),
        sa.Column("content_hash", sa.Text, nullable=False),
        sa.Column("completeness_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("reliability_pct", sa.Numeric(5, 2), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "receipt_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "obligation_id"],
            ["resilience_v2.information_obligations.tenant_id", "resilience_v2.information_obligations.obligation_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "submitted_by"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("completeness_pct BETWEEN 0 AND 100 AND reliability_pct BETWEEN 0 AND 100"),
        schema="resilience_v2",
    )
    op.create_foreign_key(
        "fk_information_obligation_current_receipt",
        "information_obligations",
        "information_receipts",
        ["tenant_id", "current_receipt_id"],
        ["tenant_id", "receipt_id"],
        source_schema="resilience_v2",
        referent_schema="resilience_v2",
    )

    op.create_table(
        "information_obligation_events",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("event_id", uuid, nullable=False),
        sa.Column("obligation_id", uuid, nullable=False),
        sa.Column("actor_id", uuid, nullable=False),
        sa.Column("event_type", sa.Text, nullable=False),
        sa.Column("event_payload", sa.JSON, nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "event_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "obligation_id"],
            ["resilience_v2.information_obligations.tenant_id", "resilience_v2.information_obligations.obligation_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "actor_id"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("event_type IN ('REQUESTED','RECEIVED','VALIDATED','REJECTED','OVERDUE','WAIVED')"),
        schema="resilience_v2",
    )

    op.create_table(
        "information_communications",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("communication_id", uuid, nullable=False),
        sa.Column("obligation_id", uuid, nullable=False),
        sa.Column("recipient_actor_id", uuid, nullable=False),
        sa.Column("communication_type", sa.Text, nullable=False),
        sa.Column("channel", sa.Text, nullable=False),
        sa.Column("template_key", sa.Text, nullable=False),
        sa.Column("idempotency_key", sa.Text, nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "communication_id"),
        sa.UniqueConstraint("tenant_id", "idempotency_key"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "obligation_id"],
            ["resilience_v2.information_obligations.tenant_id", "resilience_v2.information_obligations.obligation_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "recipient_actor_id"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("communication_type IN ('REMINDER','ESCALATION')"),
        sa.CheckConstraint("channel IN ('IN_APP','EMAIL','TASK')"),
        schema="resilience_v2",
    )

    op.create_table(
        "evidence_confidence_rules",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("rule_id", uuid, nullable=False),
        sa.Column("rule_key", sa.Text, nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("completeness_weight_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("freshness_weight_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("reliability_weight_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("established_threshold_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence_ref", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "rule_id"),
        sa.UniqueConstraint("tenant_id", "rule_key", "version"),
        sa.ForeignKeyConstraint(["tenant_id"], ["resilience_v2.tenants.tenant_id"]),
        sa.CheckConstraint("version > 0"),
        sa.CheckConstraint("completeness_weight_pct + freshness_weight_pct + reliability_weight_pct = 100"),
        sa.CheckConstraint("established_threshold_pct BETWEEN 0 AND 100"),
        sa.CheckConstraint("status IN ('ACTIVE','RETIRED')"),
        schema="resilience_v2",
    )
    op.create_index(
        "uq_evidence_confidence_rule_active",
        "evidence_confidence_rules",
        ["tenant_id", "rule_key"],
        unique=True,
        schema="resilience_v2",
        postgresql_where=sa.text("status='ACTIVE'"),
    )

    op.create_table(
        "evidence_confidence_assessments",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("assessment_id", uuid, nullable=False),
        sa.Column("obligation_id", uuid, nullable=False),
        sa.Column("rule_id", uuid, nullable=False),
        sa.Column("completeness_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("freshness_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("reliability_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("confidence_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("risk_severity_before", sa.Integer, nullable=False),
        sa.Column("risk_severity_after", sa.Integer, nullable=False),
        sa.Column("exposure_affected", sa.Boolean, nullable=False),
        sa.Column("facts_status", sa.Text, nullable=False),
        sa.Column("rationale", sa.Text, nullable=False),
        sa.Column("evidence_refs", sa.JSON, nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "assessment_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "obligation_id"],
            ["resilience_v2.information_obligations.tenant_id", "resilience_v2.information_obligations.obligation_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "rule_id"],
            ["resilience_v2.evidence_confidence_rules.tenant_id", "resilience_v2.evidence_confidence_rules.rule_id"],
        ),
        sa.CheckConstraint("completeness_pct BETWEEN 0 AND 100 AND freshness_pct BETWEEN 0 AND 100 AND reliability_pct BETWEEN 0 AND 100 AND confidence_pct BETWEEN 0 AND 100"),
        sa.CheckConstraint("risk_severity_before BETWEEN 0 AND 10 AND risk_severity_after BETWEEN 0 AND 10"),
        sa.CheckConstraint("facts_status IN ('ESTABLISHED','QUALIFIED','INSUFFICIENT')"),
        schema="resilience_v2",
    )

    immutable = (
        "data_source_events",
        "source_observation_links",
        "information_receipts",
        "information_obligation_events",
        "information_communications",
        "evidence_confidence_assessments",
    )
    for table in immutable:
        op.execute(sa.text(
            f"CREATE TRIGGER {table}_append_only BEFORE UPDATE OR DELETE ON resilience_v2.{table} "
            "FOR EACH ROW EXECUTE FUNCTION resilience_v2.guard_m24_append_only()"
        ))
        op.execute(sa.text(f"REVOKE UPDATE, DELETE ON resilience_v2.{table} FROM {profile.runtime_user}"))


def downgrade(**kwargs):
    raise RuntimeError("M25 downgrade disabled; rebuild disposable V2 database explicitly")
