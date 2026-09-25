"""M26 governed lessons learned and case intelligence."""

from alembic import op
import sqlalchemy as sa


revision = "m26_0034"
down_revision = "m25_0033"


def upgrade(profile, **kwargs):
    uuid = sa.UUID()

    op.create_table(
        "knowledge_cases",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("knowledge_case_id", uuid, nullable=False),
        sa.Column("case_key", sa.Text, nullable=False),
        sa.Column("source_type", sa.Text, nullable=False),
        sa.Column("source_ref", sa.Text, nullable=False),
        sa.Column("source_case_id", uuid, nullable=True),
        sa.Column("config_id", uuid, nullable=False),
        sa.Column("operating_model", sa.Text, nullable=False),
        sa.Column("sensitivity", sa.Text, nullable=False),
        sa.Column("contains_personal_data", sa.Boolean, nullable=False),
        sa.Column("contains_privileged_information", sa.Boolean, nullable=False),
        sa.Column("retention_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", uuid, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "knowledge_case_id"),
        sa.UniqueConstraint("tenant_id", "case_key"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "source_case_id"],
            ["resilience_v2.consultant_cases.tenant_id", "resilience_v2.consultant_cases.case_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "config_id"],
            ["resilience_v2.enterprise_configuration_versions.tenant_id", "resilience_v2.enterprise_configuration_versions.config_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "created_by"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("source_type IN ('CONSULTANT_CASE','ENTERPRISE_CASE','SIMULATION','INTERVENTION')"),
        sa.CheckConstraint("operating_model IN ('ENTERPRISE','CONSULTANT')"),
        sa.CheckConstraint("sensitivity IN ('INTERNAL','CONFIDENTIAL','RESTRICTED','PRIVILEGED')"),
        sa.CheckConstraint("(source_type='CONSULTANT_CASE' AND source_case_id IS NOT NULL) OR source_type<>'CONSULTANT_CASE'"),
        sa.CheckConstraint("NOT contains_privileged_information OR sensitivity='PRIVILEGED'"),
        sa.CheckConstraint("NOT contains_personal_data OR sensitivity IN ('RESTRICTED','PRIVILEGED')"),
        sa.CheckConstraint("retention_until > created_at"),
        schema="resilience_v2",
    )

    op.create_table(
        "knowledge_lesson_versions",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("version_id", uuid, nullable=False),
        sa.Column("knowledge_case_id", uuid, nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("context", sa.Text, nullable=False),
        sa.Column("issue", sa.Text, nullable=False),
        sa.Column("approach", sa.Text, nullable=False),
        sa.Column("decision_summary", sa.Text, nullable=False),
        sa.Column("intervention", sa.Text, nullable=False),
        sa.Column("outcome", sa.Text, nullable=False),
        sa.Column("what_worked", sa.Text, nullable=False),
        sa.Column("what_failed", sa.Text, nullable=False),
        sa.Column("new_learning", sa.Text, nullable=False),
        sa.Column("applicable_context", sa.Text, nullable=False),
        sa.Column("limitations", sa.Text, nullable=False),
        sa.Column("evidence_refs", sa.JSON, nullable=False),
        sa.Column("author_actor_id", uuid, nullable=False),
        sa.Column("reviewer_actor_id", uuid, nullable=True),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "version_id"),
        sa.UniqueConstraint("tenant_id", "knowledge_case_id", "version"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "knowledge_case_id"],
            ["resilience_v2.knowledge_cases.tenant_id", "resilience_v2.knowledge_cases.knowledge_case_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "author_actor_id"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "reviewer_actor_id"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("version > 0"),
        sa.CheckConstraint("status IN ('DRAFT','IN_REVIEW','APPROVED','RETURNED','REJECTED','PUBLISHED','SUPERSEDED','WITHDRAWN')"),
        schema="resilience_v2",
    )
    op.create_index(
        "uq_knowledge_case_published_version",
        "knowledge_lesson_versions",
        ["tenant_id", "knowledge_case_id"],
        unique=True,
        schema="resilience_v2",
        postgresql_where=sa.text("status='PUBLISHED'"),
    )

    op.create_table(
        "knowledge_lesson_links",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("version_id", uuid, nullable=False),
        sa.Column("link_type", sa.Text, nullable=False),
        sa.Column("link_key", sa.Text, nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "version_id", "link_type", "link_key"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "version_id"],
            ["resilience_v2.knowledge_lesson_versions.tenant_id", "resilience_v2.knowledge_lesson_versions.version_id"],
        ),
        sa.CheckConstraint("link_type IN ('PROCESS','RISK','CONTROL','SCENARIO','CHANGE','EVIDENCE','JURISDICTION')"),
        schema="resilience_v2",
    )

    op.create_table(
        "knowledge_lesson_reviews",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("review_id", uuid, nullable=False),
        sa.Column("version_id", uuid, nullable=False),
        sa.Column("reviewer_actor_id", uuid, nullable=False),
        sa.Column("decision", sa.Text, nullable=False),
        sa.Column("rationale", sa.Text, nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "review_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "version_id"],
            ["resilience_v2.knowledge_lesson_versions.tenant_id", "resilience_v2.knowledge_lesson_versions.version_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "reviewer_actor_id"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("decision IN ('APPROVED','RETURNED','REJECTED')"),
        schema="resilience_v2",
    )

    op.create_table(
        "knowledge_access_grants",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("grant_id", uuid, nullable=False),
        sa.Column("knowledge_case_id", uuid, nullable=False),
        sa.Column("actor_id", uuid, nullable=False),
        sa.Column("granted_by", uuid, nullable=False),
        sa.Column("purpose", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence_ref", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "grant_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "knowledge_case_id"],
            ["resilience_v2.knowledge_cases.tenant_id", "resilience_v2.knowledge_cases.knowledge_case_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "actor_id"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "granted_by"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("actor_id <> granted_by"),
        sa.CheckConstraint("status IN ('ACTIVE','REVOKED','EXPIRED')"),
        sa.CheckConstraint("expires_at > effective_from"),
        schema="resilience_v2",
    )

    op.create_table(
        "knowledge_access_events",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("access_id", uuid, nullable=False),
        sa.Column("version_id", uuid, nullable=False),
        sa.Column("actor_id", uuid, nullable=False),
        sa.Column("purpose", sa.Text, nullable=False),
        sa.Column("accessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "access_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "version_id"],
            ["resilience_v2.knowledge_lesson_versions.tenant_id", "resilience_v2.knowledge_lesson_versions.version_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "actor_id"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        sa.CheckConstraint("purpose IN ('DIRECT','SEARCH','RELATED_CASE','CONSOLE','AUDIT')"),
        schema="resilience_v2",
    )

    op.create_table(
        "knowledge_lesson_feedback",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("feedback_id", uuid, nullable=False),
        sa.Column("version_id", uuid, nullable=False),
        sa.Column("actor_id", uuid, nullable=False),
        sa.Column("relevant", sa.Boolean, nullable=False),
        sa.Column("useful", sa.Boolean, nullable=False),
        sa.Column("comment", sa.Text, nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "feedback_id"),
        sa.UniqueConstraint("tenant_id", "version_id", "actor_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "version_id"],
            ["resilience_v2.knowledge_lesson_versions.tenant_id", "resilience_v2.knowledge_lesson_versions.version_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "actor_id"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        schema="resilience_v2",
    )

    op.create_table(
        "knowledge_case_events",
        sa.Column("tenant_id", uuid, nullable=False),
        sa.Column("event_id", uuid, nullable=False),
        sa.Column("knowledge_case_id", uuid, nullable=False),
        sa.Column("version_id", uuid, nullable=False),
        sa.Column("actor_id", uuid, nullable=False),
        sa.Column("event_type", sa.Text, nullable=False),
        sa.Column("event_payload", sa.JSON, nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "event_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "knowledge_case_id"],
            ["resilience_v2.knowledge_cases.tenant_id", "resilience_v2.knowledge_cases.knowledge_case_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "version_id"],
            ["resilience_v2.knowledge_lesson_versions.tenant_id", "resilience_v2.knowledge_lesson_versions.version_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "actor_id"],
            ["resilience_v2.actors.tenant_id", "resilience_v2.actors.actor_id"],
        ),
        schema="resilience_v2",
    )

    immutable_tables = (
        "knowledge_cases",
        "knowledge_lesson_links",
        "knowledge_lesson_reviews",
        "knowledge_access_events",
        "knowledge_lesson_feedback",
        "knowledge_case_events",
    )
    for table in immutable_tables:
        op.execute(sa.text(
            f"CREATE TRIGGER {table}_append_only BEFORE UPDATE OR DELETE ON resilience_v2.{table} "
            "FOR EACH ROW EXECUTE FUNCTION resilience_v2.guard_m24_append_only()"
        ))
        op.execute(sa.text(f"REVOKE UPDATE, DELETE ON resilience_v2.{table} FROM {profile.runtime_user}"))


def downgrade(**kwargs):
    raise RuntimeError("M26 downgrade disabled; rebuild disposable V2 database explicitly")
